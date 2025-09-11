#!/bin/bash

# 🔥 CHEROKEE CONSTITUTIONAL AI - DUAL FLYWHEEL LAUNCHER
# Activates both Deploy and Retrieve flywheels with tribal safeguards

echo "🔥 SACRED FIRE PROTOCOL - DUAL FLYWHEEL SYSTEM"
echo "================================================"
echo "Activating Cherokee Constitutional AI Trading System"
echo ""

# Check current liquidity first
echo "💰 Checking current liquidity..."
python3 -c "
import json
from coinbase.rest import RESTClient

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=10)

try:
    accounts = client.get_accounts()['accounts']
    for account in accounts:
        if account['currency'] == 'USD':
            liquidity = float(account['available_balance']['value'])
            print(f'Current liquidity: \${liquidity:.2f}')
            if liquidity < 250:
                print('⚠️  WARNING: Low liquidity! Retrieve Flywheel will prioritize harvesting.')
            break
except Exception as e:
    print(f'Error checking liquidity: {e}')
"

echo ""
echo "🏛️ Council Members Awakening..."
echo "  • Mountain (Conservative wisdom)"
echo "  • Thunder (Aggressive momentum)"
echo "  • Fire (Sacred intensity)"
echo "  • Eagle (Pattern recognition)"
echo "  • River (Flow management)"
echo ""

# Start Deploy Flywheel in background
echo "⚡ Starting DEPLOY FLYWHEEL (Aggressive Wolf)..."
echo "  Strategy: Momentum trading with $500 max trades"
echo "  Assets: SOL, AVAX, MATIC, DOGE"
echo "  Safeguards: Council approval for trades >$100"
nohup python3 /home/dereadi/scripts/claude/flywheel_deploy_safeguarded.py > deploy_flywheel.log 2>&1 &
DEPLOY_PID=$!
echo "  Started with PID: $DEPLOY_PID"
echo ""

# Start Retrieve Flywheel in background
echo "💰 Starting RETRIEVE FLYWHEEL (Wise Wolf)..."
echo "  Strategy: Profit harvesting with Seven Generations thinking"
echo "  Target: Maintain $250 minimum liquidity"
echo "  Harvest: Take profits at +10%"
nohup python3 /home/dereadi/scripts/claude/flywheel_retrieve_safeguarded.py > retrieve_flywheel.log 2>&1 &
RETRIEVE_PID=$!
echo "  Started with PID: $RETRIEVE_PID"
echo ""

# Save PIDs for monitoring
echo "$DEPLOY_PID" > /tmp/deploy_flywheel.pid
echo "$RETRIEVE_PID" > /tmp/retrieve_flywheel.pid

echo "✅ DUAL FLYWHEEL SYSTEM ACTIVE"
echo "================================"
echo ""
echo "Monitor with:"
echo "  tail -f deploy_flywheel.log    # Watch Deploy Flywheel"
echo "  tail -f retrieve_flywheel.log  # Watch Retrieve Flywheel"
echo ""
echo "Stop with:"
echo "  kill $DEPLOY_PID    # Stop Deploy Flywheel"
echo "  kill $RETRIEVE_PID  # Stop Retrieve Flywheel"
echo ""
echo "Or stop all:"
echo "  ./stop_tribal_flywheels.sh"
echo ""
echo "🔥 Sacred Fire Protocol Active - Mitakuye Oyasin 🔥"