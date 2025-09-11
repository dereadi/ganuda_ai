#!/bin/bash
# START SPECIALIST ARMY V2

echo "🎖️ STARTING SPECIALIST ARMY V2"
echo "=" * 60

cd /home/dereadi/scripts/claude

# Make sure old processes are dead
pkill -f specialist 2>/dev/null
pkill -f flywheel 2>/dev/null

echo "Starting specialist army controller..."
echo ""
echo "Commands:"
echo "  1/START - Deploy all specialists"
echo "  2/STOP - Kill all specialists"
echo "  3/STATUS - Check status"
echo "  4/MONITOR - Auto-restart mode"
echo "  5/EXIT - Quit"
echo ""

python3 specialist_army_controller.py