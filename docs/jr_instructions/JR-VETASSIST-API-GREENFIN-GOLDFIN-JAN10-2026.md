# Jr Instruction: VetAssist API Integration (greenfin → goldfin)

**Date**: January 10, 2026
**Priority**: HIGH
**Target Nodes**: greenfin (API), goldfin (Database)
**TPM**: Flying Squirrel (dereadi)

## Background

VetAssist needs a secure API that:
1. Receives queries containing veteran PII
2. Anonymizes PII via Presidio before any processing
3. Fetches non-PII context from goldfin database
4. Returns safe response with veteran context

## Architecture

```
Client Request (with PII)
        ↓
   greenfin:8091 (VetAssist API)
        ↓
   greenfin:8090 (Presidio) → Anonymize
        ↓
   goldfin:5432 (vetassist_pii DB) → Fetch context
        ↓
   Response (anonymized + context)
```

## Prerequisites

- [x] Presidio running on greenfin:8090
- [x] PostgreSQL on goldfin:5432 with vetassist_pii database
- [x] greenfin can reach goldfin (VLAN 20 working)
- [x] Database credentials in `/ganuda/config/secrets/vetassist_db.conf`

## Network Verification

```bash
# From greenfin, verify goldfin connectivity
ping 192.168.20.10
psql -h 192.168.20.10 -U vetassist -d vetassist_pii -c "SELECT 1;"
```

## API Design (FastAPI - MANDATORY)

**IMPORTANT**: Per KB article FASTAPI_STANDARDIZATION.md, all new HTTP services MUST use FastAPI.

### File Location

```
/ganuda/services/vetassist_api/
├── vetassist_api.py      # Main FastAPI application
├── requirements.txt      # Dependencies
├── config.py             # Configuration
└── models.py             # Pydantic models
```

### Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check (Presidio + DB) |
| `/v1/query` | POST | Anonymize query + get context |
| `/v1/veteran/{id}` | GET | Direct non-PII context fetch |

### Request/Response Models

```python
from pydantic import BaseModel
from typing import Optional, List

class QueryRequest(BaseModel):
    query: str
    veteran_id: Optional[str] = None

class AnonymizedQuery(BaseModel):
    original_query: str
    anonymized_query: str
    entities_found: List[dict]

class VeteranContext(BaseModel):
    veteran_id: str
    branch_of_service: Optional[str]
    discharge_status: Optional[str]
    service_start: Optional[str]
    service_end: Optional[str]
    active_benefits: List[str]
    pending_benefits: int

class QueryResponse(BaseModel):
    anonymized: AnonymizedQuery
    context: Optional[VeteranContext]
    request_id: str
```

### Core Implementation

```python
from fastapi import FastAPI, HTTPException, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address
import httpx
import asyncpg
import uuid
from datetime import datetime

app = FastAPI(title="VetAssist API", version="1.0.0")
limiter = Limiter(key_func=get_remote_address)

PRESIDIO_URL = "http://localhost:8090"
DB_HOST = "192.168.20.10"
DB_NAME = "vetassist_pii"
DB_USER = "vetassist"
# Load password from /ganuda/config/secrets/vetassist_db.conf

class PIISafetyError(Exception):
    """Raised when PII safety cannot be guaranteed - FAIL CLOSED"""
    pass

async def anonymize_text(text: str) -> dict:
    """Send text to Presidio for anonymization - FAIL CLOSED on error"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Analyze
            analyze_response = await client.post(
                f"{PRESIDIO_URL}/analyze",
                json={"text": text, "language": "en"}
            )
            if analyze_response.status_code != 200:
                raise PIISafetyError("Presidio analyze failed")

            entities = analyze_response.json()

            # Anonymize
            anonymize_response = await client.post(
                f"{PRESIDIO_URL}/anonymize",
                json={"text": text, "analyzer_results": entities}
            )
            if anonymize_response.status_code != 200:
                raise PIISafetyError("Presidio anonymize failed")

            result = anonymize_response.json()
            return {
                "original": text,
                "anonymized": result["text"],
                "entities": entities
            }
    except httpx.TimeoutException:
        raise PIISafetyError("Presidio timeout - cannot guarantee PII safety")
    except Exception as e:
        raise PIISafetyError(f"Presidio error: {str(e)}")

async def get_veteran_context(veteran_id: str, pool) -> dict:
    """Fetch non-PII veteran context from goldfin"""
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT
                veteran_id,
                branch_of_service,
                discharge_status,
                service_start_date,
                service_end_date,
                is_active
            FROM pii.veteran_profiles
            WHERE veteran_id = $1
        """, veteran_id)

        if not row:
            return None

        # Get benefits
        benefits = await conn.fetch("""
            SELECT benefit_type, status
            FROM pii.benefits_tracking
            WHERE veteran_id = $1
        """, veteran_id)

        return {
            "veteran_id": row["veteran_id"],
            "branch_of_service": row["branch_of_service"],
            "discharge_status": row["discharge_status"],
            "service_start": str(row["service_start_date"]) if row["service_start_date"] else None,
            "service_end": str(row["service_end_date"]) if row["service_end_date"] else None,
            "active_benefits": [b["benefit_type"] for b in benefits if b["status"] == "active"],
            "pending_benefits": len([b for b in benefits if b["status"] == "pending"])
        }

async def log_access(pool, request_id: str, action: str, veteran_id: str = None):
    """Log all access to audit table"""
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO pii.audit_log (request_id, action, veteran_id, timestamp, actor)
            VALUES ($1, $2, $3, $4, 'vetassist_api')
        """, request_id, action, veteran_id, datetime.utcnow())

@app.post("/v1/query")
@limiter.limit("30/minute")
async def query_veteran(request: QueryRequest):
    request_id = str(uuid.uuid4())

    # ALWAYS anonymize first - FAIL CLOSED
    try:
        anonymized = await anonymize_text(request.query)
    except PIISafetyError as e:
        # Log the failure but don't expose details
        await log_access(app.state.pool, request_id, f"BLOCKED: {str(e)}")
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")

    # Log the anonymized query
    await log_access(app.state.pool, request_id, "query", request.veteran_id)

    # Fetch context if veteran_id provided
    context = None
    if request.veteran_id:
        context = await get_veteran_context(request.veteran_id, app.state.pool)

    return {
        "anonymized": anonymized,
        "context": context,
        "request_id": request_id
    }

@app.get("/health")
async def health_check():
    # Check Presidio
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{PRESIDIO_URL}/health")
            presidio_ok = resp.status_code == 200
    except:
        presidio_ok = False

    # Check DB
    try:
        async with app.state.pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
            db_ok = True
    except:
        db_ok = False

    status = "healthy" if (presidio_ok and db_ok) else "degraded"
    return {
        "status": status,
        "presidio": "up" if presidio_ok else "down",
        "database": "up" if db_ok else "down"
    }
```

## Security Requirements

### FAIL-CLOSED Pattern

```python
# CORRECT - Fail closed
try:
    result = await anonymize_text(query)
except PIISafetyError:
    raise HTTPException(503, "Service unavailable")  # Block request

# WRONG - Fail open (NEVER DO THIS)
try:
    result = await anonymize_text(query)
except:
    result = {"anonymized": query}  # DANGEROUS - passes through PII
```

### Rate Limiting

```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@app.post("/v1/query")
@limiter.limit("30/minute")
async def query_veteran(request: QueryRequest):
    ...
```

### Audit Logging

ALL access must be logged to `pii.audit_log`:
- Request ID
- Action (query, fetch, blocked)
- Veteran ID (if applicable)
- Timestamp
- Actor (vetassist_api)

## Database Schema (already exists on goldfin)

```sql
-- pii.veteran_profiles
-- pii.benefits_tracking
-- pii.audit_log
```

## Deployment

### Requirements.txt

```
fastapi>=0.104.0
uvicorn>=0.24.0
asyncpg>=0.29.0
httpx>=0.25.0
slowapi>=0.1.9
pydantic>=2.5.0
```

### Systemd Service

```ini
[Unit]
Description=VetAssist API
After=network.target

[Service]
Type=simple
User=dereadi
WorkingDirectory=/ganuda/services/vetassist_api
ExecStart=/ganuda/services/vetassist_api/venv/bin/uvicorn vetassist_api:app --host 0.0.0.0 --port 8091
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Start Commands

```bash
cd /ganuda/services/vetassist_api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn vetassist_api:app --host 0.0.0.0 --port 8091
```

## Testing

```bash
# Health check
curl http://192.168.132.224:8091/health

# Query with PII (should be anonymized)
curl -X POST http://192.168.132.224:8091/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "My name is John Smith and my SSN is 123-45-6789", "veteran_id": "VET001"}'

# Expected response:
# {
#   "anonymized": {
#     "original": "My name is John Smith and my SSN is 123-45-6789",
#     "anonymized": "My name is <PERSON> and my SSN is <US_SSN>",
#     "entities": [...]
#   },
#   "context": {
#     "veteran_id": "VET001",
#     "branch_of_service": "Army",
#     ...
#   },
#   "request_id": "uuid..."
# }
```

## TPM Concern Flag

**NOTE**: TPM has a "nagging feeling" about this pipeline (logged temp 92). Before production deployment:
1. Review with Council (ULTRATHINK)
2. Verify token mapping persistence
3. Confirm audit trail completeness
4. Test Presidio failure scenarios

## Related Documentation

- FastAPI Standard: /Users/Shared/ganuda/docs/kb/FASTAPI_STANDARDIZATION.md
- Presidio: greenfin:8090
- goldfin DB: /ganuda/config/secrets/vetassist_db.conf
- TPM Concern: thermal_memory_archive (tags: concern, pii)

---

For Seven Generations.
