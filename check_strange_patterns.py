#!/usr/bin/env python3

import json
from coinbase.rest import RESTClient

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=10)

print('🔍 CHECKING ETH & SOL - STRANGE PATTERNS?')
print('=' * 60)

# Try to get live data
coins = ['ETH', 'SOL', 'BTC']
data = {}

for coin in coins:
    try:
        # Get 24h stats
        stats = client.get_product_stats(f'{coin}-USD')
        
        current = float(stats.last)
        open_24h = float(stats.open)
        high = float(stats.high)
        low = float(stats.low)
        volume = float(stats.volume)
        
        # Calculate metrics
        change = ((current - open_24h) / open_24h) * 100
        range_size = high - low
        volatility = (range_size / current) * 100
        
        if high != low:
            position_in_range = ((current - low) / (high - low)) * 100
        else:
            position_in_range = 50
        
        data[coin] = {
            'current': current,
            'change': change,
            'volatility': volatility,
            'position': position_in_range,
            'high': high,
            'low': low
        }
        
        print(f'{coin}:')
        print(f'  Current: ${current:,.2f}')
        print(f'  24h Range: ${low:,.2f} - ${high:,.2f}')
        print(f'  Range Size: ${range_size:.2f} ({volatility:.1f}% volatility)')
        print(f'  Position: {position_in_range:.0f}% of range')
        print(f'  24h Change: {change:+.2f}%')
        
        # Detect strange patterns
        if volatility > 5:
            print(f'  ⚠️  HIGH VOLATILITY!')
        if position_in_range < 20:
            print(f'  📉 NEAR DAILY LOW!')
        elif position_in_range > 80:
            print(f'  📈 NEAR DAILY HIGH!')
        if abs(change) > 5:
            print(f'  🚨 LARGE MOVE!')
            
        print()
        
    except Exception as e:
        print(f'{coin}: Error - {str(e)[:100]}')
        print()

# Pattern analysis
if len(data) >= 2:
    print('🔮 PATTERN ANALYSIS:')
    print('-' * 40)
    
    # Check if ETH and SOL are synced
    if 'ETH' in data and 'SOL' in data:
        eth_change = data['ETH']['change']
        sol_change = data['SOL']['change']
        
        if abs(eth_change - sol_change) < 1:
            print('📊 ETH & SOL moving in SYNC')
        elif (eth_change > 0 and sol_change < 0) or (eth_change < 0 and sol_change > 0):
            print('⚡ ETH & SOL DIVERGING (opposite directions!)')
        
        # Check relative strength
        if sol_change > eth_change + 2:
            print('🚀 SOL showing RELATIVE STRENGTH vs ETH')
        elif eth_change > sol_change + 2:
            print('💪 ETH showing RELATIVE STRENGTH vs SOL')
    
    # Check positions in range
    positions = [data[coin]['position'] for coin in data]
    if all(p > 70 for p in positions):
        print('🔥 ALL near daily HIGHS - potential resistance')
    elif all(p < 30 for p in positions):
        print('❄️ ALL near daily LOWS - potential bounce')
    
    # Check for outliers
    volatilities = [data[coin]['volatility'] for coin in data]
    avg_vol = sum(volatilities) / len(volatilities)
    for coin in data:
        if data[coin]['volatility'] > avg_vol * 1.5:
            print(f'🎯 {coin} showing UNUSUAL volatility vs others')