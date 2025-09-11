#!/bin/bash
# Council monitoring wrapper

# Activate virtual environment
source /home/dereadi/scripts/claude/quantum_crawdad_env/bin/activate

# Run the monitor
python3 /home/dereadi/scripts/claude/council_news_monitor.py >> /home/dereadi/scripts/claude/council_monitor.log 2>&1

# Check DOGE price for alerts
python3 -c "
import json
from coinbase.rest import RESTClient

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=10)

ticker = client.get_product('DOGE-USD')
price = float(ticker['price'])

thresholds = [0.22, 0.24, 0.26, 0.28]
for t in thresholds:
    if abs(price - t) < 0.005:  # Within 0.5 cents of threshold
        print(f'🚨 DOGE ALERT: ${price:.4f} near bleed point ${t}!')
        # Could send Discord alert here
"
