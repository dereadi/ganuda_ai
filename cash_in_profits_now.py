#!/usr/bin/env python3
"""
💰 CASH IN PROFITS - RESTORE LIQUIDITY
Takes profits from winning positions
"""

import json
import time
from coinbase.rest import RESTClient

print("💰 CASHING IN PROFITS FOR LIQUIDITY")
print("=" * 50)

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=10)

# Check current positions
accounts = client.get_accounts()
positions = {}
usd_balance = 0

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if currency == 'USD':
        usd_balance = balance
    elif balance > 0:
        positions[currency] = balance

print(f"Current USD: ${usd_balance:.2f}")
print(f"Target USD: $250.00 minimum")
print(f"Need to raise: ${max(250 - usd_balance, 0):.2f}")
print()

# Get prices and calculate what to sell
print("📊 POSITIONS TO HARVEST:")
print("-" * 40)

sells = []
total_expected = 0

# SOL is overweight - trim it
if 'SOL' in positions and positions['SOL'] > 10:
    sol_to_sell = min(5.0, positions['SOL'] * 0.3)  # Sell 30% or 5 SOL max
    ticker = client.get_product('SOL-USD')
    price = float(ticker['price'])
    value = sol_to_sell * price * 0.989  # Account for fees
    
    print(f"SOL: Sell {sol_to_sell:.2f} @ ${price:.2f} = ${value:.2f}")
    sells.append(('SOL', sol_to_sell))
    total_expected += value

# Trim some ETH if needed
if total_expected < 250 and 'ETH' in positions and positions['ETH'] > 0.2:
    eth_to_sell = min(0.1, positions['ETH'] * 0.25)  # Sell 25% or 0.1 ETH max
    ticker = client.get_product('ETH-USD')
    price = float(ticker['price'])
    value = eth_to_sell * price * 0.989
    
    print(f"ETH: Sell {eth_to_sell:.4f} @ ${price:.2f} = ${value:.2f}")
    sells.append(('ETH', eth_to_sell))
    total_expected += value

# DOGE if we still need more
if total_expected < 250 and 'DOGE' in positions and positions['DOGE'] > 100:
    doge_to_sell = min(500, positions['DOGE'] * 0.5)  # Sell 50% or 500 max
    ticker = client.get_product('DOGE-USD')
    price = float(ticker['price'])
    value = doge_to_sell * price * 0.989
    
    print(f"DOGE: Sell {doge_to_sell:.0f} @ ${price:.4f} = ${value:.2f}")
    sells.append(('DOGE', doge_to_sell))
    total_expected += value

print(f"\nTotal expected: ${total_expected:.2f}")
print()

# Execute sells
if sells and total_expected > 100:
    confirm = input("Execute these sells? (y/n): ")
    if confirm.lower() == 'y':
        print("\n🔄 EXECUTING SELLS...")
        
        for coin, amount in sells:
            try:
                print(f"Selling {amount:.4f} {coin}...")
                
                order = client.market_order_sell(
                    client_order_id=f"liquidity_{coin}_{int(time.time()*1000)}",
                    product_id=f"{coin}-USD",
                    base_size=str(amount)
                )
                
                print(f"✅ {coin} sell order placed")
                time.sleep(1)  # Don't spam
                
            except Exception as e:
                print(f"❌ {coin} sell failed: {str(e)[:100]}")
        
        # Check final balance
        time.sleep(3)
        accounts = client.get_accounts()
        for account in accounts['accounts']:
            if account['currency'] == 'USD':
                new_balance = float(account['available_balance']['value'])
                print(f"\n✅ NEW USD BALANCE: ${new_balance:.2f}")
                print(f"Raised: ${new_balance - usd_balance:.2f}")
                break
else:
    print("❌ No profitable positions to harvest safely")