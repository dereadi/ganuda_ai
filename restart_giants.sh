#!/bin/bash
# Restart Giants with updates

echo "🔥 Restarting Cherokee Giants..."

# Kill old
pkill -f giant_sept15 2>/dev/null
sleep 2

# Start new
cd /home/dereadi/scripts/claude
python3 giant_sept15.py > /tmp/giants.log 2>&1 &
echo "PID: $!"

echo "✅ Giants updated with:"
echo "   - Portfolio: $16,696.02"
echo "   - Pepperjack cheese awareness"
echo "   - September 15, 2025 knowledge"