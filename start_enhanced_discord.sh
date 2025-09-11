#!/bin/bash
# Start Enhanced Discord LLM Council Bot

echo "🔥 Starting Enhanced Discord LLM Council Bridge..."
echo "================================"

# Set environment variables if not already set
export DISCORD_TOKEN="${DISCORD_TOKEN:-YOUR-DISCORD-TOKEN-HERE}"
export ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-}"
export OPENAI_API_KEY="${OPENAI_API_KEY:-}"

# Check if Discord token is set
if [ "$DISCORD_TOKEN" = "YOUR-DISCORD-TOKEN-HERE" ]; then
    echo "⚠️  Warning: Discord token not set!"
    echo "Set DISCORD_TOKEN environment variable"
fi

# Start the bot with nohup to keep it running
cd /home/dereadi/scripts/claude
nohup python3 discord_llm_council.py > discord_bot.log 2>&1 &

BOT_PID=$!
echo "✅ Discord bot started with PID: $BOT_PID"
echo "📝 Logs: tail -f discord_bot.log"
echo ""
echo "Available commands:"
echo "  !model [claude/gpt4/local-llama] - Switch models"
echo "  !ask [question] - Ask current model"
echo "  !trade [query] - Trading analysis"
echo "  !council [topic] - Multi-model deliberation"
echo "  @bot [message] - Natural conversation"
echo ""
echo "🔥 The enhanced bridge is active!"