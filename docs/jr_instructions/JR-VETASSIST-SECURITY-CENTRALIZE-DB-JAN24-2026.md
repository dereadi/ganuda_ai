# Jr Instruction: Centralize VetAssist Database Configuration

**Task ID:** VETASSIST-SEC-001
**Priority:** P0 (Critical Security)
**Date:** January 24, 2026

## Objective

Remove hardcoded database credentials from 12 files by creating a centralized configuration module.

## Background

Security audit found password `jawaseatlasers2` hardcoded in multiple files due to copy-paste pattern. This is a security risk and operational burden.

## Part 1: Create Central Config Module

**IMPORTANT**: We have a FreeIPA secrets vault on **Silverfin** that already contains `bluefin_claude_password`. Use the vault as primary source, env vars as fallback.

**Create file:** `/ganuda/vetassist/backend/app/core/database_config.py`

```python
"""
Centralized database configuration for VetAssist.

All database connections MUST use this module.
Never hardcode credentials in endpoint or service files.

Credentials are retrieved from:
1. Silverfin FreeIPA vault (preferred)
2. Environment variables (fallback)
"""
import os
import subprocess
import logging
from functools import lru_cache
from typing import Dict, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


def _get_vault_secret(secret_name: str) -> Optional[str]:
    """
    Retrieve secret from Silverfin FreeIPA vault.

    Requires valid Kerberos ticket or keytab.
    Returns None if vault unavailable (allows env fallback).
    """
    try:
        result = subprocess.run(
            ["/ganuda/scripts/get-vault-secret.sh", secret_name],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            logger.info(f"Retrieved {secret_name} from Silverfin vault")
            return result.stdout.strip()
    except Exception as e:
        logger.warning(f"Vault retrieval failed for {secret_name}: {e}")
    return None


@lru_cache()
def get_db_config() -> Dict[str, Any]:
    """
    Single source of truth for database configuration.

    Credential priority:
    1. Silverfin FreeIPA vault (bluefin_claude_password)
    2. Environment variables (DB_USER, DB_PASSWORD)

    Optional (with defaults):
    - DB_HOST: Database host (default: 192.168.132.222)
    - DB_NAME: Database name (default: triad_federation)
    - DB_PORT: Database port (default: 5432)
    """
    # Try vault first
    vault_password = _get_vault_secret("bluefin_claude_password")

    # Fall back to env vars
    user = os.environ.get("DB_USER", "claude")
    password = vault_password or os.environ.get("DB_PASSWORD")

    if not password:
        raise ValueError(
            "Database password not available. Either:\n"
            "1. Ensure Silverfin vault is accessible (kinit required), or\n"
            "2. Set DB_PASSWORD environment variable.\n"
            "Never hardcode credentials in code."
        )

    return {
        "host": os.environ.get("DB_HOST", "192.168.132.222"),
        "database": os.environ.get("DB_NAME", "triad_federation"),
        "user": user,
        "password": password,
        "port": int(os.environ.get("DB_PORT", "5432")),
    }


def get_connection_string() -> str:
    """Get SQLAlchemy-compatible connection string."""
    cfg = get_db_config()
    return f"postgresql://{cfg['user']}:{cfg['password']}@{cfg['host']}:{cfg['port']}/{cfg['database']}"


def get_db_connection():
    """
    Get a psycopg2 database connection.

    Usage:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        # ... use cursor ...
        cur.close()
        conn.close()
    """
    cfg = get_db_config()
    return psycopg2.connect(
        host=cfg["host"],
        database=cfg["database"],
        user=cfg["user"],
        password=cfg["password"],
        port=cfg["port"]
    )


def get_dict_cursor(conn):
    """Get a RealDictCursor for dictionary-style results."""
    return conn.cursor(cursor_factory=RealDictCursor)
```

## Part 2: Update All Affected Files

For each file, replace the hardcoded DB_CONFIG dict with import from central config.

### 2.1 wizard.py (line 30)

**Before:**
```python
DB_CONFIG = {
    "host": "192.168.132.222",
    "database": "triad_federation",
    "user": "claude",
    "password": "jawaseatlasers2"
}
```

**After:**
```python
from app.core.database_config import get_db_config, get_db_connection, get_dict_cursor

# Remove the DB_CONFIG dict entirely
# Replace psycopg2.connect calls with get_db_connection()
```

### 2.2 Files to Update (same pattern)

Apply identical changes to:

| File | Line | Action |
|------|------|--------|
| `endpoints/wizard.py` | 30 | Remove DB_CONFIG, use get_db_connection() |
| `endpoints/research.py` | 23 | Remove DB_CONFIG, use get_db_connection() |
| `endpoints/export.py` | 22 | Remove DB_CONFIG, use get_db_connection() |
| `endpoints/family.py` | 20 | Remove DB_CONFIG, use get_db_connection() |
| `endpoints/workbench.py` | 21 | Remove DB_CONFIG, use get_db_connection() |
| `endpoints/conditions.py` | 18 | Remove DB_CONFIG, use get_db_connection() |
| `endpoints/evidence_analysis.py` | 20 | Remove DB_CONFIG, use get_db_connection() |
| `endpoints/rag.py` | 106 | Remove inline connect(), use get_db_connection() |
| `services/evidence_service.py` | 18 | Remove DB_CONFIG, use get_db_connection() |
| `services/rag_ingestion.py` | 49 | Remove inline config, use get_db_config() |
| `services/rag_query.py` | 54 | Remove inline config, use get_db_config() |
| `db/database.py` | 16 | Update to use get_db_config() or remove fallback |

### 2.3 Example Transformation

**Before (rag.py lines 102-107):**
```python
conn = psycopg2.connect(
    host='192.168.132.222',
    database='triad_federation',
    user='claude',
    password='jawaseatlasers2'
)
```

**After:**
```python
from app.core.database_config import get_db_connection, get_dict_cursor

conn = get_db_connection()
cur = get_dict_cursor(conn)
```

## Part 3: Update Environment Files

### 3.1 Update .env.example

**File:** `/ganuda/vetassist/backend/.env.example`

```bash
# Database Configuration (REQUIRED)
DB_HOST=192.168.132.222
DB_NAME=triad_federation
DB_USER=claude
DB_PASSWORD=your_password_here
DB_PORT=5432

# Other existing variables...
```

### 3.2 Verify .env has values

Ensure `/ganuda/vetassist/backend/.env` has actual DB_USER and DB_PASSWORD set.

## Part 4: Clean Up Backup Files

Remove all backup files from endpoints directory:

```bash
cd /ganuda/vetassist/backend/app/api/v1/endpoints/
rm -f *.backup_*.py
```

Files to remove:
- auth.py.backup_20260119_211848
- chat.py.backup_20260116
- dashboard.py.backup_20260118_201905
- dashboard.py.backup_20260118_201910
- dashboard.py.backup_20260119_211848
- evidence_analysis.py.backup_20260118_091140

## Testing

After changes:

```bash
cd /ganuda/vetassist/backend

# Ensure env vars are set
export DB_USER=claude
export DB_PASSWORD=jawaseatlasers2

# Test import
python3 -c "from app.core.database_config import get_db_connection; print('Config OK')"

# Run existing tests
pytest tests/ -v

# Test an endpoint
curl http://localhost:8001/health
```

## Verification Checklist

- [ ] database_config.py created and tested
- [ ] All 12 files updated to use central config
- [ ] No grep results for hardcoded password: `grep -r "jawaseatlasers2" app/`
- [ ] .env.example updated
- [ ] .env has required variables
- [ ] Backup files removed
- [ ] Tests pass
- [ ] Service restarts successfully

## Cluster Learning

This task teaches:
- **Centralization**: Single source of truth prevents drift
- **Secure defaults**: Never provide credential fallbacks in code
- **Import discipline**: Always import from core modules

---

**FOR SEVEN GENERATIONS** - The code changes, the principles endure.
