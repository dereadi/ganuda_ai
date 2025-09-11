#!/usr/bin/env python3
"""
📊 REAL-TIME TRADING STATS MONITOR
"""
import json
import time
from datetime import datetime
from coinbase.rest import RESTClient

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                     📊 LIVE TRADING STATISTICS 📊                          ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

# Load API
with open('cdp_api_key_new.json', 'r') as f:
    api_data = json.load(f)

client = RESTClient(
    api_key=api_data['name'].split('/')[-1],
    api_secret=api_data['privateKey']
)

# Track initial state
start_time = datetime.now()
accounts = client.get_accounts()['accounts']
initial_usd = 0
for account in accounts:
    if account['currency'] == 'USD':
        initial_usd = float(account['available_balance']['value'])
        break

print(f"⏰ Start Time: {start_time.strftime('%I:%M %p')}")
print(f"💵 Starting USD: ${initial_usd:,.2f}")
print("=" * 60)

# Monitor for 30 seconds
trades_seen = []
for i in range(6):  # Check every 5 seconds for 30 seconds
    time.sleep(5)
    
    # Check orders
    try:
        orders = client.get_orders(order_status=['FILLED'])
        recent_fills = orders.get('orders', [])[:10]
        
        for order in recent_fills:
            order_id = order.get('order_id')
            if order_id not in trades_seen:
                trades_seen.append(order_id)
                print(f"\n🔄 NEW TRADE DETECTED!")
                print(f"  Type: {order['side']}")
                print(f"  Pair: {order['product_id']}")
                print(f"  Size: {order.get('filled_size', 'N/A')}")
                print(f"  Price: ${order.get('average_filled_price', 'N/A')}")
                print(f"  Time: {order.get('created_time', 'N/A')[:19]}")
    except:
        pass
    
    # Check balance change
    accounts = client.get_accounts()['accounts']
    current_usd = 0
    for account in accounts:
        if account['currency'] == 'USD':
            current_usd = float(account['available_balance']['value'])
            break
    
    change = current_usd - initial_usd
    if abs(change) > 0.01:
        print(f"\n💰 USD CHANGE: ${change:+.2f} (Now: ${current_usd:,.2f})")

# Final stats
print("\n" + "=" * 60)
print("📈 30-SECOND SUMMARY:")
print(f"  Trades Captured: {len(trades_seen)}")
print(f"  USD Change: ${(current_usd - initial_usd):+.2f}")
print(f"  Final USD: ${current_usd:,.2f}")

if len(trades_seen) == 0:
    print("\n⚠️ NO TRADES DETECTED!")
    print("Possible issues:")
    print("  • Minimum order sizes not met")
    print("  • API authentication issues")
    print("  • Network/connection problems")
else:
    print(f"\n✅ TRADING ACTIVE! {len(trades_seen)} trades in 30 seconds")