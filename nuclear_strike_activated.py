#!/usr/bin/env python3
"""
💥 NUCLEAR STRIKE ACTIVATED - BTC HIT $110,000!
Check fills and execute profit taking
"""

import json
from coinbase.rest import RESTClient
import time
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("💥💥💥 NUCLEAR STRIKE ACTIVATED 💥💥💥")
print("=" * 70)
print("BTC CROSSED $110,000 - CHECKING FILLS!")
print("=" * 70)

# Get current price
btc = client.get_product('BTC-USD')
btc_price = float(btc['price'])
print(f"\nCurrent BTC: ${btc_price:,.2f}")

# Check our nuclear orders
print("\n🎯 CHECKING NUCLEAR STRIKE FILLS:")
print("-" * 70)

nuclear_orders = {
    "fa353625-5603-4a99-bfcf-0400943c9de2": {"price": 109921.90, "size": 0.00276674},
    "497833b5-0a2b-444b-a035-9896ac540d21": {"price": 110251.01, "size": 0.00276674},
    "5813a2c1-64a8-4191-8ffe-01e9517073b5": {"price": 110580.12, "size": 0.00368899}
}

total_filled = 0
total_proceeds = 0

for order_id, details in nuclear_orders.items():
    try:
        order = client.get_order(order_id)
        
        if hasattr(order, 'order'):
            status = order.order.status
            filled_size = float(order.order.filled_size) if hasattr(order.order, 'filled_size') else 0
            
            if filled_size > 0:
                proceeds = filled_size * details['price']
                print(f"✅ FILLED: {filled_size:.8f} BTC @ ${details['price']:.2f} = ${proceeds:.2f}")
                total_filled += filled_size
                total_proceeds += proceeds
            elif btc_price > details['price']:
                print(f"🔄 SHOULD BE FILLED: ${details['price']:.2f} (checking...)")
            else:
                print(f"⏳ Waiting: ${details['price']:.2f}")
                
    except Exception as e:
        print(f"Error checking {order_id[:8]}: {e}")

print(f"\n💰 TOTAL FILLED: {total_filled:.8f} BTC")
print(f"💵 PROCEEDS: ${total_proceeds:.2f}")

# If we have fills, place profit-taking buy orders
if total_filled > 0:
    print("\n🎯 EXECUTING PROFIT TAKING:")
    print("-" * 70)
    
    avg_sell_price = total_proceeds / total_filled
    print(f"Average sell price: ${avg_sell_price:.2f}")
    
    # Calculate buy targets
    target_1pct = avg_sell_price * 0.99
    target_15pct = avg_sell_price * 0.985
    target_2pct = avg_sell_price * 0.98
    
    print(f"\n🎯 PROFIT TARGETS:")
    print(f"1% profit: ${target_1pct:.2f}")
    print(f"1.5% profit: ${target_15pct:.2f}")
    print(f"2% profit: ${target_2pct:.2f}")
    
    # Place buy orders
    try:
        # First third at 1%
        order1 = client.create_order(
            client_order_id=f"profit_1pct_{int(time.time())}",
            product_id="BTC-USD",
            side="BUY",
            order_configuration={
                "limit_limit_gtc": {
                    "post_only": True,
                    "limit_price": f"{target_1pct:.2f}",
                    "base_size": f"{total_filled * 0.33:.8f}"
                }
            }
        )
        print(f"✅ Buy order placed at ${target_1pct:.2f}")
        
        # Second third at 1.5%
        order2 = client.create_order(
            client_order_id=f"profit_15pct_{int(time.time())}",
            product_id="BTC-USD",
            side="BUY",
            order_configuration={
                "limit_limit_gtc": {
                    "post_only": True,
                    "limit_price": f"{target_15pct:.2f}",
                    "base_size": f"{total_filled * 0.33:.8f}"
                }
            }
        )
        print(f"✅ Buy order placed at ${target_15pct:.2f}")
        
        # Final third at 2%
        order3 = client.create_order(
            client_order_id=f"profit_2pct_{int(time.time())}",
            product_id="BTC-USD",
            side="BUY",
            order_configuration={
                "limit_limit_gtc": {
                    "post_only": True,
                    "limit_price": f"{target_2pct:.2f}",
                    "base_size": f"{total_filled * 0.34:.8f}"
                }
            }
        )
        print(f"✅ Buy order placed at ${target_2pct:.2f}")
        
        # Calculate expected profit
        expected_profit = total_proceeds * 0.015  # 1.5% average
        fees = total_proceeds * 0.008  # 0.8% round trip
        net_profit = expected_profit - fees
        
        print(f"\n💰 PROFIT PROJECTION:")
        print(f"Gross: ${expected_profit:.2f}")
        print(f"Fees: ${fees:.2f}")
        print(f"NET: ${net_profit:.2f}")
        
        print("\n🔥 FLYWHEEL SPINNING!")
        print("Nuclear Strike ONE successful!")
        print("Momentum building for Strike TWO!")
        
    except Exception as e:
        print(f"Error placing profit orders: {e}")
        
else:
    print("\n⏳ Orders may still be processing...")
    print("Run again in a moment to confirm fills")

# Check account balances
print("\n💎 ACCOUNT STATUS:")
print("-" * 70)
accounts = client.get_accounts()
for acc in accounts['accounts']:
    if acc['currency'] in ['BTC', 'ETH', 'USD', 'USDC']:
        available = float(acc['available_balance']['value'])
        if available > 0.001 or acc['currency'] in ['USD', 'USDC']:
            print(f"{acc['currency']}: {available:.8f}")

print("\n" + "=" * 70)
print("🔥 THE FLYWHEEL TURNS!")
print("=" * 70)