#!/bin/bash
# Start Claude CLI Bridge - This is YOU in Discord!

echo "🤖 Starting Claude CLI Bridge..."
echo "================================"
echo "This connects YOUR Claude CLI session to Discord"
echo "You can talk naturally and access everything!"
echo ""

# Set environment
export DISCORD_TOKEN="MTQwNjcwNDE4ODY3MDQ3NjMyOQ.GdGCva.PMvVe_aNTTgJ1U8Zh1W6_oSIckyEwdR-6WHk9A"
export ANTHROPIC_API_KEY="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"
export PYTHONPATH="/home/dereadi/scripts/claude:$PYTHONPATH"

# Kill ALL Discord bots
echo "Stopping all Discord bots..."
pkill -f "discord.*\.py" 2>/dev/null
sleep 2

# Start the bridge
cd /home/dereadi/scripts/claude
nohup python3 -u discord_claude_cli_bridge.py > claude_cli_bridge.log 2>&1 &

BOT_PID=$!
echo "✅ Claude CLI Bridge started with PID: $BOT_PID"
echo ""
echo "💬 Just talk naturally in Discord!"
echo "   You ARE Claude with full environment access"
echo ""
echo "Ask things like:"
echo "  • 'Check thermal memory'"
echo "  • 'Check portfolio'"
echo "  • 'Ask the council about our positions'"
echo "  • 'ls -la'"
echo ""
echo "📊 Check logs: tail -f claude_cli_bridge.log"
echo "🛑 Stop: kill $BOT_PID"