#!/bin/bash
# Start Discord LLM Council Bot with all API keys

echo "🔥 Starting Discord LLM Council Bot..."

# Set all API keys
export DISCORD_TOKEN="MTQwNjcwNDE4ODY3MDQ3NjMyOQ.GdGCva.PMvVe_aNTTgJ1U8Zh1W6_oSIckyEwdR-6WHk9A"
export ANTHROPIC_API_KEY="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"
export OPENAI_API_KEY="sk-proj-yzn7JGhnKmofTNMlLwidMIGoh_hTfAsPS_qWweyvKLmlzMi1GGWUZJQbx9lRfZuC2F_AW4gIACT3BlbkFJ9xOHiRASDcW3gkv0qdOteX1pyVHcrwqV-a-7mLOt"

# Kill any existing bot
pkill -f discord_llm_council.py 2>/dev/null
sleep 2

# Start the bot
cd /home/dereadi/scripts/claude
nohup python3 discord_llm_council.py > discord_bot_live.log 2>&1 &

BOT_PID=$!
echo "✅ Bot started with PID: $BOT_PID"
echo ""
echo "📝 To check logs: tail -f discord_bot_live.log"
echo "🛑 To stop: kill $BOT_PID"
echo ""
echo "🔥 Bot features:"
echo "  • Claude (Anthropic) support ✅"
echo "  • GPT-4 (OpenAI) support ✅"
echo "  • Model switching with !model"
echo "  • Trading analysis with !trade"
echo "  • @ mention for conversations"
echo ""
echo "The enhanced Council Bridge is active!"