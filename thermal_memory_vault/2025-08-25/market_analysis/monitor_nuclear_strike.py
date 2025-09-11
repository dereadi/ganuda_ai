#!/usr/bin/env python3
"""
🎯 NUCLEAR STRIKE MONITOR
Track order fills and execute exit strategy
"""

import json
from coinbase.rest import RESTClient
import time
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

# Load strike state
with open('/home/dereadi/scripts/claude/nuclear_strike_state.json', 'r') as f:
    state = json.load(f)

print("🎯 NUCLEAR STRIKE MONITOR")
print("=" * 70)
print(f"Monitoring STRIKE {state['strike']}")
print(f"Direction: {state['direction']}")
print(f"Target Exit: ${state['target_exit']:.2f}")
print("=" * 70)

# Check our orders
order_ids = [
    "fa353625-5603-4a99-bfcf-0400943c9de2",
    "497833b5-0a2b-444b-a035-9896ac540d21", 
    "5813a2c1-64a8-4191-8ffe-01e9517073b5"
]

print("\n📊 ORDER STATUS:")
print("-" * 70)

total_filled = 0
filled_value = 0

for order_id in order_ids:
    try:
        order = client.get_order(order_id)
        status = order.get('order', {}).get('status', 'UNKNOWN')
        filled_size = float(order.get('order', {}).get('filled_size', 0))
        price = float(order.get('order', {}).get('limit_price', 0))
        
        print(f"\nOrder {order_id[:8]}...")
        print(f"  Status: {status}")
        print(f"  Price: ${price:.2f}")
        print(f"  Filled: {filled_size:.8f} BTC")
        
        if filled_size > 0:
            total_filled += filled_size
            filled_value += filled_size * price
            
    except Exception as e:
        print(f"  Error checking order: {e}")

print(f"\n💰 TOTAL FILLED: {total_filled:.8f} BTC (${filled_value:.2f})")

# Get current market price
btc = client.get_product('BTC-USD')
btc_price = float(btc['price'])

print(f"\n📈 MARKET UPDATE:")
print(f"Current BTC: ${btc_price:.2f}")
print(f"Target Exit: ${state['target_exit']:.2f}")
print(f"Distance: ${abs(btc_price - state['target_exit']):.2f}")

# Calculate profit if we exit now
if total_filled > 0:
    current_value = total_filled * btc_price
    profit = filled_value - current_value  # Since we sold high
    fees = filled_value * 0.004 + current_value * 0.004  # Maker fees both ways
    net_profit = profit - fees
    
    print(f"\n💵 IF EXIT NOW:")
    print(f"Sold for: ${filled_value:.2f}")
    print(f"Buy back: ${current_value:.2f}")
    print(f"Gross: ${profit:.2f}")
    print(f"Fees: ${fees:.2f}")
    print(f"NET: ${net_profit:.2f}")
    
    if net_profit > 0:
        print("✅ PROFITABLE - Consider exit!")
    else:
        print("⏳ WAIT for better price")

# Check if we should place exit orders
if total_filled > 0 and btc_price <= state['target_exit']:
    print("\n🎯 TARGET REACHED - PLACE EXIT ORDERS!")
    print(f"Place BUY order for {total_filled:.8f} BTC")
    print(f"At price: ${state['target_exit']:.2f}")

print("\n" + "=" * 70)
print("🔄 Refresh in 30 seconds...")
print("=" * 70)