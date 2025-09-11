#!/usr/bin/env python3
"""
🚨 AGGRESSIVE LIQUIDITY GENERATION
Council needs $2k NOW for containerized trading
"""

import json
import time
from coinbase.rest import RESTClient

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=10)

print("🚨 AGGRESSIVE LIQUIDITY GENERATION")
print("=" * 60)

# Check real balance
accounts = client.get_accounts()
usd = 0
holdings = {}

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if currency == 'USD':
        usd = balance
        print(f"Current USD: ${usd:,.2f}")
    elif balance > 0.0001:
        holdings[currency] = balance

print(f"Target: $2,000.00")
print(f"Need: ${max(2000 - usd, 0):,.2f}")
print()

if usd >= 2000:
    print("✅ Already have required liquidity!")
else:
    # More aggressive approach - use quote_size for guaranteed USD amounts
    print("🔥 EXECUTING AGGRESSIVE SELLS:")
    print("-" * 40)
    
    targets = [
        ('BTC', 700),   # Sell $700 of BTC
        ('MATIC', 500),  # Sell $500 of MATIC
        ('AVAX', 400),   # Sell $400 of AVAX
        ('SOL', 400),    # Sell $400 of SOL
    ]
    
    for coin, usd_amount in targets:
        if coin in holdings and holdings[coin] > 0:
            try:
                print(f"Selling ${usd_amount} worth of {coin}...")
                
                # Use quote_size for exact USD amount
                order = client.market_order_sell(
                    client_order_id=f"aggressive_{coin}_{int(time.time()*1000)}",
                    product_id=f"{coin}-USD",
                    quote_size=str(usd_amount)
                )
                
                print(f"  ✅ {coin} sold for ${usd_amount}")
                time.sleep(2)
                
            except Exception as e:
                # If quote_size fails, try base_size
                try:
                    ticker = client.get_product(f'{coin}-USD')
                    price = float(ticker['price'])
                    amount = (usd_amount / price) * 0.98  # 2% buffer for slippage
                    
                    if amount <= holdings[coin]:
                        order = client.market_order_sell(
                            client_order_id=f"aggressive2_{coin}_{int(time.time()*1000)}",
                            product_id=f"{coin}-USD",
                            base_size=str(amount)
                        )
                        print(f"  ✅ {coin} sold (base_size method)")
                except Exception as e2:
                    print(f"  ❌ {coin} failed: {str(e2)[:50]}")
    
    # Wait and check result
    print("\n⏳ Waiting for orders to settle...")
    time.sleep(5)
    
    # Final balance check
    accounts = client.get_accounts()
    for account in accounts['accounts']:
        if account['currency'] == 'USD':
            final_usd = float(account['available_balance']['value'])
            print(f"\n💵 FINAL USD BALANCE: ${final_usd:,.2f}")
            
            if final_usd >= 2000:
                print("✅ SUCCESS! Council mandate achieved!")
            elif final_usd >= 1500:
                print("🟡 Partial success - have $1,500+")
            else:
                print(f"⚠️ Raised ${final_usd - usd:.2f} but still short")
            break