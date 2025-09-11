#!/bin/bash
# Tribal Night Watch - Automated through the night

echo "🔥 TRIBAL NIGHT WATCH ACTIVE"
echo "Running until market open..."

while true; do
    current_hour=$(date +%H)
    current_min=$(date +%M)
    
    # Check if market is open (9:30 AM)
    if [ $current_hour -eq 9 ] && [ $current_min -ge 30 ]; then
        echo "🌅 Dawn has come. Night watch complete."
        break
    fi
    
    # Run harvest check
    echo ""
    echo "🔥 Night Watch Check - $(date +%H:%M:%S)"
    python3 /home/dereadi/scripts/claude/check_and_harvest.py
    
    # Feed crawdads if needed
    usd_balance=$(python3 -c "
import json
from coinbase.rest import RESTClient
config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])
accounts = client.get_accounts()
for account in accounts['accounts']:
    if account['currency'] == 'USD':
        print(float(account['available_balance']['value']))
        break
")
    
    if (( $(echo "$usd_balance > 100" | bc -l) )); then
        echo "🦀 Crawdads have fuel: $${usd_balance}"
    else
        echo "⚠️ Low fuel: $${usd_balance} - Harvesting..."
        python3 /home/dereadi/scripts/claude/execute_feast_harvest.py
    fi
    
    # Sleep 15 minutes
    echo "💤 Next check in 15 minutes..."
    sleep 900
done
