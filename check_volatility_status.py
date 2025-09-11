#!/usr/bin/env python3
"""Check current volatility capture status"""

import json
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("=== VOLATILITY CAPTURE STATUS ===")
print(datetime.now().strftime("%H:%M:%S"))
print("-" * 40)

# Get accounts
accounts = client.get_accounts()['accounts']
usd = 0
positions = {}

for acc in accounts:
    bal = float(acc['available_balance']['value'])
    if bal > 0.01:
        if acc['currency'] == 'USD':
            usd = bal
        else:
            positions[acc['currency']] = bal

print(f"USD: ${usd:.2f}")
print(f"Active positions: {len(positions)}")

# Get current prices for top movers
products = ['BTC-USD', 'ETH-USD', 'SOL-USD']
prices = {}
for product in products:
    ticker = client.get_product(product)
    prices[product] = float(ticker['price'])
    print(f"{product}: ${prices[product]:,.2f}")

# Check if profit bleeder is working
if usd < 100:
    print("\n⚠️  NEED MORE USD LIQUIDITY!")
    print("   Profit bleeder should be extracting...")
    print("   Checking for profitable positions to milk...")
    
    # Find positions to milk
    for coin, balance in positions.items():
        if coin in ['MATIC', 'DOGE', 'AVAX', 'SOL']:
            print(f"   - {coin}: {balance:.2f} units available")
else:
    print(f"\n✅ USD adequate: ${usd:.2f}")
    print("   Ready to capture volatility swings")