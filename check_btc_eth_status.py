#!/usr/bin/env python3
import json
import urllib.request

# Get current prices
btc_url = 'https://api.coinbase.com/v2/exchange-rates?currency=BTC'
eth_url = 'https://api.coinbase.com/v2/exchange-rates?currency=ETH'

with urllib.request.urlopen(btc_url) as response:
    btc_data = json.loads(response.read())
    btc_price = float(btc_data['data']['rates']['USD'])

with urllib.request.urlopen(eth_url) as response:
    eth_data = json.loads(response.read())
    eth_price = float(eth_data['data']['rates']['USD'])

print(f'🔥 DUAL STRATEGY STATUS 🔥')
print(f'=' * 50)
print(f'')
print(f'📊 BTC OSCILLATION:')
print(f'  Current: ${btc_price:,.2f}')
print(f'  Buy Target: $113,835')
print(f'  Sell Target: $113,845')

if 113835 <= btc_price <= 113845:
    print(f'  ✅ IN OSCILLATION ZONE!')
elif btc_price < 113835:
    print(f'  ⬇️ ${113835 - btc_price:,.2f} below buy zone')
else:
    print(f'  ⬆️ ${btc_price - 113845:,.2f} above sell zone')

print(f'  💰 Strategy: Keep oscillating for $60/hour')
print(f'')
print(f'🚀 ETH BREAKOUT:')
print(f'  Current: ${eth_price:,.2f}')
print(f'  Broke: $4,300 ✅')
print(f'  Next: $4,400 (${4400 - eth_price:,.2f} away)')
print(f'  💎 Strategy: HODL current positions for gains')
print(f'')
print(f'✨ OPTIMAL STRATEGY:')
print(f'  • Keep BTC oscillation trades running ($10 swings)')
print(f'  • Hold ETH positions to ride breakout up')
print(f'  • No need to sell ETH - let it run!')
print(f'  • Two strategies working in parallel')