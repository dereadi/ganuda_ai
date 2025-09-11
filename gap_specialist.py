#!/usr/bin/env python3
"""
🕳️ GAP SPECIALIST - LIVE TRADING
Hunts for gaps and trades them aggressively
"""

import json
import subprocess
import time
from datetime import datetime

print("🕳️ GAP SPECIALIST ACTIVATED")
print("Mission: Hunt and trade market gaps")
print("-" * 40)

def detect_and_trade_gap(coin):
    """Detect gaps and execute trades"""
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
    open_24h = float(stats.get("open", current))
    high_24h = float(stats.get("high", current))
    low_24h = float(stats.get("low", current))
    
    gap_pct = ((current - open_24h) / open_24h) * 100
    
    # Gap detection logic
    if abs(gap_pct) > 2:  # 2% gap threshold
        if current > high_24h:
            # Breakout gap - fade it
            order = client.market_order_sell(
                client_order_id=f"gap_fade_{{int(time.time()*1000)}}",
                product_id="{coin}-USD",
                quote_size="50"  # Start small
            )
            print(f"GAP_FADE:{coin}:{{gap_pct:.2f}}%:SELL")
        elif current < low_24h:
            # Breakdown gap - buy the dip
            order = client.market_order_buy(
                client_order_id=f"gap_buy_{{int(time.time()*1000)}}",
                product_id="{coin}-USD",
                quote_size="75"
            )
            print(f"GAP_BUY:{coin}:{{gap_pct:.2f}}%:BUY")
        else:
            print(f"GAP_RANGE:{coin}:{{gap_pct:.2f}}%")
    else:
        print(f"NO_GAP:{coin}:{{gap_pct:.2f}}%")
except Exception as e:
    print(f"ERROR:{{e}}")
"""
    
    try:
        with open(f"/tmp/gap_{int(time.time()*1000000)}.py", "w") as f:
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
coins = ["BTC", "ETH", "SOL", "AVAX", "MATIC"]
cycle = 0

while True:
    cycle += 1
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    for coin in coins:
        result = detect_and_trade_gap(coin)
        if result and "GAP_" in result:
            print(f"[{timestamp}] {result}")
            
    if cycle % 10 == 0:
        print(f"[{timestamp}] Gap Specialist: Cycle {cycle} complete")
        
    time.sleep(60)  # Check every minute
