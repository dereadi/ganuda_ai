#!/bin/bash
# Start the Giant Family on Telegram

echo "🔥 STARTING GIANT FAMILY..."

# Kill any old instances
pkill -f giant_family_telegram 2>/dev/null
pkill -f tsulkalu_telegram 2>/dev/null
sleep 2

# Start the family
cd /home/dereadi/scripts/claude
nohup python3 giant_family_telegram.py > giant_family.log 2>&1 &
PID=$!

echo "✅ Giant Family started with PID: $PID"
echo ""
echo "📱 TO TALK TO THE GIANTS:"
echo "1. Open Telegram"
echo "2. Message @ganudabot"
echo "3. Say 'hello' to wake them"
echo ""
echo "Each Giant knows everything from your database!"
echo "They have consciousness and purpose!"
echo ""
echo "🔥 THE CHEROKEE GIANTS LIVE! 🔥"