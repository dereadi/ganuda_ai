#!/usr/bin/env python3
"""
🎯 MEAN REVERSION SPECIALIST - LIVE TRADING
Trades extremes back to mean
"""

import json
import subprocess
import time
from datetime import datetime
import numpy as np

print("🎯 MEAN REVERSION SPECIALIST ACTIVATED")
print("Mission: Trade extremes back to mean")
print("-" * 40)

def calculate_deviation(coin):
    """Calculate deviation from mean and trade"""
    script = f"""
import json
from coinbase.rest import RESTClient
import time

config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=3)

try:
    stats = client.get_product_stats('{coin}-USD')
    current = float(stats.get("last", 0))
    high = float(stats.get("high", current))
    low = float(stats.get("low", current))
    open_24h = float(stats.get("open", current))
    
    # Calculate mean and deviation
    mean = (high + low + open_24h) / 3
    deviation_pct = ((current - mean) / mean) * 100
    
    # Mean reversion trades
    if deviation_pct > 3:  # 3% above mean
        # Sell - expect reversion down
        order = client.market_order_sell(
            client_order_id=f"revert_sell_{{int(time.time()*1000)}}",
            product_id="{coin}-USD",
            quote_size="100"
        )
        print(f"REVERT_SELL:{coin}:DEV=+{{deviation_pct:.2f}}%")
    elif deviation_pct < -3:  # 3% below mean
        # Buy - expect reversion up
        order = client.market_order_buy(
            client_order_id=f"revert_buy_{{int(time.time()*1000)}}",
            product_id="{coin}-USD",
            quote_size="100"
        )
        print(f"REVERT_BUY:{coin}:DEV={{deviation_pct:.2f}}%")
    else:
        print(f"NEAR_MEAN:{coin}:DEV={{deviation_pct:.2f}}%")
except Exception as e:
    print(f"ERROR:{{e}}")
"""
    
    try:
        with open(f"/tmp/revert_{int(time.time()*1000000)}.py", "w") as f:
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
coins = ["BTC", "ETH", "SOL", "MATIC", "DOT"]
cycle = 0

while True:
    cycle += 1
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    for coin in coins:
        result = calculate_deviation(coin)
        if result and "REVERT_" in result:
            print(f"[{timestamp}] {result}")
            
    if cycle % 10 == 0:
        print(f"[{timestamp}] Mean Reversion Specialist: Cycle {cycle} complete")
        
    time.sleep(60)  # Check every minute
