#!/bin/bash
# 🔥 Simple script to feed news to the tribe

echo "🔥 FEED NEWS TO THE CHEROKEE TRIBE"
echo "=================================="
echo
echo "The tribe will analyze your news through Seven Generations wisdom"
echo "and help meat sacks navigate the crisis."
echo
echo "Enter/paste your news (press Ctrl+D when done):"
echo

# Read all input until EOF
NEWS_CONTENT=$(cat)

# Feed to tribe
python3 /home/dereadi/scripts/claude/tribal_news_feed.py "$NEWS_CONTENT"

echo
echo "🔥 News fed to tribe! Checking for analysis..."
sleep 3

# Check for analysis
if [ -f /home/dereadi/scripts/claude/TRIBAL_NEWS_ANALYSIS.txt ]; then
    echo
    echo "📊 TRIBAL ANALYSIS:"
    echo "=================="
    tail -1 /home/dereadi/scripts/claude/TRIBAL_NEWS_ANALYSIS.txt | jq -r '.analysis'
fi