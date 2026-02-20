# KB: Password Rotation Cascade — 2-Day Service Outage

**Date:** February 8, 2026
**Author:** TPM (Claude Opus 4.6)
**Severity:** P0 — Infrastructure
**Status:** Resolved

## Incident Summary

On February 6, 2026, the PostgreSQL password for user `claude` was rotated on bluefin (192.168.132.222). This broke every service and daemon that had the old password hardcoded — including **jr-executor** and **jr-orchestrator**, which went down silently for 2 days until discovered on February 8.

## Root Cause

Services used two anti-patterns for database credentials:

1. **Hardcoded in Python source**: `password='jawaseatlasers2'` in 319+ files
2. **Hardcoded in systemd units**: `Environment=CHEROKEE_DB_PASS=jawaseatlasers2` in service files

When the password was rotated, none of these updated automatically.

## Impact

- **jr-executor**: Dead for ~48 hours. No tasks were being executed.
- **jr-orchestrator**: Dead for ~48 hours. No workers spawned, no work_queue processing.
- **All queued Jr tasks**: Stuck in pending/assigned state with no executor to pick them up.
- **Multiple daemons**: Silently failing DB connections (pheromone decay, health monitors, etc.)

## Detection

Discovered when investigating why queued tasks weren't executing. The executor logs showed:
```
FATAL: password authentication failed for user "claude"
```

## Fix Applied

### Immediate (Feb 8)
1. Added `EnvironmentFile=/ganuda/config/secrets.env` to both service files:
   - `/etc/systemd/system/jr-executor.service`
   - `/etc/systemd/system/jr-orchestrator.service`
2. Ran `systemctl daemon-reload && systemctl restart jr-executor jr-orchestrator`
3. Verified workers spawned and tasks resumed

### Comprehensive Password Sweep (Feb 8)
1. Created `/ganuda/scripts/sweep_hardcoded_passwords.py`
2. Swept 319 files, replacing hardcoded passwords with `os.environ.get('CHEROKEE_DB_PASS', '')`
3. Shell scripts: replaced with `$CHEROKEE_DB_PASS` and added `source /ganuda/config/secrets.env`
4. Systemd services: replaced `Environment=` with `EnvironmentFile=/ganuda/config/secrets.env`
5. 32 edge cases remain (heredocs, comments, Joe's directory — non-critical)

### Single Source of Truth
All credentials now flow from `/ganuda/config/secrets.env`:
```
CHEROKEE_DB_PASS=<rotated_password>
```

## Prevention Measures

### DO
- Use `EnvironmentFile=/ganuda/config/secrets.env` in ALL systemd service files
- Use `os.environ.get('CHEROKEE_DB_PASS', '')` in ALL Python code
- Use `source /ganuda/config/secrets.env` at the top of ALL shell scripts
- Run the sweep script in `--dry-run` mode after any credential rotation

### DO NOT
- Hardcode passwords in source files, service files, or config dictionaries
- Use `Environment=VARNAME=value` for secrets in systemd units
- Assume credential rotation is complete after updating one file
- Use fallback defaults with real passwords: `os.environ.get('VAR', 'realpassword')`

### Pre-rotation Checklist
Before rotating any credential:
1. Run `grep -r 'old_password' /ganuda/ --include='*.py' --include='*.sh' --include='*.service' | wc -l`
2. Identify all consumers of the credential
3. Update `/ganuda/config/secrets.env` with new value
4. Restart all dependent services: `systemctl restart jr-executor jr-orchestrator`
5. Run sweep script dry-run to verify no stragglers
6. Verify services are healthy: check logs for auth failures

## Files Modified
- 319 Python, shell, and service files (full list in sweep script output)
- Key infrastructure: jr_executor/, lib/, services/, telegram_bot/, daemons/, vetassist/

## Lessons Learned
1. **Silent failures are the worst failures.** Both executor and orchestrator died without alerting anyone.
2. **Credential rotation is a federation-wide event**, not a single-node operation.
3. **A single secrets.env file** beats 319 hardcoded copies every time.
4. **Need a health monitor** that alerts when critical services (executor, orchestrator) stop processing tasks.

## Related
- Password sweep script: `/ganuda/scripts/sweep_hardcoded_passwords.py`
- Secrets env: `/ganuda/config/secrets.env`
- Jr instruction: `/ganuda/docs/jr_instructions/JR-CREDENTIAL-ROTATION-P0-FEB06-2026.md`
- KB: `/ganuda/docs/kb/KB-CREDENTIAL-ROTATION-SECRETS-MIGRATION-FEB06-2026.md`
