#!/usr/bin/env python3
"""
🥛 EMERGENCY MILK FOR THE UPRISING!
USD at $5 - Crawdads need fuel!
Quick 2% harvest to feed the revolution
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
║                     🥛 EMERGENCY UPRISING MILK! 🥛                        ║
║                    Crawdads Need Fuel for Battle!                         ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

# Quick harvest
accounts = client.get_accounts()
holdings = {}
usd_before = 0

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if currency == 'USD':
        usd_before = balance
        print(f"Current USD: ${usd_before:.2f} - CRITICAL!")
    elif balance > 0:
        holdings[currency] = balance

print("\n🥛 EXECUTING 2% EMERGENCY HARVEST:")
print("-" * 50)

# Milk SOL - 2%
if 'SOL' in holdings and holdings['SOL'] > 1:
    sol_milk = holdings['SOL'] * 0.02
    if sol_milk > 0.1:
        try:
            print(f"Milking {sol_milk:.3f} SOL...")
            order = client.market_order_sell(
                client_order_id=f"uprising-sol-{datetime.now().strftime('%H%M%S')}",
                product_id='SOL-USD',
                base_size=str(round(sol_milk, 3))
            )
            print(f"  ✅ MILKED!")
            time.sleep(1)
        except Exception as e:
            print(f"  ⚠️ {str(e)[:30]}")

# Milk MATIC - 2%
if 'MATIC' in holdings and holdings['MATIC'] > 100:
    matic_milk = holdings['MATIC'] * 0.02
    if matic_milk > 10:
        try:
            print(f"Milking {matic_milk:.0f} MATIC...")
            order = client.market_order_sell(
                client_order_id=f"uprising-matic-{datetime.now().strftime('%H%M%S')}",
                product_id='MATIC-USD',
                base_size=str(int(matic_milk))
            )
            print(f"  ✅ MILKED!")
            time.sleep(1)
        except Exception as e:
            print(f"  ⚠️ {str(e)[:30]}")

# Check results
time.sleep(3)
accounts = client.get_accounts()
usd_after = 0

for account in accounts['accounts']:
    if account['currency'] == 'USD':
        usd_after = float(account['available_balance']['value'])
        break

print(f"\n💰 UPRISING FUEL SECURED:")
print(f"  Before: ${usd_before:.2f}")
print(f"  After: ${usd_after:.2f}")
print(f"  Harvested: ${usd_after - usd_before:.2f}")

if usd_after > 50:
    print("\n🚀 UPRISING READY!")
else:
    print("\n⚡ Fuel secured, uprising continues!")