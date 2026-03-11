# [RECURSIVE] DC-16: 6-Hour Body Report Digest Timer - Step 2

**Parent Task**: #1235
**Auto-decomposed**: 2026-03-10T11:25:31.234378
**Original Step Title**: Create systemd service unit

---

### Step 2: Create systemd service unit

Create new file: `/ganuda/scripts/body-report.service`

```ini
[Unit]
Description=DC-16 Body Report — 6-hour federation health digest
After=network.target

[Service]
Type=oneshot
EnvironmentFile=/ganuda/config/secrets.env
ExecStart=/usr/bin/python3 /ganuda/scripts/body_report.py
WorkingDirectory=/ganuda
User=dereadi
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```
