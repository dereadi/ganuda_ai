#!/usr/bin/env python3
"""
🤯 WOW! JUST WOW!
The 23:00 party delivered EVERYTHING!
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                           🤯 WOW! JUST WOW! 🤯                           ║
║                    The 23:00 Party Exceeded ALL Expectations!             ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

# Get current prices
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])
xrp = float(client.get_product('XRP-USD')['price'])

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - ABSOLUTE INSANITY!")
print("=" * 70)

print("\n🚀 THE INCREDIBLE JOURNEY (Last 15 minutes):")
print("-" * 40)
print("BTC: $111,968 → $112,107 (+$139!)")
print("ETH: $4,535 (FLAT) → $4,547 (ESCAPED!)")
print("SOL: $207.50 → $208.45 (BREAKOUT!)")
print("XRP: $2.978 → $2.985 (NEW SUPPORT!)")

print("\n🎉 WHAT JUST HAPPENED:")
print("-" * 40)
print("• 22:00 - Everything was flat, crawdads hungry")
print("• 22:05 - 0.000% squeeze detected!")
print("• 22:30 - Breakout begins, flywheel fed")
print("• 22:45 - Crawdads spent $1,450 in frenzy")
print("• 23:00 - THE PARTY STARTED!")
print("• 23:07 - BTC hits $112,075!")
print("• 23:09 - ETH breaks free from flatness!")
print("• 23:10 - SOL confirms $208+ breakout!")
print("• 23:11 - XRP establishes $2.98 support!")

print("\n💎 YOUR PORTFOLIO RIGHT NOW:")
print("-" * 40)

# Calculate portfolio
accounts = client.get_accounts()['accounts']
total_value = 0

for acc in accounts:
    bal = float(acc['available_balance']['value'])
    if bal > 0:
        currency = acc['currency']
        if currency == 'USD':
            total_value += bal
            print(f"USD: ${bal:.2f}")
        elif currency == 'BTC':
            value = bal * btc
            total_value += value
            print(f"BTC: {bal:.6f} = ${value:,.2f}")
        elif currency == 'ETH':
            value = bal * eth
            total_value += value
            print(f"ETH: {bal:.4f} = ${value:.2f}")
        elif currency == 'SOL':
            value = bal * sol
            total_value += value
            print(f"SOL: {bal:.2f} = ${value:,.2f}")

print(f"\n🔥 TOTAL PORTFOLIO: ${total_value:,.2f}")

print("\n🎵 THE SOUNDTRACK:")
print("-" * 40)
print("• 'Colorful' - The Verve Pipe (the beginning)")
print("• 'Fake Plastic Trees' - Radiohead (consolidation)")
print("• 'Zombie' - The Cranberries (the battle)")
print("• 'Birds of a Feather' - Billie Eilish (synchronization)")
print("• 'Pink Pony Club' - Chappell Roan (the party)")
print("• 'Into the Ocean' - Blue October (the dive)")
print("• 'Sleeping on the Blacktop' - Colter Wall (late night)")
print("• 'Bad Romance' - Lady Gaga (BTC/ETH sync)")
print("• 'P.Control' - Prince (23:00 takeover!)")

print("\n🤯 JUST... WOW!")
print("This is why we love crypto!")
print("This is why we stay up late!")
print("This is the 23:00 magic!")
print("=" * 70)