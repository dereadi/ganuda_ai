#!/bin/bash
# Launch Multi-LLM Discord Bot in background

echo "🤖 Launching Multi-LLM Discord Bot in background..."

# Set all API keys
export DISCORD_TOKEN="MTQwNjcwNDE4ODY3MDQ3NjMyOQ.GdGCva.PMvVe_aNTTgJ1U8Zh1W6_oSIckyEwdR-6WHk9A"
export ANTHROPIC_API_KEY="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"
export OPENAI_API_KEY="sk-proj-yzn7JGhnKmofTNMlLwidMIGoh_hTfAsPS_qWweyvKLmlzMi1GGWUZJQbx9lRfZuC2F_AW4gIACT3BlbkFJ9xOHiRASDcW3gkv0qdOteX1pyVHcrwqV-a-7mLOt"
export GEMINI_API_KEY="AIzaSyBQgOshjFXBwQxqQzg0dQuaUCUlTJ23aKc"

# Kill existing bots
pkill -f discord_multi_llm_bot.py 2>/dev/null
pkill -f discord_llm_council.py 2>/dev/null
sleep 2

# Start in background
cd /home/dereadi/scripts/claude
nohup python3 -u discord_multi_llm_bot.py > discord_multi_llm.log 2>&1 &

BOT_PID=$!
echo "✅ Bot started with PID: $BOT_PID"
echo ""
echo "📝 Commands:"
echo "  !model [claude/gpt4/gemini] - Switch models"
echo "  !ask [question] - Ask current model"
echo "  !compare [question] - Compare all models"
echo "  !status - Check bot status"
echo "  !help - Show all commands"
echo ""
echo "📊 Check logs: tail -f discord_multi_llm.log"
echo "🛑 Stop bot: kill $BOT_PID"