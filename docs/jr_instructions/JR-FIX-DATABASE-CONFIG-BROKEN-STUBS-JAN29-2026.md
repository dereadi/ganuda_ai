# JR Instruction: Fix database_config.py Broken Function Stubs

**JR ID:** JR-FIX-DATABASE-CONFIG-BROKEN-STUBS-JAN29-2026
**Priority:** P0 - CRITICAL
**Assigned To:** Software Engineer Jr.
**Related:** ULTRATHINK-VETASSIST-DATABASE-CONFIG-DEBT-JAN29-2026
**Council Vote:** 3c944bed582ce3d3 (88.3% confidence)

---

## Objective

Remove broken function stubs from `/ganuda/vetassist/backend/app/core/database_config.py` that are causing `get_db_connection()` to return `None`.

---

## Problem

Lines 154-174 contain incomplete function definitions that override the working `get_db_connection()` function:

```python
# These lines are BROKEN - they return None when USE_CENTRAL_CONFIG is False
def get_db_connection(database: str = None):
    if USE_CENTRAL_CONFIG and database is None:
        return get_non_pii_connection()
    # ... existing fallback code ...   <-- THIS IS A COMMENT, NOT CODE!
```

Since `/ganuda/lib/vetassist_db_config.py` doesn't exist yet, `USE_CENTRAL_CONFIG = False`, and the function falls through without returning anything.

---

## Implementation

### Step 1: Read the file
```bash
cat -n /ganuda/vetassist/backend/app/core/database_config.py | tail -30
```

### Step 2: Delete lines 154-174

Delete the following content from the file (lines 154 through end of file):

```python
# Try to use centralized config (Jan 29, 2026)
try:
    import sys
    sys.path.insert(0, '/ganuda/lib')
    from vetassist_db_config import get_non_pii_connection, get_pii_connection, validate_on_startup
    USE_CENTRAL_CONFIG = True
except ImportError:
    USE_CENTRAL_CONFIG = False


def get_db_connection(database: str = None):
    if USE_CENTRAL_CONFIG and database is None:
        return get_non_pii_connection()
    # ... existing fallback code ...


def get_db_connection(database: str = None):
    if USE_CENTRAL_CONFIG and database is None:
        return get_non_pii_connection()
    # ... existing fallback code ...
```

The file should end after line 153 (the `get_dict_cursor` function).

### Step 3: Verify the fix
```python
cd /ganuda/vetassist/backend
source venv/bin/activate
python3 -c "
from app.core.database_config import get_db_connection
conn = get_db_connection()
print('Connection:', conn)
print('Database:', conn.info.dbname)
conn.close()
print('SUCCESS: get_db_connection() returns valid connection')
"
```

Expected output:
```
Connection: <connection object ...>
Database: zammad_production
SUCCESS: get_db_connection() returns valid connection
```

---

## Verification

After fix:
1. `get_db_connection()` returns a valid psycopg2 connection (not None)
2. Connection is to `zammad_production` database
3. VetAssist dashboard shows Marcus's data (1 claim, 1 file, 6 research results)

---

## Do NOT

- Do NOT create `/ganuda/lib/vetassist_db_config.py` in this task (that's a separate JR)
- Do NOT modify the working `get_db_connection()` function (lines 113-138)
- Do NOT change database credentials

---

FOR SEVEN GENERATIONS
