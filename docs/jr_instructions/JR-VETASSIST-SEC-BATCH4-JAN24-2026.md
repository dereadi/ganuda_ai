# Jr Instruction: VetAssist Security - Batch 4 (3 files)

**Task ID:** VETASSIST-SEC-BATCH4
**Priority:** P1
**Date:** January 24, 2026
**Parent Task:** VETASSIST-SEC-001

## Objective

Update final 3 files to use centralized database config.

## Files to Modify

1. `/ganuda/vetassist/backend/app/services/rag_ingestion.py`
2. `/ganuda/vetassist/backend/app/services/rag_query.py`
3. `/ganuda/vetassist/backend/app/db/database.py`

## Change Pattern

For each file:

1. **Add import at top:**
```python
from app.core.database_config import get_db_config, get_db_connection, get_dict_cursor
```

2. **Remove DB_CONFIG dict or inline credentials**

3. **Replace connection calls:**
```python
# Old patterns:
conn = psycopg2.connect(**DB_CONFIG)
# or
config = {"host": "...", "password": "jawaseatlasers2", ...}

# New:
conn = get_db_connection()
cur = get_dict_cursor(conn)
# or for config dict:
config = get_db_config()
```

## Special Note for database.py

This file may have a fallback pattern. Update to use centralized config as primary:
```python
from app.core.database_config import get_db_config

def get_database_url():
    config = get_db_config()
    return f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
```

## Output Format

Generate each modified file completely. Use separator:
```
# FILE: /ganuda/vetassist/backend/app/services/rag_ingestion.py
<complete file content>

# FILE: /ganuda/vetassist/backend/app/services/rag_query.py
<complete file content>

# FILE: /ganuda/vetassist/backend/app/db/database.py
<complete file content>
```

## Success Criteria

- [ ] No hardcoded passwords in any file
- [ ] All 3 files import from database_config
- [ ] All connections use centralized config
- [ ] grep -r "jawaseatlasers2" returns no results in app/
