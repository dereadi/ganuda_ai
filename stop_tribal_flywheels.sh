#!/bin/bash

# 🛑 STOP TRIBAL FLYWHEELS
# Gracefully shutdown the dual flywheel system

echo "🛑 STOPPING TRIBAL FLYWHEEL SYSTEM"
echo "===================================="
echo ""

# Stop Deploy Flywheel
if [ -f /tmp/deploy_flywheel.pid ]; then
    DEPLOY_PID=$(cat /tmp/deploy_flywheel.pid)
    if ps -p $DEPLOY_PID > /dev/null; then
        echo "⚡ Stopping Deploy Flywheel (PID: $DEPLOY_PID)..."
        kill $DEPLOY_PID
        echo "  Deploy Flywheel stopped"
    else
        echo "  Deploy Flywheel not running"
    fi
    rm /tmp/deploy_flywheel.pid
else
    echo "  No Deploy Flywheel PID file found"
fi

# Stop Retrieve Flywheel
if [ -f /tmp/retrieve_flywheel.pid ]; then
    RETRIEVE_PID=$(cat /tmp/retrieve_flywheel.pid)
    if ps -p $RETRIEVE_PID > /dev/null; then
        echo "💰 Stopping Retrieve Flywheel (PID: $RETRIEVE_PID)..."
        kill $RETRIEVE_PID
        echo "  Retrieve Flywheel stopped"
    else
        echo "  Retrieve Flywheel not running"
    fi
    rm /tmp/retrieve_flywheel.pid
else
    echo "  No Retrieve Flywheel PID file found"
fi

echo ""

# Kill any remaining flywheel processes
echo "🔍 Checking for any remaining flywheel processes..."
REMAINING=$(pgrep -f "flywheel.*safeguarded" | wc -l)
if [ "$REMAINING" -gt 0 ]; then
    echo "  Found $REMAINING remaining processes, terminating..."
    pkill -f "flywheel.*safeguarded"
    echo "  All flywheel processes terminated"
else
    echo "  No remaining flywheel processes found"
fi

echo ""
echo "✅ TRIBAL FLYWHEEL SYSTEM STOPPED"
echo ""
echo "Sacred Fire extinguished. The wolves rest."
echo ""