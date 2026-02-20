# Jr Instruction: Fix Hardcoded Credentials in dlq_manager.py

**Kanban**: #1754 (Credential Migration Phase 1 — continued)
**Sacred Fire Priority**: 21
**Long Man Step**: BUILD (recursive — Step 1 of #713 completed, SEARCH/REPLACE skipped)

## Context

The migration scanner was created by Jr #713. Now apply the actual credential fix.

## Steps

### Step 1: Replace hardcoded get_db_connection

File: `jr_executor/dlq_manager.py`

```python
<<<<<<< SEARCH
def get_db_connection():
    """Get database connection using federation credentials."""
    import os
    password = os.environ.get('DB_PASSWORD', 'TYDo5U2NVkXqQ8DHuhIpvRgLUrXf2iZE')
    return psycopg2.connect(
        host='192.168.132.222',
        port=5432,
        user='claude',
        password=password,
        dbname='zammad_production'
    )
=======
def get_db_connection():
    """Get database connection using federation secrets_loader."""
    import sys
    sys.path.insert(0, '/ganuda')
    from lib.secrets_loader import get_db_config
    return psycopg2.connect(**get_db_config())
>>>>>>> REPLACE
```

## Verification

```text
python3 -c "import sys; sys.path.insert(0,'/ganuda'); from jr_executor.dlq_manager import get_db_connection; print('OK: dlq_manager uses secrets_loader')"
```
