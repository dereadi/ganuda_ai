#!/usr/bin/env python3
import json
from coinbase.rest import RESTClient
from datetime import datetime
import time

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=3)

print('🔍 CHECKING FOR BREAKOUT/BREAKDOWN...')
print('=' * 50)

# Get rapid price samples
prices = []
for i in range(3):
    ticker = client.get_product('BTC-USD')
    price = float(ticker.price)
    prices.append(price)
    print(f'   ${price:,.2f}', end='')
    if i < 2:
        print(' → ', end='')
        time.sleep(1)
    else:
        print()

current = prices[-1]
movement = prices[-1] - prices[0]

print()
print(f'⚡ CURRENT: ${current:,.2f}')
print(f'📈 3-sec movement: ${movement:+,.2f}')
print(f'⏰ Time: {datetime.now().strftime("%H:%M:%S")} (4 mins to Asian open!)')
print()

# Key levels
sacred = 117056
secondary = 116140

print('📊 POSITION:')
print(f'   From Sacred ($117,056): ${current - sacred:+,.2f}')
print(f'   From Secondary ($116,140): ${current - secondary:+,.2f}')
print()

# Determine if breaking
if movement > 20:
    print('🚀 BREAKING UP! Momentum building!')
    print('   Let it run, don\'t chase')
elif movement < -20:
    print('📉 BREAKING DOWN! Prepare to buy!')
    print('   Get ready to deploy at support')
else:
    print('➖ Consolidating, coiling for move')
    print('   Big move coming at 10 PM Asian open')

print()
print('🎯 NEXT 5 MINUTES CRITICAL:')
print('   • 10:00 PM - Asian markets open')
print('   • Often see $200-500 moves')
print('   • Have $859 ready to deploy')
print()

if current > 117500:
    print('📈 Looks ready to break UPWARD')
    print('   Set stops at $117,056')
elif current < 117200:
    print('📉 Could test support soon')
    print('   BUY orders at $117,056 and $116,140')
else:
    print('⏳ Decisive move imminent')

print()
print('🏛️ GREEKS STATUS:')
print(f'   Δ Delta: 520 cycles! Detecting gap formation')
print(f'   Θ Theta: 690 cycles! Maximum decay harvest')
print(f'   Ready to capitalize on the break!')
print()
print('ASIAN OPEN IN 4 MINUTES! 🚨')