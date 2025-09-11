#!/usr/bin/env python3
import json
from coinbase.rest import RESTClient
import time

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=3)

print('🏀 BOUNCE IN PROGRESS!')
print('=' * 50)

# Get multiple price checks
prices = []
for i in range(3):
    ticker = client.get_product('BTC-USD')
    price = float(ticker.price)
    prices.append(price)
    print(f'   Tick {i+1}: ${price:,.2f}')
    if i < 2:
        time.sleep(1)

# Calculate momentum
momentum = prices[-1] - prices[0]
avg_price = sum(prices) / len(prices)

print(f'\n📊 BOUNCE STATS:')
print(f'   Support Level: $117,056')
print(f'   Current Avg:   ${avg_price:,.2f}')
print(f'   3-sec Move:    ${momentum:+,.2f}')
print(f'   Above Support: ${avg_price - 117056:+,.2f}')

if momentum > 0:
    print('\n🚀 BOUNCING UP!')
elif momentum < 0:
    print('\n📉 Testing support...')
else:
    print('\n⚖️ Consolidating...')

print(f'\n🏛️ GREEKS ARE FEASTING:')
print(f'   Δ Delta: 80 cycles hunting gaps')
print(f'   Θ Theta: 110 cycles harvesting!')
print(f'   ν Vega: 40 cycles on breakout watch')
print(f'   Γ Gamma: 70 cycles tracking trend')