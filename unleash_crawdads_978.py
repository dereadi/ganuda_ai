#!/usr/bin/env python3
"""
🦀🔥 UNLEASHING THE CRAWDADS WITH $978!
Time to feed during the ESCAPE momentum!
"""

import json
import time
from coinbase.rest import RESTClient
from datetime import datetime
import random

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                   🦀 CRAWDAD FEEDING FRENZY 2.0! 🦀                      ║
║                       $978 WAR CHEST UNLEASHED!                           ║
║                    During the Great ESCAPE of 23:15!                      ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

# The crawdad swarm
crawdads = [
    {"name": "Thunder", "style": "aggressive", "allocation": 0.20},
    {"name": "River", "style": "flowing", "allocation": 0.15},
    {"name": "Mountain", "style": "steady", "allocation": 0.15},
    {"name": "Fire", "style": "explosive", "allocation": 0.15},
    {"name": "Wind", "style": "swift", "allocation": 0.15},
    {"name": "Earth", "style": "grounded", "allocation": 0.10},
    {"name": "Spirit", "style": "intuitive", "allocation": 0.10}
]

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - RELEASING THE SWARM!")
print(f"War Chest: $978.90")
print("=" * 70)

# Get current prices
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])
xrp = float(client.get_product('XRP-USD')['price'])

print(f"\n🎯 TARGET PRICES:")
print(f"  BTC: ${btc:,.0f}")
print(f"  ETH: ${eth:.2f}")
print(f"  SOL: ${sol:.2f}")
print(f"  XRP: ${xrp:.4f}")

# Split the war chest
total_usd = 978.90
print(f"\n🦀 CRAWDAD ATTACK PLAN:")
print("-" * 40)

for crawdad in crawdads:
    crawdad_budget = total_usd * crawdad['allocation']
    print(f"🦀 {crawdad['name']}: ${crawdad_budget:.2f} ({crawdad['style']} style)")

print("\n🔥 FEEDING FRENZY BEGINNING!")
print("-" * 40)

# Execute the frenzy
total_spent = 0
orders_placed = 0

for crawdad in crawdads:
    budget = total_usd * crawdad['allocation']
    
    # Each crawdad chooses targets based on style
    if crawdad['style'] == 'aggressive':
        targets = [("BTC-USD", budget * 0.6), ("ETH-USD", budget * 0.4)]
    elif crawdad['style'] == 'explosive':
        targets = [("SOL-USD", budget * 0.7), ("BTC-USD", budget * 0.3)]
    elif crawdad['style'] == 'flowing':
        targets = [("ETH-USD", budget * 0.5), ("SOL-USD", budget * 0.5)]
    elif crawdad['style'] == 'swift':
        targets = [("XRP-USD", budget * 0.6), ("SOL-USD", budget * 0.4)]
    elif crawdad['style'] == 'steady':
        targets = [("BTC-USD", budget * 0.8), ("ETH-USD", budget * 0.2)]
    elif crawdad['style'] == 'grounded':
        targets = [("ETH-USD", budget * 0.7), ("BTC-USD", budget * 0.3)]
    else:  # intuitive
        targets = [("SOL-USD", budget * 0.4), ("XRP-USD", budget * 0.3), ("ETH-USD", budget * 0.3)]
    
    print(f"\n🦀 {crawdad['name']} ATTACKS!")
    
    for product, amount in targets:
        if amount > 5:  # Min order size
            try:
                print(f"   → ${amount:.2f} into {product.split('-')[0]}")
                order = client.market_order_buy(
                    client_order_id=f"crawdad_{crawdad['name']}_{int(time.time()*1000)}",
                    product_id=product,
                    quote_size=str(round(amount, 2))
                )
                orders_placed += 1
                total_spent += amount
                time.sleep(0.5)
            except Exception as e:
                print(f"   ⚠️ {crawdad['name']} stumbled: {str(e)[:50]}")

print("\n" + "=" * 70)
print(f"🦀 FEEDING FRENZY COMPLETE!")
print(f"  Orders placed: {orders_placed}")
print(f"  Total deployed: ${total_spent:.2f}")

# Check remaining balance
time.sleep(3)
accounts = client.get_accounts()['accounts']
for acc in accounts:
    if acc['currency'] == 'USD':
        remaining = float(acc['available_balance']['value'])
        print(f"  Remaining USD: ${remaining:.2f}")
        break

print("\n💭 THE CRAWDADS FEAST DURING THE ESCAPE!")
print("Perfect timing with BTC $112k+, ETH $4,551+, SOL $208+!")
print("The flywheel is spinning at maximum velocity!")
print("=" * 70)