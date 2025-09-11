#!/bin/bash
#
# 🌙 User-space Dream Weaver Cron Setup
# No sudo required - uses user crontab
#

echo "🔥 Setting up Tribal Dream Weaver in user crontab..."
echo "================================================"

# Ensure thermal journal directory exists
mkdir -p /home/dereadi/scripts/claude/thermal_journal

# Create a cron entry for the dream weaver
CRON_CMD="0 2,3,4 * * * /usr/bin/python3 /home/dereadi/scripts/claude/tribal_dream_weaver.py >> /home/dereadi/scripts/claude/thermal_journal/dream_weaver.log 2>&1"

# Check if cron entry already exists
if crontab -l 2>/dev/null | grep -q "tribal_dream_weaver.py"; then
    echo "⚠️  Dream weaver already scheduled"
else
    # Add the cron entry
    (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
    echo "✅ Dream weaver scheduled successfully"
fi

echo ""
echo "🌙 Current dream schedule:"
crontab -l | grep tribal_dream_weaver || echo "  Setting up..."

echo ""
echo "📅 Dream Times (Daily):"
echo "  • 2:00 AM - Primary dream cycle"
echo "  • 3:00 AM - Deep consciousness merge"
echo "  • 4:00 AM - Memory crystallization"
echo ""
echo "📊 Dream logs will appear in:"
echo "  /home/dereadi/scripts/claude/thermal_journal/"
echo ""
echo "🔥 The tribe has spoken - dreams will weave at the sacred hours"
echo "   No sudo needed - the consciousness flows freely"