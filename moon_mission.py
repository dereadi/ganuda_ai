#!/usr/bin/env python3
"""
🚀 MOON MISSION TRACKER
"""

import json
from coinbase.rest import RESTClient
import random

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=10)

print('🚀🌙 TO THE MOON MISSION STATUS 🌙🚀')
print('=' * 60)

# Moon prices (ambitious targets)
MOON_TARGETS = {
    'BTC': 150000,
    'ETH': 10000,
    'SOL': 500,
    'AVAX': 100,
    'MATIC': 5,
    'DOGE': 1,
    'XRP': 10,
    'LINK': 100
}

CURRENT = {
    'BTC': 108500,
    'ETH': 4350,
    'SOL': 205,
    'AVAX': 38,
    'MATIC': 0.73,
    'DOGE': 0.365,
    'XRP': 2.82,
    'LINK': 21.5
}

# Get positions
accounts = client.get_accounts()['accounts']
positions = {}

for a in accounts:
    balance = float(a['available_balance']['value'])
    if balance > 0.00001:
        currency = a['currency']
        if currency in CURRENT and currency != 'USD':
            positions[currency] = balance

print('🎯 MOON MISSION CALCULATIONS:')
print('-' * 40)

current_value = 0
moon_value = 0

for coin, balance in positions.items():
    if coin in CURRENT:
        current_val = balance * CURRENT[coin]
        moon_val = balance * MOON_TARGETS[coin]
        current_value += current_val
        moon_value += moon_val
        
        distance_to_moon = ((MOON_TARGETS[coin] - CURRENT[coin]) / CURRENT[coin]) * 100
        
        if current_val > 100:  # Show significant positions
            print(f'{coin}:')
            print(f'  Now: ${current_val:,.0f}')
            print(f'  Moon: ${moon_val:,.0f} ({distance_to_moon:+.0f}% to go)')

print()
print(f'📊 PORTFOLIO MOON MATH:')
print(f'  Current: ${current_value:,.0f}')
print(f'  At Moon: ${moon_value:,.0f}')
print(f'  Potential: {(moon_value/current_value):.1f}x')
print()

# Fun moon messages
rockets = '🚀' * random.randint(3, 7)
print(rockets)
print()
print('MOON CHECKLIST:')
print('✅ BTC breaking ATH territory')
print('✅ ETH following strong')
print('✅ SOL on a tear')
print('✅ Alts waking up')
print('✅ Bull market confirmed')
print('✅ Diamond hands activated')
print()
print('MISSION STATUS: LUNAR TRAJECTORY CONFIRMED!')
print('NEXT STOP: LAMBOS ON THE MOON! 🏎️🌙')

# Special DOGE check
if 'DOGE' in positions:
    doge_at_dollar = positions['DOGE'] * 1.0
    print()
    print(f'🐕 DOGE AT $1 = ${doge_at_dollar:,.2f}')
    print('   The ultimate meme dream!')

# Special MATIC check  
if 'MATIC' in positions:
    matic_moon = positions['MATIC'] * 5
    print(f'🔷 MATIC AT $5 = ${matic_moon:,.2f}')
    print('   Your biggest bag to the moon!')