# Startup script with all required environment variables
#!/bin/bash
# Cherokee Chief Telegram Bot Startup
# For Seven Generations - Cherokee AI Federation

export TELEGRAM_BOT_TOKEN='7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8'
export TELEGRAM_GROUP_CHAT_ID='-1001234567890'  # TODO: Get actual group ID
export GATEWAY_URL='http://localhost:8080'

cd /ganuda/telegram_bot

# Kill any existing instance
pkill -f telegram_chief.py 2>/dev/null
sleep 2

# Start with logging
echo "[$(date)] Starting Cherokee Chief Telegram Bot..."
/home/dereadi/cherokee_venv/bin/python3 telegram_chief.py >> /ganuda/logs/telegram_chief.log 2>&1 &

PID=$!
echo $PID > /ganuda/telegram_bot/telegram_chief.pid
echo "[$(date)] Bot started with PID $PID"