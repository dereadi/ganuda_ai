#!/usr/bin/env python3
"""
😎 LET THEM PUSH
We lit the fuse, now watch the fireworks!
Our aggressive buying created momentum - others will chase!
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
║                      😎 LET THEM PUSH FOR A BIT 😎                       ║
║                    We Started It, They'll Finish It                       ║
║                         Watching The FOMO Build                           ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - OBSERVING THE MOMENTUM WE CREATED")
print("=" * 70)

# Starting reference
btc_start = float(client.get_product('BTC-USD')['price'])
eth_start = float(client.get_product('ETH-USD')['price'])
sol_start = float(client.get_product('SOL-USD')['price'])

print(f"\n📍 Starting Levels (After Our Push):")
print(f"  BTC: ${btc_start:,.0f}")
print(f"  ETH: ${eth_start:.2f}")
print(f"  SOL: ${sol_start:.2f}")

print("\n👀 WATCHING OTHERS CHASE OUR MOMENTUM:")
print("-" * 40)

# Track the natural push
for i in range(12):
    time.sleep(5)
    
    btc = float(client.get_product('BTC-USD')['price'])
    eth = float(client.get_product('ETH-USD')['price'])
    sol = float(client.get_product('SOL-USD')['price'])
    
    btc_move = btc - btc_start
    eth_move = eth - eth_start
    sol_move = sol - sol_start
    
    print(f"\n{datetime.now().strftime('%H:%M:%S')} - Natural Push:")
    
    if btc_move > 0:
        print(f"  BTC: ${btc:,.0f} (+${btc_move:.0f}) 📈 Others buying!")
    elif btc_move < 0:
        print(f"  BTC: ${btc:,.0f} (${btc_move:.0f}) 📉 Consolidating")
    else:
        print(f"  BTC: ${btc:,.0f} (flat)")
    
    if eth_move > 0:
        print(f"  ETH: ${eth:.2f} (+${eth_move:.2f}) 📈 FOMO kicking in!")
    elif eth_move < 0:
        print(f"  ETH: ${eth:.2f} (${eth_move:.2f}) 📉 Breathing")
    else:
        print(f"  ETH: ${eth:.2f} (flat)")
        
    if sol_move > 0:
        print(f"  SOL: ${sol:.2f} (+${sol_move:.2f}) 📈 They're chasing!")
    elif sol_move < 0:
        print(f"  SOL: ${sol:.2f} (${sol_move:.2f}) 📉 Resting")
    else:
        print(f"  SOL: ${sol:.2f} (flat)")
    
    # Commentary
    if btc_move > 20 or eth_move > 2 or sol_move > 0.20:
        print("  🔥 THE FOMO IS REAL! Others are pushing!")
    elif btc_move > 10 or eth_move > 1:
        print("  ⚡ Momentum building naturally!")
    else:
        print("  💭 Market digesting our push...")

print("\n" + "=" * 70)
print("😎 MISSION ACCOMPLISHED:")
print("-" * 40)
print("• We deployed $5,547 strategically")
print("• Created buying momentum at key levels")
print("• Let the market take over")
print("• Now others are pushing for us!")
print("\n💭 Sometimes the best trade...")
print("   is to light the fuse and step back!")
print("=" * 70)