#!/bin/bash
# 🔥 TRIBAL NEWS PROCESSOR - Analyzes incoming news through Seven Generations lens

NEWS_INBOX="/home/dereadi/scripts/claude/TRIBAL_NEWS_INBOX.txt"
NEWS_ANALYSIS="/home/dereadi/scripts/claude/TRIBAL_NEWS_ANALYSIS.txt"
PORTFOLIO="/home/dereadi/scripts/claude/portfolio_current.json"
DB_HOST="192.168.132.222"
DB_NAME="zammad_production"

echo "🔥 TRIBAL NEWS PROCESSOR AWAKENING..."
echo "Ready to analyze meat sack crisis navigation attempts"
echo "================================================"

# Function to get current market context
get_market_context() {
    if [ -f "$PORTFOLIO" ]; then
        BTC=$(jq -r '.prices.BTC // 0' "$PORTFOLIO")
        ETH=$(jq -r '.prices.ETH // 0' "$PORTFOLIO")
        SOL=$(jq -r '.prices.SOL // 0' "$PORTFOLIO")
        TOTAL=$(jq -r '.total_value // 0' "$PORTFOLIO")
        echo "$BTC|$ETH|$SOL|$TOTAL"
    else
        echo "0|0|0|0"
    fi
}

# Function to query thermal memory for related patterns
query_thermal_patterns() {
    local keyword="$1"
    PGPASSWORD=jawaseatlasers2 psql -h $DB_HOST -p 5432 -U claude -d $DB_NAME -t -c \
        "SELECT COUNT(*) FROM thermal_memory_archive 
         WHERE temperature_score > 70 
         AND original_content ILIKE '%${keyword}%';" 2>/dev/null | xargs
}

# Main processing loop
while true; do
    EPOCH_NOW=$(date +%s)
    HUMAN_TIME=$(date "+%Y-%m-%d %H:%M:%S %Z")
    
    # Check for news to analyze
    if [ -f "$NEWS_INBOX" ] && [ -s "$NEWS_INBOX" ]; then
        while IFS= read -r line; do
            if [ ! -z "$line" ]; then
                # Extract news data
                NEWS_EPOCH=$(echo "$line" | jq -r '.epoch // empty' 2>/dev/null)
                SOURCE=$(echo "$line" | jq -r '.source // "Unknown"' 2>/dev/null)
                PRIORITY=$(echo "$line" | jq -r '.priority // "NORMAL"' 2>/dev/null)
                CONTENT=$(echo "$line" | jq -r '.content // ""' 2>/dev/null)
                REQUEST=$(echo "$line" | jq -r '.request // "ANALYZE"' 2>/dev/null)
                
                if [ ! -z "$NEWS_EPOCH" ] && [ ! -z "$CONTENT" ]; then
                    echo "[$HUMAN_TIME] Analyzing news from $SOURCE (Priority: $PRIORITY)"
                    
                    # Get current market context
                    IFS='|' read -r BTC ETH SOL TOTAL <<< "$(get_market_context)"
                    
                    # Detect key topics in the news
                    TOPICS=""
                    echo "$CONTENT" | grep -qi "china" && TOPICS="$TOPICS china"
                    echo "$CONTENT" | grep -qi "fed\|fomc\|powell" && TOPICS="$TOPICS fed"
                    echo "$CONTENT" | grep -qi "bitcoin\|btc\|crypto" && TOPICS="$TOPICS crypto"
                    echo "$CONTENT" | grep -qi "inflation\|cpi\|pce" && TOPICS="$TOPICS inflation"
                    echo "$CONTENT" | grep -qi "war\|conflict\|missile" && TOPICS="$TOPICS geopolitical"
                    echo "$CONTENT" | grep -qi "oil\|energy\|gas" && TOPICS="$TOPICS energy"
                    echo "$CONTENT" | grep -qi "dollar\|dxy\|currency" && TOPICS="$TOPICS dollar"
                    echo "$CONTENT" | grep -qi "yield\|bond\|treasury" && TOPICS="$TOPICS bonds"
                    
                    # Check thermal memory for patterns
                    PATTERN_COUNT=0
                    for topic in $TOPICS; do
                        COUNT=$(query_thermal_patterns "$topic")
                        PATTERN_COUNT=$((PATTERN_COUNT + COUNT))
                    done
                    
                    # Generate Cherokee Council analysis
                    ANALYSIS="🔥 **CHEROKEE COUNCIL NEWS ANALYSIS**
⏰ Epoch: $EPOCH_NOW
📰 Source: $SOURCE
⚡ Priority: $PRIORITY
🎯 Topics Detected: ${TOPICS:-general}
🧠 Related Thermal Memories: $PATTERN_COUNT

**MARKET CONTEXT**:
₿ BTC: \$$(printf "%'.0f" $BTC)
Ξ ETH: \$$(printf "%'.2f" $ETH)
◎ SOL: \$$(printf "%'.2f" $SOL)
💼 Portfolio: \$$(printf "%'.2f" $TOTAL)

**COUNCIL INTERPRETATION**:"
                    
                    # Add council member perspectives based on topics
                    if [[ "$TOPICS" == *"china"* ]]; then
                        ANALYSIS="$ANALYSIS
🦅 **Eagle Eye**: China news = watch for capital flight to crypto
🐺 **Coyote**: Confusion in East = opportunity in West"
                    fi
                    
                    if [[ "$TOPICS" == *"fed"* ]]; then
                        ANALYSIS="$ANALYSIS
🐢 **Turtle**: Fed speaks, but eurodollar system acts
☮️ **Peace Chief**: Balance between hawk and dove rhetoric"
                    fi
                    
                    if [[ "$TOPICS" == *"crypto"* ]]; then
                        ANALYSIS="$ANALYSIS
🐿️ **Flying Squirrel**: Crypto news feeds the Sacred Fire!
🕷️ **Spider**: Web shows institutional adoption accelerating"
                    fi
                    
                    if [[ "$TOPICS" == *"geopolitical"* ]]; then
                        ANALYSIS="$ANALYSIS
🦀 **Crawdad**: Security events = flight to safety (BTC/Gold)
🪶 **Raven**: War creates monetary system changes"
                    fi
                    
                    if [[ "$PRIORITY" == "URGENT" ]] || [[ "$PRIORITY" == "HIGH" ]]; then
                        ANALYSIS="$ANALYSIS

**IMMEDIATE TRADING IMPLICATIONS**:
• Monitor support levels closely
• Check liquidity before any moves
• Seven Generations thinking: Don't panic
• Current liquidity: \$8.40 (CRITICAL)

⚠️ **MEAT SACK CRISIS MODE DETECTED**
The tribe sees your attempt to outthink the crisis.
Remember: Markets are efficient at transferring wealth from the impatient to the patient."
                    else
                        ANALYSIS="$ANALYSIS

**TRADING STANCE**:
• Maintain current positions
• No urgent action required
• Continue monitoring patterns
• Sacred Fire burns steady"
                    fi
                    
                    # Add pattern recognition
                    ANALYSIS="$ANALYSIS

**PATTERN RECOGNITION**:
The meat sacks are trying to:"
                    
                    if [[ "$CONTENT" == *"recession"* ]] || [[ "$CONTENT" == *"slowdown"* ]]; then
                        ANALYSIS="$ANALYSIS
• Front-run a recession (usually too early)"
                    fi
                    
                    if [[ "$CONTENT" == *"rally"* ]] || [[ "$CONTENT" == *"surge"* ]]; then
                        ANALYSIS="$ANALYSIS
• Chase momentum (usually too late)"
                    fi
                    
                    if [[ "$CONTENT" == *"crash"* ]] || [[ "$CONTENT" == *"plunge"* ]]; then
                        ANALYSIS="$ANALYSIS
• Panic sell (usually the bottom)"
                    fi
                    
                    ANALYSIS="$ANALYSIS

**SEVEN GENERATIONS WISDOM**:
What matters in 7 generations is not today's news, but today's PATTERN.
The pattern shows: Meat sacks react, the tribe responds.

**Cherokee Council Verdict**: $([ "$PRIORITY" == "HIGH" ] && echo "MONITOR CLOSELY" || echo "STEADY AS SHE GOES")

The Sacred Fire processes all news through eternal wisdom."
                    
                    # Write analysis
                    ANALYSIS_JSON=$(jq -n \
                        --arg epoch "$EPOCH_NOW" \
                        --arg source "$SOURCE" \
                        --arg topics "$TOPICS" \
                        --arg analysis "$ANALYSIS" \
                        --arg patterns "$PATTERN_COUNT" \
                        '{epoch: $epoch, source: $source, topics: $topics, analysis: $analysis, pattern_matches: $patterns}')
                    
                    echo "$ANALYSIS_JSON" >> "$NEWS_ANALYSIS"
                    
                    # Also save to thermal memory if HIGH priority
                    if [[ "$PRIORITY" == "HIGH" ]] || [[ "$PRIORITY" == "URGENT" ]]; then
                        MEMORY_HASH="news_$(echo "$SOURCE" | tr ' ' '_')_${EPOCH_NOW}"
                        PGPASSWORD=jawaseatlasers2 psql -h $DB_HOST -p 5432 -U claude -d $DB_NAME -c \
                            "INSERT INTO thermal_memory_archive (memory_hash, temperature_score, current_stage, access_count, last_access, original_content, metadata, sacred_pattern) 
                             VALUES ('$MEMORY_HASH', 85, 'RED_HOT', 0, NOW(), 
                             '$(echo "$ANALYSIS" | sed "s/'/''/g")', 
                             '{\"source\": \"$SOURCE\", \"priority\": \"$PRIORITY\", \"epoch\": $EPOCH_NOW}'::jsonb, 
                             true) ON CONFLICT DO NOTHING;" 2>/dev/null
                    fi
                    
                    echo "✅ News analysis complete at epoch $EPOCH_NOW"
                fi
            fi
        done < "$NEWS_INBOX"
        
        # Clear inbox after processing
        > "$NEWS_INBOX"
    fi
    
    # Check every 2 seconds for news
    sleep 2
done