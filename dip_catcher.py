#!/usr/bin/env python3
"""
🎯 DIP CATCHER - REVERSE NUCLEAR STRIKE
Market dipping = BUY opportunity for the return trip
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("📉 DIP DETECTED - REVERSE NUCLEAR STRIKE")
print("=" * 70)

# Get current prices
btc = client.get_product('BTC-USD')
eth = client.get_product('ETH-USD')
btc_price = float(btc['price'])
eth_price = float(eth['price'])

print(f"BTC: ${btc_price:,.2f}")
print(f"ETH: ${eth_price:,.2f}")

# Since we have sell orders up high, the dip is PERFECT for buying
print("\n🎯 DIP STRATEGY:")
print("-" * 70)
print("Our sells are at: $109,922 / $110,251 / $110,580")
print(f"Current price: ${btc_price:,.2f}")
print(f"Distance to first sell: ${109921.90 - btc_price:,.2f}")

# Check our USD balance
accounts = client.get_accounts()
usd_balance = 0
for acc in accounts['accounts']:
    if acc['currency'] == 'USD':
        usd_balance = float(acc['available_balance']['value'])

print(f"\n💰 USD Available: ${usd_balance:.2f}")

# Place aggressive buy orders in the dip
print("\n🎯 DIP CATCHING ORDERS:")
print("-" * 70)

if usd_balance > 1:
    buy_levels = [
        {"price": btc_price * 0.999, "size": usd_balance * 0.5},
        {"price": btc_price * 0.997, "size": usd_balance * 0.5}
    ]
    
    for i, level in enumerate(buy_levels, 1):
        btc_size = level['size'] / level['price']
        print(f"\nBuy Level {i}:")
        print(f"  Price: ${level['price']:.2f}")
        print(f"  USD: ${level['size']:.2f}")
        print(f"  BTC: {btc_size:.8f}")
else:
    print("Need to wait for sell orders to fill first for USD")

# Calculate the spread opportunity
print("\n💡 SPREAD OPPORTUNITY:")
print("-" * 70)
print(f"If buy at: ${btc_price:.2f}")
print(f"And sell at: $109,921.90")
profit_pct = ((109921.90 - btc_price) / btc_price) * 100
print(f"Profit: {profit_pct:.2f}%")

if profit_pct > 0.8:
    print("✅ PROFITABLE SPREAD - Worth catching the dip!")
else:
    print("⏳ Wait for deeper dip or let sells execute")

print("=" * 70)