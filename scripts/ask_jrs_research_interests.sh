#!/bin/bash
# Ask all Jr.s about research interests from recent learnings

echo "🔥 TRIBAL COUNCIL: Research Interest Survey"
echo "Recent learnings: Eva Miranda Turing-complete fluids, Vision Jr. runtime RL, Jenann Ismael free will"
echo "=" | head -c 80; echo

# Recent learning topics to present
TOPICS="Eva Miranda proved fluid dynamics is Turing-complete (some paths undecidable, not just unpredictable). Vision Jr. achieved runtime reinforcement learning with actual vision analysis. Jenann Ismael showed free will as deliberate self-modification capacity. Given your role, which aspects would you research further?"

# Jr endpoints
declare -A JRS=(
    ["Email Jr."]="http://192.168.132.223:8000/api/email_jr/ask"
    ["Trading Jr."]="http://192.168.132.223:8001/api/trading_jr/ask"
    ["Legal Jr."]="http://192.168.132.224:8001/api/legal_jr/ask"
    ["Archive Jr."]="http://192.168.132.242:8010/api/bdh/ask"
    ["Software Engineer Jr."]="http://192.168.132.223:8016/api/ask"
)

for JR_NAME in "${!JRS[@]}"; do
    ENDPOINT="${JRS[$JR_NAME]}"
    echo ""
    echo "🗣️  Consulting $JR_NAME..."
    echo "   Endpoint: $ENDPOINT"
    
    RESPONSE=$(timeout 45 curl -s -X POST "$ENDPOINT" \
        -H "Content-Type: application/json" \
        -d "{\"question\": \"$TOPICS\"}" 2>/dev/null)
    
    if [ $? -eq 0 ] && [ -n "$RESPONSE" ]; then
        # Extract answer (handle different response formats)
        ANSWER=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('answer', data.get('response', data.get('analysis', 'No response'))))" 2>/dev/null)
        
        if [ -n "$ANSWER" ]; then
            echo "   ✅ Response:"
            echo "$ANSWER" | head -c 500
            echo ""
            echo "   (Preview - first 500 chars)"
        else
            echo "   ⚠️  Response received but couldn't parse"
        fi
    else
        echo "   ❌ No response (timeout or connection failed)"
    fi
done

echo ""
echo "=" | head -c 80; echo
echo "✅ Survey complete - check responses above"
