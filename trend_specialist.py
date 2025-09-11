#!/usr/bin/env python3
"""
📈 TREND SPECIALIST - LIVE TRADING
Rides strong trends with momentum
"""

import json
import subprocess
import time
from datetime import datetime
import numpy as np

print("📈 TREND SPECIALIST ACTIVATED")
print("Mission: Ride strong directional trends")
print("-" * 40)

def calculate_trend_and_trade(coin):
    """Calculate trend strength and trade accordingly"""
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
    open_24h = float(stats.get("open", current))
    high = float(stats.get("high", current))
    low = float(stats.get("low", current))
    
    # Calculate trend metrics
    trend_pct = ((current - open_24h) / open_24h) * 100
    position_in_range = (current - low) / (high - low) if high != low else 0.5
    
    # Strong trend detection
    if trend_pct > 3 and position_in_range > 0.7:
        # Strong uptrend - buy
        order = client.market_order_buy(
            client_order_id=f"trend_buy_{{int(time.time()*1000)}}",
            product_id="{coin}-USD",
            quote_size="100"
        )
        print(f"TREND_BUY:{coin}:+{{trend_pct:.2f}}%")
    elif trend_pct < -3 and position_in_range < 0.3:
        # Strong downtrend - sell if we have position
        accounts = client.get_accounts()["accounts"]
        for a in accounts:
            if a["currency"] == "{coin}":
                balance = float(a["available_balance"]["value"])
                if balance > 0.001:
                    order = client.market_order_sell(
                        client_order_id=f"trend_sell_{{int(time.time()*1000)}}",
                        product_id="{coin}-USD",
                        base_size=str(balance * 0.1)
                    )
                    print(f"TREND_SELL:{coin}:{{trend_pct:.2f}}%")
                break
    else:
        print(f"TREND_NEUTRAL:{coin}:{{trend_pct:.2f}}%")
except Exception as e:
    print(f"ERROR:{{e}}")
"""
    
    try:
        with open(f"/tmp/trend_{int(time.time()*1000000)}.py", "w") as f:
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
coins = ["BTC", "ETH", "SOL", "LINK", "UNI"]
cycle = 0

while True:
    cycle += 1
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    for coin in coins:
        result = calculate_trend_and_trade(coin)
        if result and "TREND_" in result and "NEUTRAL" not in result:
            print(f"[{timestamp}] {result}")
            
    if cycle % 10 == 0:
        print(f"[{timestamp}] Trend Specialist: Cycle {cycle} complete")
        
    time.sleep(90)  # Check every 1.5 minutes
