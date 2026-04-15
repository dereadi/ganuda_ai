#!/bin/bash
# Chiefs Deliberation Cron Job Diagnostic Script
# Run this on redfin as a user with sudo privileges
# Usage: sudo bash diagnose_chiefs_cron.sh

echo "=============================================================================="
echo "CHIEFS DELIBERATION CRON JOB DIAGNOSTIC"
echo "Date: $(date)"
echo "Host: $(hostname)"
echo "User: $(whoami)"
echo "=============================================================================="
echo ""

echo "STEP 1: View Exact Cron Command"
echo "=============================================================================="
sudo crontab -u dereadi -l | grep -v "^#" | grep chiefs
if [ $? -ne 0 ]; then
    echo "❌ No cron job found containing 'chiefs'"
    echo "Expected: */5 * * * * cd /home/dereadi && source cherokee_venv/bin/activate && python3 /home/dereadi/it_triad/it_triad_chiefs_agent.py >> /u/ganuda/logs/chiefs_deliberation.log 2>&1"
else
    echo "✅ Cron job found"
fi
echo ""

echo "STEP 2: Check Log Directory Status"
echo "=============================================================================="
ls -lah /u/ganuda/logs/ 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Log directory does not exist: /u/ganuda/logs/"
    echo "Creating log directory..."
    sudo -u dereadi mkdir -p /u/ganuda/logs
    sudo chown dereadi:dereadi /u/ganuda/logs
    sudo chmod 755 /u/ganuda/logs
    echo "✅ Log directory created"
    ls -lah /u/ganuda/logs/
else
    echo "✅ Log directory exists"
fi
echo ""

echo "STEP 3: Check Queue File Status"
echo "=============================================================================="
ls -lah /u/ganuda/chiefs_pending_decisions.json 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Queue file does not exist"
else
    echo "✅ Queue file exists"
    echo "Queue file size: $(du -h /u/ganuda/chiefs_pending_decisions.json | cut -f1)"
fi
echo ""

echo "STEP 4: Verify Python Virtual Environment"
echo "=============================================================================="
sudo -u dereadi bash << 'VENVEOF'
cd /home/dereadi
source cherokee_venv/bin/activate
echo "Python: $(which python3)"
echo "Python version: $(python3 --version)"
echo ""
echo "Checking required packages..."
python3 -c "import psycopg2; print('✅ psycopg2 version:', psycopg2.__version__)" 2>&1
python3 -c "import json; print('✅ json: OK')" 2>&1
python3 -c "from datetime import datetime, timezone; print('✅ datetime: OK')" 2>&1
VENVEOF
echo ""

echo "STEP 5: Test Database Connection"
echo "=============================================================================="
sudo -u dereadi bash << 'DBEOF'
cd /home/dereadi
source cherokee_venv/bin/activate
python3 << 'PYEOF'
import psycopg2
try:
    conn = psycopg2.connect(
        host="192.168.132.222",
        user="claude",
        password="jawaseatlasers2",
        database="triad_federation"
    )
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM triad_shared_memories;")
    count = cur.fetchone()[0]
    print(f"✅ Database connection successful")
    print(f"✅ Thermal memory has {count} entries")
    conn.close()
except Exception as e:
    print(f"❌ Database connection failed: {str(e)}")
PYEOF
DBEOF
echo ""

echo "STEP 6: Manual Test Run of Chiefs Agent"
echo "=============================================================================="
echo "Running Chiefs agent manually (timeout: 30 seconds)..."
sudo -u dereadi bash << 'AGENTEOF'
cd /home/dereadi
source cherokee_venv/bin/activate
timeout 30 python3 /home/dereadi/it_triad/it_triad_chiefs_agent.py 2>&1
AGENTEOF
AGENT_EXIT=$?
echo ""
echo "Agent exit code: $AGENT_EXIT"
if [ $AGENT_EXIT -eq 124 ]; then
    echo "⚠️  Agent timed out after 30 seconds (may be processing large queue)"
elif [ $AGENT_EXIT -eq 0 ]; then
    echo "✅ Agent completed successfully"
else
    echo "❌ Agent failed with exit code: $AGENT_EXIT"
fi
echo ""

echo "STEP 7: Check Cron Service Status"
echo "=============================================================================="
systemctl status cron | head -20
echo ""

echo "STEP 8: Check Recent Cron Execution Logs"
echo "=============================================================================="
echo "Recent cron executions for dereadi user:"
journalctl -u cron -n 20 --no-pager | grep dereadi
echo ""

echo "STEP 9: Check System Logs for CRON"
echo "=============================================================================="
echo "Recent CRON entries in syslog:"
tail -50 /var/log/syslog | grep CRON | grep dereadi
echo ""

echo "=============================================================================="
echo "DIAGNOSTIC COMPLETE"
echo "=============================================================================="
echo ""
echo "Next steps:"
echo "1. Review the output above for any errors"
echo "2. Common issues to look for:"
echo "   - Missing log directory (/u/ganuda/logs/)"
echo "   - Missing Python packages (psycopg2)"
echo "   - Database connection failures"
echo "   - Python errors during manual test run"
echo ""
echo "3. If the manual test run succeeded, check:"
echo "   ls -lah /u/ganuda/logs/chiefs_deliberation.log"
echo "   tail -50 /u/ganuda/logs/chiefs_deliberation.log"
echo ""
