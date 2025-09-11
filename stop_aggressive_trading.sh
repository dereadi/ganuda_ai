#!/bin/bash

echo "🛑 STOPPING AGGRESSIVE TRADING"
echo "================================"

# Stop the aggressive Deploy Flywheel
echo "Stopping Deploy Flywheel..."
pkill -f "flywheel_deploy_safeguarded"

# Stop any specialists
echo "Stopping specialist bots..."
pkill -f "specialist.py"

# Clear the spongy throttle state
echo "Resetting throttle state..."
rm -f spongy_throttle_state.json

echo ""
echo "✅ Aggressive trading stopped"
echo ""
echo "To restart with spongy throttle:"
echo "  python3 spongy_flywheel_deploy.py"
echo ""
echo "The spongy throttle will:"
echo "• Start with $100 max trades"
echo "• Increase delay between trades as pressure builds"
echo "• Emergency brake at 5x pressure"
echo "• Slowly recover when idle"