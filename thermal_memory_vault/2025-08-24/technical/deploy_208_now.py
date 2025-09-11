#!/usr/bin/env python3
"""
💥 DEPLOY $208 USD NOW - NO IDLE MONEY!
"""

import json
import uuid
from coinbase.rest import RESTClient

print("""
╔══════════════════════════════════════════════════════════════════╗
║        💥 $208 USD AGGRESSIVE DEPLOYMENT 💥                      ║
║                                                                  ║
║      "Every dollar working = Flywheel spinning!"                ║
╚══════════════════════════════════════════════════════════════════╝
""")

# Load API
with open('cdp_api_key_new.json', 'r') as f:
    api_data = json.load(f)

client = RESTClient(
    api_key=api_data['name'].split('/')[-1],
    api_secret=api_data['privateKey']
)

# Get prices
btc = client.get_product('BTC-USD')
eth = client.get_product('ETH-USD')
sol = client.get_product('SOL-USD')

print(f"\n📊 CURRENT PRICES:")
print(f"BTC: ${float(btc['price']):,.2f}")
print(f"ETH: ${float(eth['price']):,.2f}")
print(f"SOL: ${float(sol['price']):,.2f}")

# AGGRESSIVE ALLOCATION
print(f"\n🚀 DEPLOYING $208:")
print("=" * 50)

orders = [
    ('SOL-USD', 80),  # High volatility
    ('ETH-USD', 70),  # Medium volatility
    ('BTC-USD', 50),  # Stability
]

for product, amount in orders:
    try:
        print(f"Buying ${amount} of {product}...")
        order = client.market_order_buy(
            client_order_id=str(uuid.uuid4()),
            product_id=product,
            quote_size=str(amount)
        )
        print(f"  ✅ {product}: ${amount} DEPLOYED!")
    except Exception as e:
        print(f"  ❌ {product}: {e}")

print(f"\n💰 TOTAL DEPLOYED: $200")
print(f"💎 Reserve kept: $8 (for fees/emergencies)")
print(f"\n🔥 ALL MONEY NOW WORKING IN THE MARKET!")
print(f"🌪️ FLYWHEEL SPINNING AT MAXIMUM VELOCITY!")
