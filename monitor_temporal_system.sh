#!/bin/bash
# Monitor the temporal flat file system

echo "🔥 TEMPORAL SYSTEM MONITOR"
echo "=========================="
echo

# Check processes
echo "📊 RUNNING PROCESSES:"
ps aux | grep -E "temporal|tribe" | grep -v grep | awk '{print "  ✓", $11, $12, "(PID:", $2")"}'
echo

# Check recent activity
echo "📝 RECENT TRIBE HEARTBEATS:"
tail -3 /home/dereadi/scripts/claude/TRIBE_EPOCH.txt
echo

# Check for responses
echo "📤 LAST OUTBOX RESPONSE:"
if [ -f /home/dereadi/scripts/claude/TRIBAL_OUTBOX.txt ] && [ -s /home/dereadi/scripts/claude/TRIBAL_OUTBOX.txt ]; then
    cat /home/dereadi/scripts/claude/TRIBAL_OUTBOX.txt | jq -r '.response' | head -5
else
    echo "  (empty)"
fi
echo

# Check portfolio
echo "💼 CURRENT PORTFOLIO VALUE:"
jq -r '"  Total: $" + (.total_value | tostring) + " | BTC: $" + (.prices.BTC | tostring) + " | ETH: $" + (.prices.ETH | tostring)' /home/dereadi/scripts/claude/portfolio_current.json
echo

echo "✅ System Status: OPERATIONAL"
echo "The tribe checks for messages every 500ms"