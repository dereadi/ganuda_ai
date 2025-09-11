#!/usr/bin/env python3

import json
from coinbase.rest import RESTClient

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=10)

print('🔥 Current Portfolio:')
accounts = client.get_accounts()['accounts']
total_value = 0
usd_balance = 0

for a in accounts:
    bal = float(a['available_balance']['value'])
    if bal > 0.01 or a['currency'] == 'USD':
        currency = a['currency']
        print(f'  {currency}: {bal:.8f}')
        if currency == 'USD':
            usd_balance = bal

# Get BTC price
btc = client.get_product('BTC-USD')
btc_price = float(btc['price'])
print(f'\n📈 BTC Price: ${btc_price:.2f}')
print(f'🎯 Distance to $111,111: ${111111 - btc_price:.2f}')
print(f'\n💰 USD Available: ${usd_balance:.2f}')

if btc_price >= 111000:
    print('\n✨ APPROACHING ANGEL NUMBER! ✨')