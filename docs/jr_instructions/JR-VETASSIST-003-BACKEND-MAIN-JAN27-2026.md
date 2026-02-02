# JR Instruction: VetAssist Backend Main Entry Point

**JR ID:** JR-VETASSIST-003
**Priority:** P0 (CRITICAL - Dashboard Blocked)
**Created:** 2026-01-27
**Author:** TPM via Claude Code
**Assigned To:** Software Engineer Jr.
**Effort:** Medium

## Problem Statement

VetAssist dashboard is broken because the FastAPI backend doesn't exist. The frontend (Next.js on port 3000) is running, but the API (expected on port 8001) has no entry point.

Current backend structure:
```
/ganuda/vetassist/backend/app/
├── api/v1/endpoints/
│   ├── evidence_analysis.py
│   ├── family.py
│   └── wizard.py
├── core/
│   ├── __init__.py
│   └── database_config.py
└── services/
    └── rag_ingestion.py
```

**Missing:** `main.py` entry point, router setup, requirements.txt, venv

## Required Implementation

### 1. Create Main Entry Point

CREATE: `/ganuda/vetassist/backend/main.py`

```python
"""
VetAssist Backend API
Cherokee AI Federation - Council Approved
"""

import os
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="VetAssist API",
    description="Cherokee AI Federation - Veterans Assistance Platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://vetassist.ganuda.us",
        "http://localhost:3000",
        "http://localhost:8001"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "VetAssist API",
        "version": "1.0.0"
    }

# Import and include routers
try:
    from app.api.v1.endpoints import wizard, family, evidence_analysis

    app.include_router(
        wizard.router,
        prefix="/api/v1/wizard",
        tags=["wizard"]
    )
    app.include_router(
        family.router,
        prefix="/api/v1/family",
        tags=["family"]
    )
    app.include_router(
        evidence_analysis.router,
        prefix="/api/v1/evidence",
        tags=["evidence"]
    )
    logger.info("[VetAssist] All routers loaded successfully")
except ImportError as e:
    logger.warning(f"[VetAssist] Some routers not loaded: {e}")

# Placeholder routes for dashboard
@app.get("/api/auth/session")
async def get_session():
    """Placeholder for auth session."""
    return {"user": None, "authenticated": False}

@app.get("/api/veteran/profile")
async def get_veteran_profile():
    """Placeholder for veteran profile."""
    return {"profile": None, "status": "not_authenticated"}

@app.get("/api/claims")
async def get_claims():
    """Placeholder for claims list."""
    return {"claims": [], "total": 0}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
```

### 2. Fix Router Definitions

Each endpoint file needs a router. Check and add if missing:

MODIFY: `/ganuda/vetassist/backend/app/api/v1/endpoints/wizard.py`

Add at top if missing:
```python
from fastapi import APIRouter

router = APIRouter()
```

Same for `family.py` and `evidence_analysis.py`.

### 3. Create Requirements File

CREATE: `/ganuda/vetassist/backend/requirements.txt`

```
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
psycopg2-binary>=2.9.9
python-dotenv>=1.0.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
```

### 4. Setup Virtual Environment and Install

```bash
cd /ganuda/vetassist/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 5. Create Systemd Service

CREATE: `/etc/systemd/system/vetassist-backend.service`

```ini
[Unit]
Description=VetAssist Backend API
After=network.target postgresql.service

[Service]
Type=simple
User=dereadi
Group=dereadi
WorkingDirectory=/ganuda/vetassist/backend
Environment="PATH=/ganuda/vetassist/backend/venv/bin"
ExecStart=/ganuda/vetassist/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 6. Enable and Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable vetassist-backend
sudo systemctl start vetassist-backend
sudo systemctl status vetassist-backend
```

## Verification

```bash
# 1. Check service is running
systemctl status vetassist-backend

# 2. Test health endpoint locally
curl http://localhost:8001/api/health

# 3. Test through Caddy
curl https://vetassist.ganuda.us/api/health

# 4. Check dashboard loads
curl -s https://vetassist.ganuda.us/dashboard -o /dev/null -w "%{http_code}\n"
```

## Architecture

```
vetassist.ganuda.us
        │
        ▼
   Cloudflare Tunnel
        │
        ▼
      Caddy
        │
    ┌───┴───┐
    │       │
    ▼       ▼
/api/*    /*
    │       │
    ▼       ▼
 :8001    :3000
FastAPI  Next.js
```

---

FOR SEVEN GENERATIONS
