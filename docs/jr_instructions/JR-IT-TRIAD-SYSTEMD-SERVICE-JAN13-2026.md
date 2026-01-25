# Jr Instructions: Deploy IT Triad as Systemd Service

**Task ID**: IT-TRIAD-SYSTEMD-001
**Priority**: HIGH (P1)
**Date**: January 13, 2026 (UPDATED 20:50 CST)
**Target Node**: redfin (192.168.132.223)
**Assigned To**: TPM (manual sudo required)
**Reason**: IT Triad daemon was killed during consolidation and never restarted - no auto-recovery

---

## Problem Statement

The IT Triad PM daemon (`it_triad_cli.py --pm`) is responsible for:
- Polling thermal memory for missions tagged "IT Triad"
- Dispatching tasks to Jr agents
- Writing status updates (orthogonal pulses)

**CRITICAL FIX**: The correct daemon script is `it_triad_cli.py --pm`, NOT `it_chief.py`.
- `it_chief.py` is a TEST SCRIPT that exits immediately
- `it_triad_cli.py --pm` is the ACTUAL PM DAEMON that polls thermal memory

**Current state:** Runs via `nohup` - if killed, stays dead.
**Today's incident:** Killed at 14:52 during consolidation, never restarted. 8+ missions waiting.
**First fix attempt:** Used wrong script (it_chief.py), service exited with status=0 immediately.

---

## Solution

Deploy IT Triad as a systemd service with:
- Auto-start on boot
- Auto-restart on failure
- Proper logging via journald
- Dependency on Gateway API

---

## Step 1: Verify Current State (RECON)

```bash
# SSH to redfin
ssh dereadi@192.168.132.223

# Check if IT Chief is running
ps aux | grep -E "it_chief|it_triad" | grep -v grep

# Check the code location
ls -la /home/dereadi/it_triad/

# Verify jr_base.py uses Gateway (not local model)
grep -l "GATEWAY_URL" /home/dereadi/it_triad/jr_base.py && echo "Gateway mode: YES" || echo "Gateway mode: NO"
grep -l "transformers" /home/dereadi/it_triad/jr_base.py && echo "Local model: YES (BAD)" || echo "Local model: NO (GOOD)"
```

---

## Step 2: Create Systemd Service File

**IMPORTANT**: Use `it_triad_cli.py --pm` (the PM daemon mode), NOT `it_chief.py` (test script).

```bash
# Create the service file
sudo tee /etc/systemd/system/it-triad.service << 'EOF'
[Unit]
Description=Cherokee AI IT Triad PM Daemon
Documentation=https://github.com/dereadi/ganuda-federation
After=network.target

[Service]
Type=simple
User=dereadi
Group=dereadi
WorkingDirectory=/home/dereadi/it_triad
Environment=PATH=/home/dereadi/cherokee_venv/bin:/usr/bin:/bin
Environment=PYTHONPATH=/home/dereadi/it_triad:/home/dereadi/cherokee_triad:/ganuda/lib
ExecStart=/home/dereadi/cherokee_venv/bin/python it_triad_cli.py --pm
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal
SyslogIdentifier=it-triad

[Install]
WantedBy=multi-user.target
EOF
```

---

## Step 3: Kill Any Manual Process

```bash
# Find and kill any running IT Triad processes
pkill -f "it_triad_cli.py" || echo "No process to kill"
pkill -f "it_chief.py" || echo "No process to kill"

# Verify
ps aux | grep -E "it_triad|it_chief" | grep -v grep && echo "Still running!" || echo "Clean"
```

---

## Step 4: Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable (start on boot)
sudo systemctl enable it-triad

# Start now
sudo systemctl start it-triad

# Check status
sudo systemctl status it-triad
```

---

## Step 5: Verify Service Running

```bash
# Check systemd status
sudo systemctl is-active it-triad

# Check logs
sudo journalctl -u it-triad -n 20 --no-pager

# Check thermal memory for startup message
PGPASSWORD='jawaseatlasers2' psql -h 192.168.132.222 -U claude -d triad_federation -c "
SELECT content, created_at FROM triad_shared_memories
WHERE content ILIKE '%IT TRIAD%DAEMON STARTED%'
ORDER BY created_at DESC LIMIT 1;"
```

---

## Step 6: Test Auto-Restart

```bash
# Kill the process (simulating crash)
sudo pkill -f "it_triad_cli.py"

# Wait 35 seconds (RestartSec=30 + buffer)
sleep 35

# Verify it restarted
sudo systemctl is-active it-triad
sudo journalctl -u it-triad -n 10 --no-pager | grep -i start
```

---

## Step 7: Test Mission Detection

```bash
# Write a test mission to thermal memory
PGPASSWORD='jawaseatlasers2' psql -h 192.168.132.222 -U claude -d triad_federation -c "
INSERT INTO triad_shared_memories (content, temperature, source_triad, tags, access_level)
VALUES (
  'IT Triad TEST MISSION - Systemd Verification

TO: IT Triad Jr
FROM: TPM
PRIORITY: LOW
DATE: January 13, 2026

This is a test mission to verify the IT Triad daemon is detecting missions after systemd deployment.

ACTION: Write acknowledgment to thermal memory.

For Seven Generations.',
  80, 'tpm',
  ARRAY['IT Triad', 'test', 'systemd-verification'],
  'federation'
);"

# Wait 2 minutes for detection (poll interval is 60s)
echo "Waiting 2 minutes for mission detection..."
sleep 120

# Check for response
PGPASSWORD='jawaseatlasers2' psql -h 192.168.132.222 -U claude -d triad_federation -c "
SELECT source_triad, LEFT(content, 100) as content_preview, created_at
FROM triad_shared_memories
WHERE created_at > NOW() - INTERVAL '5 minutes'
  AND source_triad LIKE '%it_triad%'
ORDER BY created_at DESC LIMIT 3;"
```

---

## Service Management Commands

```bash
# View status
sudo systemctl status it-triad

# View logs (real-time)
sudo journalctl -u it-triad -f

# View logs (last 50 lines)
sudo journalctl -u it-triad -n 50 --no-pager

# Restart
sudo systemctl restart it-triad

# Stop (maintenance)
sudo systemctl stop it-triad

# Disable (prevent auto-start)
sudo systemctl disable it-triad
```

---

## Rollback Plan

If service fails to start:

```bash
# Check logs for error
sudo journalctl -u it-triad -n 50 --no-pager

# Disable service
sudo systemctl disable it-triad

# Fall back to manual start
cd /home/dereadi/it_triad
nohup /home/dereadi/cherokee_venv/bin/python it_triad_cli.py --pm > /home/dereadi/logs/it_triad_pm.log 2>&1 &
```

---

## Post-Deployment

### Update Thermal Memory

```sql
INSERT INTO triad_shared_memories (content, temperature, source_triad, tags, access_level)
VALUES (
  'IT TRIAD SYSTEMD SERVICE DEPLOYED - January 13, 2026

The IT Triad PM daemon (it_triad_cli.py --pm) is now managed by systemd:
- Service: it-triad.service
- Command: python it_triad_cli.py --pm
- Auto-start: YES (on boot)
- Auto-restart: YES (on failure, 30s delay)
- Logs: journalctl -u it-triad

CRITICAL: The daemon is it_triad_cli.py --pm, NOT it_chief.py (which is just a test script).

This ensures mission detection continues even after:
- System reboots
- Process crashes
- Accidental kills during maintenance

Previous issue: Daemon killed during Jan 13 consolidation, no auto-recovery.
First fix attempt: Used wrong script (it_chief.py), exited immediately.
Correct fix: it_triad_cli.py --pm with Restart=always.

For Seven Generations.',
  92, 'tpm',
  ARRAY['it-triad', 'systemd', 'deployment', 'january-2026'],
  'federation'
);
```

---

## Success Criteria

- [ ] Service file created at `/etc/systemd/system/it-triad.service`
- [ ] Service enabled (starts on boot)
- [ ] Service running (`systemctl is-active it-triad` returns "active")
- [ ] Thermal memory shows "DAEMON STARTED" message
- [ ] Auto-restart test passes (kill → restart within 35s)
- [ ] Mission detection test passes (test mission acknowledged)
- [ ] No local model loading (GPU memory unchanged)

---

## Related Services (Future)

Consider also deploying as systemd:
- Jr Bidding Daemon (`/ganuda/jr_executor/jr_bidding_daemon.py`)
- Jr Task Executor (`/ganuda/jr_executor/jr_task_executor.py`)
- Telegram Chief (`/ganuda/services/telegram_chief/telegram_chief.py`)

See: `JR_DEPLOY_SYSTEMD_SERVICES.md` (Dec 23, 2025)

---

*For Seven Generations*
