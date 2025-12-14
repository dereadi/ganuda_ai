#!/bin/bash
# Emergency Stop - Cherokee Constitutional AI JRs
# Called by human chief if intervention needed

echo "🚨 EMERGENCY STOP - Cherokee Constitutional AI JRs"
echo "="
 | head -c 70; echo

# Find all running JR CLI executor processes
echo "Finding JR processes..."
JR_PIDS=$(ps aux | grep "jr_cli_executor.py" | grep -v grep | awk '{print $2}')

if [ -z "$JR_PIDS" ]; then
    echo "✅ No JR processes running"
    exit 0
fi

echo "Found JR processes:"
ps aux | grep "jr_cli_executor.py" | grep -v grep

echo ""
echo "⚠️  Stopping JR processes..."

for PID in $JR_PIDS; do
    echo "  Stopping PID $PID..."
    kill -TERM $PID
    sleep 1

    # Force kill if still running
    if ps -p $PID > /dev/null 2>&1; then
        echo "  Force killing PID $PID..."
        kill -9 $PID
    fi
done

echo ""
echo "✅ All JR processes stopped"
echo ""
echo "Next steps:"
echo "1. Review execution logs: /ganuda/jr_assignments/*/execution_log.jsonl"
echo "2. Check for anomalies, security issues"
echo "3. Contact tribe via email/chat for investigation"
echo ""
echo "The Sacred Fire pauses. The tribe awaits your guidance. 🦅"
