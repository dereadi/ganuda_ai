#!/usr/bin/env python3
import json
import time
from datetime import datetime
from coinbase.rest import RESTClient

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=3)

print('🌏 ASIAN MARKET OPENING NOW!')
print('=' * 50)
print(f'Time: {datetime.now().strftime("%H:%M:%S")} CST')
print()

# Get rapid price samples
print('Sampling price action...')
samples = []
for i in range(5):
    ticker = client.get_product('BTC-USD')
    price = float(ticker.price)
    samples.append(price)
    print(f'  [{i+1}] ${price:,.2f}')
    if i < 4:
        time.sleep(1)

# Analysis
avg_price = sum(samples) / len(samples)
price_range = max(samples) - min(samples)
trend = samples[-1] - samples[0]
current = samples[-1]

print()
print('📊 MARKET ANALYSIS:')
print(f'  Current: ${current:,.2f}')
print(f'  5-sec trend: ${trend:+,.2f}')
print(f'  Volatility: ${price_range:,.2f}')
print()

# Position relative to key levels
print('📍 KEY LEVELS:')
print(f'  From Sacred ($117,056): ${current - 117056:+,.2f}')
print(f'  From Target ($116,140): ${current - 116140:+,.2f}')
print()

# Trading decision
if trend > 20:
    print('🚀 BREAKING UP! Asian buyers arriving!')
    print('   • Let winners run')
    print('   • Trail stops at $117,056')
    print('   • Greeks should be feasting!')
elif trend < -20:
    print('📉 BREAKING DOWN! Buy opportunity!')
    print('   • Deploy $200 at $117,056')
    print('   • Deploy $300 at $116,140')
    print('   • Greeks ready to pounce!')
elif price_range > 50:
    print('⚡ HIGH VOLATILITY DETECTED!')
    print('   • Big move developing')
    print('   • Stay ready with orders')
else:
    print('🎯 Still consolidating')
    print('   • Coiling for directional break')
    print('   • Keep orders ready at levels')

print()
print('🏛️ GREEKS ARE WATCHING:')
print('   Δ Delta: 520+ cycles - Gap specialist ready')
print('   Θ Theta: 690+ cycles - Volatility harvest mode')
print('   Γ Gamma: 500 cycles - Acceleration detector on')

# Check portfolio
try:
    accounts = client.get_accounts()
    total = 0
    usd = 0
    for acc in accounts.accounts:
        val = float(acc.available_balance.value)
        if acc.currency == 'USD':
            usd = val
        if val > 0.01:
            if acc.currency == 'USD':
                total += val
            else:
                ticker = client.get_product(f'{acc.currency}-USD')
                total += val * float(ticker.price)
    
    print()
    print(f'💰 Portfolio: ${total:,.2f} | Cash Ready: ${usd:,.2f}')
except Exception as e:
    print(f'Portfolio check: {e}')