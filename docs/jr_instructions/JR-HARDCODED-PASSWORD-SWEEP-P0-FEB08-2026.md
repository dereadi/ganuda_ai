# Jr Instruction: Hardcoded Password Sweep (P0 Security)

**Task ID:** PASSWORD-SWEEP-001
**Priority:** P0 (security — rotated credential still hardcoded everywhere)
**Date:** February 8, 2026
**Node:** All nodes (redfin, bluefin, greenfin)
**Assigned:** Security Jr.
**Related:** JR-CREDENTIAL-ROTATION-P0-FEB06-2026.md, JR-SECRETS-LOADER-MIGRATION-P1-FEB06-2026.md

## Overview

The database password was rotated from `jawaseatlasers2` to a new value on Feb 6, 2026. The new password is in `/ganuda/config/secrets.env` as `CHEROKEE_DB_PASS`. However, **100+ files** across the codebase still have the old password hardcoded. Some files use `os.environ.get('CHEROKEE_DB_PASS', 'jawaseatlasers2')` which works IF the env var is set, but the fallback is the old (now invalid) password.

The jr-executor was broken for 2 days because of this. Any service restart or script execution that touches the database will fail until fixed.

## Scope

### Category 1: Active Systemd Services (FIX FIRST)

These are running right now and will break on next restart:

| File | Current State |
|------|--------------|
| `scripts/systemd/moltbook-proxy.service` | `Environment=CHEROKEE_DB_PASS=jawaseatlasers2` |
| `scripts/systemd/cherokee-email-daemon.service` | `Environment=CHEROKEE_DB_PASS=jawaseatlasers2` |
| `scripts/systemd/tribal-vision.service` | `Environment="CHEROKEE_DB_PASS=jawaseatlasers2"` |
| `services/jr-executor/jr-executor.service` | `Environment="CHEROKEE_DB_PASS=jawaseatlasers2"` |

**Fix:** Replace `Environment=CHEROKEE_DB_PASS=jawaseatlasers2` with `EnvironmentFile=/ganuda/config/secrets.env` in all service files. Then:
```bash
sudo cp scripts/systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
# Restart each affected service
```

**ALSO check deployed copies** — the service files in `/etc/systemd/system/` on each node may differ from the repo copies. Fix BOTH.

### Category 2: Core Jr Executor (FIX SECOND)

Files in `/ganuda/jr_executor/` — the task execution engine:

| File | Line | Pattern |
|------|------|---------|
| `thermal_queue.py` | 16 | Hardcoded directly |
| `thermal_poller.py` | 20 | Hardcoded directly |
| `awareness_service.py` | 67 | `self.db_password = 'jawaseatlasers2'` |
| `consultation_responder.py` | 5 | Hardcoded in dict |
| `jr_cli.py` | 157 | Hardcoded directly |
| `jr_task_executor.py` | 70 | `os.environ.get` with bad fallback |
| `jr_bidding_daemon.py` | 30 | `os.environ.get` with bad fallback |
| `execution_audit.py` | 31 | `os.environ.get` with bad fallback |
| `jr_observer.py` | 68 | `os.environ.get` with bad fallback |
| `learning_tracker.py` | 36 | `os.environ.get` with bad fallback |
| `tpm_queue_manager.py` | 24 | `os.environ.get` with bad fallback |
| `proposal_workflow.py` | 32 | `os.environ.get` with bad fallback |

### Category 3: Libraries (`/ganuda/lib/`)

| File | Pattern |
|------|---------|
| `memory_graph.py` | Hardcoded |
| `hivemind_tracker.py` | Hardcoded |
| `consciousness_cascade/gpu_monitor.py` | Hardcoded |
| `jr_bidding_daemon.py` | `os.environ.get` with bad fallback |
| `jr_task_executor_v2.py` | `os.environ.get` with bad fallback |
| `triad_thermal_memory_api.py` | Hardcoded in connection string |
| `specialist_council_modified.py` | Hardcoded |
| `specialist_council_backup.py` | Hardcoded |
| `metacognition/resonance_lookup.py` | Hardcoded |
| `metacognition/council_integration.py` | Hardcoded |
| `metacognition/reflection_api.py` | Hardcoded |
| `mar_reflexion.py` | Hardcoded |
| `smadrl_pheromones.py` | `os.environ.get` with bad fallback |
| `halo_council.py` | `os.environ.get` with bad fallback |

### Category 4: Services

| File | Pattern |
|------|---------|
| `services/notifications/notify.py` | Hardcoded |
| `services/openview_resonance/daemon.py` | Hardcoded |
| `services/longhouse/power_reporter.py` | Hardcoded |
| `services/research_file_watcher.py` | Hardcoded |
| `services/embedding_service/embedding_server.py` | Hardcoded |
| `services/fedattn/coordinator.py` | Hardcoded |
| `services/health_monitor/health_monitor.py` | Hardcoded |
| `services/health_monitor.py` | Hardcoded |
| `services/spatial_discovery/discovery.py` | Hardcoded |
| `services/vision/tribal_vision.py` | `os.environ.get` with bad fallback |
| `services/research_worker.py` | Hardcoded |
| `services/resonance/thermal_extractor.py` | Hardcoded |
| `services/research_monitor/arxiv_crawler.py` | Hardcoded |

### Category 5: Telegram Bot

| File | Pattern |
|------|---------|
| `telegram_bot/telegram_chief.py` | Hardcoded |
| `telegram_bot/status_notifier.py` | Hardcoded |
| `telegram_bot/code_generation_handler.py` | Hardcoded |
| `telegram_bot/task_assigner.py` | Hardcoded |
| `telegram_bot/derpatobot_claude.py` | Hardcoded |
| `telegram_bot/tribe_interface_fix.py` | Hardcoded |
| `telegram_bot/telegram_chief_v3.py` | `os.environ.get` with bad fallback |

### Category 6: Daemons

| File | Pattern |
|------|---------|
| `daemons/governance_agent.py` | Hardcoded |
| `daemons/sanctuary_state.py` | Hardcoded |
| `daemons/staleness_scorer.py` | Hardcoded |
| `daemons/sacred_fire_daemon.py` | Hardcoded in config dict |
| `daemons/meta_jr_autonomic.py` | Hardcoded in config dict |
| `daemons/memory_jr_autonomic.py` | Hardcoded in config dict |
| `daemons/meta_jr_autonomic_phase1.py` | Hardcoded in config dict |
| `daemons/ganuda_heartbeat_agent.py` | Hardcoded |
| `daemons/memory_consolidation_daemon.py` | `os.environ.get` with bad fallback |
| `daemons/integration_jr_autonomic.py` | Hardcoded |

### Category 7: Shell Scripts

| File | Pattern |
|------|---------|
| `ganuda_env.sh` | `export THERMAL_MEMORY_PASS="jawaseatlasers2"` |
| `scripts/pheromone_decay_v2.sh` | `PGPASSWORD='jawaseatlasers2'` |
| `scripts/pheromone_decay_v3.sh` | `PGPASSWORD='jawaseatlasers2'` |
| `scripts/backup_postgres.sh` | `DB_PASS="jawaseatlasers2"` |
| `scripts/chaos_test_suite.sh` | Multiple PGPASSWORD references |
| `scripts/deploy_cherokee_council.sh` | PGPASSWORD inline |
| `scripts/deploy-secrets-silverfin.sh` | Multiple references |
| `vetassist/backend/start_backend.sh` | `export DB_PASSWORD=jawaseatlasers2` |
| `vetassist/backend/start_with_env.sh` | `export DB_PASSWORD=jawaseatlasers2` |

### Category 8: VetAssist

| File | Pattern |
|------|---------|
| `vetassist/backend/app/api/v1/endpoints/wizard.py` | Hardcoded |
| `vetassist/backend/scripts/seed_educational_content.py` | Hardcoded |
| `vetassist/backend/scripts/link_monitor.py` | Hardcoded |
| `vetassist/backend/scripts/expand_articles.py` | Hardcoded |
| `cherokee_admin/cherokee_admin/settings.py` | Django DATABASES |
| `cherokee_admin/cherokee_admin/settings_local.py` | Django DATABASES |

### Category 9: Config Files

| File | Pattern |
|------|---------|
| `email_daemon/config.json` | `"db_password": "jawaseatlasers2"` |

## Fix Strategy

### Pattern A: Python files with `os.environ.get()` and bad fallback

Change:
```python
'password': os.environ.get('CHEROKEE_DB_PASS', 'jawaseatlasers2')
```
To:
```python
'password': os.environ.get('CHEROKEE_DB_PASS', '')
```

This ensures failure-loud instead of silently using the wrong password. All services should have the env var set via `EnvironmentFile=/ganuda/config/secrets.env`.

### Pattern B: Python files with hardcoded password

Change:
```python
'password': 'jawaseatlasers2'
```
To:
```python
'password': os.environ.get('CHEROKEE_DB_PASS', '')
```

Add `import os` at top if not already present.

### Pattern C: Python connection strings

Change:
```python
"postgresql://claude:jawaseatlasers2@192.168.132.222:5432/triad_federation"
```
To:
```python
f"postgresql://claude:{os.environ.get('CHEROKEE_DB_PASS', '')}@192.168.132.222:5432/zammad_production"
```

### Pattern D: Shell scripts

Change:
```bash
PGPASSWORD='jawaseatlasers2'
```
To:
```bash
source /ganuda/config/secrets.env
PGPASSWORD="$CHEROKEE_DB_PASS"
```

### Pattern E: Systemd service files

Remove:
```ini
Environment=CHEROKEE_DB_PASS=jawaseatlasers2
```
Add:
```ini
EnvironmentFile=/ganuda/config/secrets.env
```

### Pattern F: Django settings

Change:
```python
'PASSWORD': 'jawaseatlasers2',
```
To:
```python
'PASSWORD': os.environ.get('CHEROKEE_DB_PASS', ''),
```

### Pattern G: JSON config files

`email_daemon/config.json` cannot use environment variables directly. The daemon that reads it should override the JSON value with the env var at runtime. Add to `gmail_api_daemon.py`:
```python
config['db_password'] = os.environ.get('CHEROKEE_DB_PASS', config.get('db_password', ''))
```

## Execution Order

1. **Category 1 (systemd services)** — Fix and deploy first. These break on restart.
2. **Category 2 (jr_executor)** — Core execution engine.
3. **Category 3-6 (lib, services, telegram, daemons)** — Active Python code.
4. **Category 7 (shell scripts)** — Utility scripts and cron jobs.
5. **Category 8 (vetassist/cherokee_admin)** — Application-specific.
6. **Category 9 (config files)** — JSON configs need runtime override.

## Verification

After all fixes:

```bash
# Should return 0 matches in active code (excluding .claude/settings, backups, archives)
grep -rl 'jawaseatlasers2' /ganuda/ --include='*.py' --include='*.sh' --include='*.service' \
    | grep -v __pycache__ | grep -v node_modules | grep -v venv \
    | grep -v '.git/' | grep -v '.rlm-backups' | grep -v 'old_dereadi_data' \
    | grep -v '.claude/settings' | grep -v archive \
    | wc -l

# Should return: 0 (or only files we intentionally skipped)
```

Then restart key services and verify they connect:
```bash
sudo systemctl restart jr-executor moltbook-proxy
journalctl -u jr-executor --since '1 min ago' | grep -i 'error\|password\|failed'
```

## Security Notes

- **NEVER put the actual new password in source code** — always reference via `os.environ.get('CHEROKEE_DB_PASS')` or `$CHEROKEE_DB_PASS`
- The source of truth is `/ganuda/config/secrets.env` (chmod 600, owned by dereadi)
- The `ganuda_env.sh` file also needs updating — it exports `THERMAL_MEMORY_PASS`
- The `.claude/settings.local.json` has many references but those are in approved command patterns, not secrets — update separately if needed

## Rollback

If a service breaks after the fix, the password is in `/ganuda/config/secrets.env`. Temporarily set the env var inline:
```bash
CHEROKEE_DB_PASS=<password_from_secrets.env> python3 script.py
```

---
**FOR SEVEN GENERATIONS** — A password in one file is a secret. A password in 100 files is a liability.
