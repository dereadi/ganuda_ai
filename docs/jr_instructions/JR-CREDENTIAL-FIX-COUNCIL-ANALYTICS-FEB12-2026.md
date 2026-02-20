# Jr Instruction: Fix Hardcoded Credentials in council_analytics.py

**Kanban**: #1754 (Credential Migration Phase 1 — continued)
**Sacred Fire Priority**: 21
**Long Man Step**: BUILD (recursive — Step 1 of #713 completed, SEARCH/REPLACE skipped)

## Context

The migration scanner was created by Jr #713. Now apply the actual credential fix.

## Steps

### Step 1: Replace hardcoded DB_CONFIG

File: `services/llm_gateway/council_analytics.py`

```python
<<<<<<< SEARCH
import psycopg2
from datetime import datetime, timedelta

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'TYDo5U2NVkXqQ8DHuhIpvRgLUrXf2iZE'
}
=======
import psycopg2
from datetime import datetime, timedelta
import sys
sys.path.insert(0, '/ganuda')
from lib.secrets_loader import get_db_config

DB_CONFIG = get_db_config()
>>>>>>> REPLACE
```

## Verification

```text
python3 -c "import sys; sys.path.insert(0,'/ganuda'); exec(open('/ganuda/services/llm_gateway/council_analytics.py').read().split('def ')[0]); print('OK: uses secrets_loader')"
```
