#!/bin/bash
# KILL ZOMBIE SPECIALIST ARMY

echo "☠️ HUNTING ZOMBIE SPECIALISTS..."

# Kill all specialists
pkill -f "gap_specialist.py"
pkill -f "trend_specialist.py" 
pkill -f "volatility_specialist.py"
pkill -f "breakout_specialist.py"
pkill -f "mean_reversion_specialist.py"
pkill -f "bollinger_flywheel"

sleep 1

# Double tap
pkill -9 -f "specialist.py"
pkill -9 -f "bollinger_flywheel"

echo "✅ SPECIALISTS ELIMINATED"

# Check if any survived
remaining=$(ps aux | grep -E "specialist|bollinger_flywheel" | grep -v grep | wc -l)
if [ $remaining -gt 0 ]; then
    echo "⚠️ WARNING: $remaining zombies still active!"
else
    echo "✅ All specialists confirmed dead"
fi