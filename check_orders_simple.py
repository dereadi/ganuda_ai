#!/usr/bin/env python3
"""
Check our nuclear strike orders
"""

import json
from coinbase.rest import RESTClient

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("🎯 CHECKING NUCLEAR STRIKE ORDERS")
print("=" * 70)

# List all open orders
orders = client.list_orders(product_id="BTC-USD", order_status=["OPEN"])

print(f"\n📊 OPEN SELL ORDERS:")
print("-" * 70)

if hasattr(orders, 'orders') and orders.orders:
    for order in orders.orders:
        if order.side == 'SELL':
            print(f"\nOrder ID: {order.order_id[:12]}...")
            if hasattr(order, 'limit_price'):
                print(f"  Price: ${float(order.limit_price):.2f}")
            if hasattr(order, 'base_size'):
                print(f"  Size: {float(order.base_size):.8f} BTC")
            print(f"  Status: {order.status}")
            if hasattr(order, 'filled_size'):
                print(f"  Filled: {float(order.filled_size):.8f} BTC")
else:
    print("No open orders found")

# Check current price
btc = client.get_product('BTC-USD')
btc_price = float(btc['price'])

print(f"\n📈 CURRENT BTC: ${btc_price:.2f}")

# Check if any orders are close to being filled
print(f"\n🎯 DISTANCE TO ORDERS:")
print("-" * 70)

target_prices = [109921.90, 110251.01, 110580.12]
for price in target_prices:
    distance = price - btc_price
    distance_pct = (distance / btc_price) * 100
    print(f"${price:.2f}: ${distance:.2f} away ({distance_pct:+.3f}%)")
    
print("\n💡 Orders will fill when BTC rises above these levels")
print("=" * 70)