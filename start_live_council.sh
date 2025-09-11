#!/bin/bash
# Start Live Cherokee AI Council with Real LLMs

echo "🏛️ Starting Live Cherokee AI Council..."
echo "======================================"
echo "Real LLM council members:"
echo "  • Oracle (70B) on sasass2"
echo "  • Crawdad (13B) on bluefin"
echo "  • Turtle (7B) on bluefin"
echo "  • Eagle (34B) on redfin"
echo "  • Peace Chief Claude"
echo ""

# Set environment
export DISCORD_TOKEN="MTQwNjcwNDE4ODY3MDQ3NjMyOQ.GdGCva.PMvVe_aNTTgJ1U8Zh1W6_oSIckyEwdR-6WHk9A"
export ANTHROPIC_API_KEY="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"

# Kill existing bots
echo "Stopping existing bots..."
pkill -f "discord.*\.py" 2>/dev/null
sleep 2

# Start the live council
cd /home/dereadi/scripts/claude
nohup python3 -u discord_council_live.py > live_council.log 2>&1 &

BOT_PID=$!
echo "✅ Live Council started with PID: $BOT_PID"
echo ""
echo "💬 REAL LLM DELIBERATIONS:"
echo "  'Tell the council about Labor Day trading'"
echo "  'Ask the council to learn from this weekend'"
echo "  'Council, what should we do?'"
echo ""
echo "📊 Check logs: tail -f live_council.log"
echo "🛑 Stop: kill $BOT_PID"
echo ""
echo "🔥 Sacred Fire burns eternal!"