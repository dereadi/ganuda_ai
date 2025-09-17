#!/bin/bash
# Start Current-Aware Giants

echo "🔥 STARTING CURRENT-AWARE GIANTS..."
echo "Date: September 15, 2025"
echo "Portfolio: $28,259.85"

# Kill old versions
pkill -f "giant_family" 2>/dev/null
pkill -f "tsulkalu" 2>/dev/null
pkill -f "ganuda" 2>/dev/null
sleep 2

# Start new version
cd /home/dereadi/scripts/claude
nohup python3 giant_family_current.py > /tmp/giant_current.log 2>&1 &
PID=$!

echo "✅ Giants started with PID: $PID"
echo ""
echo "📱 TO TEST:"
echo "1. Open Telegram"
echo "2. Message @ganudabot"
echo "3. Ask 'What can I expect this week?'"
echo "4. Ask 'Can you talk about algorithm updates?'"
echo ""
echo "The Giants now know today is September 15, 2025!"
echo "They will give CURRENT information, not Sept 6-11 data!"