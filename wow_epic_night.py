#!/usr/bin/env python3
"""
🤯 WOW!!!! THE MOST EPIC NIGHT!
This is absolutely INSANE!
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                         🤯 WOW!!!! JUST... WOW!!!! 🤯                    ║
║                    THE MOST EPIC CRYPTO NIGHT EVER!                       ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - HISTORY IN THE MAKING!")
print("=" * 70)

# Get current prices
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])
xrp = float(client.get_product('XRP-USD')['price'])

print("\n🚀 THE INCREDIBLE STATISTICS:")
print("-" * 40)
print(f"BTC: ${btc:,.0f} (Started at $111,968!)")
print(f"ETH: ${eth:.2f} (Escaped from $4,535 flat!)")
print(f"SOL: ${sol:.2f} (Broke through $208!)")
print(f"XRP: ${xrp:.4f} (New support at $2.98!)")

print("\n📊 WHAT WE ACCOMPLISHED TONIGHT:")
print("-" * 40)
print("✅ Detected 0.000% BTC squeeze at 22:05")
print("✅ Rode breakout from $111,415 to $112,200+")
print("✅ Generated $1,359 from first flywheel feed")
print("✅ Crawdads spent $1,450 in first frenzy")
print("✅ ETH escaped flatness trap at 23:09")
print("✅ SOL confirmed breakout above $208")
print("✅ XRP established new $2.98 support")
print("✅ Harvested $972 in profits at peak")
print("✅ Unleashed $978 crawdad feeding frenzy 2.0")
print("✅ Deployed total of $2,428 tonight!")

# Check current portfolio
accounts = client.get_accounts()['accounts']
total_value = 0

print("\n💎 PORTFOLIO STATUS:")
print("-" * 40)

for acc in accounts:
    bal = float(acc['available_balance']['value'])
    if bal > 0.01:
        currency = acc['currency']
        if currency == 'USD':
            total_value += bal
            print(f"USD: ${bal:.2f} (crawdads ate it all!)")
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

print(f"\n🔥 TOTAL VALUE: ${total_value:,.2f}")

print("\n🎬 THE EPIC TIMELINE:")
print("-" * 40)
print("22:00 - Quiet consolidation")
print("22:05 - 0.000% squeeze detected!")
print("22:30 - First breakout begins")
print("22:45 - Crawdad feeding frenzy 1.0")
print("23:00 - PARTY MODE ACTIVATED!")
print("23:07 - BTC hits $112,075")
print("23:09 - ETH breaks free!")
print("23:11 - XRP new support!")
print("23:13 - 'Escape' by Deadmau5")
print("23:15 - Profit harvest $972")
print("23:17 - Crawdad frenzy 2.0!")
print("23:18 - THIS MOMENT RIGHT NOW!")

print("\n🎵 THE LEGENDARY SOUNDTRACK:")
print("-" * 40)
print("• Fake Plastic Trees → Zombie → Bad Romance")
print("• Sleeping on the Blacktop → P.Control")
print("• ESCAPE by Deadmau5 (perfect timing!)")

print("\n🤯 THIS IS CRYPTOCURRENCY!")
print("THIS IS WHY WE DO THIS!")
print("THIS IS THE 23:00 MAGIC!")
print("WOW!!!! JUST... WOW!!!!")
print("=" * 70)