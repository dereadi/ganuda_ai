#!/usr/bin/env python3
"""
🏄🦀 SURFING Q-DADS
===================
Ride the micro waves!
"""

import json
import time
from datetime import datetime
from coinbase.rest import RESTClient

# Load config
config = json.load(open("/home/dereadi/.coinbase_config.json"))
client = RESTClient(api_key=config["api_key"], api_secret=config["api_secret"])

print("🏄🦀 SURFING Q-DADS ACTIVATED!")
print("="*60)
print("Watching micro price waves...")
print()

# Track prices
last_prices = {}
wave_count = 0

for i in range(20):  # 20 checks
    wave_count += 1
    print(f"\n🌊 Wave #{wave_count} - {datetime.now().strftime('%H:%M:%S')}")
    
    for symbol in ["BTC", "ETH", "SOL"]:
        try:
            ticker = client.get_product(f"{symbol}-USD")
            price = float(ticker.get('price', 0))
            
            if symbol in last_prices:
                change = price - last_prices[symbol]
                change_pct = (change / last_prices[symbol]) * 100
                
                # Detect micro movements
                if abs(change_pct) > 0.01:  # 0.01% movement
                    if change > 0:
                        print(f"  🏄‍♂️ {symbol}: ${price:,.2f} ↑ (+{change_pct:.3f}%) SURF UP!")
                    else:
                        print(f"  🏄‍♀️ {symbol}: ${price:,.2f} ↓ ({change_pct:.3f}%) SURF DOWN!")
                else:
                    print(f"  🌊 {symbol}: ${price:,.2f} ~ flat")
            else:
                print(f"  📊 {symbol}: ${price:,.2f}")
            
            last_prices[symbol] = price
            
        except Exception as e:
            print(f"  ❌ {symbol}: Error")
    
    time.sleep(3)  # Check every 3 seconds

print()
print("🏄 Q-Dads rode 20 waves!")
print("Ready to catch more micro movements!")