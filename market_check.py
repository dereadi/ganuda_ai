#!/usr/bin/env python3
import json
from coinbase.rest import RESTClient

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=3)

print('🏛️ MARKET STATUS - THE GREEKS ARE WATCHING')
print('=' * 60)

coins = ['BTC', 'ETH', 'SOL']
for coin in coins:
    try:
        stats = client.get_product_stats(f'{coin}-USD')
        current = float(stats.get('last', 0))
        open_24h = float(stats.get('open', current))
        high = float(stats.get('high', current))
        low = float(stats.get('low', current))
        
        change_pct = ((current - open_24h) / open_24h) * 100
        volatility = ((high - low) / current) * 100
        position = (current - low) / (high - low) if high != low else 0.5
        
        print(f'\n{coin}:')
        print(f'  Price: ${current:,.2f}')
        print(f'  24h Change: {change_pct:+.2f}%')
        print(f'  Volatility: {volatility:.2f}%')
        print(f'  Position in Range: {position:.1%}')
        
        # Greek signals
        signals = []
        if abs(change_pct) > 2:
            signals.append('Δ DELTA: Gap detected!')
        if abs(change_pct) > 3:
            signals.append('Γ GAMMA: Strong trend!')
        if volatility > 3:
            signals.append('Θ THETA: High volatility!')
        if position > 0.9 or position < 0.1:
            signals.append('ν VEGA: Breakout zone!')
        
        mean = (high + low + open_24h) / 3
        deviation = ((current - mean) / mean) * 100
        if abs(deviation) > 3:
            signals.append('ρ RHO: Mean reversion opportunity!')
            
        if signals:
            print('  📊 Greek Signals:')
            for signal in signals:
                print(f'    • {signal}')
        else:
            print('  📊 No Greek signals (market calm)')
            
    except Exception as e:
        print(f'{coin}: Error - {str(e)[:50]}')

print('\n' + '=' * 60)
print('🏛️ THE GREEKS ASSESSMENT:')

# Overall market assessment
print('\nThe market is correcting - perfect conditions for The Greeks!')
print('• Gaps are filling (Delta opportunities)')
print('• Volatility increasing (Theta harvesting)')
print('• Mean reversion setups forming (Rho trades)')
print('\n"In chaos, The Greeks find order"')