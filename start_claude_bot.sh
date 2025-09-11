#!/bin/bash
# Start Simple Claude Discord Bot

echo "🤖 Starting Simple Claude Discord Bot..."

# Set API keys
export DISCORD_TOKEN="MTQwNjcwNDE4ODY3MDQ3NjMyOQ.GdGCva.PMvVe_aNTTgJ1U8Zh1W6_oSIckyEwdR-6WHk9A"
export ANTHROPIC_API_KEY="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"

# Kill existing bots
pkill -f discord_multi_llm_bot.py 2>/dev/null
pkill -f discord_claude_simple.py 2>/dev/null
sleep 2

# Install requirements
pip3 install -q discord.py requests 2>/dev/null

# Start in background
cd /home/dereadi/scripts/claude
nohup python3 -u discord_claude_simple.py > claude_bot.log 2>&1 &

BOT_PID=$!
echo "✅ Bot started with PID: $BOT_PID"
echo ""
echo "📝 Commands:"
echo "  !ask [question] - Ask Claude"
echo "  !clear - Clear conversation history"
echo "  @mention - Chat with Claude"
echo ""
echo "📊 Check logs: tail -f claude_bot.log"
echo "🛑 Stop bot: kill $BOT_PID"