#!/usr/bin/env python3
"""
📊 ETH & BTC Market Analysis
"""

import json
from coinbase.rest import RESTClient

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=10)

print('📊 ETH & BTC ANALYSIS')
print('=' * 60)

# Get current prices and stats
for coin in ['ETH', 'BTC']:
    try:
        ticker = client.get_product(f'{coin}-USD')
        price = float(ticker.price)
        
        stats = client.get_product_stats(f'{coin}-USD')
        open_24h = float(stats.open)
        high_24h = float(stats.high)
        low_24h = float(stats.low)
        volume_24h = float(stats.volume)
        
        change_24h = price - open_24h
        change_pct = (change_24h / open_24h) * 100
        
        # Calculate position in range
        if high_24h != low_24h:
            range_position = ((price - low_24h) / (high_24h - low_24h)) * 100
        else:
            range_position = 50
        
        print(f'🪙 {coin}')
        print(f'  Price: ${price:,.2f}')
        print(f'  24h Change: ${change_24h:+,.2f} ({change_pct:+.2f}%)')
        print(f'  24h Range: ${low_24h:,.2f} - ${high_24h:,.2f}')
        print(f'  Position in range: {range_position:.0f}%')
        print(f'  24h Volume: {volume_24h:,.2f} {coin}')
        
        # Technical signals
        if range_position > 80:
            print(f'  📈 Signal: Near 24h high - potential resistance')
        elif range_position < 20:
            print(f'  📉 Signal: Near 24h low - potential support')
        elif 45 < range_position < 55:
            print(f'  ➡️ Signal: Mid-range - consolidating')
            
        # Momentum analysis
        mid = (high_24h + low_24h) / 2
        if price > mid * 1.02:
            print(f'  🔥 Above mid-range, momentum up')
        elif price < mid * 0.98:
            print(f'  ❄️ Below mid-range, momentum down')
            
        print()
        
    except Exception as e:
        print(f'{coin}: Error - {str(e)[:50]}')
        print()

# Check our positions
print('💼 OUR POSITIONS:')
print('-' * 40)
accounts = client.get_accounts()['accounts']

eth_balance = 0
btc_balance = 0
usd_balance = 0

for a in accounts:
    balance = float(a['available_balance']['value'])
    if balance > 0:
        currency = a['currency']
        if currency == 'ETH':
            eth_balance = balance
        elif currency == 'BTC':
            btc_balance = balance
        elif currency == 'USD':
            usd_balance = balance

# Display positions with values
if eth_balance > 0:
    eth_ticker = client.get_product('ETH-USD')
    eth_price = float(eth_ticker.price)
    eth_value = eth_balance * eth_price
    print(f'ETH: {eth_balance:.8f} = ${eth_value:,.2f}')
    
if btc_balance > 0:
    btc_ticker = client.get_product('BTC-USD')
    btc_price = float(btc_ticker.price)
    btc_value = btc_balance * btc_price
    print(f'BTC: {btc_balance:.8f} = ${btc_value:,.2f}')

print(f'USD: ${usd_balance:.2f}')

print()
print('📈 TRADING OPPORTUNITY ANALYSIS:')
print('-' * 40)

# ETH opportunity
if 'eth_price' in locals():
    if range_position < 30 and change_pct < -2:
        print('🟢 ETH: Good buying opportunity (oversold)')
    elif range_position > 70 and change_pct > 2:
        print('🔴 ETH: Consider taking profits (overbought)')
    else:
        print('⚪ ETH: No clear signal')

# BTC opportunity  
btc_range = 0
for coin in ['BTC']:
    ticker = client.get_product(f'{coin}-USD')
    price = float(ticker.price)
    stats = client.get_product_stats(f'{coin}-USD')
    high = float(stats.high)
    low = float(stats.low)
    if high != low:
        btc_range = ((price - low) / (high - low)) * 100
    
    if btc_range < 30:
        print('🟢 BTC: Near daily lows - potential bounce')
    elif btc_range > 70:
        print('🟡 BTC: Near daily highs - watch for resistance')
    else:
        print('⚪ BTC: Mid-range, no edge')