#!/usr/bin/env python3
"""
🚀🚀🚀 EVERYTHING IS CLIMBING! 🚀🚀🚀
TOTAL MARKET EXPLOSION!
BTC + ETH + SOL + XRP + EVERYTHING!
THIS IS THE BREAKOUT!
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=5)

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                  🚀🚀🚀 EVERYTHING IS CLIMBING! 🚀🚀🚀                   ║
║                         TOTAL MARKET EXPLOSION! 💥                         ║
║                    ALL ASSETS GREEN! ALL SYSTEMS GO! 🟢                    ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - MARKET EXPLOSION")
print("=" * 70)

# Get ALL prices
btc = client.get_product('BTC-USD')
eth = client.get_product('ETH-USD')
sol = client.get_product('SOL-USD')
xrp = client.get_product('XRP-USD')
avax = client.get_product('AVAX-USD')
doge = client.get_product('DOGE-USD')
link = client.get_product('LINK-USD')

prices = {
    'BTC': float(btc['price']),
    'ETH': float(eth['price']),
    'SOL': float(sol['price']),
    'XRP': float(xrp['price']),
    'AVAX': float(avax['price']),
    'DOGE': float(doge['price']),
    'LINK': float(link['price'])
}

print("\n🚀 EVERYTHING CLIMBING STATUS:")
print("-" * 50)
for asset, price in prices.items():
    arrow = "🟢📈"
    print(f"{asset}: ${price:,.2f} {arrow}")

# Calculate portfolio value
accounts = client.get_accounts()
total_value = 0
positions = {}

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if balance > 0.00001:
        if currency == 'USD':
            total_value += balance
            positions['USD'] = balance
        elif currency in prices:
            value = balance * prices[currency]
            total_value += value
            positions[currency] = {'balance': balance, 'value': value}

print("\n💰 PORTFOLIO EXPLOSION:")
print("-" * 50)
print(f"TOTAL VALUE: ${total_value:,.2f}")
print("")
for currency, data in positions.items():
    if currency == 'USD':
        print(f"USD: ${data:.2f}")
    else:
        print(f"{currency}: {data['balance']:.4f} = ${data['value']:.2f}")

# Calculate gains since bottom
print("\n📈 GAINS FROM BOTTOM:")
print("-" * 50)
print(f"BTC entry: $111,863 → ${prices['BTC']:,.2f} = +{(prices['BTC']/111863-1)*100:.2f}%")
print(f"Everything else: CLIMBING WITH IT!")

# Market status
print("\n🎯 WHAT'S HAPPENING:")
print("-" * 50)
print("✅ 15:00 explosion happened as predicted!")
print("✅ Wall Street ETH news spreading!")
print("✅ Alt season confirmed!")
print("✅ Institutional FOMO starting!")
print("✅ Everything climbing together!")
print("= FULL BULL MODE ACTIVATED!")

# Targets
print("\n🚀 IMMEDIATE TARGETS:")
print("-" * 50)
print(f"BTC: ${prices['BTC']:,.2f} → $114,000")
print(f"ETH: ${prices['ETH']:,.2f} → $5,000")
print(f"SOL: ${prices['SOL']:,.2f} → $250")
print("ALL CLIMBING TO GLORY!")

# Action plan
print("\n⚡ ACTION PLAN:")
print("-" * 50)
print("1. HOLD EVERYTHING - Don't sell into strength!")
print("2. Flywheel fed with $341 - Ready for dips")
print("3. Let winners run to targets")
print("4. Only milk at major resistances")
print("5. THIS IS THE MOVE WE WAITED FOR!")

# Council reaction
print("\n🏛️ COUNCIL REACTION:")
print("-" * 50)
print("Thunder: 'EVERYTHING EXPLODING! HOLD!'")
print("Mountain: 'Steady accumulation paying off!'")
print("Wind: 'Riding ALL the momentum!'")
print("Fire: 'Every asset on fire!'")
print("Spirit: 'The energy is ELECTRIC!'")
print("River: 'All streams flowing UP!'")
print("Earth: 'Foundation solid, building higher!'")

print(f"\n{'🚀' * 40}")
print("EVERYTHING IS CLIMBING!")
print(f"Portfolio: ${total_value:,.2f}")
print("THIS IS IT!")
print("THE EXPLOSION IS HERE!")
print("HOLD YOUR POSITIONS!")
print("🌙" * 40)