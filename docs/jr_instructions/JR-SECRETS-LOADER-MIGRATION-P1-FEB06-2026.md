# JR-SECRETS-LOADER-MIGRATION-P1-FEB06-2026

## Priority: P1 (Security Debt)
## Assigned Specialist: Software Engineer Jr.
## Date: February 6, 2026

---

## 1. Context

The Trust Paradox Audit found 50+ files with hardcoded credentials. A `secrets_loader.py` module exists but is not being used. This task migrates all files to use the centralized secrets loader.

## 2. Target Files

Replace hardcoded DB_CONFIG blocks in these files:

| File | Line | Current Pattern |
|------|------|-----------------|
| `/ganuda/lib/specialist_council.py` | 34 | `"password": "jawaseatlasers2"` |
| `/ganuda/lib/agemem_tools.py` | 12 | `"password": "jawaseatlasers2"` |
| `/ganuda/lib/rlm_bootstrap.py` | 17 | `'password': 'jawaseatlasers2'` |
| `/ganuda/lib/hive_mind.py` | 22 | `'password': 'jawaseatlasers2'` |
| `/ganuda/lib/saga_transactions.py` | 416 | `'password': 'jawaseatlasers2'` |
| `/ganuda/lib/magrpo_tracker.py` | 30 | `'password': 'jawaseatlasers2'` |
| `/ganuda/lib/jr_momentum_learner.py` | 38 | `'password': 'jawaseatlasers2'` |
| `/ganuda/lib/drift_detection.py` | 36 | `'password': 'jawaseatlasers2'` |
| `/ganuda/lib/research_dispatcher.py` | 19 | `'password': 'jawaseatlasers2'` |
| `/ganuda/lib/telegram_session_manager.py` | 19 | `'password': 'jawaseatlasers2'` |
| `/ganuda/lib/vlm_clause_evaluator.py` | 16 | `"password": "jawaseatlasers2"` |
| `/ganuda/lib/vlm_relationship_storer.py` | 19 | `"password": "jawaseatlasers2"` |
| `/ganuda/lib/constitutional_constraints.py` | 31 | `"password": "jawaseatlasers2"` |
| `/ganuda/lib/amem_memory.py` | 20 | `'password': 'jawaseatlasers2'` |
| `/ganuda/lib/jr_state_manager.py` | 19 | `"password": "jawaseatlasers2"` |
| `/ganuda/lib/jr_task_executor_v2.py` | 70 | Uses env with fallback |
| `/ganuda/lib/jr_bidding_daemon.py` | 50 | Uses env with fallback |
| `/ganuda/lib/consciousness_cascade/gpu_monitor.py` | 26 | `'password': 'jawaseatlasers2'` |
| `/ganuda/lib/metacognition/reflection_api.py` | 285 | `'password': 'jawaseatlasers2'` |
| `/ganuda/lib/metacognition/council_integration.py` | 341 | `'password': 'jawaseatlasers2'` |
| `/ganuda/lib/metacognition/resonance_lookup.py` | 17 | `"password": "jawaseatlasers2"` |
| `/ganuda/jr_executor/jr_queue_client.py` | 22-27 | `'password': ...` |
| `/ganuda/jr_executor/jr_queue_worker.py` | varies | Check for hardcoded |
| `/ganuda/jr_executor/task_executor.py` | varies | Check for hardcoded |

## 3. Migration Pattern

### Before (Hardcoded):
```python
DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}
```

### After (Using secrets_loader):
```python
from lib.secrets_loader import get_db_config

def _get_db_config():
    """Lazy load database config from secrets."""
    return get_db_config()

# Usage: conn = psycopg2.connect(**_get_db_config())
```

### For files that need connection at import time:
```python
import os
from lib.secrets_loader import get_db_config

# Only load config when actually needed
_db_config = None

def get_connection():
    global _db_config
    if _db_config is None:
        _db_config = get_db_config()
    return psycopg2.connect(**_db_config)
```

## 4. Steps

### Step 1: Verify secrets_loader works
```bash
python3 -c "from lib.secrets_loader import get_db_config; print(get_db_config())"
```

### Step 2: Update each file
For each file in the target list:
1. Add import: `from lib.secrets_loader import get_db_config`
2. Remove hardcoded DB_CONFIG dict
3. Replace with lazy-loading pattern
4. Test the module imports correctly

### Step 3: Delete backup files with credentials
```bash
find /ganuda/lib -name "*.bak" -o -name "*.backup_*" | xargs rm -f
```

### Step 4: Add .gitignore entry
```bash
echo "config/secrets.env" >> /ganuda/.gitignore
```

## 5. Verification

```bash
# Should return NO matches for hardcoded password
grep -r "jawaseatlasers2" /ganuda/lib/ --include="*.py" | grep -v ".pyc" | grep -v "__pycache__"
```

## 6. Testing

After migration, verify all services start correctly:
```bash
sudo systemctl restart jr-queue-worker jr-research telegram-chief
journalctl -u jr-queue-worker --since "1 minute ago" | grep -i error
```

## For Seven Generations

Clean code is secure code. Removing hardcoded secrets protects future generations from inherited vulnerabilities.
