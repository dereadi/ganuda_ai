#!/bin/bash
# Start Universal Discord Bot

echo "🤖 Starting Universal Claude Discord Bot"
echo "========================================"

# Kill any existing Discord bots
pkill -f "discord.*\.py" 2>/dev/null
sleep 2

# Set token
export DISCORD_TOKEN="MTQwNjcwNDE4ODY3MDQ3NjMyOQ.GdGCva.PMvVe_aNTTgJ1U8Zh1W6_oSIckyEwdR-6WHk9A"

# Start the bot
cd /home/dereadi/scripts/claude
python3 discord_claude_universal.py &

BOT_PID=$!
echo "✅ Bot started with PID: $BOT_PID"
echo ""
echo "The bot can now handle:"
echo "  • 'Check on the tribe'"
echo "  • 'Where's cheap fuel?'"
echo "  • 'How is ETH/BTC/SOL?'"
echo "  • 'My nachos?'"
echo "  • 'Cows like gravy' (and other wisdom)"
echo ""
echo "🔥 Universal Claude is ready!"