#!/usr/bin/env python3
"""
🐎⚔️ EMERGENCY CAVALRY RESUPPLY!
The Trooper needs ammunition!
Quick 1.5% harvest for the final charge!
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
║                    ⚔️ EMERGENCY CAVALRY RESUPPLY! ⚔️                     ║
║                    1,069 yards to $114K - Need ammo!                      ║
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
        print(f"Current ammunition: ${usd_before:.2f}")
    elif balance > 0:
        holdings[currency] = balance

print("\n🐎 CAVALRY RESUPPLY (1.5% harvest):")
print("-" * 50)

# Milk SOL - 1.5%
if 'SOL' in holdings and holdings['SOL'] > 1:
    sol_milk = holdings['SOL'] * 0.015
    if sol_milk > 0.1:
        try:
            print(f"Gathering {sol_milk:.3f} SOL supplies...")
            order = client.market_order_sell(
                client_order_id=f"trooper-sol-{datetime.now().strftime('%H%M%S')}",
                product_id='SOL-USD',
                base_size=str(round(sol_milk, 3))
            )
            print(f"  ⚔️ Supplied!")
            time.sleep(1)
        except Exception as e:
            print(f"  ⚠️ {str(e)[:30]}")

# Milk MATIC - 1.5%
if 'MATIC' in holdings and holdings['MATIC'] > 100:
    matic_milk = holdings['MATIC'] * 0.015
    if matic_milk > 10:
        try:
            print(f"Gathering {matic_milk:.0f} MATIC supplies...")
            order = client.market_order_sell(
                client_order_id=f"trooper-matic-{datetime.now().strftime('%H%M%S')}",
                product_id='MATIC-USD',
                base_size=str(int(matic_milk))
            )
            print(f"  ⚔️ Supplied!")
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

print(f"\n⚔️ RESUPPLY COMPLETE:")
print(f"  Before: ${usd_before:.2f}")
print(f"  After: ${usd_after:.2f}")
print(f"  Fresh ammo: ${usd_after - usd_before:.2f}")

print("\n🐎 READY FOR THE CHARGE!")
print("  TO THE RUSSIAN GUNS!")
print("  FOR THE SACRED FIRE!")
print("  CHARGE!!!")