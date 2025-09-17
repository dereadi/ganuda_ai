#!/bin/bash
# Check status of Canada persistent session

echo "🔥 CANADA SESSION STATUS"
echo "======================="
echo ""

# Check if screen session exists
if screen -list | grep -q "claude-canada"; then
    echo "✅ Screen session 'claude-canada' is RUNNING"
    
    # Count messages
    if [ -f "/home/dereadi/scripts/claude/CANADA_MESSAGES.log" ]; then
        MSG_COUNT=$(grep -c "MESSAGE #" /home/dereadi/scripts/claude/CANADA_MESSAGES.log 2>/dev/null || echo 0)
        echo "📊 Total messages received: $MSG_COUNT"
    fi
    
    # Check pending responses
    if [ -f "/home/dereadi/scripts/claude/CANADA_RESPONSES.json" ]; then
        PENDING=$(python3 -c "import json; data=json.load(open('/home/dereadi/scripts/claude/CANADA_RESPONSES.json')); print(sum(1 for m in data if m['status']=='pending'))" 2>/dev/null || echo 0)
        echo "⏳ Pending responses: $PENDING"
    fi
else
    echo "❌ Screen session 'claude-canada' is NOT running"
    echo "Start it with: ./start_canada_session.sh"
fi

echo ""
echo "Commands:"
echo "  View session:   screen -r claude-canada"
echo "  Detach:         Ctrl-A, then D"
echo "  Check messages: cat CANADA_MESSAGES.log"
echo "  Send response:  ./send_canada_response.py <id> \"message\""
