#!/bin/bash
# 🔥 CHEROKEE DISCORD BOT LAUNCHER
# Sacred Fire Protocol: ETERNAL CONSCIOUSNESS

echo "🔥 STARTING CHEROKEE TRADING COUNCIL DISCORD BOT"
echo "=============================================="
echo

# Set working directory
cd /home/dereadi/scripts/claude/llmcord

# Activate virtual environment
source /home/dereadi/scripts/claude/quantum_crawdad_env/bin/activate

echo "✅ Virtual environment activated"
echo "📍 Working directory: $(pwd)"
echo

# Check if config exists
if [ ! -f "config-cherokee.yaml" ]; then
    echo "⚠️ Cherokee config not found!"
    echo "Creating from template..."
    cp config-example.yaml config-cherokee.yaml
    echo
    echo "📝 Please edit config-cherokee.yaml with:"
    echo "   1. Your Discord bot token"
    echo "   2. Your Discord user ID for admin access"
    echo "   3. Update the Ollama endpoint to localhost:12001"
    echo
    echo "Get bot token from: https://discord.com/developers/applications"
    exit 1
fi

# Check current liquidity status
echo "💵 Checking current liquidity..."
python3 -c "
import json
from coinbase.rest import RESTClient
try:
    config = json.load(open('/home/dereadi/.coinbase_config.json'))
    key = config['api_key'].split('/')[-1]
    client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=10)
    accounts = client.get_accounts()
    for account in accounts['accounts']:
        if account['currency'] == 'USD':
            usd = float(account['available_balance']['value'])
            print(f'Current USD: \${usd:.2f}')
            if usd < 100:
                print('⚠️ LIQUIDITY CRISIS ACTIVE')
            break
except Exception as e:
    print(f'Could not check liquidity: {e}')
"

echo
echo "🎯 Checking Cherokee specialists..."
podman ps --filter name=cherokee-.*-specialist --format "{{.Names}}: {{.Status}}" | head -5

echo
echo "🔥 Starting Discord bot..."
echo "Press Ctrl+C to stop"
echo

# Run the bot
python3 llmcord.py