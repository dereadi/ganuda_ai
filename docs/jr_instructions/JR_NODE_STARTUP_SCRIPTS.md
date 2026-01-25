# Jr Task: Create Node Startup Scripts for Jr Agents

**Task ID:** task-node-startup-001
**Priority:** P2 (Operational)
**Created:** December 22, 2025
**TPM:** Cherokee AI Federation

---

## Overview

Each node in the Cherokee AI Federation needs startup scripts to launch Jr bidding daemons and executors on boot. This ensures the distributed task system is always operational.

---

## Current Node Configuration

| Node | IP | Python Path | Jr Agents |
|------|-----|------------|-----------|
| redfin | 192.168.132.223 | `/home/dereadi/cherokee_venv/bin/python3` | jr-redfin-gecko, jr-redfin-eagle |
| bluefin | 192.168.132.222 | `/usr/bin/python3` | jr-bluefin-turtle |
| greenfin | 192.168.132.224 | `/usr/bin/python3` | jr-greenfin-eagle |
| sasass | 192.168.132.241 | `/usr/bin/python3` | jr-sasass-spider |
| bmasass | local | `/opt/homebrew/bin/python3` | jr-bmasass-council, jr-bmasass-tpm |

---

## Scripts Needed

### 1. Linux Nodes (redfin, bluefin, greenfin)

**File:** `/ganuda/scripts/start_jr_agents.sh`

```bash
#!/bin/bash
# Cherokee AI Jr Agent Startup Script
# For Seven Generations

NODE_NAME=$(hostname)
LOG_DIR="/home/dereadi/logs"
JR_DIR="/ganuda/jr_executor"

mkdir -p $LOG_DIR

case $NODE_NAME in
    redfin)
        PYTHON="/home/dereadi/cherokee_venv/bin/python3"
        AGENTS=("jr-redfin-gecko" "jr-redfin-eagle")
        ;;
    bluefin)
        PYTHON="/usr/bin/python3"
        AGENTS=("jr-bluefin-turtle")
        ;;
    greenfin)
        PYTHON="/usr/bin/python3"
        AGENTS=("jr-greenfin-eagle")
        ;;
    *)
        echo "Unknown node: $NODE_NAME"
        exit 1
        ;;
esac

for AGENT in "${AGENTS[@]}"; do
    # Start bidding daemon
    if ! pgrep -f "jr_bidding_daemon.py $AGENT" > /dev/null; then
        echo "Starting bidding daemon for $AGENT"
        cd $JR_DIR
        nohup $PYTHON -u jr_bidding_daemon.py $AGENT $NODE_NAME >> $LOG_DIR/${AGENT}-bidding.log 2>&1 &
    fi

    # Start executor
    if ! pgrep -f "jr_task_executor.py $AGENT" > /dev/null; then
        echo "Starting executor for $AGENT"
        cd $JR_DIR
        nohup $PYTHON -u jr_task_executor.py $AGENT $NODE_NAME >> $LOG_DIR/${AGENT}-executor.log 2>&1 &
    fi
done

echo "Jr agents started on $NODE_NAME"
```

### 2. macOS Nodes (sasass, bmasass)

**File:** `/Users/Shared/ganuda/scripts/start_jr_agents.sh`

```bash
#!/bin/bash
# Cherokee AI Jr Agent Startup Script (macOS)
# For Seven Generations

NODE_NAME=$(hostname -s)
LOG_DIR="$HOME/logs"
JR_DIR="/Users/Shared/ganuda/jr_executor"

mkdir -p $LOG_DIR

case $NODE_NAME in
    sasass|sasass2)
        PYTHON="/usr/bin/python3"
        AGENTS=("jr-sasass-spider")
        ;;
    bmasass|Dereks-MacBook-Pro)
        PYTHON="/opt/homebrew/bin/python3"
        AGENTS=("jr-bmasass-council")
        ;;
    *)
        echo "Unknown node: $NODE_NAME"
        exit 1
        ;;
esac

for AGENT in "${AGENTS[@]}"; do
    # Start bidding daemon
    if ! pgrep -f "jr_bidding_daemon.py $AGENT" > /dev/null; then
        echo "Starting bidding daemon for $AGENT"
        cd $JR_DIR
        nohup $PYTHON -u jr_bidding_daemon.py $AGENT ${NODE_NAME,,} >> $LOG_DIR/${AGENT}-bidding.log 2>&1 &
    fi

    # Start executor
    if ! pgrep -f "jr_task_executor.py $AGENT" > /dev/null; then
        echo "Starting executor for $AGENT"
        cd $JR_DIR
        nohup $PYTHON -u jr_task_executor.py $AGENT ${NODE_NAME,,} >> $LOG_DIR/${AGENT}-executor.log 2>&1 &
    fi
done

echo "Jr agents started on $NODE_NAME"
```

---

## Systemd Service (Linux)

**File:** `/etc/systemd/system/jr-agents.service`

```ini
[Unit]
Description=Cherokee AI Jr Agents
After=network.target postgresql.service

[Service]
Type=forking
User=dereadi
ExecStart=/ganuda/scripts/start_jr_agents.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

**Enable:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable jr-agents
sudo systemctl start jr-agents
```

---

## LaunchAgent (macOS)

**File:** `~/Library/LaunchAgents/com.cherokee.jr-agents.plist`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.cherokee.jr-agents</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/Shared/ganuda/scripts/start_jr_agents.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>
```

**Enable:**
```bash
launchctl load ~/Library/LaunchAgents/com.cherokee.jr-agents.plist
```

---

## Status Check Script

**File:** `/ganuda/scripts/jr_status.sh` or `/Users/Shared/ganuda/scripts/jr_status.sh`

```bash
#!/bin/bash
# Check Jr agent status

echo "=== Jr Agent Status ==="
echo ""
echo "Bidding Daemons:"
pgrep -af jr_bidding_daemon || echo "  None running"
echo ""
echo "Executors:"
pgrep -af jr_task_executor || echo "  None running"
echo ""
echo "Recent Logs:"
tail -5 ~/logs/*-bidding.log 2>/dev/null || echo "  No logs"
```

---

## Deployment Steps

1. Copy startup script to each node
2. Make executable: `chmod +x start_jr_agents.sh`
3. For Linux: Create systemd service and enable
4. For macOS: Create LaunchAgent and load
5. Test: Reboot node and verify agents start

---

*For Seven Generations - Cherokee AI Federation*
