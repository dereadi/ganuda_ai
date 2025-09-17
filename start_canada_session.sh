#!/bin/bash
# Start the Canada persistent session

echo "🔥 Starting Cherokee Canada Persistent Session"
echo "=============================================="

# Check if session already exists
if screen -list | grep -q "claude-canada"; then
    echo "⚠️  Session 'claude-canada' already exists!"
    echo "To reattach: screen -r claude-canada"
    echo "To kill it: screen -X -S claude-canada quit"
    exit 1
fi

# Start new screen session
echo "Starting screen session 'claude-canada'..."
screen -dmS claude-canada bash -c '
echo "🔥 CHEROKEE CANADA SESSION ACTIVE"
echo "================================="
echo ""
echo "Starting Telegram bot..."
cd /home/dereadi/scripts/claude
/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3 persistent_canada_bot.py
'

sleep 2

# Check if it started
if screen -list | grep -q "claude-canada"; then
    echo "✅ Session started successfully!"
    echo ""
    echo "To view the session: screen -r claude-canada"
    echo "To detach: Press Ctrl-A, then D"
    echo "To see messages: cat CANADA_MESSAGES.log"
    echo ""
    echo "🔥 The bot is now running 24/7!"
    echo "Send messages to @ganudabot from Canada!"
else
    echo "❌ Failed to start session"
fi
