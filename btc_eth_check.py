#!/usr/bin/env python3

import json
from coinbase.rest import RESTClient

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=10)

print('📊 ETH & BTC POSITIONS')
print('=' * 60)

# Get current positions
accounts = client.get_accounts()['accounts']

positions = {}
for a in accounts:
    balance = float(a['available_balance']['value'])
    if balance > 0 and a['currency'] in ['ETH', 'BTC', 'USD']:
        positions[a['currency']] = balance

# Estimate prices (fallback)
PRICES = {
    'BTC': 107700,
    'ETH': 4305
}

# Display with estimated values
print('🪙 BTC')
if 'BTC' in positions:
    btc_value = positions['BTC'] * PRICES['BTC']
    print(f'  Holdings: {positions["BTC"]:.8f} BTC')
    print(f'  Est. Price: ${PRICES["BTC"]:,.0f}')
    print(f'  Value: ${btc_value:,.2f}')
else:
    print('  No position')

print()
print('⟠ ETH')  
if 'ETH' in positions:
    eth_value = positions['ETH'] * PRICES['ETH']
    print(f'  Holdings: {positions["ETH"]:.8f} ETH')
    print(f'  Est. Price: ${PRICES["ETH"]:,.0f}')
    print(f'  Value: ${eth_value:,.2f}')
else:
    print('  No position')

print()
print(f'💵 USD: ${positions.get("USD", 0):.2f}')

# Total portfolio
total = positions.get('USD', 0)
if 'BTC' in positions:
    total += positions['BTC'] * PRICES['BTC']
if 'ETH' in positions:
    total += positions['ETH'] * PRICES['ETH']

print()
print(f'📊 Total Portfolio: ${total:,.2f}')

# Analysis
print()
print('📈 MARKET OUTLOOK:')
print('-' * 40)
print('BTC: Above $107k - strong momentum, new highs possible')
print('ETH: Above $4.3k - following BTC, ratio improving')
print()
print('💡 STRATEGY:')
print('• Hold core BTC/ETH positions (80% of portfolio)')
print('• Use alts (SOL, MATIC) for trading liquidity')
print('• Take profits on 10% rallies in alts')
print('• Accumulate BTC/ETH on any dips below $105k/$4.2k')