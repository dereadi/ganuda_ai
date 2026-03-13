# [RECURSIVE] DC-16: Body Report Timer Deployment (retry) - Step 1

**Parent Task**: #1318
**Auto-decomposed**: 2026-03-12T20:03:04.260501
**Original Step Title**: Create the systemd service unit file

---

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
