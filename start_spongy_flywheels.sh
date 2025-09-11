#!/bin/bash

# 🧽 START SPONGY FLYWHEEL SYSTEM
# Two flywheels with elastic resistance

echo "🧽 SPONGY FLYWHEEL SYSTEM"
echo "=========================="
echo ""

# Check current liquidity
echo "💰 Checking liquidity..."
LIQUIDITY=$(python3 -c "
import json
from coinbase.rest import RESTClient
config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=10)
accounts = client.get_accounts()['accounts']
for a in accounts:
    if a['currency'] == 'USD':
        print(float(a['available_balance']['value']))
        break
" 2>/dev/null)

echo "Current USD: \$$LIQUIDITY"
echo ""

# Stop old flywheels
echo "🛑 Stopping old flywheels..."
pkill -f "flywheel_deploy_safeguarded"
pkill -f "flywheel_retrieve_safeguarded"
pkill -f "specialist.py"
sleep 2

# Start Deploy Flywheel with spongy throttle
echo "⚡ Starting SPONGY DEPLOY FLYWHEEL..."
echo "  • Starts with \$100 max trades"
echo "  • Increases resistance with each trade"
echo "  • Emergency brake at 5x pressure"
nohup python3 /home/dereadi/scripts/claude/spongy_flywheel_deploy.py > spongy_deploy.log 2>&1 &
DEPLOY_PID=$!
echo "  Started with PID: $DEPLOY_PID"
echo ""

# Start Retrieve Flywheel with spongy throttle
echo "💰 Starting SPONGY RETRIEVE FLYWHEEL..."
echo "  • Harvests profits with resistance"
echo "  • Maintains \$250 liquidity target"
echo "  • Takes 15% profits on winners"
nohup python3 /home/dereadi/scripts/claude/spongy_flywheel_retrieve.py > spongy_retrieve.log 2>&1 &
RETRIEVE_PID=$!
echo "  Started with PID: $RETRIEVE_PID"
echo ""

# Save PIDs
echo "$DEPLOY_PID" > /tmp/spongy_deploy.pid
echo "$RETRIEVE_PID" > /tmp/spongy_retrieve.pid

echo "✅ SPONGY SYSTEM ACTIVE"
echo "======================="
echo ""
echo "🧽 The spongy throttle prevents rapid-fire trading:"
echo "  • Trade 1: \$100 allowed"
echo "  • Trade 2: \$67 allowed (pressure building)"
echo "  • Trade 3: \$44 allowed (more resistance)"
echo "  • Trade 4: Wait 180s (high pressure)"
echo "  • Trade 5: Emergency brake!"
echo ""
echo "Monitor with:"
echo "  tail -f spongy_deploy.log"
echo "  tail -f spongy_retrieve.log"
echo ""
echo "Check throttle status:"
echo "  python3 spongy_throttle_controller.py"
echo ""
echo "Stop with:"
echo "  kill $DEPLOY_PID $RETRIEVE_PID"
echo ""
echo "🧽 Elastic resistance engaged!"