#!/usr/bin/env python3
"""
🚀 BREAKOUT SPECIALIST - LIVE TRADING
Catches explosive breakout moves
"""

import json
import subprocess
import time
from datetime import datetime

print("🚀 BREAKOUT SPECIALIST ACTIVATED")
print("Mission: Catch explosive breakouts")
print("-" * 40)

def detect_breakout(coin):
    """Detect and trade breakouts"""
    script = f"""
import json
from coinbase.rest import RESTClient
import time

config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=3)

try:
    ticker = client.get_product('{coin}-USD')
    current = float(ticker.get("price", 0))
    
    stats = client.get_product_stats('{coin}-USD')
    high_24h = float(stats.get("high", current))
    low_24h = float(stats.get("low", current))
    volume = float(stats.get("volume", 0))
    volume_30d = float(stats.get("volume_30day", volume)) / 30
    
    # Volume surge detection
    volume_surge = volume / max(volume_30d, 1)
    
    # Breakout detection
    if current > high_24h * 1.01 and volume_surge > 1.5:
        # Upward breakout with volume
        order = client.market_order_buy(
            client_order_id=f"breakout_buy_{{int(time.time()*1000)}}",
            product_id="{coin}-USD",
            quote_size="200"
        )
        print(f"BREAKOUT_UP:{coin}:VOL_SURGE={{volume_surge:.2f}}x")
    elif current < low_24h * 0.99 and volume_surge > 1.5:
        # Downward breakout - avoid or short
        print(f"BREAKOUT_DOWN:{coin}:VOL_SURGE={{volume_surge:.2f}}x")
    else:
        range_pct = ((high_24h - low_24h) / current) * 100
        if range_pct < 2:
            print(f"CONSOLIDATING:{coin}:RANGE={{range_pct:.2f}}%")
except Exception as e:
    print(f"ERROR:{{e}}")
"""
    
    try:
        with open(f"/tmp/breakout_{int(time.time()*1000000)}.py", "w") as f:
            f.write(script)
        
        result = subprocess.run(["timeout", "3", "python3", f.name],
                              capture_output=True, text=True)
        subprocess.run(["rm", f.name], capture_output=True)
        
        if result.stdout:
            return result.stdout.strip()
    except:
        pass
    return None

# Main loop
coins = ["BTC", "ETH", "SOL", "DOGE", "SHIB"]
cycle = 0

while True:
    cycle += 1
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    for coin in coins:
        result = detect_breakout(coin)
        if result and "BREAKOUT_" in result:
            print(f"[{timestamp}] {result}")
            
    if cycle % 10 == 0:
        print(f"[{timestamp}] Breakout Specialist: Cycle {cycle} complete")
        
    time.sleep(120)  # Check every 2 minutes
