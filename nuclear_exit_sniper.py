#!/usr/bin/env python3
"""
🎯 NUCLEAR EXIT SNIPER
When sell orders fill, immediately place buy orders for profit
"""

import json
from coinbase.rest import RESTClient
import time
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("🎯 NUCLEAR EXIT SNIPER ACTIVATED")
print("=" * 70)
print("Watching for filled sell orders to execute profit taking")
print("=" * 70)

# Our nuclear strike sell orders
nuclear_orders = {
    "fa353625-5603-4a99-bfcf-0400943c9de2": {"price": 109921.90, "size": 0.00276674},
    "497833b5-0a2b-444b-a035-9896ac540d21": {"price": 110251.01, "size": 0.00276674},
    "5813a2c1-64a8-4191-8ffe-01e9517073b5": {"price": 110580.12, "size": 0.00368899}
}

while True:
    print(f"\n⏰ Check at {datetime.now().strftime('%H:%M:%S')}")
    print("-" * 70)
    
    # Get current price
    btc = client.get_product('BTC-USD')
    btc_price = float(btc['price'])
    print(f"BTC: ${btc_price:.2f}")
    
    # Check each nuclear order
    filled_orders = []
    total_btc_to_buy = 0
    avg_sell_price = 0
    
    for order_id, details in nuclear_orders.items():
        try:
            order = client.get_order(order_id)
            
            # Access order details properly
            if hasattr(order, 'order'):
                status = order.order.status
                filled_size = float(order.order.filled_size) if hasattr(order.order, 'filled_size') else 0
                
                if filled_size > 0:
                    print(f"✅ FILLED: {filled_size:.8f} BTC @ ${details['price']:.2f}")
                    filled_orders.append(order_id)
                    total_btc_to_buy += filled_size
                    avg_sell_price += filled_size * details['price']
                elif status == 'OPEN':
                    distance = details['price'] - btc_price
                    print(f"⏳ Waiting: ${details['price']:.2f} (${distance:.2f} away)")
                    
        except Exception as e:
            print(f"Error checking {order_id[:8]}: {e}")
    
    # If we have filled orders, place exit buys
    if total_btc_to_buy > 0:
        avg_sell_price = avg_sell_price / total_btc_to_buy
        
        print(f"\n💥 NUCLEAR STRIKE SUCCESSFUL!")
        print(f"Sold {total_btc_to_buy:.8f} BTC @ avg ${avg_sell_price:.2f}")
        
        # Calculate profit targets
        target_1pct = avg_sell_price * 0.99  # 1% below sell
        target_15pct = avg_sell_price * 0.985  # 1.5% below
        
        print(f"\n🎯 PLACING EXIT ORDERS:")
        print(f"Target 1%: ${target_1pct:.2f}")
        print(f"Target 1.5%: ${target_15pct:.2f}")
        
        # Place buy orders to capture profit
        try:
            # First half at 1% profit
            buy1 = client.create_order(
                client_order_id=f"exit1_{int(time.time())}",
                product_id="BTC-USD",
                side="BUY",
                order_configuration={
                    "limit_limit_gtc": {
                        "post_only": True,
                        "limit_price": f"{target_1pct:.2f}",
                        "base_size": f"{total_btc_to_buy * 0.5:.8f}"
                    }
                }
            )
            print(f"✅ Buy order 1 placed at ${target_1pct:.2f}")
            
            # Second half at 1.5% profit
            buy2 = client.create_order(
                client_order_id=f"exit2_{int(time.time())}",
                product_id="BTC-USD",
                side="BUY",
                order_configuration={
                    "limit_limit_gtc": {
                        "post_only": True,
                        "limit_price": f"{target_15pct:.2f}",
                        "base_size": f"{total_btc_to_buy * 0.5:.8f}"
                    }
                }
            )
            print(f"✅ Buy order 2 placed at ${target_15pct:.2f}")
            
            # Calculate expected profit
            expected_profit = total_btc_to_buy * avg_sell_price * 0.0125  # 1.25% avg
            fees = total_btc_to_buy * avg_sell_price * 0.008  # 0.8% round trip
            net_profit = expected_profit - fees
            
            print(f"\n💰 EXPECTED PROFIT:")
            print(f"Gross: ${expected_profit:.2f}")
            print(f"Fees: ${fees:.2f}")
            print(f"NET: ${net_profit:.2f}")
            
            print("\n🎯 FLYWHEEL IGNITED! Momentum building...")
            break  # Exit loop after placing orders
            
        except Exception as e:
            print(f"Error placing exit orders: {e}")
    
    # Sleep and check again
    print("\n💤 Checking again in 30 seconds...")
    time.sleep(30)