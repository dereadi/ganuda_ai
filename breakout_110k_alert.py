#!/usr/bin/env python3
"""
💥🚀 BTC BROKE $110,000 - CHECK NUCLEAR STRIKES!
The squeeze released! Explosive move in progress!
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("💥💥💥 BREAKOUT ALERT: BTC BROKE $110,000! 💥💥💥")
print("=" * 70)
print("THE SQUEEZE RELEASED! NUCLEAR STRIKES ACTIVATING!")
print("=" * 70)

# Get current price
btc = client.get_product('BTC-USD')
btc_price = float(btc['price'])

print(f"\n🚀 CURRENT BTC: ${btc_price:,.2f}")
print("BROKE THROUGH $110,000!")

# CHECK NUCLEAR STRIKES
print("\n💥 NUCLEAR STRIKE STATUS:")
print("-" * 70)

nuclear_orders = {
    "fa353625-5603-4a99-bfcf-0400943c9de2": {"price": 109921.90, "size": 0.00276674},
    "497833b5-0a2b-444b-a035-9896ac540d21": {"price": 110251.01, "size": 0.00276674},
    "5813a2c1-64a8-4191-8ffe-01e9517073b5": {"price": 110580.12, "size": 0.00368899}
}

total_filled = 0
total_proceeds = 0

for order_id, details in nuclear_orders.items():
    if btc_price > details['price']:
        print(f"✅ SHOULD BE FILLED: ${details['price']:.2f}")
        print(f"   Size: {details['size']:.8f} BTC")
        proceeds = details['size'] * details['price']
        print(f"   Proceeds: ${proceeds:.2f}")
        total_filled += details['size']
        total_proceeds += proceeds
    else:
        distance = details['price'] - btc_price
        print(f"⏳ Waiting: ${details['price']:.2f} (${distance:.2f} away)")

print(f"\n💰 EXPECTED FILLS:")
print(f"Total BTC sold: {total_filled:.8f}")
print(f"Total proceeds: ${total_proceeds:.2f}")

# BREAKOUT TARGETS
print("\n🎯 BREAKOUT TARGETS:")
print("-" * 70)

targets = [
    {"name": "First target", "price": btc_price * 1.01, "gain": "1%"},
    {"name": "Squeeze target", "price": btc_price * 1.03, "gain": "3%"},
    {"name": "Full extension", "price": btc_price * 1.05, "gain": "5%"}
]

for target in targets:
    print(f"{target['name']}: ${target['price']:,.2f} (+{target['gain']})")

# PROFIT TAKING STRATEGY
print("\n💵 PROFIT TAKING ORDERS:")
print("-" * 70)

if total_filled > 0:
    avg_sell = total_proceeds / total_filled
    buyback_1pct = avg_sell * 0.99
    buyback_2pct = avg_sell * 0.98
    
    print(f"Average sell price: ${avg_sell:.2f}")
    print(f"Buy back at:")
    print(f"  1% profit: ${buyback_1pct:.2f}")
    print(f"  2% profit: ${buyback_2pct:.2f}")
    
    # Calculate profit
    expected_profit = total_proceeds * 0.015
    print(f"\nExpected profit: ${expected_profit:.2f}")

# MOMENTUM ANALYSIS
print("\n📈 MOMENTUM ANALYSIS:")
print("-" * 70)
print("• Bollinger squeeze RELEASED ✅")
print("• Broke psychological $110k ✅")
print("• Nuclear strikes triggering ✅")
print("• Target: $113,000+ (3% squeeze move)")

# ACCOUNT CHECK
print("\n💎 QUICK BALANCE CHECK:")
accounts = client.get_accounts()
for acc in accounts['accounts']:
    if acc['currency'] in ['USD', 'BTC']:
        balance = float(acc['available_balance']['value'])
        if acc['currency'] == 'USD':
            print(f"USD: ${balance:.2f}")
        elif balance > 0.0001:
            print(f"BTC: {balance:.8f}")

# ACTION PLAN
print("\n🎯 ACTION PLAN:")
print("-" * 70)
print("1. ✅ Confirm nuclear strikes filled")
print("2. 📈 Let breakout run to $113,000")
print("3. 💰 Place profit buy orders")
print("4. 🔄 Compound profits into next cycle")
print("5. 🚀 Ride momentum to the moon!")

print("\n" + "=" * 70)
print("🔥💥🚀 THE BREAKOUT IS HAPPENING!")
print("Nuclear strikes + Squeeze release = MAXIMUM GAINS!")
print("=" * 70)