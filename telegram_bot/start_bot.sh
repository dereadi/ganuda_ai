#!/bin/bash
# Start Cherokee Chief Telegram Bot

cd /ganuda/telegram_bot

# Check for existing instance
if pgrep -f "telegram_chief.py" > /dev/null; then
    echo "Bot already running. Killing old instance..."
    pkill -f "telegram_chief.py"
    sleep 2
fi

# Export token
export TELEGRAM_BOT_TOKEN="YOUR_BOT_TOKEN_HERE"

# Start with logging
echo "Starting Cherokee Chief Telegram Bot..."
/home/dereadi/cherokee_venv/bin/python3 telegram_chief.py >> /tmp/telegram_chief.log 2>&1 &

echo "Bot started. PID: $!"
echo "Logs: tail -f /tmp/telegram_chief.log"