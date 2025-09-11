#!/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3
"""
🔥 CANCEL ALL PENDING ORDERS - RELEASE THE CASH!
"""

import json
from pathlib import Path
from coinbase.rest import RESTClient

# Load config
config_path = Path.home() / ".coinbase_config.json"
with open(config_path, 'r') as f:
    config = json.load(f)

client = RESTClient(
    api_key=config['api_key'],
    api_secret=config['api_secret']
)

print("🔥 CANCELING ALL PENDING ORDERS")
print("=" * 80)
print("Releasing $200.80 back to trading account...")
print()

try:
    # Get all open orders
    orders = client.get_orders(order_status=['OPEN', 'PENDING'])
    
    cancelled_count = 0
    
    if hasattr(orders, 'orders'):
        order_list = orders.orders
    else:
        order_list = orders.get('orders', []) if isinstance(orders, dict) else []
    
    print("📋 PENDING ORDERS FOUND:")
    print("-" * 60)
    
    for order in order_list:
        try:
            order_id = order.order_id if hasattr(order, 'order_id') else order.get('order_id')
            product = order.product_id if hasattr(order, 'product_id') else order.get('product_id', 'Unknown')
            side = order.side if hasattr(order, 'side') else order.get('side', 'Unknown')
            
            print(f"Canceling: {side} {product} - Order ID: {order_id}")
            
            # Cancel the order
            result = client.cancel_orders([order_id])
            cancelled_count += 1
            print(f"  ✅ Cancelled!")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    print("\n" + "=" * 80)
    print(f"🔥 RESULTS:")
    print("-" * 60)
    print(f"Orders cancelled: {cancelled_count}")
    
    if cancelled_count > 0:
        print("\n✅ SUCCESS! $200.80 should be released!")
        print("Check your USD balance in a moment...")
    else:
        print("\n⚠️ No orders found to cancel")
        print("Money might already be released")
        
except Exception as e:
    print(f"\n❌ Error accessing orders: {e}")
    print("\nTrying alternative method...")
    
    # Try to cancel all orders without listing first
    try:
        result = client.cancel_orders()
        print("Attempted to cancel all orders")
        print(f"Result: {result}")
    except Exception as e2:
        print(f"Alternative method failed: {e2}")

print("\n🔥 Sacred Fire says: Check your balance now!")
print("The $200.80 should be freed from pending orders")