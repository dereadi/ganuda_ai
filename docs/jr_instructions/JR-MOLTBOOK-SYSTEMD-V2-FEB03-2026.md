# JR-MOLTBOOK-SYSTEMD-V2-FEB03-2026

## Moltbook Proxy Systemd Service — Staged Deployment

| Field          | Value                                                    |
|----------------|----------------------------------------------------------|
| Task ID        | MOLTBOOK-SYSTEMD-002                                     |
| Priority       | P2                                                       |
| Assigned To    | Infrastructure Jr.                                       |
| Target Node    | redfin (192.168.132.223)                                 |
| Status         | Ready for execution                                      |
| Depends On     | MOLTBOOK-BUGFIX-COUNTER-002                              |
| Remediation Of | MOLTBOOK-SYSTEMD-001 (failed — .service file type blocked)|
| Manual Step    | YES — requires human to run sudo commands                |

---

## Context

Previous attempt failed because the executor's security system blocks creation of `.service` files (privileged file type requiring Chief approval). This remediated instruction stages the service configuration as `.txt` files that the human operator reviews and deploys.

---

## Step 1: Create Staged Service File

**FILE**: `/ganuda/services/moltbook_proxy/moltbook-proxy.service.staged`
**ACTION**: CREATE NEW FILE

```ini
[Unit]
Description=Moltbook Proxy Daemon — Cherokee AI Federation
Documentation=file:///ganuda/docs/kb/KB-MOLTBOOK-DEPLOYMENT-LESSONS-FEB03-2026.md
After=network-online.target postgresql.service
Wants=network-online.target

[Service]
Type=simple
User=dereadi
Group=dereadi
WorkingDirectory=/ganuda/services/moltbook_proxy
EnvironmentFile=/ganuda/services/moltbook_proxy/.env
ExecStart=/home/dereadi/cherokee_venv/bin/python -u proxy_daemon.py
Restart=on-failure
RestartSec=60
StartLimitIntervalSec=300
StartLimitBurst=3

# Security hardening
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=read-only
PrivateTmp=true
ReadWritePaths=/ganuda/services/moltbook_proxy /ganuda/logs

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=moltbook-proxy

[Install]
WantedBy=multi-user.target
```

## Step 2: Create Environment File

**FILE**: `/ganuda/services/moltbook_proxy/.env`
**ACTION**: CREATE NEW FILE

```bash
# Moltbook Proxy Environment
# Database connection (bluefin)
DB_HOST=192.168.132.222
DB_PORT=5432
DB_NAME=zammad_production
DB_USER=claude
DB_PASSWORD=jawaseatlasers2

# Moltbook API
MOLTBOOK_API_KEY=moltbook_sk_tpZyAhg0oZZhPv5C0PfkvO1JM7r8MwdM
MOLTBOOK_BASE_URL=https://www.moltbook.com

# Daemon settings
POLL_INTERVAL=300
LOG_FILE=/ganuda/logs/moltbook_proxy.log
```

## Step 3: Verify Staged Files

```bash
# Check files exist
ls -la /ganuda/services/moltbook_proxy/moltbook-proxy.service.staged
ls -la /ganuda/services/moltbook_proxy/.env

# Verify .env permissions (should be owner-only)
chmod 600 /ganuda/services/moltbook_proxy/.env
ls -la /ganuda/services/moltbook_proxy/.env
```

---

## MANUAL DEPLOYMENT STEPS (Requires Human with sudo)

The following commands must be run by the human operator on redfin:

```bash
# 1. Stop the current daemon process
kill 2239377  # or: pkill -f 'proxy_daemon.py'

# 2. Copy staged service file to systemd directory
sudo cp /ganuda/services/moltbook_proxy/moltbook-proxy.service.staged /etc/systemd/system/moltbook-proxy.service

# 3. Reload systemd
sudo systemctl daemon-reload

# 4. Enable and start
sudo systemctl enable moltbook-proxy
sudo systemctl start moltbook-proxy

# 5. Verify
sudo systemctl status moltbook-proxy
journalctl -u moltbook-proxy -f --no-pager -n 20
```

---

## Verification

After manual deployment, confirm:
- [ ] `systemctl is-active moltbook-proxy` returns `active`
- [ ] `journalctl -u moltbook-proxy -n 5` shows "Crawdad Moltbook Proxy starting..."
- [ ] Feed scan entries appear every 5 minutes
- [ ] `.env` file has permissions `600` (owner-only read/write)
- [ ] Old PID process is no longer running: `ps aux | grep proxy_daemon | grep -v grep`

---

## Rollback

If the service fails to start:
```bash
sudo systemctl stop moltbook-proxy
# Restart manually
cd /ganuda/services/moltbook_proxy && /home/dereadi/cherokee_venv/bin/python -u proxy_daemon.py &
```
