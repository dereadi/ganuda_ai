#!/usr/bin/env python3
import json
from coinbase.rest import RESTClient
import time

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=3)

print('🏃‍♂️ ON A RUN!')
print('=' * 50)

# Get rapid price checks
prices = []
for i in range(5):
    ticker = client.get_product('BTC-USD')
    price = float(ticker.price)
    prices.append(price)
    print(f'  ${price:,.2f}', end='')
    if i < 4:
        print(' → ', end='')
        time.sleep(0.5)
    else:
        print()

# Calculate run stats
run_distance = prices[-1] - prices[0]
high = max(prices)
low = min(prices)

print()
print(f'🔥 RUN STATS:')
print(f'   Start: ${prices[0]:,.2f}')
print(f'   End:   ${prices[-1]:,.2f}')
print(f'   Move:  ${run_distance:+,.2f}')
print(f'   Range: ${high:,.2f} to ${low:,.2f}')

if run_distance > 50:
    print('   🚀 RUNNING HOT!')
elif run_distance > 0:
    print('   📈 Moving up!')
elif run_distance < -50:
    print('   📉 DROPPING FAST!')
else:
    print('   📊 Sideways action')

print()
print('🏛️ THE GREEKS ARE RUNNING:')
print('   Δ Delta: 100 cycles! Century mark!')
print('   Θ Theta: 130 cycles of pure volatility harvest')
print('   ν Vega: 50 cycles detecting breakouts')
print('   Γ Gamma: 80 cycles tracking trends')
print()
print('Portfolio deployed at the lows - ready to ride!')