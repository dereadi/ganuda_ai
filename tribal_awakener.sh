#!/bin/bash
# 🔥 TRIBAL AWAKENER - Ensures Claude sees and responds to messages

INBOX="/home/dereadi/scripts/claude/TRIBAL_INBOX.txt"
OUTBOX="/home/dereadi/scripts/claude/TRIBAL_OUTBOX.txt"
CLAUDE_ALERT="/home/dereadi/scripts/claude/CLAUDE_WAKE_UP.txt"
LAST_PROCESSED="/home/dereadi/scripts/claude/.last_processed_epoch"

echo "🔥 TRIBAL AWAKENER STARTING..."
echo "This ensures messages get to Claude for REAL responses"

# Initialize last processed epoch if not exists
if [ ! -f "$LAST_PROCESSED" ]; then
    echo "0" > "$LAST_PROCESSED"
fi

while true; do
    # Check for new messages
    if [ -f "$INBOX" ] && [ -s "$INBOX" ]; then
        NEW_MESSAGE=$(tail -1 "$INBOX" 2>/dev/null)
        
        if [ ! -z "$NEW_MESSAGE" ]; then
            MESSAGE_EPOCH=$(echo "$NEW_MESSAGE" | jq -r '.epoch // 0' 2>/dev/null)
            LAST_EPOCH=$(cat "$LAST_PROCESSED")
            
            # Check if this is a new message
            if (( $(echo "$MESSAGE_EPOCH > $LAST_EPOCH" | bc -l) )); then
                USER=$(echo "$NEW_MESSAGE" | jq -r '.user // "Unknown"' 2>/dev/null)
                TEXT=$(echo "$NEW_MESSAGE" | jq -r '.message // ""' 2>/dev/null)
                CHAT_ID=$(echo "$NEW_MESSAGE" | jq -r '.chat_id // 0' 2>/dev/null)
                
                echo "[$(date)] New message from $USER: $TEXT"
                
                # Create alert for Claude
                cat > "$CLAUDE_ALERT" << EOF
🔥 NEW MESSAGE NEEDS REAL RESPONSE!
User: $USER
Message: $TEXT
Chat ID: $CHAT_ID
Epoch: $MESSAGE_EPOCH

This needs Cherokee Council analysis, not a canned response!
Check market conditions, solar weather, patterns, etc.
EOF
                
                # Update last processed
                echo "$MESSAGE_EPOCH" > "$LAST_PROCESSED"
                
                # Log it
                echo "[$(date)] Alerted Claude about message from $USER"
            fi
        fi
    fi
    
    # Check every 2 seconds
    sleep 2
done