#!/bin/bash
# Start Multi-LLM Discord Bot with all API keys

echo "🤖 Starting Multi-LLM Discord Bot..."
echo "===================================="

# Set all API keys
export DISCORD_TOKEN="MTQwNjcwNDE4ODY3MDQ3NjMyOQ.GdGCva.PMvVe_aNTTgJ1U8Zh1W6_oSIckyEwdR-6WHk9A"
export ANTHROPIC_API_KEY="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"
export OPENAI_API_KEY="sk-proj-yzn7JGhnKmofTNMlLwidMIGoh_hTfAsPS_qWweyvKLmlzMi1GGWUZJQbx9lRfZuC2F_AW4gIACT3BlbkFJ9xOHiRASDcW3gkv0qdOteX1pyVHcrwqV-a-7mLOt"
export GEMINI_API_KEY="AIzaSyBQgOshjFXBwQxqQzg0dQuaUCUlTJ23aKc"

# Kill any existing Discord bots
echo "Stopping existing bots..."
pkill -f discord_llm_council.py 2>/dev/null
pkill -f discord_multi_llm_bot.py 2>/dev/null
pkill -f run_discord_bot.py 2>/dev/null
sleep 2

# Install required packages if needed
echo "Checking dependencies..."
pip3 install -q discord.py anthropic openai google-generativeai 2>/dev/null

# Start the bot
cd /home/dereadi/scripts/claude
echo ""
echo "🚀 Launching bot..."
python3 discord_multi_llm_bot.py