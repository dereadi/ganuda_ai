#!/bin/bash

# 🛑 KILL ALL ROGUE TRADING BOTS
# Emergency stop for unauthorized traders

echo "🛑 STOPPING ALL ROGUE TRADERS"
echo "=============================="

# Kill specialist bots
echo "Stopping specialist bots..."
pkill -f "specialist.py"

# Kill any rogue crawdads
echo "Stopping rogue crawdads..."
pkill -f "quantum_crawdad.*\.py"

# Kill rogue flywheels (but not our safeguarded ones)
echo "Stopping unsafe flywheels..."
pkill -f "flywheel_(?!.*safeguarded).*\.py"

# Kill any other suspicious trading processes
ROGUE_SCRIPTS=(
    "aggressive_crawdad_trader"
    "execute_market_move"
    "deploy_300_crawdads"
    "specialist_army"
    "milk_all_alts"
    "execute_profit_bleed"
    "nuclear_strike"
)

for script in "${ROGUE_SCRIPTS[@]}"; do
    if pgrep -f "$script" > /dev/null; then
        echo "Killing $script..."
        pkill -f "$script"
    fi
done

echo ""
echo "✅ Rogue traders stopped"
echo ""
echo "Safe processes still running:"
ps aux | grep -E 'flywheel.*safeguarded|portfolio_alerts|discord' | grep -v grep