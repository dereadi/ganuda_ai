#!/usr/bin/env python3
import json
import subprocess
import time
from datetime import datetime
import sys

print("Θ THETA (Volatility Specialist) ACTIVATED", flush=True)
print("Mission: Harvest volatility premium", flush=True)
print("-" * 40, flush=True)

def check_volatility(coin):
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
    
    vol = ((high - low) / current) * 100 if current > 0 else 0
    position = (current - low) / (high - low) if high != low else 0.5
    
    if vol > 5:
        print(f"HIGH_VOL:{coin}:{{vol:.2f}}%:POS={{position:.2f}}")
    elif vol > 3:
        print(f"MED_VOL:{coin}:{{vol:.2f}}%")
    else:
        print(f"LOW_VOL:{coin}:{{vol:.2f}}%")
except Exception as e:
    print(f"ERROR:{coin}")
"""
    
    try:
        with open(f"/tmp/theta_{int(time.time()*1000000)}.py", "w") as f:
            f.write(script)
        result = subprocess.run(["python3", f.name], capture_output=True, text=True, timeout=5)
        subprocess.run(["rm", f.name], capture_output=True)
        return result.stdout.strip() if result.stdout else "ERROR"
    except:
        return "TIMEOUT"

coins = ["BTC", "ETH", "SOL", "MATIC"]
cycle = 0

while True:
    cycle += 1
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    for coin in coins:
        result = check_volatility(coin)
        if "HIGH_VOL" in result or "MED_VOL" in result:
            print(f"[{timestamp}] Θ {result}", flush=True)
    
    if cycle % 10 == 0:
        print(f"[{timestamp}] Θ Theta: Cycle {cycle} complete", flush=True)
    
    time.sleep(45)
