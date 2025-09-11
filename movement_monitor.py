#!/usr/bin/env python3
"""
📈 REAL-TIME MOVEMENT MONITOR
Track the volatility as it happens
"""

import json
import time
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("🎢 LIVE MOVEMENT TRACKER")
print("=" * 50)

# Starting prices
start_prices = {
    'BTC': float(client.get_product('BTC-USD')['price']),
    'ETH': float(client.get_product('ETH-USD')['price']),
    'SOL': float(client.get_product('SOL-USD')['price'])
}

print(f"Starting at {datetime.now().strftime('%H:%M:%S')}:")
for coin, price in start_prices.items():
    print(f"  {coin}: ${price:,.2f}")

print("\nMONITORING MOVEMENT...")
print("-" * 50)

for i in range(10):
    time.sleep(6)
    
    # Get current prices
    current = {
        'BTC': float(client.get_product('BTC-USD')['price']),
        'ETH': float(client.get_product('ETH-USD')['price']),
        'SOL': float(client.get_product('SOL-USD')['price'])
    }
    
    # Calculate changes
    print(f"\n{datetime.now().strftime('%H:%M:%S')}:")
    for coin in ['BTC', 'ETH', 'SOL']:
        change = current[coin] - start_prices[coin]
        pct = (change / start_prices[coin]) * 100
        
        # Emoji based on movement
        if pct > 0.1:
            emoji = "🚀"
        elif pct < -0.1:
            emoji = "🩸"
        else:
            emoji = "➡️"
            
        print(f"  {emoji} {coin}: ${current[coin]:,.2f} ({pct:+.3f}%)")

print("\n" + "=" * 50)
print("MOVEMENT CAPTURED!")