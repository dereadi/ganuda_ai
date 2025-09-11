#!/usr/bin/env python3
"""Check if bleed orders are set"""

import json
from coinbase.rest import RESTClient

config = json.load(open('/home/dereadi/scripts/claude/cdp_api_key_new.json'))
key = config['name'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['privateKey'], timeout=10)

# Check for any open orders
try:
    orders = client.get_orders()
    if orders and len(orders) > 0:
        print('🎯 OPEN ORDERS DETECTED:')
        for order in orders[:10]:  # Show first 10
            print(f"  {order['product_id']}: {order['side']} {order.get('size', 'N/A')} @ ${order.get('limit_price', 'market')}")
    else:
        print('⚠️ NO BLEED ORDERS SET!')
        print('SOL IS 34 CENTS FROM $210!')
        print('SET YOUR LIMITS NOW!')
        print()
        print('SUGGESTED BLEED ORDERS:')
        print('• BTC: Sell 0.0009 @ $113,650')
        print('• ETH: Sell 0.082 @ $4,500')
        print('• SOL: Sell 1.09 @ $210')
        print('• XRP: Sell 8.8 @ $2.90')
except Exception as e:
    print(f'No open orders found (or error: {e})')
    print()
    print('⚠️ SOL APPROACHING $210 RAPIDLY!')
    print('Consider setting bleed orders NOW!')