# Jr Instruction: DC-16 Body Report Timer (FIXED)

**Task #:** 1235/1258 retry
**Title:** DC-16: 6-Hour Body Report Digest Timer — Deploy systemd units
**Date:** March 12, 2026
**Priority:** 2 (DC-16 Fail Loud — Phase 1, observability)
**Replaces:** JR-DC16-BODY-REPORT-TIMER-MAR10-2026.md (tasks #1235, #1258 failed)

## Context

The body report script already exists at `/ganuda/scripts/body_report.py` and is correct.
The previous Jr tasks failed during systemd deployment. This instruction ONLY deploys the
systemd service and timer unit files. The script is NOT modified.

The timer fires every 6 hours at :15 past (00:15, 06:15, 12:15, 18:15 CT) to produce a
federation health digest — fire guard alerts, Jr task stats, circuit breaker states, and
connection recovery counts. Posts to Slack #dawn-mist and thermalizes the report.

## Constraints

- Do NOT modify `/ganuda/scripts/body_report.py` — it already exists and is correct.
- Follow the same unit file pattern as `fire-guard.service` / `fire-guard.timer`.
- Use `EnvironmentFile=/ganuda/config/secrets.env` for DB credentials.
- Use FreeIPA scoped sudo (already configured for dereadi) for systemctl and cp commands.
- Timer uses `Persistent=true` so missed runs fire on next boot.

## Steps

### Step 1: Create the systemd service unit file

**File:** `/ganuda/scripts/body-report.service`

```ini
[Unit]
Description=DC-16 Body Report — 6-hour federation health digest
After=network.target

[Service]
Type=oneshot
User=dereadi
WorkingDirectory=/ganuda
EnvironmentFile=/ganuda/config/secrets.env
ExecStart=/usr/bin/python3 /ganuda/scripts/body_report.py
StandardOutput=journal
StandardError=journal
```

### Step 2: Create the systemd timer unit file

**File:** `/ganuda/scripts/body-report.timer`

```ini
[Unit]
Description=DC-16 Body Report Timer — every 6 hours

[Timer]
OnCalendar=*-*-* 00,06,12,18:15:00
Persistent=true

[Install]
WantedBy=timers.target
```

### Step 3: Copy unit files to systemd directory

```bash
sudo cp /ganuda/scripts/body-report.service /etc/systemd/system/body-report.service
sudo cp /ganuda/scripts/body-report.timer /etc/systemd/system/body-report.timer
```

### Step 4: Reload systemd and enable the timer

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now body-report.timer
```

### Step 5: Verify timer is active and scheduled

```bash
systemctl list-timers body-report.timer --no-pager
systemctl status body-report.timer --no-pager
```

Expected output: timer shows next firing at :15 past the next 6-hour mark.

### Step 6: Test the service manually (one-shot dry run)

```bash
sudo systemctl start body-report.service
journalctl -u body-report.service --since "1 minute ago" --no-pager
```

Expected output: log lines showing "Generating body report", the digest text, and
"Body report complete". If Slack post fails, that is acceptable (best-effort).

## Acceptance Criteria

1. `body-report.timer` appears in `systemctl list-timers` with next firing time.
2. `body-report.service` runs `/ganuda/scripts/body_report.py` as user dereadi.
3. Manual `systemctl start body-report.service` completes without error (exit 0).
4. Journal logs show the digest output from the manual run.
5. No modifications to `/ganuda/scripts/body_report.py`.
