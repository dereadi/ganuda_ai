#!/usr/bin/env python3
"""Check Coinbase balance"""

import json
from coinbase.rest import RESTClient

# Load API key
with open('cdp_api_key_new.json', 'r') as f:
    api_data = json.load(f)

# Create client
client = RESTClient(
    api_key=api_data['name'].split('/')[-1],
    api_secret=api_data['privateKey']
)

# Get accounts
accounts = client.get_accounts()

print("\n💰 COINBASE BALANCES:")
print("=" * 40)

total_usd = 0
for account in accounts['accounts']:
    balance = float(account['available_balance']['value'])
    if balance > 0:
        currency = account['currency']
        print(f"{currency}: ${balance:.2f}")
        if currency == 'USD':
            total_usd = balance

print(f"\nTOTAL USD: ${total_usd:.2f}")
print("\nGreeks: 'See? The money is REAL!'")
