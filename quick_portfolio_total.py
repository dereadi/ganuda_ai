#!/usr/bin/env python3
"""
💰 QUICK TOTAL VALUE CHECK
"""

import json
from coinbase.rest import RESTClient

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("💰 TOTAL PORTFOLIO VALUE")
print("=" * 70)

# Get prices
btc = client.get_product('BTC-USD')
eth = client.get_product('ETH-USD')
btc_price = float(btc['price'])
eth_price = float(eth['price'])

# Get main balances
accounts = client.get_accounts()
total = 0

print("\n📊 HOLDINGS:")
for acc in accounts['accounts']:
    currency = acc['currency']
    balance = float(acc['available_balance']['value'])
    
    if balance > 0.00001:
        if currency == 'BTC':
            value = balance * btc_price
            print(f"BTC: {balance:.8f} = ${value:,.2f}")
            total += value
        elif currency == 'ETH':
            value = balance * eth_price
            print(f"ETH: {balance:.8f} = ${value:,.2f}")
            total += value
        elif currency in ['USD', 'USDC']:
            print(f"{currency}: ${balance:.2f}")
            total += balance

# Add locked BTC in sell orders
locked_btc = 0.00276674 + 0.00368899  # Our nuclear strikes
locked_value = locked_btc * btc_price
print(f"\n🔒 In sell orders: {locked_btc:.8f} BTC = ${locked_value:,.2f}")
total += locked_value

print("\n" + "=" * 70)
print(f"💎 TOTAL VALUE: ${total:,.2f}")
print("=" * 70)

# Quick projections
print("\n🚀 MOON TARGETS:")
print(f"To $10k: need {10000/total:.1f}x")
print(f"To $100k: need {100000/total:.1f}x")
print(f"To $500k: need {500000/total:.1f}x")
print(f"To $1M: need {1000000/total:.1f}x")