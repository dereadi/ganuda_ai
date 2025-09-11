#!/bin/bash
# Start Unified AI Discord Bot (Claude + Gemini)

echo "🤖 Starting Unified AI Discord Bot..."
echo "====================================="

# Set API keys
export DISCORD_TOKEN="MTQwNjcwNDE4ODY3MDQ3NjMyOQ.GdGCva.PMvVe_aNTTgJ1U8Zh1W6_oSIckyEwdR-6WHk9A"
export ANTHROPIC_API_KEY="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"
export GEMINI_API_KEY="AIzaSyBQgOshjFXBwQxqQzg0dQuaUCUlTJ23aKc"

# Kill all existing Discord bots
echo "Stopping existing bots..."
pkill -f discord_claude_simple.py 2>/dev/null
pkill -f discord_multi_llm_bot.py 2>/dev/null
pkill -f discord_unified_bot.py 2>/dev/null
sleep 2

# Install requirements
pip3 install -q discord.py requests google-generativeai 2>/dev/null

# Start in background
cd /home/dereadi/scripts/claude
nohup python3 -u discord_unified_bot.py > unified_bot.log 2>&1 &

BOT_PID=$!
echo "✅ Bot started with PID: $BOT_PID"
echo ""
echo "📝 Commands:"
echo "  !model [claude/gemini] - Switch AI models"
echo "  !ask [question] - Ask current model"
echo "  !clear - Clear conversation history"
echo "  !status - Check bot status"
echo "  !help - Show all commands"
echo "  @mention - Chat with bot"
echo ""
echo "📊 Check logs: tail -f unified_bot.log"
echo "🛑 Stop bot: kill $BOT_PID"