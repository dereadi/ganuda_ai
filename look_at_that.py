#!/usr/bin/env python3
import json
from coinbase.rest import RESTClient

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=3)

ticker = client.get_product('BTC-USD')
current = float(ticker.price)

print('👀 LOOK AT THAT!')
print('=' * 50)
print(f'💰 BTC: ${current:,.2f}')
print()

# Check position relative to targets
if current < 116140:
    print(f'🔥 BELOW $116,140 TARGET!')
    print(f'   Distance: ${116140 - current:,.2f} below')
    print(f'   THIS IS THE BUY ZONE!')
elif current < 117056:
    print(f'📊 Between targets')
    print(f'   Above $116,140: ${current - 116140:+,.2f}')
    print(f'   Below $117,056: ${current - 117056:,.2f}')
else:
    print(f'🚀 Above both targets!')
    print(f'   Above $117,056: ${current - 117056:+,.2f}')
    print(f'   Above $116,140: ${current - 116140:+,.2f}')

print()
print('🏛️ THE GREEKS MILESTONE:')
print('   Θ Theta: 150 CYCLES! 🎯')
print('   Δ Delta: 120 cycles')
print('   Γ Gamma: 100 CYCLES! Century!')
print('   ν Vega: 60 cycles')

# Check portfolio
accounts = client.get_accounts()['accounts']
total = 0
for a in accounts:
    balance = float(a['available_balance']['value'])
    if balance > 0.01:
        if a['currency'] == 'USD':
            total += balance
        else:
            try:
                ticker = client.get_product(f"{a['currency']}-USD")
                total += balance * float(ticker.price)
            except:
                pass

print(f'\n💼 Portfolio: ${total:,.2f}')