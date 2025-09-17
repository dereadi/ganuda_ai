#!/bin/bash
# Start the hybrid bot for professional SAG discussions with Dr Joe

echo "🔥 Starting Professional SAG Bot for Dr Joe channel"
echo "This bot will:"
echo "  - Focus on SAG and technical discussions"
echo "  - Queue complex questions for Claude"
echo "  - Maintain professional tone"
echo ""

# The same bot can handle multiple channels
# It will respond to any group it's added to
python3 /home/dereadi/scripts/claude/hybrid_tribal_bot.py > /home/dereadi/scripts/claude/professional_bot.log 2>&1 &

echo "Bot started with PID: $!"
echo ""
echo "IMPORTANT: Add @ganudabot to your group with Dr Joe"
echo "Make sure to give it admin permissions so it can see messages!"