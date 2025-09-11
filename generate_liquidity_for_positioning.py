#!/usr/bin/env python3
"""
Generate liquidity so specialists can position
"""

import json
import time
from coinbase.rest import RESTClient

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("💰 GENERATING LIQUIDITY FOR POSITIONING")
print("=" * 50)

accounts = client.get_accounts()
positions = {}
usd = 0

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if currency == 'USD':
        usd = balance
    elif balance > 0:
        positions[currency] = balance

print(f"Current USD: ${usd:.2f}")
print(f"Target: $500+ for DEPLOY MODE")
print()

# Sell some positions to raise $500
targets = [
    ('SOL', 2.0, "Trimming heavy position"),
    ('AVAX', 20.0, "Taking some AVAX profits"),
    ('MATIC', 1500.0, "Reducing MATIC"),
    ('DOGE', 1000.0, "Liquidating some DOGE")
]

print("🔄 EXECUTING LIQUIDITY TRADES:")
print("-" * 40)

for coin, amount, reason in targets:
    if coin in positions and positions[coin] >= amount:
        try:
            print(f"Selling {amount} {coin}: {reason}")
            
            order = client.market_order_sell(
                client_order_id=f"liquidity_{coin}_{int(time.time()*1000)}",
                product_id=f"{coin}-USD",
                base_size=str(amount)
            )
            
            print(f"  ✅ {coin} sold")
            time.sleep(2)
            
        except Exception as e:
            print(f"  ❌ {coin} failed: {str(e)[:50]}")

# Check new balance
time.sleep(3)
accounts = client.get_accounts()
for account in accounts['accounts']:
    if account['currency'] == 'USD':
        new_usd = float(account['available_balance']['value'])
        print()
        print(f"💵 NEW USD BALANCE: ${new_usd:.2f}")
        
        if new_usd > 500:
            print("🟢 DEPLOY MODE ACTIVATED!")
            print("Specialists can now position aggressively")
        elif new_usd > 250:
            print("🟡 BALANCED MODE - Normal operations")
        else:
            print("🔴 Still in RETRIEVE MODE")
        break