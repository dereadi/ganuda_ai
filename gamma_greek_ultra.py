#!/usr/bin/env python3
"""
Γ GAMMA ULTRA - Fast Trend Acceleration Specialist
Simplified for speed, no timeouts
"""

import json
import time
from datetime import datetime
from coinbase.rest import RESTClient

print("Γ GAMMA ULTRA - FAST TREND SPECIALIST", flush=True)
print("=" * 40, flush=True)

# Initialize client once
config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=2)

coins = ["BTC", "ETH", "SOL"]
last_prices = {}
cycle = 0

print(f"[{datetime.now().strftime('%H:%M:%S')}] Γ Gamma Ultra initialized", flush=True)

while True:
    cycle += 1
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    for coin in coins:
        try:
            # Single fast API call
            ticker = client.get_product(f'{coin}-USD')
            price = float(ticker.get("price", 0))
            
            if price > 0:
                if coin in last_prices:
                    # Calculate acceleration
                    change_pct = ((price - last_prices[coin]) / last_prices[coin]) * 100
                    
                    # Detect trends
                    if abs(change_pct) > 0.1:  # 0.1% movement
                        if change_pct > 0.5:
                            print(f"[{timestamp}] Γ STRONG_UP:{coin}:+{change_pct:.2f}%:${price:.2f}", flush=True)
                        elif change_pct > 0.1:
                            print(f"[{timestamp}] Γ TREND_UP:{coin}:+{change_pct:.2f}%", flush=True)
                        elif change_pct < -0.5:
                            print(f"[{timestamp}] Γ STRONG_DOWN:{coin}:{change_pct:.2f}%:${price:.2f}", flush=True)
                        elif change_pct < -0.1:
                            print(f"[{timestamp}] Γ TREND_DOWN:{coin}:{change_pct:.2f}%", flush=True)
                
                last_prices[coin] = price
                
        except Exception as e:
            # Silent fail, keep going
            pass
    
    if cycle % 10 == 0:
        active_coins = [c for c in last_prices if last_prices[c] > 0]
        print(f"[{timestamp}] Γ Gamma Ultra: Cycle {cycle} | Tracking {len(active_coins)} coins", flush=True)
    
    time.sleep(60)  # Check every minute