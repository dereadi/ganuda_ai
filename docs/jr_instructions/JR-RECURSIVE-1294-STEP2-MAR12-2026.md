# [RECURSIVE] Greenfin Sentinel — Sub-Claude Watchdog on Critical Infrastructure Node - Step 2

**Parent Task**: #1294
**Auto-decomposed**: 2026-03-12T17:57:59.071199
**Original Step Title**: Create the systemd service unit file

---

### Step 2: Create the systemd service unit file

**File:** `/ganuda/services/greenfin-sentinel.service`

```ini
[Unit]
Description=Greenfin Sentinel — Cherokee AI Federation Watchdog
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=dereadi
Group=dereadi
WorkingDirectory=/ganuda
EnvironmentFile=/ganuda/config/secrets.env
ExecStart=/usr/bin/python3 /ganuda/services/greenfin_sentinel.py
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal
SyslogIdentifier=greenfin-sentinel

[Install]
WantedBy=multi-user.target
```

---
