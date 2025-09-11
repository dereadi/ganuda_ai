#!/bin/bash
# Monitor crawdad trading activity

echo "🦀 QUANTUM CRAWDAD MONITOR"
echo "=========================="

while true; do
    # Get current balance
    BALANCE=$(./quantum_crawdad_env/bin/python3 -c "from coinbase.rest import RESTClient; import json; c=json.load(open('/home/dereadi/.coinbase_config.json')); key=c['api_key'].split('/')[-1]; client=RESTClient(api_key=key, api_secret=c['api_secret']); print([a for a in client.get_accounts()['accounts'] if a['currency']=='USD'][0]['available_balance']['value'][:7])")
    
    # Get timestamp
    TIME=$(date +"%H:%M:%S")
    
    # Display status
    echo "[$TIME] Balance: \$$BALANCE | Crawdads learning..."
    
    # Check if process is still running
    if ! ps -p 1172028 > /dev/null; then
        echo "⚠️  Crawdads stopped! Restarting..."
        nohup ./quantum_crawdad_env/bin/python3 quantum_crawdads_live_final.py >> crawdad_trades.log 2>&1 &
    fi
    
    sleep 60
done