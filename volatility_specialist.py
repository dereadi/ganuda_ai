#!/usr/bin/env python3
"""
⚡ VOLATILITY SPECIALIST - LIVE TRADING
Harvests volatility premiums and extreme moves
"""

import json
import subprocess
import time
from datetime import datetime

print("⚡ VOLATILITY SPECIALIST ACTIVATED")
print("Mission: Harvest volatility premiums")
print("-" * 40)

def trade_volatility(coin):
    """Trade based on volatility conditions"""
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
    
    volatility = ((high - low) / current) * 100
    position = (current - low) / (high - low) if high != low else 0.5
    
    # Extreme volatility trading
    if volatility > 5:  # 5% daily range
        if position > 0.85:
            # Extreme overbought in high vol
            order = client.market_order_sell(
                client_order_id=f"vol_sell_{{int(time.time()*1000)}}",
                product_id="{coin}-USD",
                quote_size="150"
            )
            print(f"VOL_SELL:{coin}:{{volatility:.2f}}%:POS={{position:.2f}}")
        elif position < 0.15:
            # Extreme oversold in high vol
            order = client.market_order_buy(
                client_order_id=f"vol_buy_{{int(time.time()*1000)}}",
                product_id="{coin}-USD",
                quote_size="150"
            )
            print(f"VOL_BUY:{coin}:{{volatility:.2f}}%:POS={{position:.2f}}")
        else:
            print(f"VOL_WAIT:{coin}:{{volatility:.2f}}%")
    else:
        print(f"LOW_VOL:{coin}:{{volatility:.2f}}%")
except Exception as e:
    print(f"ERROR:{{e}}")
"""
    
    try:
        with open(f"/tmp/vol_{int(time.time()*1000000)}.py", "w") as f:
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
coins = ["BTC", "ETH", "SOL", "AVAX", "ATOM"]
cycle = 0

while True:
    cycle += 1
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    for coin in coins:
        result = trade_volatility(coin)
        if result and "VOL_" in result and "LOW_VOL" not in result:
            print(f"[{timestamp}] {result}")
            
    if cycle % 10 == 0:
        print(f"[{timestamp}] Volatility Specialist: Cycle {cycle} complete")
        
    time.sleep(45)  # Check every 45 seconds for volatility
