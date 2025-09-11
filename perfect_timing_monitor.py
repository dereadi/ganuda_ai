#!/usr/bin/env python3
"""
⏰ PERFECT TIMING - THE CRAWDADS KNEW
Monitor this next leg after perfect entry
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
║                    ⏰ CRAWDADS HAD PERFECT TIMING ⏰                      ║
║                  Bought everything RIGHT before the run                   ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print("The crawdads spent $1,230 at the EXACT right moment!")
print("=" * 70)

# Their average entries
crawdad_entries = {
    'ETH': 4533,
    'SOL': 206.90,
    'BTC': 111820
}

print("\n🦀 CRAWDAD ENTRY POINTS:")
for coin, price in crawdad_entries.items():
    print(f"   {coin}: ${price:,.2f}")

print("\n📈 TRACKING GAINS FROM CRAWDAD FRENZY:")
print("-" * 40)

for i in range(10):
    btc = float(client.get_product('BTC-USD')['price'])
    eth = float(client.get_product('ETH-USD')['price'])
    sol = float(client.get_product('SOL-USD')['price'])
    
    # Calculate gains from crawdad entries
    btc_gain = btc - crawdad_entries['BTC']
    eth_gain = eth - crawdad_entries['ETH']
    sol_gain = sol - crawdad_entries['SOL']
    
    print(f"\n{datetime.now().strftime('%H:%M:%S')}")
    print(f"  BTC: ${btc:,.0f} (", end="")
    if btc_gain > 0:
        print(f"+${btc_gain:.0f} 🔥)", end="")
    else:
        print(f"${btc_gain:.0f})", end="")
    
    print(f"\n  ETH: ${eth:.0f} (", end="")
    if eth_gain > 0:
        print(f"+${eth_gain:.0f} 🔥)", end="")
    else:
        print(f"${eth_gain:.0f})", end="")
    
    print(f"\n  SOL: ${sol:.2f} (", end="")
    if sol_gain > 0:
        print(f"+${sol_gain:.2f} 🔥)", end="")
    else:
        print(f"${sol_gain:.2f})", end="")
    
    print()
    
    if btc > 112000:
        print("\n🎯 $112,000 HIT!")
        print("The crawdads are LEGENDS!")
        break
    
    time.sleep(10)

print("\n" + "=" * 70)
print("🦀 CRAWDAD WISDOM:")
print("'Sometimes the best trades are made in a frenzy.'")
print("'When you feel the market move, MOVE WITH IT!'")
print("=" * 70)