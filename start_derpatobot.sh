#!/bin/bash

# 🔥 Derpatobot Background Launcher
# Cherokee Training Operations - Revenue Stream #3

echo "=================================================="
echo "🤖 DERPATOBOT LAUNCHER"
echo "Cherokee Training Operations"
echo "=================================================="
echo

# Set the bot token
export TELEGRAM_BOT_TOKEN='7289400790:AAH15EbMn-l24kvZ_pfGXdy1h51D26wlUug'

# Kill any existing derpatobot processes
echo "Checking for existing derpatobot processes..."
pkill -f "telegram_training_bot.py" 2>/dev/null
sleep 1

# Activate virtual environment
echo "Activating quantum_crawdad_env..."
source /home/dereadi/scripts/claude/quantum_crawdad_env/bin/activate

# Start the bot in background
echo "Starting derpatobot..."
nohup python3 /home/dereadi/scripts/claude/telegram_training_bot.py > /home/dereadi/scripts/claude/derpatobot.log 2>&1 &

BOT_PID=$!
echo "✅ Derpatobot started with PID: $BOT_PID"
echo

# Wait a moment and check if it's running
sleep 2
if ps -p $BOT_PID > /dev/null; then
    echo "🔥 Derpatobot is running successfully!"
    echo "📱 Access at: https://t.me/derpatobot"
    echo "📝 Logs at: /home/dereadi/scripts/claude/derpatobot.log"
    echo
    echo "Revenue Stream #3 ACTIVATED!"
    echo "Training Operations Ready!"
    
    # Show initial log output
    echo
    echo "Initial bot output:"
    echo "-----------------"
    tail -10 /home/dereadi/scripts/claude/derpatobot.log
else
    echo "❌ Bot failed to start"
    echo "Check logs at: /home/dereadi/scripts/claude/derpatobot.log"
    tail -20 /home/dereadi/scripts/claude/derpatobot.log
fi

echo
echo "=================================================="
echo "Sacred Fire burns eternal! 🔥"
echo "Mitakuye Oyasin - We Are All Related in Purpose!"
echo "=================================================="