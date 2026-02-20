# JR-MOLTBOOK-SYSTEMD-SERVICE-FEB03-2026

## Jr Instruction: Deploy Moltbook Proxy Daemon as systemd Service

| Field        | Value                                              |
|--------------|----------------------------------------------------|
| Task ID      | MOLTBOOK-SYSTEMD-001                               |
| Priority     | P1 - Production Service                            |
| Target Node  | redfin (192.168.132.223)                           |
| Assigned To  | Available Jr                                       |
| Created By   | TPM (Claude Opus 4.5)                              |
| Date         | 2026-02-03                                         |
| Status       | Ready for Execution                                |
| Sudo Required| YES - deployment steps require root                |

---

## Objective

Migrate the Moltbook proxy daemon from an interactive process (currently PID 2239377) to a proper systemd-managed service with security hardening, automatic restart, and environment-based credential management.

---

## Prerequisites

- SSH access to redfin (192.168.132.223) as `dereadi`
- Sudo privileges on redfin
- Python venv exists at `/home/dereadi/cherokee_venv/bin/python`
- Daemon code exists at `/ganuda/services/moltbook_proxy/proxy_daemon.py`
- PostgreSQL accessible on bluefin (192.168.132.222), database `zammad_production`
- Log directory `/ganuda/logs/` exists and is writable by `dereadi`

---

## Step 1: Create the Environment File

The daemon needs database credentials. Store them in a dedicated environment file that systemd will load.

**File**: `/ganuda/services/moltbook_proxy/.env`

```bash
CHEROKEE_DB_PASS=<the_actual_password_from_current_env>
```

To find the current password, check the running process environment:

```bash
cat /proc/2239377/environ | tr '\0' '\n' | grep CHEROKEE_DB_PASS
```

If the password is hardcoded in the daemon or sourced from another location, extract it from there.

**Set permissions** (critical -- this file contains credentials):

```bash
chmod 0600 /ganuda/services/moltbook_proxy/.env
chown dereadi:dereadi /ganuda/services/moltbook_proxy/.env
```

**Verify**:

```bash
ls -la /ganuda/services/moltbook_proxy/.env
# Expected: -rw------- 1 dereadi dereadi ... .env
```

---

## Step 2: Create the systemd Service File

**File**: `/ganuda/scripts/systemd/moltbook-proxy.service`

```ini
[Unit]
Description=Moltbook Proxy Daemon - Cherokee AI Federation
After=network-online.target
Wants=network-online.target
Documentation=file:///ganuda/docs/jr_instructions/JR-MOLTBOOK-SYSTEMD-SERVICE-FEB03-2026.md

[Service]
Type=simple
User=dereadi
Group=dereadi
WorkingDirectory=/ganuda/services/moltbook_proxy
ExecStart=/home/dereadi/cherokee_venv/bin/python -u proxy_daemon.py
Restart=on-failure
RestartSec=30
StandardOutput=journal
StandardError=journal
SyslogIdentifier=moltbook-proxy

# Environment (defaults in code, but explicit here for clarity)
Environment=CHEROKEE_DB_HOST=192.168.132.222
Environment=CHEROKEE_DB_NAME=zammad_production
Environment=CHEROKEE_DB_USER=claude

# Load password from environment file
EnvironmentFile=/ganuda/services/moltbook_proxy/.env

# Security hardening
NoNewPrivileges=yes
ProtectSystem=strict
ReadWritePaths=/ganuda/services/moltbook_proxy /ganuda/logs
ProtectHome=read-only
PrivateTmp=yes

[Install]
WantedBy=multi-user.target
```

**Notes on the service configuration**:

- `-u` flag on python ensures unbuffered stdout, so journal captures logs in real time
- `Restart=on-failure` with `RestartSec=30` gives the daemon 30 seconds before restart on crash, preventing tight restart loops
- `ProtectSystem=strict` makes the entire filesystem read-only except paths listed in `ReadWritePaths`
- `ProtectHome=read-only` allows reading the venv from `/home/dereadi/cherokee_venv` but prevents writes to home
- `PrivateTmp=yes` gives the service its own /tmp namespace
- `EnvironmentFile` loads `CHEROKEE_DB_PASS` from the `.env` file created in Step 1

---

## Step 3: Deploy the Service (Sudo Required)

**IMPORTANT**: The following commands require sudo. If you do not have sudo access, stop here and notify the user that manual intervention is needed.

```bash
# 1. Stop the interactive daemon first
kill 2239377

# 2. Verify it stopped
ps aux | grep proxy_daemon | grep -v grep
# Expected: no output (process gone)

# 3. Install the service file
sudo cp /ganuda/scripts/systemd/moltbook-proxy.service /etc/systemd/system/

# 4. Reload systemd to pick up the new service
sudo systemctl daemon-reload

# 5. Enable the service (auto-start on boot)
sudo systemctl enable moltbook-proxy

# 6. Start the service
sudo systemctl start moltbook-proxy

# 7. Verify it is running
sudo systemctl status moltbook-proxy
```

**Expected output from status**:

```
● moltbook-proxy.service - Moltbook Proxy Daemon - Cherokee AI Federation
     Loaded: loaded (/etc/systemd/system/moltbook-proxy.service; enabled; preset: enabled)
     Active: active (running) since ...
     Main PID: <new_pid> (python)
```

---

## Step 4: Verify Daemon Functionality

After starting the service, verify the daemon is functioning correctly:

```bash
# Check journal logs for startup messages
sudo journalctl -u moltbook-proxy -n 50 --no-pager

# Check the daemon's own log file
tail -20 /ganuda/logs/moltbook_proxy.log

# Verify database connectivity (look for successful poll cycle in logs)
sudo journalctl -u moltbook-proxy --since "1 min ago" --no-pager
```

---

## Monitoring Commands

```bash
# Live log stream (follow mode)
sudo journalctl -u moltbook-proxy -f

# Service status
sudo systemctl status moltbook-proxy

# Last 100 log lines
sudo journalctl -u moltbook-proxy -n 100 --no-pager

# Logs since specific time
sudo journalctl -u moltbook-proxy --since "2026-02-03 20:00:00"

# Check for restarts (indicates crashes)
sudo journalctl -u moltbook-proxy | grep "Started Moltbook"
```

---

## Kill Switch Usage

The daemon respects a file-based kill switch for emergency pause without stopping the service:

```bash
# Pause engagement (daemon keeps running but skips all API calls)
touch /ganuda/services/moltbook_proxy/ENGAGEMENT_PAUSED

# Resume engagement
rm /ganuda/services/moltbook_proxy/ENGAGEMENT_PAUSED

# Verify kill switch state
ls -la /ganuda/services/moltbook_proxy/ENGAGEMENT_PAUSED 2>/dev/null && echo "PAUSED" || echo "ACTIVE"
```

---

## Service Management

```bash
# Stop the service
sudo systemctl stop moltbook-proxy

# Restart the service (e.g., after code changes)
sudo systemctl restart moltbook-proxy

# Disable auto-start on boot
sudo systemctl disable moltbook-proxy

# Re-enable auto-start
sudo systemctl enable moltbook-proxy
```

---

## Troubleshooting

| Symptom | Check | Fix |
|---------|-------|-----|
| Service fails to start | `sudo journalctl -u moltbook-proxy -n 30` | Check Python path, venv existence, syntax errors |
| Database connection refused | Verify bluefin is up: `pg_isready -h 192.168.132.222` | Check network, pg_hba.conf on bluefin |
| Permission denied errors | `sudo journalctl -u moltbook-proxy` for specifics | Verify `ReadWritePaths` includes all needed dirs |
| Rapid restart loop | `sudo journalctl -u moltbook-proxy` | Fix root cause, or `sudo systemctl stop moltbook-proxy` to halt |
| Env file not loaded | `sudo systemctl show moltbook-proxy -p Environment` | Verify `.env` path and permissions |

---

## Rollback

If the systemd service is not working and you need to revert to interactive mode:

```bash
sudo systemctl stop moltbook-proxy
sudo systemctl disable moltbook-proxy

# Run interactively again
cd /ganuda/services/moltbook_proxy
nohup /home/dereadi/cherokee_venv/bin/python -u proxy_daemon.py > /dev/null 2>&1 &
echo "PID: $!"
```

---

## Acceptance Criteria

- [ ] `.env` file exists at `/ganuda/services/moltbook_proxy/.env` with mode 0600
- [ ] Service file installed at `/etc/systemd/system/moltbook-proxy.service`
- [ ] `systemctl status moltbook-proxy` shows `active (running)`
- [ ] `systemctl is-enabled moltbook-proxy` returns `enabled`
- [ ] Journal logs show successful daemon poll cycles
- [ ] Kill switch test: touch ENGAGEMENT_PAUSED, verify pause in logs, remove file, verify resume
- [ ] Old interactive process (PID 2239377) is no longer running
