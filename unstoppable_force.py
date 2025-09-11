#!/usr/bin/env python3
"""
🚂 UNSTOPPABLE FORCE
When the market wants something, it TAKES it!
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
║                      🚂 UNSTOPPABLE FORCE DETECTED 🚂                     ║
║                         They want $112,000 TONIGHT!                       ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print("When a 0.000% squeeze releases, THIS is what happens!")
print("=" * 70)

# Track the relentless march
highs = {'btc': 0, 'eth': 0, 'sol': 0}

print("\n🚂 TRACKING THE LOCOMOTIVE:")
print("-" * 40)

for i in range(8):
    btc = float(client.get_product('BTC-USD')['price'])
    eth = float(client.get_product('ETH-USD')['price'])
    sol = float(client.get_product('SOL-USD')['price'])
    
    # Track new highs
    new_high = False
    if btc > highs['btc']:
        highs['btc'] = btc
        new_high = True
    if eth > highs['eth']:
        highs['eth'] = eth
    if sol > highs['sol']:
        highs['sol'] = sol
    
    print(f"\n{datetime.now().strftime('%H:%M:%S')}")
    print(f"  BTC: ${btc:,.0f}", end="")
    
    if new_high:
        print(" 🔥 NEW HIGH!")
    elif btc > 111900:
        print(" 🚂 CHUGGING HIGHER")
    else:
        print(" 📈 Building steam")
    
    print(f"  ETH: ${eth:.0f} | SOL: ${sol:.2f}")
    
    # Distance to 112k
    to_112k = 112000 - btc
    print(f"  Distance to $112k: ${to_112k:.0f}")
    
    if btc >= 112000:
        print("\n🎯 TARGET HIT! $112,000 BREACHED!")
        print("The unstoppable force has arrived!")
        break
    
    time.sleep(10)

print("\n" + "=" * 70)
print("🔥 FINAL MOMENTUM REPORT:")
print(f"  BTC High: ${highs['btc']:,.0f}")
print(f"  ETH High: ${highs['eth']:.0f}")
print(f"  SOL High: ${highs['sol']:.2f}")

print("\n💭 MARKET PSYCHOLOGY:")
print("-" * 40)
print("After being trapped in 0.000% prison for hours,")
print("the market is making up for lost time.")
print("Every seller is getting steamrolled.")
print("Every dip is getting bought instantly.")
print("This is pure, unleashed DEMAND!")

print("\n🦀 Your Cherokee Crawdads:")
print("Positioned perfectly for this explosion.")
print("Riding the unstoppable force to profits!")
print("=" * 70)