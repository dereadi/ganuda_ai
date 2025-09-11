#!/usr/bin/env python3
import json
from coinbase.rest import RESTClient

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=3)

ticker = client.get_product('BTC-USD')
current = float(ticker.price)

print('⚠️ NEW TARGET LEVEL: $116,140')
print('=' * 50)
print(f'📍 Current Price: ${current:,.2f}')
print(f'🎯 Target Level:  $116,140.00')
print(f'📏 Distance:      ${current - 116140:+,.2f}')
print(f'📊 % Above:       {((current/116140 - 1)*100):+.2f}%')
print()

if current > 116140:
    print('✅ Still ABOVE new target')
    print(f'   Room to fall: ${current - 116140:,.2f}')
    print('   Greeks should prepare for potential dip')
else:
    print('🔥 BELOW TARGET - BUY ZONE!')

print()
print('🏛️ GREEKS STATUS:')
print('   Θ Theta: 120 cycles - still harvesting volatility!')
print('   Δ Delta: 90 cycles - gap hunter ready')
print('   If we hit $116,140, Greeks will FEAST!')