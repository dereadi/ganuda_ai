# Jr Instruction: Credential Migration Phase 1 — secrets_loader Integration

**Kanban**: #1754 (Security: Migrate Edge-Case Password Files)
**Sacred Fire Priority**: 21
**Story Points**: 8
**River Cycle**: RC-2026-02A
**Long Man Step**: BUILD

## Context

The federation has `lib/secrets_loader.py` — a 3-tier secret resolution system (secrets.env file → environment variables → FreeIPA vault). However, many Python files still use hardcoded database credentials in `DB_CONFIG` dicts or `psycopg2.connect()` calls.

Phase 1 targets the **active service files** — gateway analytics, thermal health, DLQ manager, and creates a migration helper for the remaining ~30 files.

**Pattern to replace:**
```text
DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': '<PLAINTEXT>'
}
```

**Replacement pattern:**
```text
import sys
sys.path.insert(0, '/ganuda')
from lib.secrets_loader import get_db_config
DB_CONFIG = get_db_config()
```

Note: `get_db_config()` returns `{'host', 'dbname', 'user', 'password', 'port'}` — `psycopg2.connect()` accepts both `database` and `dbname` as keywords, so this is safe.

## Steps

### Step 1: Fix council_analytics.py

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

### Step 2: Fix thermal_health.py

File: `services/llm_gateway/thermal_health.py`

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

### Step 3: Fix dlq_manager.py

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

### Step 4: Create Migration Helper Script

Create `/ganuda/scripts/security/credential_migration.py`

```python
#!/usr/bin/env python3
"""Credential Migration Helper — Phase 1 to Phase 2 bridge.

Kanban #1754 — Security: Migrate Password Files to secrets_loader
Scans Python files for known hardcoded credential patterns and reports
which files still need migration. Optionally applies fixes.

Usage:
    python3 /ganuda/scripts/security/credential_migration.py --scan
    python3 /ganuda/scripts/security/credential_migration.py --apply --file PATH

For Seven Generations
"""

import os
import re
import sys
import argparse
from datetime import datetime

GANUDA_ROOT = '/ganuda'

# Patterns that indicate hardcoded credentials
PATTERNS = [
    {
        'name': 'DB_CONFIG dict with password',
        'regex': re.compile(
            r"DB_CONFIG\s*=\s*\{[^}]*'password'\s*:\s*'[^']{8,}'",
            re.DOTALL
        ),
        'severity': 'CRITICAL',
    },
    {
        'name': 'psycopg2.connect with password kwarg',
        'regex': re.compile(
            r"psycopg2\.connect\([^)]*password\s*=\s*['\"][^'\"]{8,}['\"]",
            re.DOTALL
        ),
        'severity': 'HIGH',
    },
    {
        'name': 'os.environ.get DB_PASSWORD with fallback',
        'regex': re.compile(
            r"os\.environ\.get\(\s*['\"]DB_PASSWORD['\"],\s*'[^']{8,}'"
        ),
        'severity': 'HIGH',
    },
]

# Directories to skip
SKIP_DIRS = {
    '__pycache__', '.git', 'venv', '.venv', 'node_modules',
    'site-packages', 'amem_venv', 'cherokee_training_env',
    'icl_research_env', 'venv-django', 'week1_integration_env',
}

# Files already migrated (use secrets_loader)
ALREADY_MIGRATED = {
    'jr_executor/jr_queue_client.py',
    'jr_executor/jr_task_executor.py',
}


def scan_files():
    """Scan all Python files for hardcoded credential patterns."""
    findings = []

    for root, dirs, files in os.walk(GANUDA_ROOT):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        for fname in files:
            if not fname.endswith('.py'):
                continue

            filepath = os.path.join(root, fname)
            rel_path = os.path.relpath(filepath, GANUDA_ROOT)

            if rel_path in ALREADY_MIGRATED:
                continue

            try:
                with open(filepath, 'r', errors='ignore') as f:
                    content = f.read()
            except (IOError, OSError):
                continue

            # Check if already uses secrets_loader
            uses_loader = 'secrets_loader' in content or 'get_db_config' in content

            for pattern in PATTERNS:
                matches = pattern['regex'].findall(content)
                if matches:
                    findings.append({
                        'file': rel_path,
                        'pattern': pattern['name'],
                        'severity': pattern['severity'],
                        'uses_loader': uses_loader,
                        'match_count': len(matches),
                    })

    return findings


def print_report(findings):
    """Print a formatted scan report."""
    print("=" * 70)
    print(f"CREDENTIAL MIGRATION SCAN — {datetime.now().isoformat()}")
    print(f"Cherokee AI Federation — Kanban #1754")
    print("=" * 70)

    if not findings:
        print("\nNo hardcoded credentials found. All clear.")
        return

    # Group by severity
    by_severity = {}
    for f in findings:
        by_severity.setdefault(f['severity'], []).append(f)

    for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
        items = by_severity.get(severity, [])
        if not items:
            continue

        print(f"\n{severity} ({len(items)} findings):")
        for item in sorted(items, key=lambda x: x['file']):
            loader_status = " [PARTIAL — already imports secrets_loader]" if item['uses_loader'] else ""
            print(f"  [{item['severity']}] {item['file']}")
            print(f"         Pattern: {item['pattern']}{loader_status}")

    # Summary
    total = len(findings)
    critical = len(by_severity.get('CRITICAL', []))
    high = len(by_severity.get('HIGH', []))
    already_partial = sum(1 for f in findings if f['uses_loader'])

    print(f"\nSUMMARY: {total} findings ({critical} CRITICAL, {high} HIGH)")
    print(f"  Already partially migrated: {already_partial}")
    print(f"  Need full migration: {total - already_partial}")
    print(f"\nRecommendation: Fix CRITICAL files first, then sweep HIGH.")
    print(f"Pattern: Replace DB_CONFIG dict with `from lib.secrets_loader import get_db_config`")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Credential Migration Helper')
    parser.add_argument('--scan', action='store_true', help='Scan for hardcoded credentials')
    args = parser.parse_args()

    if args.scan or len(sys.argv) == 1:
        findings = scan_files()
        print_report(findings)
    else:
        parser.print_help()
```

## Verification

After applying, verify the three fixed files:

```text
python3 -c "import sys; sys.path.insert(0, '/ganuda'); from services.llm_gateway.council_analytics import DB_CONFIG; print('council_analytics OK:', 'password' not in str(DB_CONFIG.get('password',''))[:5])"
```

Run the migration scanner to see remaining files:

```text
python3 /ganuda/scripts/security/credential_migration.py --scan
```

## What This Does NOT Cover

- ganuda.yaml plaintext password (needs gateway.py loader changes — Phase 2)
- Moltbook proxy files (service currently STOPPED + DISABLED)
- Telegram bot tokens (different pattern — needs get_telegram_token())
- LLM API keys (different pattern — needs get_llm_api_key())
- FreeIPA vault integration (Tier 3, separate kanban #1757)
