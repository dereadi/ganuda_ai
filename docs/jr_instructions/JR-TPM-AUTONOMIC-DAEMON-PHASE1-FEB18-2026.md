# Jr Instruction: TPM Autonomic Daemon — Phase 1

**Task**: Build a polling-based daemon that monitors federation health and alerts the Chief at detected phase transitions
**Priority**: 8/10
**Story Points**: 8
**Kanban**: #1819
**Council Vote**: #b82aea3e6ceb8906 (PROCEED WITH CAUTION, 0.888)
**Assigned Jr**: Software Engineer Jr.

## Context

The federation is transitioning to a Level 5+ operating model where the TPM daemon runs persistently, monitoring system state and only alerting the human (Chief) when the system is stuck in a basin — not for routine work.

Study these existing patterns before building:
- `/ganuda/daemons/staleness_scorer.py` — polling daemon pattern with DB connection
- `/ganuda/daemons/sacred_fire_daemon.py` — persistent daemon with thermal memory writes
- `/ganuda/scripts/gpu_power_monitor.py` — adaptive polling intervals, Telegram alerts
- `/ganuda/telegram_bot/telegram_chief_v3.py` — Telegram bot message sending pattern
- `/ganuda/lib/secrets_loader.py` — secrets.env loading pattern (use this, don't reinvent)

## Requirements

Create `/ganuda/daemons/tpm_autonomic.py` — a single-file daemon that:

### 1. Polls Federation State (every 5 minutes, configurable via `--interval`)

Query the database for these basin detection signals:

**a) Council Disagreement**: Query `council_votes` for votes in the last 24 hours where `confidence < 0.7`. Low confidence = specialists disagree = potential basin boundary.

**b) DLQ Depth**: Count records in `jr_work_queue` with `status = 'failed'` in the last 48 hours. Threshold: 5 or more = basin signal.

**c) Jr Failure Rate**: Of tasks completed or failed in the last 24 hours, if failure rate exceeds 25% (and at least 4 tasks total), flag it.

**d) Stale Kanban**: Find `duyuktv_tickets` stuck in `status = 'in_progress'` with `updated_at` older than 7 days.

**e) Work State Summary**: Count pending Jr tasks and open kanban items (informational, not a basin signal).

### 2. Alert Chief via Telegram When Basin Signals Detected

Use the `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHIEF_CHAT_ID` environment variables (loaded from secrets.env via EnvironmentFile). Send a markdown-formatted message listing each detected signal with relevant numbers.

Only send alerts when signals are detected. Clean cycles get logged but do NOT alert.

### 3. Log All Basin Detections to Thermal Memory

When basin signals are detected, write a thermal memory record (temperature 75, `sacred_pattern=false`) with the signal details in `original_content` and `metadata` jsonb containing `{"source": "tpm-autonomic-basin-detect"}`. Use the standard `memory_hash` sha256 pattern. Use `ON CONFLICT (memory_hash) DO NOTHING` to avoid duplicates.

### 4. Support CLI Modes

- `--once`: Run a single monitoring cycle and exit (for testing)
- `--interval N`: Override poll interval in seconds (default 300)
- `--verbose`: Debug-level logging

### Design Constraints (from Council vote)

- **Lightweight**: Polling only, no persistent GPU usage, no model inference. Basin detection is threshold comparisons against DB queries.
- **Audit trail**: Every basin detection logged to thermal memory. Every cycle logged to file.
- **Independent signals**: Each check function should work independently. If one DB query fails, the others still run.
- **Reconnect on failure**: If the DB connection drops, reconnect on next cycle. Don't crash.

### Schema Reference

- `thermal_memory_archive`: columns `original_content`, `temperature_score`, `memory_hash` (sha256, NOT NULL), `sacred_pattern` (boolean), `metadata` (jsonb)
- `council_votes`: columns `audit_hash`, `confidence`, `recommendation`, `voted_at`
- `jr_work_queue`: columns `task_id`, `title`, `status`, `updated_at`
- `duyuktv_tickets`: columns `id`, `title`, `status`, `updated_at`
- DB connection: host=192.168.132.222, user=claude, dbname=zammad_production, password from secrets.env

### Logging

Log to both stderr and `/ganuda/logs/tpm_autonomic.log`. Format: `%(asctime)s [TPM-AUTO] %(levelname)s %(message)s`

## Step 1: Create the daemon

Create `/ganuda/daemons/tpm_autonomic.py` implementing the above requirements.

## Step 2: Create log directory

Ensure `/ganuda/logs/` exists.

## Acceptance Criteria

- [ ] Script runs with `python3 /ganuda/daemons/tpm_autonomic.py --once --verbose` without errors
- [ ] Each basin detection function queries the correct table and applies the correct threshold
- [ ] Telegram alerts fire only when signals are detected, not on clean cycles
- [ ] Thermal memory records are written with proper schema (memory_hash, sacred_pattern=false, metadata jsonb)
- [ ] DB reconnection works if connection is dropped between cycles
- [ ] Log file is written to `/ganuda/logs/tpm_autonomic.log`

## Out of Scope

- systemd service file (TPM will create directly — executor blocked for .service files)
- Council calling (Phase 2)
- Shadow council wiring (Phase 4)
