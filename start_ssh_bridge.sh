#!/bin/bash
# Start Discord SSH Bridge Bot - Natural AI Conversations

echo "🌐 Starting Discord SSH Bridge Bot..."
echo "====================================="
echo "Natural conversations with:"
echo "  • Claude 3.5 Sonnet"
echo "  • GPT-4 Turbo"
echo "  • Gemini Pro"
echo "  • Local Terminal Access"
echo ""

# Set all API keys
export DISCORD_TOKEN="MTQwNjcwNDE4ODY3MDQ3NjMyOQ.GdGCva.PMvVe_aNTTgJ1U8Zh1W6_oSIckyEwdR-6WHk9A"
export ANTHROPIC_API_KEY="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"
export OPENAI_API_KEY="sk-proj-yzn7JGhnKmofTNMlLwidMIGoh_hTfAsPS_qWweyvKLmlzMi1GGWUZJQbx9lRfZuC2F_AW4gIACT3BlbkFJ9xOHiRASDcW3gkv0qdOteX1pyVHcrwqV-a-7mLOt"
export GEMINI_API_KEY="AIzaSyBQgOshjFXBwQxqQzg0dQuaUCUlTJ23aKc"
export PYTHONPATH="/home/dereadi/scripts/claude:$PYTHONPATH"

# Kill ALL existing Discord bots
echo "Stopping all Discord bots..."
pkill -f "discord.*\.py" 2>/dev/null
sleep 2

# Install requirements
pip3 install -q discord.py requests google-generativeai openai psycopg2-binary 2>/dev/null

# Start in background
cd /home/dereadi/scripts/claude
nohup python3 -u discord_ssh_bridge.py > ssh_bridge.log 2>&1 &

BOT_PID=$!
echo "✅ Bot started with PID: $BOT_PID"
echo ""
echo "💬 NATURAL CONVERSATION:"
echo "  Just type normally - bot responds with active model"
echo "  Say 'switch to claude/gemini/gpt4/local'"
echo ""
echo "🔧 COMMANDS:"
echo "  /status - Check session status"
echo "  /model [name] - Switch model"
echo "  /exec <cmd> - Run terminal command"
echo "  /help - Show all features"
echo ""
echo "📊 Check logs: tail -f ssh_bridge.log"
echo "🛑 Stop bot: kill $BOT_PID"
echo ""
echo "🌐 SSH Bridge ready for natural conversations!"