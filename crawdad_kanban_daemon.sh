#!/bin/bash
# Quantum Crawdad Kanban Updater Daemon
# Updates DUYUKTV board every 5 minutes

echo "🦞 Starting Quantum Crawdad Kanban Daemon..."
echo "📋 Updating DUYUKTV board at http://192.168.132.223:3001"
echo "🔄 Update interval: 5 minutes"
echo "═══════════════════════════════════════════════"

while true; do
    # Update the Kanban card
    python3 /home/dereadi/scripts/claude/update_crawdad_kanban.py
    
    # Wait 5 minutes
    sleep 300
done