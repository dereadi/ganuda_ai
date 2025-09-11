#!/bin/bash
# Start Stateful Shell Bridge for Discord

echo "🖥️ Starting Stateful Shell Bridge..."
echo "==================================="
echo "Features:"
echo "  • Persistent sessions per channel"
echo "  • Working directory preservation"
echo "  • Environment variable management"
echo "  • Script creation & execution"
echo "  • Full shell access like SSH!"
echo ""

# Set environment
export DISCORD_TOKEN="MTQwNjcwNDE4ODY3MDQ3NjMyOQ.GdGCva.PMvVe_aNTTgJ1U8Zh1W6_oSIckyEwdR-6WHk9A"
export ANTHROPIC_API_KEY="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"

# Kill any existing Discord bots
echo "Stopping existing bots..."
pkill -f "discord.*\.py" 2>/dev/null
sleep 2

# Start the stateful shell bridge
cd /home/dereadi/scripts/claude
nohup python3 -u discord_stateful_shell.py > stateful_shell.log 2>&1 &

BOT_PID=$!
echo "✅ Stateful Shell started with PID: $BOT_PID"
echo ""
echo "💬 USAGE IN DISCORD:"
echo "  '$ ls' - Run shell commands"
echo "  '$ cd pathfinder' - Change directory (persists!)"
echo "  '$ python3 script.py' - Run Python scripts"
echo "  'create script test.py' + code - Create scripts"
echo "  'status' - Show session info"
echo "  'help' - Full command list"
echo ""
echo "📊 Check logs: tail -f stateful_shell.log"
echo "🛑 Stop: kill $BOT_PID"
echo ""
echo "Each Discord channel = separate persistent session!"