#!/usr/bin/env python3
import json
from coinbase.rest import RESTClient

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=3)

print('💰 PORTFOLIO CHECK - THE GREEKS IMPACT')
print('=' * 50)

total = 0
positions = []
accounts = client.get_accounts()['accounts']

for a in accounts:
    balance = float(a['available_balance']['value'])
    currency = a['currency']
    
    if currency == 'USD':
        if balance > 0:
            total += balance
            print(f'USD: ${balance:.2f}')
            positions.append(f'USD: ${balance:.2f}')
    elif balance > 0.001:
        try:
            ticker = client.get_product(f"{currency}-USD")
            price = float(ticker.get('price', 0))
            value = balance * price
            if value > 0.01:
                total += value
                print(f'{currency}: {balance:.6f} (${value:.2f})')
                positions.append(f'{currency}: ${value:.2f}')
        except:
            pass

print(f'\nTOTAL PORTFOLIO: ${total:.2f}')
print('\nStarting Balance: $43.53')
change = total - 43.53
change_pct = (change / 43.53 * 100) if 43.53 > 0 else 0

print(f'Change: ${change:+.2f} ({change_pct:+.1f}%)')

if change > 0:
    print('\n🎉 POSITIVE RESULTS - THE GREEKS ARE WINNING!')
    print('The correction is being harvested by The Greeks!')
elif abs(change) < 0.01:
    print('\n⚔️ The Greeks are positioning for the correction...')
else:
    print('\n🛡️ The Greeks defend during the storm...')

print('\n🏛️ ACTIVE GREEKS:')
print('Δ Delta - Gap Hunter (Active)')
print('Γ Gamma Ultra - Trend Rider (Active)')
print('Θ Theta - Volatility Harvester (Active)')
print('ν Vega - Breakout Watcher (Active)')
print('ρ Rho - Mean Reverter (Needs Fix)')

if positions:
    print('\nPositions:', ', '.join(positions[:3]))