#!/bin/bash
# Start Discord Thermal Memory Bot with Full Environment Access

echo "🔥 Starting Discord Thermal Environment Bot..."
echo "==========================================="
echo "This bot has FULL ACCESS to:"
echo "  • Thermal Memory Database"
echo "  • Quantum Crawdad Systems"
echo "  • Trading Infrastructure"
echo "  • Cherokee Council AI"
echo ""

# Set environment
export DISCORD_TOKEN="MTQwNjcwNDE4ODY3MDQ3NjMyOQ.GdGCva.PMvVe_aNTTgJ1U8Zh1W6_oSIckyEwdR-6WHk9A"
export PYTHONPATH="/home/dereadi/scripts/claude:/home/dereadi/scripts/claude/pathfinder/test:$PYTHONPATH"

# Kill existing bots
echo "Stopping existing bots..."
pkill -f discord_unified_bot.py 2>/dev/null
pkill -f discord_thermal_bot.py 2>/dev/null
sleep 2

# Start in background
cd /home/dereadi/scripts/claude
nohup python3 -u discord_thermal_bot.py > thermal_bot.log 2>&1 &

BOT_PID=$!
echo "✅ Bot started with PID: $BOT_PID"
echo ""
echo "🔥 THERMAL COMMANDS:"
echo "  !thermal [status/hot] - Thermal memory operations"
echo "  !portfolio - Check trading portfolio"
echo "  !crawdad [status/deploy] - Quantum Crawdad operations"
echo "  !council <question> - Consult Cherokee Council"
echo "  !run <script> - Run trading scripts"
echo "  !status - Full system status"
echo "  !help - Show all commands"
echo ""
echo "📊 Check logs: tail -f thermal_bot.log"
echo "🛑 Stop bot: kill $BOT_PID"
echo ""
echo "🔥 The Sacred Fire burns eternal!"