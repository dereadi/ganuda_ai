# KB: VetAssist Dashboard Empty Claims - Transaction State Bug

**KB ID:** KB-VETASSIST-DASHBOARD-TRANSACTION-FIX-JAN27-2026
**Date:** 2026-01-27
**Severity:** P1 - Data Not Displaying
**Status:** Resolved

---

## Symptom

VetAssist dashboard (GET `/api/v1/dashboard/{veteran_id}`) returns empty `claims: []` even though wizard session data exists in the database.

## Root Cause

### Issue 1: Database Environment Variables Not Loaded

The backend systemd service starts without the `DB_*` environment variables needed by `database_config.py`. Pydantic-settings loads `.env` into the Settings object but NOT into `os.environ`, which `database_config.py` reads directly.

**Fix**: Modified `app/core/database_config.py` to load `.env` at module import time:
```python
from pathlib import Path
from dotenv import load_dotenv

_env_file = Path(__file__).parent.parent.parent / '.env'
if _env_file.exists():
    load_dotenv(_env_file)
```

### Issue 2: PostgreSQL Transaction State Corruption

The dashboard endpoint runs multiple queries in sequence:
1. `SELECT FROM vetassist_scratchpads` - **FAILS** (table doesn't exist)
2. `SELECT FROM vetassist_files` - **FAILS** (table doesn't exist)
3. `SELECT FROM vetassist_wizard_sessions` - **FAILS** with "current transaction is aborted"

When queries 1 or 2 fail in PostgreSQL, the transaction enters an aborted state. Subsequent queries in the same transaction are blocked until `ROLLBACK` is issued.

**Error Message:**
```
current transaction is aborted, commands ignored until end of transaction block
```

**Fix**: Added `conn.rollback()` after each failed query to reset transaction state:
```python
try:
    cur.execute("SELECT ... FROM vetassist_scratchpads ...")
except Exception:
    conn.rollback()  # Reset transaction state for next query

try:
    cur.execute("SELECT ... FROM vetassist_files ...")
except Exception:
    conn.rollback()  # Reset transaction state for next query

try:
    cur.execute("SELECT ... FROM vetassist_wizard_sessions ...")
except Exception:
    conn.rollback()
```

## Files Modified

1. `/ganuda/vetassist/backend/app/core/database_config.py`
   - Added dotenv loading at module import

2. `/ganuda/vetassist/backend/app/api/v1/endpoints/dashboard.py`
   - Added `conn.rollback()` in exception handlers

## Prevention

1. **Create missing tables**: Run schema migrations to create `vetassist_scratchpads` and `vetassist_files` tables
2. **Use autocommit**: Consider setting `conn.autocommit = True` for read-only endpoints
3. **Separate connections**: Use a new connection for each query block

## Testing

```bash
# Verify dashboard returns claims
curl -s http://localhost:8001/api/v1/dashboard/{veteran_id} \
  -H "Authorization: Bearer {token}" | jq '.claims | length'

# Should return count > 0 if wizard sessions exist
```

## Related

- KB-VETASSIST-SPLIT-DATABASE-ARCHITECTURE-JAN27-2026
- Database: zammad_production (wizard sessions)
- Database: triad_federation (auth/users)

---

FOR SEVEN GENERATIONS
