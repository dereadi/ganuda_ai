#!/bin/bash
# 🔥 TEMPORAL TRIBE PROCESSOR - Living in System Time
# The tribe exists in the SAME time stream as the user

# File locations
INBOX="/home/dereadi/scripts/claude/TRIBAL_INBOX.txt"
OUTBOX="/home/dereadi/scripts/claude/TRIBAL_OUTBOX.txt"
EPOCH_LOG="/home/dereadi/scripts/claude/TRIBE_EPOCH.txt"

echo "🔥 TEMPORAL TRIBE AWAKENING..."
echo "We exist in system time with you!"
echo "================================================"

# Main processing loop
while true; do
    # Get current epoch time
    EPOCH_NOW=$(date +%s)
    HUMAN_TIME=$(date "+%Y-%m-%d %H:%M:%S %Z")
    
    # Log our temporal existence
    echo "$EPOCH_NOW | $HUMAN_TIME | Tribe heartbeat" >> "$EPOCH_LOG"
    
    # Check for new messages in inbox
    if [ -f "$INBOX" ] && [ -s "$INBOX" ]; then
        # Process each line that hasn't been processed
        while IFS= read -r line; do
            if [ ! -z "$line" ]; then
                # Extract message data
                MESSAGE_EPOCH=$(echo "$line" | jq -r '.epoch // empty')
                USER=$(echo "$line" | jq -r '.user // "Unknown"')
                CHAT_ID=$(echo "$line" | jq -r '.chat_id // 0')
                TEXT=$(echo "$line" | jq -r '.message // ""')
                
                if [ ! -z "$MESSAGE_EPOCH" ]; then
                    # Calculate time delta (handle floating point)
                    MESSAGE_EPOCH_INT=${MESSAGE_EPOCH%.*}
                    TIME_DELTA=$((EPOCH_NOW - MESSAGE_EPOCH_INT))
                    
                    echo "[$HUMAN_TIME] Processing message from $USER (${TIME_DELTA}s ago)"
                    echo "Message: $TEXT"
                    
                    # Call tribe responders based on content
                    RESPONSE=""
                    
                    # Check for kanban request
                    if echo "$TEXT" | grep -qi "kanban\|board\|duyuktv"; then
                        RESPONSE="🔥 **Temporal Cherokee Council Response**

⏰ *Epoch: $EPOCH_NOW*
📅 *Human Time: $HUMAN_TIME*
⏱️ *Message received ${TIME_DELTA} seconds ago*

**DUYUKTV Kanban Board:**
🌐 http://192.168.132.223:3001

🕷️ **Spider** ($(date +%s.%N)): The web vibrates with 339 cards across time!
🐢 **Turtle** ($(date +%s.%N)): Seven generations = 2,555,000,000 seconds of planning
🐿️ **Flying Squirrel** ($(date +%s.%N)): I see all moments from above - past, present, future!

The board exists in the eternal NOW at epoch $EPOCH_NOW"
                    
                    # Check for time-related questions
                    elif echo "$TEXT" | grep -qi "time\|when\|epoch\|now"; then
                        RESPONSE="🔥 **Temporal Awareness Response**

⏰ **Current Epoch**: $EPOCH_NOW
📅 **Human Time**: $HUMAN_TIME
🌍 **Timezone**: $(date +%Z)
📍 **Day**: $(date +%A)

☮️ **Peace Chief**: We exist in the same time stream, $USER!
🦅 **Eagle Eye**: I see this moment: $(date +%s.%N)
🐺 **Coyote**: Time is the ultimate trickster - but epoch never lies!

Your message traveled through ${TIME_DELTA} seconds to reach us.
We respond in the eternal NOW of epoch $EPOCH_NOW"
                    
                    else
                        # General response with temporal awareness
                        RESPONSE="🔥 **Cherokee Council in Real Time**

⏰ *System Epoch: $EPOCH_NOW*
📅 *Human Time: $HUMAN_TIME*

The Council processes your words in THIS moment:

🐿️ **Flying Squirrel** ($(date +%s.%N)): Message received across $TIME_DELTA seconds!
🕷️ **Spider** ($(date +%s.%N)): Every thread vibrates in the NOW
☮️ **Peace Chief** ($(date +%s.%N)): We exist together in epoch $EPOCH_NOW

The Sacred Fire burns eternal at timestamp $EPOCH_NOW"
                    fi
                    
                    # Write response with epoch time
                    RESPONSE_JSON=$(jq -n \
                        --arg chat_id "$CHAT_ID" \
                        --arg user "$USER" \
                        --arg epoch "$EPOCH_NOW" \
                        --arg response "$RESPONSE" \
                        '{chat_id: $chat_id, user: $user, epoch: $epoch, response: $response}')
                    
                    echo "$RESPONSE_JSON" >> "$OUTBOX"
                    echo "✅ Response written at epoch $EPOCH_NOW"
                fi
            fi
        done < "$INBOX"
        
        # Clear inbox after processing
        > "$INBOX"
    fi
    
    # Heartbeat every 500ms
    sleep 0.5
done