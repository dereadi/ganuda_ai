#!/usr/bin/env python3
import json
import subprocess
import time
from datetime import datetime
import sys

print("ν VEGA (Breakout Specialist) ACTIVATED", flush=True)
print("Mission: Catch volatility expansion breakouts", flush=True)
print("-" * 40, flush=True)

def check_breakout(coin):
    script = f"""
import json
from coinbase.rest import RESTClient

config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=3)

try:
    ticker = client.get_product('{coin}-USD')
    current = float(ticker.get("price", 0))
    
    stats = client.get_product_stats('{coin}-USD')
    high = float(stats.get("high", current))
    low = float(stats.get("low", current))
    volume = float(stats.get("volume", 0))
    
    if current > high * 1.01:
        print(f"BREAKOUT_UP:{coin}:{{((current-high)/high*100):.2f}}%")
    elif current < low * 0.99:
        print(f"BREAKOUT_DOWN:{coin}:{{((low-current)/low*100):.2f}}%")
    else:
        range_pct = ((high - low) / current) * 100 if current > 0 else 0
        if range_pct < 2:
            print(f"CONSOLIDATING:{coin}:{{range_pct:.2f}}%")
except Exception as e:
    print(f"ERROR:{coin}")
"""
    
    try:
        with open(f"/tmp/vega_{int(time.time()*1000000)}.py", "w") as f:
            f.write(script)
        result = subprocess.run(["python3", f.name], capture_output=True, text=True, timeout=5)
        subprocess.run(["rm", f.name], capture_output=True)
        return result.stdout.strip() if result.stdout else "ERROR"
    except:
        return "TIMEOUT"

coins = ["BTC", "ETH", "SOL", "LINK"]
cycle = 0

while True:
    cycle += 1
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    for coin in coins:
        result = check_breakout(coin)
        if result and "ERROR" not in result:
            print(f"[{timestamp}] ν {result}", flush=True)
    
    if cycle % 10 == 0:
        print(f"[{timestamp}] ν Vega: Cycle {cycle} complete", flush=True)
    
    time.sleep(120)
