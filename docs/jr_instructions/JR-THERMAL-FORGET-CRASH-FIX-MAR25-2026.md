# JR INSTRUCTION: Thermal Forget Crash Diagnosis and Fix

**Task ID**: DB-HEALTH-002
**Priority**: P0
**SP**: 2
**Longhouse Session**: 2710dbfcdab99b43
**Council Vote**: a91e34ac2d19f1f6
**Blocking**: Thermal forgetting has not run since Mar 22 crash. Cold archive pruning stalled.

## The Problem

`thermal-forget.service` crashed Sunday Mar 22 at 03:00 AM CT. It exited with status=1 after only 36ms of CPU time. A 36ms crash means it never reached the DB — this is an import error or early config failure, not a DB connection issue.

The journal has rotated so the original error is lost. We need to reproduce and fix.

## Diagnosis Steps

### Step 1: Run the script manually and capture the error

```bash
cd /ganuda
PYTHONPATH=/ganuda/lib:/ganuda/config python3 scripts/thermal_forget.py 2>&1
```

This will show the exact traceback.

### Step 2: Check for missing imports or renamed modules

The script imports from:
- `sys`, `os`, `re`, `json`, `hashlib`, `time`, `datetime` (stdlib — should be fine)
- No explicit ganuda_db import — it builds its own connection from env vars

**Likely failure modes (check in order):**

1. **Missing `psycopg2`**: Check `import psycopg2` works in the script's environment
2. **Missing `CHEROKEE_DB_PASS`**: The script reads from `/ganuda/config/secrets.env`. If that file is missing or the env var isn't set, `DB_PASS` will be empty string `""` and psycopg2 will fail at connect time (but that would take longer than 36ms)
3. **Table schema mismatch**: The script references `thermal_relationships`, `thermal_entity_links`, `thermal_heat_map`, `memory_chunks`, `memory_retrieval_log`, `jewel_feedback`. If any of these tables were renamed or dropped, the query will fail
4. **Python version mismatch**: Check which python3 the systemd service uses

### Step 3: Check the systemd unit for environment issues

```bash
systemctl cat thermal-forget.service
```

Verify:
- `WorkingDirectory=/ganuda`
- `Environment=PYTHONPATH=/ganuda/lib:/ganuda/config` (or equivalent)
- The `ExecStart` python path matches what works manually

## The Fix

Apply whatever the diagnosis reveals. Common patterns:

**If import error**: Add the missing module to the path or install the package.

**If secrets missing**: Update the systemd unit to source secrets:
```ini
EnvironmentFile=/ganuda/config/secrets.env
```

**If table missing**: Update the query to handle missing tables gracefully or create the missing table.

### Additionally: Modernize DB connection

The script currently builds its own connection manually (lines 24-27). It should use `ganuda_db.get_connection()` instead, which has:
- Three-tier secret resolution (secrets.env → env var → FreeIPA vault)
- Retry logic for transient SSL failures
- Consistent connection config across all daemons

Replace:
```python
DB_HOST = os.environ.get("CHEROKEE_DB_HOST", os.environ.get('CHEROKEE_DB_HOST', '10.100.0.2'))
DB_NAME = os.environ.get("CHEROKEE_DB_NAME", "zammad_production")
DB_USER = os.environ.get("CHEROKEE_DB_USER", "claude")
DB_PASS = os.environ.get("CHEROKEE_DB_PASS", "")
```

With:
```python
from ganuda_db import get_connection
```

And replace the manual `psycopg2.connect(host=DB_HOST, ...)` call with `get_connection()`.

This also eliminates the `load_secrets()` function (lines 39-50) since `ganuda_db` handles that.

## Test

```bash
# Dry run — see what would be forgotten without actually doing it
cd /ganuda
PYTHONPATH=/ganuda/lib:/ganuda/config python3 scripts/thermal_forget.py 2>&1

# Then via systemd
sudo systemctl restart thermal-forget.service
journalctl -u thermal-forget.service -n 50 --no-pager
```

Success = script runs to completion, reports count of thermals archived (or "0 eligible" if nothing is cold enough).

## Constraints

- Sacred thermals are NEVER touched. The script already has belt-and-suspenders checks for this. Do not weaken them.
- Do not change the forgetting criteria (temp < 10, access < 3, age > 30 days) without a council vote
- The `cold_thermal_archive` table creation is idempotent — safe to re-run
