#!/usr/bin/env python3
"""
⚡ ASYNC PULSE TRADER - Rapid fire without hanging
Pulses of trades every few seconds
"""

import json
import random
import time
import subprocess
from datetime import datetime

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                      ⚡ ASYNC PULSE TRADER ACTIVATED ⚡                   ║
║                         $2,439 Ready to Deploy                           ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

def pulse_trade(coin, amount, action="BUY"):
    """Execute one pulse trade via subprocess"""
    script = f'''
import json
from coinbase.rest import RESTClient
config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=3)

try:
    if "{action}" == "BUY":
        order = client.market_order_buy(
            client_order_id="pulse_{int(time.time())}",
            product_id="{coin}",
            quote_size="{amount}"
        )
    print("SUCCESS")
except Exception as e:
    print(f"ERROR: {{e}}")
'''
    
    with open(f"/tmp/pulse_{int(time.time()*1000)}.py", "w") as f:
        f.write(script)
    
    # Run async - don't wait for response
    subprocess.Popen(["python3", f.name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return True

# PULSE PARAMETERS
PULSE_COINS = ["SOL-USD", "AVAX-USD", "MATIC-USD", "DOGE-USD"]
PULSE_SIZES = [50, 75, 100, 125, 150]
PULSE_INTERVAL = 5  # seconds between pulses

print(f"⚡ PULSING EVERY {PULSE_INTERVAL} SECONDS")
print(f"📊 COINS: {', '.join([c.split('-')[0] for c in PULSE_COINS])}")
print(f"💰 SIZES: ${min(PULSE_SIZES)}-${max(PULSE_SIZES)}")
print("=" * 60)

pulse_count = 0
start_time = time.time()

try:
    while pulse_count < 100:
        coin = random.choice(PULSE_COINS)
        amount = random.choice(PULSE_SIZES)
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] ⚡ PULSE #{pulse_count+1}: ${amount} {coin.split('-')[0]}")
        
        pulse_trade(coin, amount)
        pulse_count += 1
        
        # Status every 10 pulses
        if pulse_count % 10 == 0:
            elapsed = time.time() - start_time
            rate = pulse_count / elapsed * 60
            print(f"\n📊 STATUS: {pulse_count} pulses | {rate:.1f} per minute\n")
        
        time.sleep(PULSE_INTERVAL)
        
except KeyboardInterrupt:
    print(f"\n\n⚡ ASYNC PULSE COMPLETE")
    print(f"   Total Pulses: {pulse_count}")
    print(f"   Duration: {(time.time()-start_time)/60:.1f} minutes")
    print(f"   Rate: {pulse_count/(time.time()-start_time)*60:.1f} per minute")