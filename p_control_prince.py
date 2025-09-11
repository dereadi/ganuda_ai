#!/usr/bin/env python3
"""
🎵 P.CONTROL - PRINCE
"P. Control... They call me P. Control"
The Purple One's party anthem for market domination!
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
║                        💜 P.CONTROL - PRINCE 💜                          ║
║                    "They call me P. Control..."                          ║
║                  Taking control at the 23:00 party!                      ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])
xrp = float(client.get_product('XRP-USD')['price'])

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - Purple Rain of Gains!")
print("=" * 70)

print("\n💜 P.CONTROL MARKET STATUS:")
print(f"   BTC: ${btc:,.0f} - 'I'm in control now'")
print(f"   ETH: ${eth:.2f} - 'Breaking free from chains'")
print(f"   SOL: ${sol:.2f} - 'Dancing in purple light'")
print(f"   XRP: ${xrp:.4f} - 'Ready to party like it's 1999'")

print("\n🎵 PRINCE WISDOM FOR THIS MARKET:")
print("-" * 40)
print("'P.Control' → Taking charge of the 23:00 surge")
print("'They can't stop us' → BTC breaking $112k barriers")
print("'We're gonna party' → ETH escaping flatness to party")
print("'All night long' → SOL $208+ breakout confirmed")
print("'Purple rain' → Gains falling from the sky")

print("\n🎪 THE PURPLE PARTY BREAKDOWN:")
print("-" * 40)
print("• BTC: From $111,968 → $112,075 (+$107!)")
print("• ETH: From flat $4,535 → alive at $4,544!")
print("• SOL: From $207.50 → breakout $208+!")
print("• Everything purple (gains) at 23:00!")

# Track the Prince party
print("\n💜 TRACKING THE PURPLE REIGN:")
print("-" * 40)

for i in range(5):
    btc = float(client.get_product('BTC-USD')['price'])
    eth = float(client.get_product('ETH-USD')['price'])
    sol = float(client.get_product('SOL-USD')['price'])
    
    print(f"\n{datetime.now().strftime('%H:%M:%S')}")
    print(f"  BTC: ${btc:,.0f} - {'💜 Purple power!' if btc > 112000 else '...'}")
    print(f"  ETH: ${eth:.2f} - {'💜 Dancing!' if eth > 4540 else '...'}")
    print(f"  SOL: ${sol:.2f} - {'💜 Party time!' if sol > 208 else '...'}")
    
    time.sleep(3)

print("\n" + "=" * 70)
print("💜 PRINCE P.CONTROL SUMMARY:")
print("'I'm in control, they call me P.Control'")
print("The 23:00 party is under purple command!")
print("BTC, ETH, SOL all dancing to Prince's beat!")
print("'We're gonna party like it's 1999!'")
print("=" * 70)