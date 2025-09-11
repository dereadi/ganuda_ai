#!/usr/bin/env python3
"""Quick portfolio check"""
import json
from coinbase.rest import RESTClient

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

accounts = client.get_accounts()['accounts']
print('🔥 CURRENT PORTFOLIO STATUS:')
print('=' * 50)
total_value = 0
for a in accounts:
    if float(a['available_balance']['value']) > 0.01:
        symbol = a['currency']
        balance = float(a['available_balance']['value'])
        if symbol == 'USD':
            print(f'💵 USD: ${balance:.2f}')
            total_value += balance
        elif symbol in ['BTC', 'ETH', 'SOL']:
            prices = {'BTC': 59000, 'ETH': 2600, 'SOL': 150}
            value = balance * prices.get(symbol, 0)
            total_value += value
            print(f'🪙 {symbol}: {balance:.8f} (~${value:.2f})')
        else:
            print(f'🪙 {symbol}: {balance:.8f}')
print('=' * 50)            
print(f'📊 TOTAL ESTIMATED VALUE: ${total_value:.2f}')
print(f'📉 vs $10,229.61 deposited: ${total_value - 10229.61:+.2f}')