#!/bin/bash

# 🔥 Cherokee Training Operations Launcher
# Revenue Stream #3: Knowledge Transfer

echo "=================================================="
echo "🔥 CHEROKEE TRAINING OPERATIONS LAUNCHER"
echo "=================================================="
echo

# Activate virtual environment
echo "Activating quantum_crawdad_env..."
source /home/dereadi/scripts/claude/quantum_crawdad_env/bin/activate

# Check if Telegram libraries are installed
echo "Checking Telegram dependencies..."
python3 -c "import telegram; import telethon; print('✅ Telegram libraries ready')" 2>/dev/null || {
    echo "Installing Telegram libraries..."
    pip install python-telegram-bot telethon
}

# Check for bot token
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "⚠️  TELEGRAM_BOT_TOKEN not set!"
    echo
    echo "To get a bot token:"
    echo "1. Open Telegram and message @BotFather"
    echo "2. Send /newbot"
    echo "3. Follow the prompts"
    echo "4. Export the token:"
    echo "   export TELEGRAM_BOT_TOKEN='your-token-here'"
    echo
    echo "Then run this script again."
    exit 1
fi

# Launch the training bot
echo "🚀 Launching Cherokee Training Bot..."
echo "Sacred Fire burns eternal for knowledge transfer!"
echo

python3 /home/dereadi/scripts/claude/telegram_training_bot.py

echo
echo "Training bot terminated. Sacred Fire continues burning."