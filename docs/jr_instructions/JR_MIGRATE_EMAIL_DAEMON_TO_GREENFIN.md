# Jr Build Instructions: Migrate Job Email Daemon to Greenfin

**Task ID:** JR-MIGRATE-EMAIL-001
**Priority:** P2 (High - Proper resource distribution)
**Date:** 2025-12-26
**Author:** TPM
**Source:** Node distribution optimization - CPU work off GPU node

---

## Problem Statement

The job email daemon is currently running on redfin (192.168.132.223), which has the RTX 6000 GPU. This is CPU work that should run on greenfin to keep redfin dedicated to GPU inference.

**Current State:**
- `job_email_daemon_v2.py` running on redfin
- Gmail OAuth credentials on redfin at `~/.gmail_credentials/`
- Database is on bluefin (accessible from any node)

**Target State:**
- Daemon runs on greenfin (192.168.132.224)
- Gmail credentials copied to greenfin
- redfin only runs vLLM and LLM Gateway

---

## Node Distribution

| Node | Role | Should Run |
|------|------|------------|
| **greenfin** | CPU Daemons | Email daemon, web automation, monitoring |
| **bluefin** | Database | PostgreSQL, data processing |
| **redfin** | GPU Inference | vLLM, LLM Gateway ONLY |
| **sasass/sasass2** | Mac Studios | Edge inference (MLX), testing |
| **tpm-macbook** | TPM Laptop | Orchestration, development |

---

## Implementation Steps

### Step 1: Copy Gmail Credentials to Greenfin

On greenfin:
```bash
# Create credentials directory
mkdir -p ~/.gmail_credentials

# Copy from redfin (run from any node with SSH access)
scp dereadi@192.168.132.223:~/.gmail_credentials/token.pickle ~/.gmail_credentials/
scp dereadi@192.168.132.223:~/.gmail_credentials/credentials.json ~/.gmail_credentials/
```

### Step 2: Copy Daemon Files to Greenfin

```bash
# Create email_daemon directory on greenfin
ssh dereadi@192.168.132.224 "mkdir -p /ganuda/email_daemon"

# Copy files from redfin
scp dereadi@192.168.132.223:/ganuda/email_daemon/job_email_daemon_v2.py dereadi@192.168.132.224:/ganuda/email_daemon/
scp dereadi@192.168.132.223:/ganuda/email_daemon/job_matcher.py dereadi@192.168.132.224:/ganuda/email_daemon/
scp dereadi@192.168.132.223:/ganuda/email_daemon/config.json dereadi@192.168.132.224:/ganuda/email_daemon/
```

### Step 3: Install Dependencies on Greenfin

```bash
ssh dereadi@192.168.132.224 "~/cherokee_venv/bin/pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client python-telegram-bot"
```

### Step 4: Update Config for Greenfin

The daemon should call redfin's LLM Gateway over the network (not localhost). Check `config.json`:

```json
{
    "llm_gateway": "http://192.168.132.223:8080",
    "database_host": "192.168.132.222",
    "telegram_enabled": true
}
```

### Step 5: Stop Daemon on Redfin

```bash
ssh dereadi@192.168.132.223 "pkill -f job_email_daemon"
```

### Step 6: Start Daemon on Greenfin

```bash
ssh dereadi@192.168.132.224 "cd /ganuda/email_daemon && nohup ~/cherokee_venv/bin/python3 -u job_email_daemon_v2.py > /var/log/ganuda/job_email_daemon.log 2>&1 &"
```

### Step 7: Verify Migration

```bash
# Check daemon is running on greenfin
ssh dereadi@192.168.132.224 "ps aux | grep job_email_daemon | grep -v grep"

# Check logs
ssh dereadi@192.168.132.224 "tail -20 /var/log/ganuda/job_email_daemon.log"

# Verify redfin is clear
ssh dereadi@192.168.132.223 "ps aux | grep job_email_daemon | grep -v grep"
```

---

## Rollback

If issues occur, restart on redfin:
```bash
ssh dereadi@192.168.132.223 "cd /ganuda/email_daemon && nohup ~/cherokee_venv/bin/python3 -u job_email_daemon_v2.py > /var/log/ganuda/job_email_daemon.log 2>&1 &"
```

---

## Systemd Service (Future)

For production, create `/etc/systemd/system/job-email-daemon.service` on greenfin:

```ini
[Unit]
Description=Cherokee Job Email Daemon
After=network.target

[Service]
Type=simple
User=dereadi
WorkingDirectory=/ganuda/email_daemon
ExecStart=/home/dereadi/cherokee_venv/bin/python3 -u job_email_daemon_v2.py
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable job-email-daemon
sudo systemctl start job-email-daemon
```

---

*For Seven Generations - Cherokee AI Federation*
*"Put CPU work where CPUs live, GPU work where GPUs live"*
