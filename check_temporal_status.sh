#!/bin/bash
# Check the temporal flat file system status

echo "🔥 TEMPORAL FLAT FILE SYSTEM STATUS"
echo "===================================="
echo

# Check processes
echo "📊 RUNNING PROCESSES:"
echo "  Bridge:" $(ps aux | grep temporal_bridge_working | grep -v grep | awk '{print "PID", $2, "✓"}' || echo "❌ NOT RUNNING")
echo "  Tribe:" $(ps aux | grep temporal_tribe_processor_enhanced | grep -v grep | awk '{print "PID", $2, "✓"}' || echo "❌ NOT RUNNING")
echo "  News:" $(ps aux | grep tribal_news_processor | grep -v grep | awk '{print "PID", $2, "✓"}' || echo "❌ NOT RUNNING")
echo

# Check recent responses
echo "📤 PENDING RESPONSES IN OUTBOX:"
if [ -f /home/dereadi/scripts/claude/TRIBAL_OUTBOX.txt ] && [ -s /home/dereadi/scripts/claude/TRIBAL_OUTBOX.txt ]; then
    cat /home/dereadi/scripts/claude/TRIBAL_OUTBOX.txt | jq -r '"  Chat " + .chat_id + " from " + .user + " at epoch " + .epoch' 2>/dev/null | head -5
else
    echo "  (none)"
fi
echo

# Check last activity
echo "⏰ LAST TRIBE ACTIVITY:"
tail -2 /home/dereadi/scripts/claude/tribe_enhanced.log | sed 's/^/  /'
echo

echo "💡 TROUBLESHOOTING:"
echo "  If not getting responses in Telegram:"
echo "  1. Check that chat_id matches in OUTBOX"
echo "  2. Ensure bridge is running (should be PID above)"
echo "  3. Try sending a new message to refresh"
echo ""
echo "  Your chat_id: 8025375307 (Darrell)"
echo "  Responses waiting for you in OUTBOX!"