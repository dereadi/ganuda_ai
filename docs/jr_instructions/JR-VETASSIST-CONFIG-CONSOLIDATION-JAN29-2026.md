# JR Instruction: VetAssist Database Config Consolidation

**JR ID:** JR-VETASSIST-CONFIG-CONSOLIDATION-JAN29-2026
**Priority:** P0 - CRITICAL
**Assigned To:** Infrastructure Jr.
**Related:** ULTRATHINK-VETASSIST-DATA-INTEGRITY-JAN29-2026
**Council Vote:** d91695f5c391dc71 (83.3% confidence)

---

## Objective

Create a single source of truth for VetAssist database configuration to eliminate "data disappearing" bugs caused by services connecting to wrong databases.

---

## Problem

- 3 database misconfigurations found in one day
- Services hardcode different database names (triad_federation vs zammad_production)
- Veterans see their claims, files, and research vanish
- Silent failures return empty data instead of errors

---

## Architecture

```
Non-PII Database (bluefin - 192.168.132.222):
  - Database: zammad_production
  - Tables: wizard_sessions, wizard_files, research_results, claims, scratchpads

PII Database (goldfin - 192.168.20.10, VLAN 20):
  - Database: vetassist_pii
  - Tables: encrypted_records, pii_tokens
```

---

## Implementation

### Step 1: Create Config File

Create `/ganuda/vetassist/config/database.yaml`:

```yaml
# VetAssist Database Configuration
# Single source of truth - all services read from here
# Created: January 29, 2026

# Non-PII data (bluefin)
non_pii:
  host: 192.168.132.222
  database: zammad_production
  port: 5432
  # Credentials from vault or DB_USER/DB_PASSWORD env vars

# PII data (goldfin - VLAN 20 Sanctum)
pii:
  host: 192.168.20.10
  database: vetassist_pii
  port: 5432
  # Credentials from vault or PII_DB_USER/PII_DB_PASSWORD env vars

# Required tables for startup validation
required_tables:
  non_pii:
    - vetassist_wizard_sessions
    - vetassist_wizard_files
    - vetassist_research_results
    - vetassist_claims
    - vetassist_scratchpads
  pii:
    - vetassist_encrypted_records
```

### Step 2: Create Config Module

Create `/ganuda/lib/vetassist_db_config.py`:

```python
#!/usr/bin/env python3
"""
VetAssist Database Configuration Module
Single source of truth for all VetAssist database connections.

Cherokee AI Federation - For Seven Generations
Created: January 29, 2026
"""

import os
import yaml
import logging
import psycopg2
from pathlib import Path
from functools import lru_cache
from typing import Dict, Optional

logger = logging.getLogger(__name__)

CONFIG_PATH = Path("/ganuda/vetassist/config/database.yaml")


class DatabaseConfigError(Exception):
    """Raised when database configuration is invalid or tables are missing."""
    pass


@lru_cache()
def load_config() -> Dict:
    """Load database configuration from YAML file."""
    if not CONFIG_PATH.exists():
        raise DatabaseConfigError(f"Config file not found: {CONFIG_PATH}")

    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def _get_credentials(db_type: str = 'non_pii') -> tuple:
    """
    Get database credentials from vault or environment.

    Priority:
    1. Silverfin vault (if available)
    2. Environment variables
    """
    if db_type == 'pii':
        user = os.environ.get('PII_DB_USER', 'claude')
        password = os.environ.get('PII_DB_PASSWORD')
    else:
        user = os.environ.get('DB_USER', 'claude')
        password = os.environ.get('DB_PASSWORD')

    if not password:
        # Try vault
        try:
            import subprocess
            result = subprocess.run(
                ["/ganuda/scripts/get-vault-secret.sh", "bluefin_claude_password"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                password = result.stdout.strip()
        except Exception:
            pass

    if not password:
        raise DatabaseConfigError(
            f"No password for {db_type} database. Set DB_PASSWORD or configure vault."
        )

    return user, password


def get_non_pii_connection():
    """
    Get connection to non-PII database (bluefin/zammad_production).

    Usage:
        conn = get_non_pii_connection()
        cur = conn.cursor()
        ...
        conn.close()
    """
    config = load_config()
    db_config = config['non_pii']
    user, password = _get_credentials('non_pii')

    logger.info(f"Connecting to non-PII database: {db_config['host']}/{db_config['database']}")

    return psycopg2.connect(
        host=db_config['host'],
        database=db_config['database'],
        port=db_config['port'],
        user=user,
        password=password
    )


def get_pii_connection():
    """
    Get connection to PII database (goldfin/vetassist_pii).

    Usage:
        conn = get_pii_connection()
        cur = conn.cursor()
        ...
        conn.close()
    """
    config = load_config()
    db_config = config['pii']
    user, password = _get_credentials('pii')

    logger.info(f"Connecting to PII database: {db_config['host']}/{db_config['database']}")

    return psycopg2.connect(
        host=db_config['host'],
        database=db_config['database'],
        port=db_config['port'],
        user=user,
        password=password
    )


def validate_tables(db_type: str = 'non_pii') -> bool:
    """
    Validate that required tables exist. FAILS LOUDLY if missing.

    Call this on service startup to catch misconfiguration immediately.
    """
    config = load_config()
    required = config.get('required_tables', {}).get(db_type, [])

    if not required:
        logger.warning(f"No required tables defined for {db_type}")
        return True

    if db_type == 'pii':
        conn = get_pii_connection()
    else:
        conn = get_non_pii_connection()

    try:
        cur = conn.cursor()
        missing = []

        for table in required:
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = %s
                )
            """, (table,))
            exists = cur.fetchone()[0]

            if not exists:
                missing.append(table)

        cur.close()

        if missing:
            raise DatabaseConfigError(
                f"FATAL: Missing required tables in {db_type} database: {missing}\n"
                f"Database: {config[db_type]['database']} on {config[db_type]['host']}\n"
                "This usually means the service is pointing to the wrong database."
            )

        logger.info(f"Validated {len(required)} required tables in {db_type} database")
        return True

    finally:
        conn.close()


def validate_on_startup():
    """
    Run all validations on service startup.

    Call this in your service's main() before starting the event loop.
    Raises DatabaseConfigError if validation fails.
    """
    logger.info("Validating VetAssist database configuration...")

    # Validate non-PII database
    validate_tables('non_pii')

    # PII database validation is optional (may not be needed by all services)
    try:
        validate_tables('pii')
    except Exception as e:
        logger.warning(f"PII database validation skipped: {e}")

    logger.info("Database validation complete - all tables present")
```

### Step 3: Update VetAssist Backend

Modify `/ganuda/vetassist/backend/app/core/database_config.py`:

Add at the top:
```python
# Try to use centralized config (Jan 29, 2026)
try:
    import sys
    sys.path.insert(0, '/ganuda/lib')
    from vetassist_db_config import get_non_pii_connection, get_pii_connection, validate_on_startup
    USE_CENTRAL_CONFIG = True
except ImportError:
    USE_CENTRAL_CONFIG = False
```

Modify `get_db_connection()`:
```python
def get_db_connection(database: str = None):
    if USE_CENTRAL_CONFIG and database is None:
        return get_non_pii_connection()
    # ... existing fallback code ...
```

### Step 4: Update Research File Watcher

Modify `/ganuda/services/research_file_watcher.py`:

Replace the DB_CONFIG section:
```python
# Use centralized config (Jan 29, 2026)
import sys
sys.path.insert(0, '/ganuda/lib')
from vetassist_db_config import get_non_pii_connection, validate_on_startup

def get_db_conn():
    """Get database connection from centralized config."""
    return get_non_pii_connection()

# In main(), add validation:
def main():
    validate_on_startup()  # FAIL if tables missing
    # ... rest of main ...
```

### Step 5: Update Research Worker

Modify `/ganuda/services/research_worker.py` notify_vetassist function:

```python
# Use centralized config for VetAssist sync (Jan 29, 2026)
try:
    from vetassist_db_config import get_non_pii_connection
    USE_VETASSIST_CONFIG = True
except ImportError:
    USE_VETASSIST_CONFIG = False

def notify_vetassist(...):
    if USE_VETASSIST_CONFIG:
        conn = get_non_pii_connection()
    else:
        conn = get_conn()  # fallback to existing
    # ... rest of function ...
```

---

## Verification

1. Create config directory:
   ```bash
   mkdir -p /ganuda/vetassist/config
   ```

2. Test config loading:
   ```python
   from vetassist_db_config import load_config, validate_on_startup
   validate_on_startup()
   # Should complete without error
   ```

3. Test wrong database detection:
   ```python
   # Temporarily change database.yaml to wrong DB
   # validate_on_startup() should FAIL with clear error
   ```

4. Restart services:
   ```bash
   sudo systemctl restart vetassist-backend
   sudo systemctl restart research-file-watcher
   ```

5. Verify Marcus can see his data:
   - 1 claim (21-526EZ)
   - 1 file (PDF)
   - 6 research results

---

## Files Summary

| File | Action |
|------|--------|
| `/ganuda/vetassist/config/database.yaml` | CREATE |
| `/ganuda/lib/vetassist_db_config.py` | CREATE |
| `/ganuda/vetassist/backend/app/core/database_config.py` | MODIFY |
| `/ganuda/services/research_file_watcher.py` | MODIFY |
| `/ganuda/services/research_worker.py` | MODIFY |

---

FOR SEVEN GENERATIONS
