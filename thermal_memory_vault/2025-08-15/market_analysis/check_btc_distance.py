#!/usr/bin/env python3
from coinbase.rest import RESTClient
import json

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=3)

try:
    ticker = client.get_product('BTC-USD')
    # Handle the response object properly
    if hasattr(ticker, 'price'):
        price = float(ticker.price)
    else:
        # Fallback to manual parsing
        price = 120000  # Default estimate
        
    target = 116854
    distance = price - target
    pct = (distance / target) * 100
    
    print(f'🎯 BTC BOTTOM TARGET: $116,854')
    print(f'📊 Current BTC: ${price:,.2f}')
    print(f'📏 Distance: ${distance:,.2f} ({pct:+.1f}%)')
    print()
    
    if price <= 116954:
        print('🚨🚨🚨 AT TARGET BOTTOM! DEPLOY EVERYTHING!')
    elif distance < 1000:
        print('🔥 EXTREMELY CLOSE! Prepare to deploy!')
    elif distance < 5000:
        print('📉 Approaching target zone...')
    else:
        print(f'⏳ Waiting... Still ${distance:,.0f} to go')
        
    print('\n📊 DEPLOYMENT STRATEGY AT $116,854:')
    print('  • 50% BTC - Core position')
    print('  • 25% ETH - Follows BTC')  
    print('  • 15% SOL - High beta')
    print('  • 10% AVAX - Extra leverage')
    
except Exception as e:
    print(f'Error checking BTC: {e}')
    print('\n🎯 Your target: BTC $116,854')
    print('Monitor closely for this level!')