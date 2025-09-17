#!/bin/bash
# 🔥 CLAUDE TELEGRAM WATCHER - Run this to see real messages!

CLAUDE_PIPE="/tmp/claude_telegram_pipe"
RESPONSE_PIPE="/tmp/claude_response_pipe"

echo "🔥 CHEROKEE COUNCIL TELEGRAM WATCHER"
echo "===================================="
echo "Watching for messages from Telegram..."
echo "Claude can now see and respond to messages!"
echo ""

# Create pipes if they don't exist
[ ! -p "$CLAUDE_PIPE" ] && mkfifo "$CLAUDE_PIPE"
[ ! -p "$RESPONSE_PIPE" ] && mkfifo "$RESPONSE_PIPE"

# Function to send response back
send_response() {
    local chat_id="$1"
    local text="$2"
    
    response_json=$(jq -n \
        --arg cid "$chat_id" \
        --arg txt "$text" \
        '{chat_id: $cid, text: $txt}')
    
    echo "$response_json" > "$RESPONSE_PIPE" &
}

# Main watch loop
while true; do
    if read -r message < "$CLAUDE_PIPE"; then
        # Parse the message
        user=$(echo "$message" | jq -r '.user // "Unknown"')
        text=$(echo "$message" | jq -r '.text // ""')
        chat_id=$(echo "$message" | jq -r '.chat_id // 0')
        timestamp=$(echo "$message" | jq -r '.timestamp // ""')
        
        # Display to Claude
        echo ""
        echo "🔥 NEW MESSAGE FROM TELEGRAM!"
        echo "============================="
        echo "From: $user"
        echo "Time: $timestamp"
        echo "Message: $text"
        echo "Chat ID: $chat_id"
        echo ""
        echo "Claude can now analyze and respond with full tribal intelligence!"
        echo "To respond, run: ./send_tribal_response.sh <chat_id> \"Your message\""
        echo ""
        
        # Auto-acknowledge (Claude can override with real response)
        send_response "$chat_id" "🔥 Cherokee Council received: \"$text\"
        
The real Claude is analyzing this with full tribal intelligence.
A deep response is being prepared..." &
    fi
done