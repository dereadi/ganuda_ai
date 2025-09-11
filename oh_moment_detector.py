#!/usr/bin/env python3
"""
😲 OH! - SOMETHING'S HAPPENING!
Quick check on what caught your attention!
"""

import json
import time
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                           😲 OH! MOMENT 😲                                ║
║                      Something Just Happened!                             ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

# Rapid fire check what's moving
print(f"Time: {datetime.now().strftime('%H:%M:%S')} - CHECKING THE SPIKE!")
print("=" * 70)

# Take rapid samples
samples = []
for i in range(5):
    btc = float(client.get_product('BTC-USD')['price'])
    eth = float(client.get_product('ETH-USD')['price'])
    sol = float(client.get_product('SOL-USD')['price'])
    
    samples.append((btc, eth, sol))
    
    print(f"\n{datetime.now().strftime('%H:%M:%S')}:")
    print(f"  BTC: ${btc:,.0f}")
    print(f"  ETH: ${eth:.2f}")
    print(f"  SOL: ${sol:.2f}")
    
    if i > 0:
        btc_move = btc - samples[0][0]
        eth_move = eth - samples[0][1]
        sol_move = sol - samples[0][2]
        
        if abs(btc_move) > 20:
            print(f"  🚨 BTC MOVING! {btc_move:+.0f}")
        if abs(eth_move) > 2:
            print(f"  🚨 ETH MOVING! {eth_move:+.2f}")
        if abs(sol_move) > 0.20:
            print(f"  🚨 SOL MOVING! {sol_move:+.2f}")
    
    time.sleep(1)

# Analysis
btc_range = max([s[0] for s in samples]) - min([s[0] for s in samples])
eth_range = max([s[1] for s in samples]) - min([s[1] for s in samples])
sol_range = max([s[2] for s in samples]) - min([s[2] for s in samples])

print("\n" + "=" * 70)
print("🎯 WHAT JUST HAPPENED:")

if btc_range > 50:
    print("💥 BTC BREAKING OUT OF RANGE!")
elif eth_range > 5:
    print("💥 ETH MAKING A MOVE!")
elif sol_range > 0.50:
    print("💥 SOL SURGING!")
elif btc > 112900:
    print("⚡ Testing upper resistance!")
elif btc < 112800:
    print("📉 Testing lower support!")
else:
    print("🌀 Still coiling but something shifted...")

print("=" * 70)