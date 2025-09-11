#!/usr/bin/env python3
"""
🚨 EMERGENCY CASH HARVEST
Direct market sells for immediate liquidity
"""

import json
import time
from coinbase.rest import RESTClient

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=10)

print("🚨 EMERGENCY CASH HARVEST")
print("=" * 50)

# Get current balances
accounts = client.get_accounts()
balances = {}
usd_balance = 0

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    if balance > 0:
        balances[currency] = balance
        if currency == 'USD':
            usd_balance = balance

print(f"Current USD: ${usd_balance:.2f}")
print("\nAvailable to sell:")
for coin, amount in balances.items():
    if coin != 'USD':
        print(f"  {coin}: {amount:.6f}")

print("\n🔥 EXECUTING EMERGENCY SELLS:")
print("-" * 40)

# SELL 5 SOL
if balances.get('SOL', 0) > 5:
    try:
        print(f"Selling 5 SOL (have {balances['SOL']:.4f})...")
        
        # Use quote_size instead for guaranteed USD amount
        order = client.market_order_sell(
            client_order_id=f"emergency_sol_{int(time.time()*1000)}",
            product_id="SOL-USD",
            quote_size="1000"  # Sell $1000 worth of SOL
        )
        
        print(f"✅ SOL sell executed for ~$1000")
        time.sleep(2)
    except Exception as e:
        print(f"❌ SOL sell failed: {str(e)}")
        # Try with base_size
        try:
            order = client.market_order_sell(
                client_order_id=f"emergency_sol2_{int(time.time()*1000)}",
                product_id="SOL-USD",
                base_size="5"
            )
            print(f"✅ SOL sell retry succeeded")
        except Exception as e2:
            print(f"❌ SOL retry failed: {str(e2)}")

# SELL 0.05 ETH if needed
if usd_balance < 200 and balances.get('ETH', 0) > 0.05:
    try:
        print(f"Selling 0.05 ETH (have {balances['ETH']:.4f})...")
        
        order = client.market_order_sell(
            client_order_id=f"emergency_eth_{int(time.time()*1000)}",
            product_id="ETH-USD",
            base_size="0.05"
        )
        
        print(f"✅ ETH sell executed")
        time.sleep(2)
    except Exception as e:
        print(f"❌ ETH sell failed: {str(e)}")

# SELL 500 DOGE if needed
if usd_balance < 200 and balances.get('DOGE', 0) > 500:
    try:
        print(f"Selling 500 DOGE (have {balances['DOGE']:.0f})...")
        
        order = client.market_order_sell(
            client_order_id=f"emergency_doge_{int(time.time()*1000)}",
            product_id="DOGE-USD",
            base_size="500"
        )
        
        print(f"✅ DOGE sell executed")
        time.sleep(2)
    except Exception as e:
        print(f"❌ DOGE sell failed: {str(e)}")

# Check final balance
print("\n📊 CHECKING FINAL BALANCE...")
time.sleep(5)

accounts = client.get_accounts()
for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if currency == 'USD':
        print(f"\n💰 FINAL USD: ${balance:.2f}")
        print(f"Raised: ${balance - usd_balance:.2f}")
    elif currency in ['SOL', 'ETH', 'DOGE'] and balance > 0:
        print(f"{currency}: {balance:.4f} remaining")