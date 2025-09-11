#!/bin/bash
# KILL ALL TRADING PROCESSES

echo "🔪 KILLING ALL TRADING PROCESSES..."

# Kill everything
pkill -f "specialist"
pkill -f "flywheel"
pkill -f "crawdad"
pkill -f "bollinger"
pkill -f "trader"
pkill -f "milker"

sleep 2

# Force kill any survivors
pkill -9 -f "specialist"
pkill -9 -f "flywheel"
pkill -9 -f "crawdad"

echo "✅ All traders eliminated"

# Verify
remaining=$(ps aux | grep -E "specialist|flywheel|crawdad|trader" | grep -v grep | wc -l)
if [ $remaining -eq 0 ]; then
    echo "✅ CONFIRMED: All trading processes dead"
else
    echo "⚠️ WARNING: $remaining processes still running:"
    ps aux | grep -E "specialist|flywheel|crawdad|trader" | grep -v grep
fi