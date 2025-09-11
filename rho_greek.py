#!/usr/bin/env python3
import json
import subprocess
import time
from datetime import datetime
import sys

print("ρ RHO (Mean Reversion Specialist) ACTIVATED", flush=True)
print("Mission: Trade rate reversions to mean", flush=True)
print("-" * 40, flush=True)

def check_deviation(coin):
    script = f"""
import json
from coinbase.rest import RESTClient

config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=3)

try:
    stats = client.get_product_stats('{coin}-USD')
    current = float(stats.get("last", 0))
    high = float(stats.get("high", current))
    low = float(stats.get("low", current))
    open_24h = float(stats.get("open", current))
    
    mean = (high + low + open_24h) / 3
    deviation = ((current - mean) / mean) * 100 if mean > 0 else 0
    
    if abs(deviation) > 3:
        direction = "ABOVE" if deviation > 0 else "BELOW"
        print(f"DEVIATION_{direction}:{coin}:{{deviation:.2f}}%:MEAN={{mean:.2f}}")
    else:
        print(f"NEAR_MEAN:{coin}:{{deviation:.2f}}%")
except Exception as e:
    print(f"ERROR:{coin}")
"""
    
    try:
        with open(f"/tmp/rho_{int(time.time()*1000000)}.py", "w") as f:
            f.write(script)
        result = subprocess.run(["python3", f.name], capture_output=True, text=True, timeout=5)
        subprocess.run(["rm", f.name], capture_output=True)
        return result.stdout.strip() if result.stdout else "ERROR"
    except:
        return "TIMEOUT"

coins = ["BTC", "ETH", "SOL", "DOT"]
cycle = 0

while True:
    cycle += 1
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    for coin in coins:
        result = check_deviation(coin)
        if "DEVIATION_" in result:
            print(f"[{timestamp}] ρ {result}", flush=True)
    
    if cycle % 10 == 0:
        print(f"[{timestamp}] ρ Rho: Cycle {cycle} complete", flush=True)
    
    time.sleep(60)
