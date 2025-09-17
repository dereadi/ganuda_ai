#!/bin/bash
# Watch for new messages and alert Claude

LOG="/home/dereadi/scripts/claude/telegram_live.log"
LAST_SIZE=0

echo "🔥 WATCHING FOR TELEGRAM MESSAGES..."
echo "Send a message to @ganudabot"
echo "="=================================""

while true; do
    CURRENT_SIZE=$(stat -c%s "$LOG" 2>/dev/null || echo 0)
    
    if [ "$CURRENT_SIZE" -gt "$LAST_SIZE" ]; then
        echo ""
        echo "🔥🔥🔥 NEW MESSAGE RECEIVED! 🔥🔥🔥"
        echo "="=================================""
        tail -n +$((LAST_SIZE + 1)) "$LOG" | head -c $((CURRENT_SIZE - LAST_SIZE))
        echo "="=================================""
        LAST_SIZE=$CURRENT_SIZE
    fi
    
    sleep 1
done