
#!/usr/bin/env python3
import json
import time
from coinbase.rest import RESTClient
import random

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=3)

MIN_ORDER = 10  # $10 minimum per trade
DEFAULT_ORDER = 25  # $25 default

print("🏛️ GREEK FUNDED AND HUNTING!")
print(f"Min order: ${MIN_ORDER}, Default: ${DEFAULT_ORDER}")

cycle = 0
while True:
    cycle += 1
    try:
        btc = client.get_product('BTC-USD')
        price = float(btc.price)
        
        # Only trade if we have the capital
        if random.random() < 0.1:  # 10% chance per cycle
            order_size = DEFAULT_ORDER / price
            if order_size * price >= MIN_ORDER:
                print(f"Cycle {cycle}: Would buy {order_size:.8f} BTC at ${price:,.2f}")
        
        if cycle % 10 == 0:
            print(f"Cycle {cycle}: Monitoring ${price:,.2f}")
        
        time.sleep(30)
        
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(10)
