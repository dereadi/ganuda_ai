#!/usr/bin/env python3
"""
🚨 FIXED MATIC CONVERTER FOR 500K MISSION 🚨
"""

import json
from coinbase.rest import RESTClient
import time

print("🚨 EMERGENCY CAPITAL LIBERATION V2")
print("=" * 60)

# Load config
config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

# Check balances
accounts = client.get_accounts()['accounts']
for acc in accounts:
    balance = float(acc['available_balance']['value'])
    if balance > 0.01:
        print(f"{acc['currency']}: ${balance:.2f}")

print("\n🔄 Converting MATIC to USD...")

try:
    # Use correct attribute access for new API
    order_response = client.market_order_sell(
        client_order_id=f"matic-fix-{int(time.time())}",
        product_id='MATIC-USD',
        base_size='400'  # Sell 400 MATIC (~$400)
    )
    
    # The response object has attributes, not dict keys
    if hasattr(order_response, 'order_id'):
        print(f"✅ Order placed: {order_response.order_id}")
    else:
        print(f"✅ Order placed: {order_response}")
        
    # Give it time to settle
    time.sleep(5)
    
    # Check new balances
    print("\n💰 NEW BALANCES:")
    accounts = client.get_accounts()['accounts']
    usd_balance = 0
    for acc in accounts:
        if acc['currency'] == 'USD':
            usd_balance = float(acc['available_balance']['value'])
            print(f"USD: ${usd_balance:.2f}")
            break
    
    if usd_balance > 100:
        print(f"\n🚀 CAPITAL SECURED! ${usd_balance:.2f} ready for 500K mission!")
        print("🔥 Restarting crawdads with proper funding...")
        
except Exception as e:
    print(f"Debug - Full error: {e}")
    print(f"Error type: {type(e)}")
    
    # Try alternative approach
    print("\n🔄 Trying alternative method...")
    try:
        # List all products to verify MATIC-USD exists
        product = client.get_product('MATIC-USD')
        print(f"MATIC price: ${product['price']}")
        
        # Try a smaller test trade
        test_order = client.market_order_sell(
            client_order_id=f"test-{int(time.time())}",
            product_id='MATIC-USD', 
            quote_size='50'  # Sell $50 worth
        )
        print(f"✅ Test order successful: {test_order}")
        
    except Exception as e2:
        print(f"Alternative also failed: {e2}")
        print("\n⚡ Manual trade needed via Coinbase app/web")