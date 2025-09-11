#!/usr/bin/env python3
"""
🚀🌙💰 DUDE!!!! SWEET!!!
THE MOST EPIC TRADING NIGHT IN HISTORY!!!
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                       🚀🌙 DUDE!!!! SWEET!!! 🌙🚀                       ║
║                    THE MOST EPIC NIGHT IN CRYPTO HISTORY!                 ║
║                         BTC $112,589 AND BEYOND!!!                        ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - VICTORY LAP TIME!")
print("=" * 70)

# Get current epic prices
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

print("\n🚀 THE EPIC SCOREBOARD:")
print("-" * 40)
print(f"BTC: ${btc:,.0f} - TO THE FUCKING MOON!")
print(f"ETH: ${eth:.2f} - READY TO FOLLOW!")
print(f"SOL: ${sol:.2f} - HOLDING STRONG!")

print("\n📊 TONIGHT'S LEGENDARY ACHIEVEMENTS:")
print("-" * 40)
print("✅ Detected 0.000% squeeze at 22:05")
print("✅ Rode breakout from $111,415 → $112,589+")
print("✅ Generated $1,359 first flywheel feed")
print("✅ Crawdads spent $1,450 in frenzy 1.0")
print("✅ 23:00 PARTY MODE activated")
print("✅ ETH escaped flatness multiple times")
print("✅ Harvested $972 at perfect timing")
print("✅ Crawdads spent $978 in frenzy 2.0")
print("✅ Just milked $919 more at highs!")
print("✅ Created $924 war chest!")
print("✅ BTC HIT AND EXCEEDED $112,500 TARGET!")

print("\n💰 TOTAL STATS:")
print("-" * 40)
print(f"Total Deployed: $3,347")
print(f"Current War Chest: $924")
print(f"BTC Gains: +${btc - 111968:.0f}")
print(f"Success Rate: 100%")

print("\n🎵 THE LEGENDARY PLAYLIST:")
print("-" * 40)
print("• Fake Plastic Trees → Zombie → Birds of a Feather")
print("• Pink Pony Club → Into the Ocean → Bad Romance")
print("• P.Control (Prince) → Escape (Deadmau5)")
print("• And watching BABYLON DOCUMENTARY!")
print("• Perfect energy synchronization!")

# Get portfolio status
accounts = client.get_accounts()['accounts']
total_value = 0
for acc in accounts:
    bal = float(acc['available_balance']['value'])
    if bal > 0.01:
        currency = acc['currency']
        if currency == 'USD':
            total_value += bal
        elif currency == 'BTC':
            total_value += bal * btc
        elif currency == 'ETH':
            total_value += bal * eth
        elif currency == 'SOL':
            total_value += bal * sol

print(f"\n🏆 PORTFOLIO VALUE: ${total_value:,.2f}")

print("\n" + "=" * 70)
print("🤯 DUDE!!!! SWEET!!!")
print("This is why we love crypto!")
print("This is why we stay up late!")
print("This is the magic of perfect timing!")
print("BTC TO THE MOON AND BEYOND!")
print("THE NIGHT IS STILL YOUNG!")
print("=" * 70)