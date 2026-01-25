# Jr Task: VetAssist + Presidio API Integration Layer

**Date**: January 6, 2026
**Priority**: HIGH
**Target Node**: greenfin (192.168.132.224)
**Depends On**: Presidio PII Filter (DEPLOYED), VetAssist PII DB (DEPLOYED)
**Council Vote**: Part of Phase 1 roadmap

## Background

We have two deployed systems that need to be wired together:
1. **Presidio PII Filter** - Running on greenfin:8090, detects/anonymizes PII
2. **VetAssist PII DB** - Running on bluefin, stores veteran data with encrypted PII

This Jr task creates the API layer that:
- Accepts veteran queries with potential PII
- Runs them through Presidio to anonymize
- Queries VetAssist DB for non-PII context
- Returns safe responses to AI agents

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      VETASSIST API FLOW                                  │
│                                                                         │
│  ┌──────────┐    ┌─────────────────┐    ┌──────────────┐               │
│  │ AI Agent │───▶│ VetAssist API   │───▶│   Presidio   │               │
│  │ (Triad)  │    │ (greenfin:8091) │    │ (greenfin:8090)              │
│  └──────────┘    └────────┬────────┘    └──────────────┘               │
│                           │                                             │
│                           │ Anonymized query                            │
│                           ▼                                             │
│                    ┌─────────────────┐                                  │
│                    │  VetAssist DB   │                                  │
│                    │ (bluefin:5432)  │                                  │
│                    │ - Non-PII view  │                                  │
│                    └────────┬────────┘                                  │
│                             │                                           │
│                             ▼                                           │
│                    ┌─────────────────┐                                  │
│                    │ Safe Response   │                                  │
│                    │ (No raw PII)    │                                  │
│                    └─────────────────┘                                  │
└─────────────────────────────────────────────────────────────────────────┘
```

## Task 1: Create veteran_context View

On bluefin, create a view that exposes only non-PII data:

```sql
-- Connect to vetassist_pii on bluefin
-- PGPASSWORD='jawaseatlasers2' psql -h 192.168.132.222 -U claude -d vetassist_pii

CREATE OR REPLACE VIEW veteran_context AS
SELECT
    vp.veteran_id,
    vp.branch_of_service,
    vp.discharge_status,
    vp.service_start_date,
    vp.service_end_date,
    vp.is_active,
    vp.created_at,
    -- Aggregated case info (no PII)
    (SELECT COUNT(*) FROM case_notes cn WHERE cn.veteran_id = vp.veteran_id) as total_cases,
    (SELECT MAX(created_at) FROM case_notes cn WHERE cn.veteran_id = vp.veteran_id) as last_interaction,
    -- Benefits summary (no amounts - those are encrypted)
    (SELECT array_agg(DISTINCT benefit_type) FROM benefits_tracking bt
     WHERE bt.veteran_id = vp.veteran_id AND bt.status = 'active') as active_benefits,
    (SELECT COUNT(*) FROM benefits_tracking bt
     WHERE bt.veteran_id = vp.veteran_id AND bt.status = 'pending') as pending_benefits
FROM veteran_profiles vp
WHERE vp.is_active = true;

-- Grant access to the API role
GRANT SELECT ON veteran_context TO claude;

-- Verify
SELECT * FROM veteran_context LIMIT 5;
```

## Task 2: Create VetAssist API Service

Create `/ganuda/services/vetassist_api/vetassist_api.py` on greenfin:

```python
#!/usr/bin/env python3
"""
Cherokee AI Federation - VetAssist API Service
Provides PII-safe veteran data access for AI agents.

Integrates:
- Presidio PII Filter (greenfin:8090) for anonymization
- VetAssist PII DB (bluefin:5432) for veteran data
"""

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import httpx
import asyncpg
import hashlib
from datetime import datetime
import os

app = FastAPI(
    title="VetAssist API",
    description="PII-safe veteran data access for Cherokee AI Federation",
    version="1.0.0"
)

# Configuration
PRESIDIO_URL = os.getenv("PRESIDIO_URL", "http://localhost:8090")
DB_HOST = os.getenv("DB_HOST", "192.168.132.222")
DB_NAME = os.getenv("DB_NAME", "vetassist_pii")
DB_USER = os.getenv("DB_USER", "claude")
DB_PASS = os.getenv("DB_PASS", "jawaseatlasers2")

# Database connection pool
db_pool = None


class QueryRequest(BaseModel):
    """Request to query veteran data."""
    veteran_id: str
    query_text: str
    requesting_agent: str = "unknown"
    session_id: Optional[str] = None


class QueryResponse(BaseModel):
    """Response with anonymized data."""
    veteran_id: str
    anonymized_query: str
    context: Dict[str, Any]
    pii_detected: int
    session_id: str
    audit_id: int


class VeteranContext(BaseModel):
    """Non-PII veteran context for AI agents."""
    veteran_id: str
    branch_of_service: Optional[str]
    discharge_status: Optional[str]
    service_start_date: Optional[str]
    service_end_date: Optional[str]
    total_cases: int
    last_interaction: Optional[str]
    active_benefits: Optional[List[str]]
    pending_benefits: int


@app.on_event("startup")
async def startup():
    """Initialize database connection pool."""
    global db_pool
    db_pool = await asyncpg.create_pool(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        min_size=2,
        max_size=10
    )


@app.on_event("shutdown")
async def shutdown():
    """Close database connection pool."""
    global db_pool
    if db_pool:
        await db_pool.close()


async def anonymize_text(text: str, veteran_id: str) -> Dict:
    """Send text to Presidio for PII anonymization."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PRESIDIO_URL}/analyze",
            json={"text": text, "veteran_id": veteran_id},
            timeout=10.0
        )
        if response.status_code != 200:
            raise HTTPException(status_code=502, detail="Presidio service error")
        return response.json()


async def log_access(veteran_id: str, agent: str, action: str, details: Dict) -> int:
    """Log access to audit table."""
    async with db_pool.acquire() as conn:
        audit_id = await conn.fetchval("""
            INSERT INTO audit_log (table_name, record_id, action, actor, new_values)
            VALUES ('veteran_context',
                    (SELECT id FROM veteran_profiles WHERE veteran_id = $1),
                    $2, $3, $4)
            RETURNING id
        """, veteran_id, action, agent, details)
        return audit_id


@app.post("/query", response_model=QueryResponse)
async def query_veteran(request: QueryRequest):
    """
    Query veteran data with automatic PII anonymization.

    1. Anonymizes the query text via Presidio
    2. Fetches non-PII context from VetAssist DB
    3. Logs access for audit trail
    4. Returns safe response
    """
    # Generate session ID if not provided
    session_id = request.session_id or hashlib.sha256(
        f"{datetime.now().isoformat()}:{request.veteran_id}".encode()
    ).hexdigest()[:16]

    # Step 1: Anonymize query text
    presidio_result = await anonymize_text(request.query_text, request.veteran_id)

    # Step 2: Get veteran context (non-PII only)
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT * FROM veteran_context WHERE veteran_id = $1
        """, request.veteran_id)

        if not row:
            raise HTTPException(status_code=404, detail="Veteran not found")

        context = dict(row)
        # Convert dates to strings for JSON
        for key in ['service_start_date', 'service_end_date', 'last_interaction']:
            if context.get(key):
                context[key] = str(context[key])

    # Step 3: Log access
    audit_id = await log_access(
        request.veteran_id,
        request.requesting_agent,
        "QUERY",
        {
            "session_id": session_id,
            "pii_detected": len(presidio_result.get("entities", [])),
            "query_anonymized": True
        }
    )

    return QueryResponse(
        veteran_id=request.veteran_id,
        anonymized_query=presidio_result.get("anonymized_text", request.query_text),
        context=context,
        pii_detected=len(presidio_result.get("entities", [])),
        session_id=session_id,
        audit_id=audit_id
    )


@app.get("/veteran/{veteran_id}", response_model=VeteranContext)
async def get_veteran_context(veteran_id: str, requesting_agent: str = "unknown"):
    """
    Get non-PII context for a veteran.
    Use this when you just need veteran metadata without processing a query.
    """
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT * FROM veteran_context WHERE veteran_id = $1
        """, veteran_id)

        if not row:
            raise HTTPException(status_code=404, detail="Veteran not found")

        context = dict(row)

        # Log access
        await log_access(veteran_id, requesting_agent, "GET_CONTEXT", {})

        # Convert dates to strings
        for key in ['service_start_date', 'service_end_date', 'last_interaction']:
            if context.get(key):
                context[key] = str(context[key])

        return VeteranContext(**context)


@app.get("/health")
async def health():
    """Health check endpoint."""
    # Check Presidio
    presidio_healthy = False
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{PRESIDIO_URL}/health", timeout=5.0)
            presidio_healthy = resp.status_code == 200
    except:
        pass

    # Check DB
    db_healthy = False
    try:
        async with db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
            db_healthy = True
    except:
        pass

    return {
        "status": "healthy" if (presidio_healthy and db_healthy) else "degraded",
        "service": "VetAssist API",
        "version": "1.0.0",
        "dependencies": {
            "presidio": "healthy" if presidio_healthy else "unhealthy",
            "database": "healthy" if db_healthy else "unhealthy"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8091)
```

## Task 3: Create Requirements File

Create `/ganuda/services/vetassist_api/requirements.txt`:

```
fastapi>=0.100.0
uvicorn>=0.23.0
httpx>=0.24.0
asyncpg>=0.28.0
pydantic>=2.0.0
```

## Task 4: Create Systemd Service

Create `/etc/systemd/system/vetassist-api.service` on greenfin:

```ini
[Unit]
Description=Cherokee AI VetAssist API Service
After=network.target presidio-filter.service
Requires=presidio-filter.service

[Service]
Type=simple
User=dereadi
WorkingDirectory=/ganuda/services/vetassist_api
Environment="PATH=/ganuda/services/vetassist_api/venv/bin"
Environment="PRESIDIO_URL=http://localhost:8090"
Environment="DB_HOST=192.168.132.222"
Environment="DB_NAME=vetassist_pii"
Environment="DB_USER=claude"
Environment="DB_PASS=jawaseatlasers2"
ExecStart=/ganuda/services/vetassist_api/venv/bin/python vetassist_api.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Task 5: Deploy Commands

```bash
# SSH to greenfin
ssh dereadi@192.168.132.224

# Create directory
sudo mkdir -p /ganuda/services/vetassist_api
sudo chown dereadi:dereadi /ganuda/services/vetassist_api
cd /ganuda/services/vetassist_api

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Copy files (vetassist_api.py and requirements.txt)
# ... or use scp from tpm-macbook

# Install dependencies
pip install -r requirements.txt

# Create systemd service
sudo cp vetassist-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable vetassist-api
sudo systemctl start vetassist-api

# Verify
curl http://localhost:8091/health
```

## Task 6: Create DB View (if not exists)

On bluefin, ensure the view exists:

```bash
PGPASSWORD='jawaseatlasers2' psql -h 192.168.132.222 -U claude -d vetassist_pii
```

Then run the CREATE VIEW from Task 1.

## Task 7: Test Integration

```bash
# Test health
curl http://192.168.132.224:8091/health

# Test query with PII (should be anonymized)
curl -X POST http://192.168.132.224:8091/query \
  -H "Content-Type: application/json" \
  -d '{
    "veteran_id": "VET001",
    "query_text": "My SSN is 123-45-6789 and I need help with benefits",
    "requesting_agent": "IT_Chief"
  }'

# Test direct context fetch
curl "http://192.168.132.224:8091/veteran/VET001?requesting_agent=IT_Chief"
```

## Acceptance Criteria

- [ ] veteran_context view created in vetassist_pii database
- [ ] vetassist_api.py deployed on greenfin
- [ ] Service running on port 8091
- [ ] /health endpoint shows both presidio and database healthy
- [ ] /query endpoint anonymizes PII before processing
- [ ] /veteran/{id} endpoint returns non-PII context
- [ ] All access logged to audit_log table
- [ ] Systemd service auto-starts on boot

## Security Notes

- AI agents NEVER receive raw PII
- All queries logged with agent name and session ID
- Database credentials in environment variables (not code)
- Service only accessible from internal network
- Presidio must be healthy for queries to work

## For Seven Generations
