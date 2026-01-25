# Jr Instruction: VetAssist Security - Batch 1 (3 files)

**Task ID:** VETASSIST-SEC-BATCH1
**Priority:** P1
**Date:** January 24, 2026
**Parent Task:** VETASSIST-SEC-001

## Objective

Update 3 endpoint files to use centralized database config.

## Files to Modify

1. `/ganuda/vetassist/backend/app/api/v1/endpoints/wizard.py`
2. `/ganuda/vetassist/backend/app/api/v1/endpoints/research.py`
3. `/ganuda/vetassist/backend/app/api/v1/endpoints/export.py`

## Change Pattern

For each file:

1. **Add import at top:**
```python
from app.core.database_config import get_db_connection, get_dict_cursor
```

2. **Remove DB_CONFIG dict** (looks like):
```python
DB_CONFIG = {
    "host": "192.168.132.222",
    "database": "...",
    "user": "claude",
    "password": "jawaseatlasers2"
}
```

3. **Replace connection calls:**
```python
# Old:
conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor(cursor_factory=RealDictCursor)

# New:
conn = get_db_connection()
cur = get_dict_cursor(conn)
```

## Output Format

Generate each modified file completely. Use separator:
```
# FILE: /ganuda/vetassist/backend/app/api/v1/endpoints/wizard.py
<complete file content>

# FILE: /ganuda/vetassist/backend/app/api/v1/endpoints/research.py
<complete file content>

# FILE: /ganuda/vetassist/backend/app/api/v1/endpoints/export.py
<complete file content>
```

## Success Criteria

- [ ] No hardcoded passwords in any file
- [ ] All 3 files import from database_config
- [ ] All connections use get_db_connection()
