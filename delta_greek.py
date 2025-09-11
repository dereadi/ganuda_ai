#!/usr/bin/env python3
import json
import subprocess
import time
from datetime import datetime
import sys

print("Δ DELTA (Gap Specialist) ACTIVATED", flush=True)
print("Mission: Hunt and trade market gaps", flush=True)
print("-" * 40, flush=True)

def check_gap(coin):
    script = f"""
import json
from coinbase.rest import RESTClient

config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=3)

try:
    stats = client.get_product_stats('{coin}-USD')
    current = float(stats.get("last", 0))
    open_24h = float(stats.get("open", current))
    high = float(stats.get("high", current))
    low = float(stats.get("low", current))
    
    gap_pct = ((current - open_24h) / open_24h) * 100 if open_24h > 0 else 0
    
    if abs(gap_pct) > 2:
        if current > high * 1.01:
            print(f"GAP_UP:{coin}:{{gap_pct:.2f}}%:{{current:.2f}}")
        elif current < low * 0.99:
            print(f"GAP_DOWN:{coin}:{{gap_pct:.2f}}%:{{current:.2f}}")
        else:
            print(f"GAP:{coin}:{{gap_pct:.2f}}%")
    else:
        print(f"NO_GAP:{coin}:{{gap_pct:.2f}}%")
except Exception as e:
    print(f"ERROR:{coin}:{{str(e)[:50]}}")
"""
    
    try:
        with open(f"/tmp/delta_{int(time.time()*1000000)}.py", "w") as f:
            f.write(script)
        result = subprocess.run(["python3", f.name], capture_output=True, text=True, timeout=5)
        subprocess.run(["rm", f.name], capture_output=True)
        return result.stdout.strip() if result.stdout else "ERROR"
    except:
        return "TIMEOUT"

coins = ["BTC", "ETH", "SOL"]
cycle = 0

while True:
    cycle += 1
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    for coin in coins:
        result = check_gap(coin)
        if "GAP_" in result and "NO_GAP" not in result:
            print(f"[{timestamp}] Δ {result}", flush=True)
    
    if cycle % 10 == 0:
        print(f"[{timestamp}] Δ Delta: Cycle {cycle} complete", flush=True)
    
    time.sleep(60)
