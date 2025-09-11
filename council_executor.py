#!/usr/bin/env python3
'''
COUNCIL EXECUTION PROTOCOL
More responsive than single actor
Each member has a role
'''

import json
import time
from coinbase.rest import RESTClient
from datetime import datetime
import random

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=3)

print("\n🏛️ COUNCIL EXECUTING PLAN:")
print("-" * 50)

# Get current state
btc = client.get_product('BTC-USD')
btc_price = float(btc['price'])
print(f"Current BTC: ${btc_price:,.2f}")

# Get balances
accounts = client.get_accounts()
usd_balance = 0
positions = {}

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    if balance > 0.00001:
        if currency == 'USD':
            usd_balance = balance
        else:
            positions[currency] = balance

print(f"USD Available: ${usd_balance:.2f}")

# COUNCIL DECISION TREE
decisions = []

# Thunder: Aggressive milking
if btc_price > 112500 and 'DOGE' in positions and positions['DOGE'] > 100:
    decisions.append({
        'member': 'Thunder',
        'action': 'MILK',
        'target': 'DOGE',
        'amount': min(500, positions['DOGE'] * 0.2),
        'reason': f'BTC above $112,500 - milk profits!'
    })

# Mountain: Steady accumulation
if btc_price < 112000 and usd_balance > 5:
    decisions.append({
        'member': 'Mountain', 
        'action': 'BUY',
        'target': 'BTC',
        'amount': min(5, usd_balance * 0.3),
        'reason': f'BTC below $112,000 - accumulate!'
    })

# Fire: Quick scalping
if abs(btc_price - 112000) < 200:  # Near pivot
    if usd_balance > 10:
        decisions.append({
            'member': 'Fire',
            'action': 'SCALP_BUY',
            'target': 'BTC',
            'amount': 5,
            'reason': 'Scalp the pivot point!'
        })

# Wind: Momentum trading
if btc_price > 112200 and btc_price < 112800:
    if 'SOL' in positions and positions['SOL'] > 1:
        decisions.append({
            'member': 'Wind',
            'action': 'MILK',
            'target': 'SOL',
            'amount': 0.2,
            'reason': 'Riding momentum - extract SOL!'
        })

# Execute council decisions
for decision in decisions:
    print(f"\n🏛️ {decision['member']} EXECUTES:")
    print(f"  Action: {decision['action']}")
    print(f"  Target: {decision['target']}")
    print(f"  Amount: {decision['amount']}")
    print(f"  Reason: {decision['reason']}")
    
    try:
        if decision['action'] in ['MILK', 'SELL']:
            order = client.market_order_sell(
                client_order_id=f"council_{decision['member'].lower()}_{int(time.time())}",
                product_id=f"{decision['target']}-USD",
                base_size=str(decision['amount'])
            )
            print(f"  ✅ {decision['member']} executed milk!")
            
        elif decision['action'] in ['BUY', 'SCALP_BUY']:
            order = client.market_order_buy(
                client_order_id=f"council_{decision['member'].lower()}_{int(time.time())}",
                product_id=f"{decision['target']}-USD",
                quote_size=str(decision['amount'])
            )
            print(f"  ✅ {decision['member']} executed buy!")
            
    except Exception as e:
        print(f"  ⚠️ {decision['member']} failed: {str(e)[:50]}")

# Council wisdom
print("\n🏛️ COUNCIL WISDOM:")
print(f"  BTC at ${btc_price:,.2f}")
print(f"  Target: $114,000")
print(f"  Strategy: Milk pumps, buy dips, accumulate")
print(f"  Council remains vigilant!")
