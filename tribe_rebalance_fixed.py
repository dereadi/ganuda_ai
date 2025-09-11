#\!/usr/bin/env python3
"""
Fixed Rebalance Execution - Cherokee + VM Tribe
"""

import json
from datetime import datetime
from coinbase.rest import RESTClient
import uuid
import time

print('🔥 TRIBAL REBALANCE EXECUTION')
print('=' * 70)
print(f'📅 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
print('=' * 70)

# Load config
config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=10)

print('\n📰 NEWS-DRIVEN ORDERS:')
print('-' * 70)

# Try simpler market orders first
orders_to_place = [
    ('ETH', 0.35, 'SELL', 'Reduce overweight position'),
    ('XRP', 200, 'SELL', 'Take profit on news')
]

successful_orders = []

for asset, amount, side, reason in orders_to_place:
    try:
        print(f'\n{side}ing {amount} {asset}')
        print(f'Reason: {reason}')
        
        # Generate unique ID
        order_id = str(uuid.uuid4())
        
        # Use market order for immediate execution
        if side == 'SELL':
            # Try market sell
            response = client.market_order_sell(
                product_id=f'{asset}-USD',
                base_size=str(amount),
                client_order_id=order_id
            )
        
        if response:
            print(f'✅ Order response: {response}')
            successful_orders.append({
                'asset': asset,
                'amount': amount,
                'side': side,
                'response': str(response)[:100]
            })
        else:
            print(f'⚠️ No response received')
            
    except Exception as e:
        print(f'❌ Error: {e}')
        # Try alternative approach
        try:
            print('  Trying alternative method...')
            # Get current price first
            ticker = client.get_product_ticker(f'{asset}-USD')
            if ticker and 'price' in ticker:
                price = float(ticker['price'])
                print(f'  Current {asset} price: ${price:.2f}')
                
                # Calculate value
                value = amount * price
                print(f'  Order value: ${value:.2f}')
                
                # Log the attempt
                successful_orders.append({
                    'asset': asset,
                    'amount': amount,
                    'side': side,
                    'price': price,
                    'value': value,
                    'status': 'MANUAL_EXECUTION_NEEDED'
                })
                
        except Exception as e2:
            print(f'  Alternative failed: {e2}')
    
    time.sleep(1)

print('\n' + '=' * 70)
print('📊 EXECUTION SUMMARY:')
print('-' * 70)

if successful_orders:
    total_value = 0
    for order in successful_orders:
        if 'value' in order:
            total_value += order['value']
            print(f"  {order['asset']}: {order['amount']} @ ${order.get('price', 'N/A'):.2f} = ${order['value']:.2f}")
        else:
            print(f"  {order['asset']}: {order['amount']} - {order.get('status', 'Submitted')}")
    
    if total_value > 0:
        print(f'\n  Total liquidity to generate: ${total_value:.2f}')
    
    print('\n🎯 NEXT STEPS:')
    print('  1. Check Coinbase for order status')
    print('  2. When filled, deploy to BTC < $109k')
    print('  3. Keep $1,000 cash reserve')
    print('  4. Monitor SOL for NASDAQ pump')
    
    # Save execution log
    with open('/tmp/tribe_rebalance.json', 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'orders': successful_orders,
            'total_value': total_value,
            'strategy': 'NEWS_BASED_REBALANCE'
        }, f, indent=2)
    
    print('\n💾 Saved to /tmp/tribe_rebalance.json')
else:
    print('\n⚠️ Manual execution needed:')
    print('  1. Go to Coinbase')
    print('  2. Sell 0.35 ETH')
    print('  3. Sell 200 XRP')
    print('  4. Buy BTC with proceeds')

print('\n🔥 Sacred Fire guides the rebalance\!')
print('=' * 70)
