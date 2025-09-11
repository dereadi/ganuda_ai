#!/usr/bin/env python3
"""
🌏 ASIAN SESSION MONITOR
Tracks Asia's impact on portfolio
"""

import json
import time
from datetime import datetime, timezone
import pytz
from coinbase.rest import RESTClient

print("🌏 ASIAN SESSION IMPACT MONITOR")
print("Watching for Asian whale activity...")
print("-" * 50)

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=10)

# Track initial prices
initial_prices = {}
coins = ['BTC', 'ETH', 'SOL']

for coin in coins:
    try:
        ticker = client.get_product(f'{coin}-USD')
        initial_prices[coin] = float(ticker['price'])
        print(f"{coin}: Starting at ${initial_prices[coin]:,.2f}")
    except:
        pass

print("\n📊 MONITORING ASIAN SESSION IMPACT:")
print("-" * 40)

# Monitor for 30 minutes
start_time = time.time()
check_interval = 300  # 5 minutes

while time.time() - start_time < 1800:  # 30 minutes
    time.sleep(check_interval)
    
    tokyo = pytz.timezone('Asia/Tokyo')
    tokyo_time = datetime.now(timezone.utc).astimezone(tokyo)
    
    print(f"\n[Tokyo {tokyo_time.strftime('%H:%M')}] Price Movement:")
    
    for coin in coins:
        try:
            ticker = client.get_product(f'{coin}-USD')
            current = float(ticker['price'])
            change_pct = ((current - initial_prices[coin]) / initial_prices[coin]) * 100
            
            # Detect significant moves
            emoji = "🚀" if change_pct > 1 else "📉" if change_pct < -1 else "➡️"
            
            print(f"  {coin}: ${current:,.2f} ({change_pct:+.2f}%) {emoji}")
            
            # SOL specific alerts
            if coin == 'SOL' and abs(change_pct) > 2:
                print(f"    ⚠️ SOL ASIAN SURGE DETECTED!")
                
        except Exception as e:
            print(f"  {coin}: Error checking")
    
    # Check volume patterns
    try:
        sol_stats = client.get_product_stats('SOL-USD')
        volume = float(sol_stats.get('volume', 0))
        if volume > 1000000:  # High volume
            print(f"  📊 SOL Volume: {volume/1000000:.1f}M (HIGH ACTIVITY)")
    except:
        pass

print("\n✅ Asian session monitoring complete")