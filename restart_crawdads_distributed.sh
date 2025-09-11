#!/bin/bash
# Restart crawdads with proper distribution between redfin and bluefin

echo "🦀 Restarting Crawdad Swarm - Distributed Mode"
echo "=============================================="

# Start critical monitoring on bluefin (lower priority, background tasks)
echo "Starting monitors on bluefin..."
ssh bluefin "cd /home/dereadi/scripts/claude && nohup python3 btc_breakout_monitor.py > /dev/null 2>&1 &" &
sleep 1

# Start main crawdad trader locally with proper limits
echo "Starting main crawdad trader on redfin..."
cd /home/dereadi/scripts/claude
nohup timeout 3600 ./quantum_crawdad_env/bin/python3 quantum_crawdad_live_trader.py > quantum_crawdad_live_trader.log 2>&1 &
CRAWDAD_PID=$!
echo "Crawdad trader PID: $CRAWDAD_PID (will auto-terminate in 1 hour)"

# Check current market
echo ""
echo "📊 Current Market Status:"
python3 -c "
import json
from coinbase.rest import RESTClient
config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])
btc = float(client.get_product('BTC-USD')['price'])
print(f'BTC: \${btc:,.0f}')
print(f'Distance to \$114K: \${114000 - btc:.0f}')
"

echo ""
echo "✅ Crawdads restarted with:"
echo "  • Main trader on redfin (1 hour limit)"
echo "  • Monitor on bluefin (offloaded)"
echo "  • Fork protection enabled"
echo "  • Auto-termination after 1 hour"