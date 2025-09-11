#!/usr/bin/env python3
"""
🎯 FEED THE WHEEL AT NEW HIGHS!
Harvest profits from BTC $113k, ETH $4,577, SOL $212
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
║                    🎯 FEEDING THE WHEEL AT HIGHS! 🎯                      ║
║                   Extracting $1,465 in Peak Profits                       ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - PROFIT HARVEST TIME!")
print("=" * 70)

# Get current prices at these highs
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

print(f"\n🚀 PEAK PRICES:")
print(f"  BTC: ${btc:,.0f}")
print(f"  ETH: ${eth:.2f}")
print(f"  SOL: ${sol:.2f}")

print("\n💰 PROFIT EXTRACTION PLAN:")
print("-" * 40)
print("• BTC: 0.0041 units = ~$463")
print("• ETH: 0.0362 units = ~$166")
print("• SOL: 3.95 units = ~$837")
print(f"• TOTAL TARGET: $1,465")

print("\n🔥 EXECUTING HARVEST:")
print("-" * 40)

total_generated = 0
orders = [
    ("BTC-USD", 0.0041, "BTC peak harvest"),
    ("ETH-USD", 0.0362, "ETH peak harvest"),
    ("SOL-USD", 3.95, "SOL peak harvest")
]

for product, amount, desc in orders:
    try:
        print(f"\n📤 {desc}: {amount} {product.split('-')[0]}")
        
        # Get pre-sell balance
        accounts_before = client.get_accounts()['accounts']
        usd_before = 0
        for acc in accounts_before:
            if acc['currency'] == 'USD':
                usd_before = float(acc['available_balance']['value'])
                break
        
        # Execute sell
        order = client.market_order_sell(
            client_order_id=f"harvest_{int(time.time()*1000)}",
            product_id=product,
            base_size=str(amount)
        )
        print(f"   ✅ Order placed!")
        
        # Wait and check USD generated
        time.sleep(2)
        accounts_after = client.get_accounts()['accounts']
        usd_after = 0
        for acc in accounts_after:
            if acc['currency'] == 'USD':
                usd_after = float(acc['available_balance']['value'])
                break
        
        generated = usd_after - usd_before
        total_generated += generated
        print(f"   💵 Generated: ${generated:.2f}")
        
    except Exception as e:
        print(f"   ⚠️ {str(e)[:50]}")

print(f"\n💰 TOTAL HARVESTED: ${total_generated:.2f}")

# Check final USD balance
time.sleep(2)
accounts = client.get_accounts()['accounts']
for acc in accounts:
    if acc['currency'] == 'USD':
        final_usd = float(acc['available_balance']['value'])
        print(f"\n🔥 FLYWHEEL FUEL READY: ${final_usd:.2f}")
        
        if final_usd > 1400:
            print("\n🚀 MASSIVE WAR CHEST READY!")
            print("• Deploy into momentum")
            print("• Feed the crawdads")
            print("• Push higher!")
        break

print("\n" + "=" * 70)
print("🎯 WHEEL FED SUCCESSFULLY!")
print("Fresh capital ready for deployment!")
print("The flywheel keeps spinning!")
print("=" * 70)