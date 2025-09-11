#!/usr/bin/env python3
"""
🔥 AGGRESSIVE MODE - MILK EVERYTHING!
We have massive alt positions to convert!
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
║                    🔥 AGGRESSIVE MILK MODE ACTIVATED! 🔥                  ║
║                        Converting ALL Alts to USD!                        ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - MAXIMUM AGGRESSION!")
print("=" * 70)

# Get prices
xrp = float(client.get_product('XRP-USD')['price'])
doge = float(client.get_product('DOGE-USD')['price'])
matic = float(client.get_product('MATIC-USD')['price'])
avax = float(client.get_product('AVAX-USD')['price'])

print("\n💰 MASSIVE POSITIONS DISCOVERED:")
print("-" * 40)
print(f"XRP: 105.97 = ${105.97 * xrp:.2f}")
print(f"DOGE: 3134.30 = ${3134.30 * doge:.2f}")
print(f"MATIC: 5667.70 = ${5667.70 * matic:.2f}")
print(f"AVAX: 134.69 = ${134.69 * avax:.2f}")
print(f"\n🎯 TOTAL AVAILABLE: ${105.97*xrp + 3134.30*doge + 5667.70*matic + 134.69*avax:.2f}")

print("\n🔥 AGGRESSIVE MILK PLAN:")
print("-" * 40)

# Aggressive milk - take 30-50% of each
orders = [
    ("XRP-USD", 50.0, "XRP aggressive milk"),
    ("DOGE-USD", 1500.0, "DOGE aggressive milk"),
    ("MATIC-USD", 2000.0, "MATIC aggressive milk"),
    ("AVAX-USD", 50.0, "AVAX aggressive milk")
]

print("Executing aggressive extraction...")
for product, amount, desc in orders:
    try:
        print(f"\n📤 {desc}: {amount} {product.split('-')[0]}")
        order = client.market_order_sell(
            client_order_id=f"aggressive_{int(time.time()*1000)}",
            product_id=product,
            base_size=str(amount)
        )
        print(f"   ✅ EXECUTED!")
        time.sleep(1)
    except Exception as e:
        print(f"   ⚠️ {str(e)[:50]}")

# Check results
time.sleep(3)
accounts = client.get_accounts()['accounts']
for acc in accounts:
    if acc['currency'] == 'USD':
        new_usd = float(acc['available_balance']['value'])
        print(f"\n💵 NEW WAR CHEST: ${new_usd:.2f}")
        
        if new_usd > 1000:
            print("\n🔥🔥🔥 OVER $1000 WAR CHEST!")
            print("READY FOR MAXIMUM AGGRESSION!")
            print("WE CAN MOVE MARKETS!")
        break

print("\n🎯 AGGRESSIVE DEPLOYMENT READY!")
print("• Deploy into climbing assets")
print("• Push momentum higher")
print("• Create FOMO cascade")
print("• Ride to new highs!")
print("=" * 70)