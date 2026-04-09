# JR INSTRUCTION: Wire Weekly Observability Report Timer

**Task ID**: OBS-REPORT-001
**Priority**: P2
**SP**: 1
**Epic**: OBSERVABILITY-EPIC

## Context

The weekly observability report script (`/ganuda/scripts/weekly_observability_report.py`) is fully functional — tested manually Mar 26 2026. It generates a complete report with:
- Event summary (fire-guard alerts, service status)
- Performance summary (P50/P95/P99 latency from api_audit_log)
- DB health (rollback rates, connection utilization, top offenders)
- Memory health (RSS per service)
- Consultation ring stats
- Auto-generated recommendations

**Problem**: No systemd timer exists to run it automatically. It should run weekly on Wednesdays at 04:50 AM CT, between db-query-report (04:45) and owl-debt-reckoning (05:00).

## Step 1: Create the systemd service unit

**File**: `/etc/systemd/system/weekly-observability-report.service`

```ini
[Unit]
Description=Weekly Observability Report — BSM Leg 3
After=network.target

[Service]
Type=oneshot
User=dereadi
WorkingDirectory=/ganuda
EnvironmentFile=/ganuda/config/secrets.env
ExecStart=/usr/bin/python3 /ganuda/scripts/weekly_observability_report.py
TimeoutStartSec=120
```

## Step 2: Create the systemd timer unit

**File**: `/etc/systemd/system/weekly-observability-report.timer`

```ini
[Unit]
Description=Weekly Observability Report Timer — Wed 04:50 CT

[Timer]
OnCalendar=Wed *-*-* 04:50:00
Persistent=true
RandomizedDelaySec=60

[Install]
WantedBy=timers.target
```

## Step 3: Enable and start

```bash
sudo systemctl daemon-reload
sudo systemctl enable weekly-observability-report.timer
sudo systemctl start weekly-observability-report.timer
systemctl list-timers | grep weekly
```

## Step 4: Test run

```bash
sudo systemctl start weekly-observability-report.service
journalctl -u weekly-observability-report.service -n 30 --no-pager
cat /ganuda/logs/weekly_observability_report.md | head -20
```

## Slack Note

The report tries to post to Slack #saturday-morning and #fire-guard. SLACK_BOT_TOKEN must be in secrets.env for this to work. If not set, the report still generates the markdown file — Slack posting is non-fatal.
