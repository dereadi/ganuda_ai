# JR INSTRUCTION: Stats Keeper Timer — Auto-Refresh Landing Page Numbers

**Task**: Create `scripts/stats_keeper.py` and a systemd timer to keep ganuda.us landing page stats current
**Priority**: P2
**Date**: 2026-03-10
**TPM**: Claude Opus
**Council Vote**: Longhouse blessed, #bc1de267de3dc86d

## Problem Statement

The ganuda.us landing page displays hardcoded stats (thermal memories, council votes, completed tasks, node count). These numbers go stale within hours because the federation is continuously active. A daily auto-refresh keeps the public-facing numbers honest without manual intervention.

## What You're Building

A Python script `scripts/stats_keeper.py` that:
1. Queries live counts from PostgreSQL
2. Reads the current `/index.html` from the `web_content` table
3. Updates ONLY the stat numbers in the HTML
4. Writes the updated HTML back to `web_content`
5. A systemd timer to run this daily at 5:00 AM CT

## Database Connection

- Host: `192.168.132.222`
- DB: `zammad_production`
- User: `claude`
- Password: from `CHEROKEE_DB_PASS` env var or `/ganuda/config/secrets.env`

Use the `ganuda_db.get_connection()` / `ganuda_db.get_dict_cursor()` pattern from `council_dawn_mist.py` (lines 23, 215-216) with a manual psycopg2 fallback if ganuda_db is not importable. See `generate_status_page.py` lines 261-271 for the secrets.env loading pattern.

## Steps

### 1. Query Live Stats

```sql
-- Thermal memory count
SELECT COUNT(*) FROM thermal_memory_archive;

-- Council vote count
SELECT COUNT(*) FROM council_votes;

-- Completed Jr tasks
SELECT COUNT(*) FROM jr_work_queue WHERE status = 'completed';
```

Node count is hardcoded to `8` (current federation size). Define it as a constant at the top of the file:
```python
FEDERATION_NODE_COUNT = 8  # redfin, bluefin, greenfin, bmasass, owlfin, eaglefin, sasass, sasass2
```

### 2. Read Current Landing Page

```sql
SELECT content FROM web_content WHERE path = '/index.html';
```

### 3. Format Numbers for Display

- Thermal memories: Format as "XXK+" (e.g., 19808 becomes "19K+", 93412 becomes "93K+"). Use `f"{count // 1000}K+"`.
- Council votes: Format with commas (e.g., "8,850"). Use `f"{count:,}"`.
- Completed tasks: Format with commas (e.g., "913"). Use `f"{count:,}"`.
- Node count: Plain integer string.

### 4. Update HTML Stats

Use regex substitution to find and replace the stat values. The landing page HTML contains stat blocks — look for patterns like number followed by descriptive label text. You will need to inspect the actual HTML to determine exact patterns. Likely patterns:

```python
import re

# Example — adapt to actual HTML structure after reading it
html = re.sub(r'(\d+K\+)(\s*</.*?thermal|memories)', f'{thermal_formatted}\\2', html, flags=re.IGNORECASE)
```

IMPORTANT: Be conservative with regex. Match as much surrounding context as possible to avoid replacing the wrong numbers. If the HTML structure is ambiguous, log a warning and skip the update rather than corrupting the page.

### 5. Write Updated HTML Back

```sql
UPDATE web_content SET content = %s, updated_at = NOW() WHERE path = '/index.html';
```

**CRITICAL CONSTRAINT**: The `web_content` table is the ONLY table this script writes to. All other tables are READ-ONLY. This is Coyote's binding condition.

### 6. Logging

- Print a summary to stdout: `Stats updated: {thermal_count} thermals, {vote_count} votes, {task_count} tasks`
- On error, print to stderr and exit with non-zero code
- Do NOT write thermals or to any other table. Coyote's write constraint takes precedence. Log to stdout/stderr only.

## Systemd Timer

### stats-keeper.service

```ini
[Unit]
Description=Stats Keeper — refresh ganuda.us landing page numbers
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=dereadi
Group=dereadi
WorkingDirectory=/ganuda
ExecStart=/usr/bin/python3 /ganuda/scripts/stats_keeper.py
Environment=PYTHONPATH=/ganuda/lib:/ganuda
EnvironmentFile=/ganuda/config/secrets.env
StandardOutput=journal
StandardError=journal
```

### stats-keeper.timer

```ini
[Unit]
Description=Run Stats Keeper daily at 5:00 AM CT

[Timer]
OnCalendar=*-*-* 05:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

Note: The timer uses local time. The system timezone on redfin must be America/Chicago. Verify with `timedatectl` before deploying.

### Deploy to redfin (local node)

```bash
sudo cp /ganuda/config/systemd/stats-keeper.service /etc/systemd/system/
sudo cp /ganuda/config/systemd/stats-keeper.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now stats-keeper.timer
```

## Target Files

- `/ganuda/scripts/stats_keeper.py` — the script (CREATE)
- `/ganuda/config/systemd/stats-keeper.service` — service unit (CREATE)
- `/ganuda/config/systemd/stats-keeper.timer` — timer unit (CREATE)

## Constraints

- **Write ONLY to `web_content` table.** Read-only on everything else. This is Coyote's binding condition.
- Do NOT hardcode DB passwords — use env var with secrets.env fallback
- Do NOT modify the HTML structure — only replace the numeric values
- If the HTML cannot be parsed or the expected patterns are not found, log an error and exit cleanly without writing anything
- All formatting thresholds and constants at the top of the file

## Files to Read Before Starting

- `/ganuda/scripts/generate_status_page.py` — DB connection pattern, secrets.env loading
- `/ganuda/scripts/council_dawn_mist.py` — ganuda_db import pattern
- `/ganuda/lib/slack_federation.py` — NOT needed for this task but reference for import patterns

## Acceptance Criteria

- After timer fires, `curl https://ganuda.us` shows updated numbers matching actual DB counts
- Numbers are formatted correctly (K+ for thermals, commas for votes/tasks)
- Script exits cleanly on success (exit 0) and with error message on failure (exit 1)
- No writes to any table other than `web_content`
- `python3 -c "import py_compile; py_compile.compile('scripts/stats_keeper.py', doraise=True)"` passes

## DO NOT

- Write to any table except `web_content`
- Modify HTML structure or layout — numbers only
- Hardcode DB credentials
- Add Slack notifications (this is a quiet background job)
- Create new DB tables or columns
