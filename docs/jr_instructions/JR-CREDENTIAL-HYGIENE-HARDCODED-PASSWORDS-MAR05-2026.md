# JR Instruction: Remove Hardcoded Database Passwords

**Task**: Remove all hardcoded DB passwords from source code
**Priority**: 10 (CRITICAL — credential hygiene)
**Sacred Fire**: No
**Assigned Jr**: Software Engineer Jr.
**Use RLM**: false
**TEG Plan**: false

## Context

Tech debt audit found 3 files with the database password hardcoded in source. All should use `ganuda_db.get_db_config()` or `os.environ.get("CHEROKEE_DB_PASS")` without a fallback default that contains the actual password.

## Changes

### Step 1: Fix specialist_council.py self_audit method

File: `lib/specialist_council.py`

<<<<<<< SEARCH
        try:
            conn = psycopg2.connect(
                host="192.168.132.222",
                dbname="zammad_production",
                user="claude",
                password="REDACTED_USE_ENV_VAR",
                cursor_factory=psycopg2.extras.RealDictCursor
            )
=======
        try:
            config = dict(DB_CONFIG)
            config["cursor_factory"] = psycopg2.extras.RealDictCursor
            conn = psycopg2.connect(**config)
>>>>>>> REPLACE

### Step 2: Fix shadow_council_sync.py DB_CONFIG

File: `daemons/shadow_council_sync.py`

<<<<<<< SEARCH
DB_CONFIG = {
    "host": "192.168.132.222",
    "dbname": "zammad_production",
    "user": "claude",
    "password": os.environ.get("CHEROKEE_DB_PASSWORD", "REDACTED_USE_ENV_VAR")
}
=======
DB_CONFIG = {
    "host": "192.168.132.222",
    "dbname": "zammad_production",
    "user": "claude",
    "password": os.environ.get("CHEROKEE_DB_PASS", "")
}
>>>>>>> REPLACE

### Step 3: Fix canary_probe.py DB_CONFIG

File: `scripts/safety/canary_probe.py`

<<<<<<< SEARCH
DB_CONFIG = {
    "host": "192.168.132.222",
    "dbname": "zammad_production",
    "user": "claude",
    "password": os.environ.get("CHEROKEE_DB_PASSWORD", "REDACTED_USE_ENV_VAR")
}
=======
DB_CONFIG = {
    "host": "192.168.132.222",
    "dbname": "zammad_production",
    "user": "claude",
    "password": os.environ.get("CHEROKEE_DB_PASS", "")
}
>>>>>>> REPLACE

## Notes
- specialist_council.py already has DB_CONFIG defined at module level (imported from secrets_loader). The self_audit method at line 1456 bypasses it with a hardcoded connection. Fix uses the existing DB_CONFIG.
- shadow_council_sync.py and canary_probe.py use CHEROKEE_DB_PASSWORD (wrong env var name). Correct name is CHEROKEE_DB_PASS (per secrets.env and ganuda_db). Fixed in both.
- Empty string fallback "" is intentional — will fail loudly if env var not set, rather than silently using a stale password.
