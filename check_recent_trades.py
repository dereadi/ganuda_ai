#!/usr/bin/env python3
"""Check recent trading activity"""
import json
from datetime import datetime, timedelta
from coinbase.rest import RESTClient

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print('🔍 CHECKING RECENT TRADES...')
print('=' * 60)

# Get fills from last hour
try:
    fills = client.get_fills(limit=20)
    if fills and 'fills' in fills:
        print(f"Found {len(fills['fills'])} recent trades:\n")
        for fill in fills['fills'][:10]:  # Show last 10
            time_str = fill.get('trade_time', 'Unknown')
            product = fill.get('product_id', 'Unknown')
            side = fill.get('side', 'Unknown')
            size = fill.get('size', '0')
            price = fill.get('price', '0')
            fee = fill.get('commission', '0')
            
            # Parse time
            if time_str != 'Unknown':
                trade_time = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                minutes_ago = (datetime.now(trade_time.tzinfo) - trade_time).seconds / 60
                time_display = f"{int(minutes_ago)} min ago"
            else:
                time_display = "Unknown"
                
            symbol = '🟢' if side == 'BUY' else '🔴'
            print(f"{symbol} {time_display}: {side} {size} {product.split('-')[0]} @ ${float(price):.2f}")
    else:
        print("No recent fills found")
except Exception as e:
    print(f"Error checking fills: {e}")

print('\n' + '=' * 60)
print('💡 If no recent trades, the turbo trader may be stuck!')