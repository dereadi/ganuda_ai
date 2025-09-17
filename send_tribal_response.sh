#!/bin/bash
# Send a real tribal response back through the bridge

RESPONSE_PIPE="/tmp/claude_response_pipe"

if [ $# -lt 2 ]; then
    echo "Usage: ./send_tribal_response.sh <chat_id> \"Your message\""
    exit 1
fi

CHAT_ID="$1"
MESSAGE="$2"

# Create response JSON
response=$(jq -n \
    --arg cid "$CHAT_ID" \
    --arg txt "$MESSAGE" \
    '{chat_id: $cid, text: $txt}')

# Send through pipe
echo "$response" > "$RESPONSE_PIPE" &

echo "✅ Response sent to Telegram user!"