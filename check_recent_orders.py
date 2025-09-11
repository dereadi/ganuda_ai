#!/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3
"""
Check recent orders and balances
"""

import json
from datetime import datetime, timedelta
from coinbase.rest import RESTClient
import time

# Load API config
config = json.load(open('/home/dereadi/scripts/claude/cdp_api_key_new.json'))
client = RESTClient(
    api_key=config['name'].split('/')[-1],
    api_secret=config['privateKey'],
    timeout=10
)

print("🔍 CHECKING RECENT ACTIVITY")
print("=" * 70)

# Get recent orders
try:
    print("\n📋 RECENT ORDERS:")
    print("-" * 40)
    
    # Get orders from last hour
    orders = client.get_orders(
        order_status=['FILLED', 'PENDING', 'OPEN'],
        limit=10
    )
    
    if hasattr(orders, 'orders'):
        order_list = orders.orders
    else:
        order_list = orders.get('orders', [])
    
    for order in order_list[:5]:  # Show last 5 orders
        if hasattr(order, 'product_id'):
            product = order.product_id
            side = order.side if hasattr(order, 'side') else 'UNKNOWN'
            status = order.status if hasattr(order, 'status') else 'UNKNOWN'
            created = order.created_time if hasattr(order, 'created_time') else 'UNKNOWN'
            
            print(f"  {product} {side} - Status: {status}")
            print(f"  Created: {created}")
        print()
    
except Exception as e:
    print(f"  Error getting orders: {e}")

# Check all balances with holds
print("\n💰 CURRENT BALANCES (with holds):")
print("-" * 40)

response = client.get_accounts()
if hasattr(response, 'accounts'):
    accounts = response.accounts
else:
    accounts = response.get('accounts', response)

total_value = 0
for account in accounts:
    try:
        currency = account.currency if hasattr(account, 'currency') else 'UNKNOWN'
        
        # Get available
        if hasattr(account, 'available_balance'):
            if hasattr(account.available_balance, 'value'):
                available = float(account.available_balance.value)
            else:
                available = 0
        else:
            available = 0
        
        # Get hold
        hold = 0
        if hasattr(account, 'hold'):
            if hasattr(account.hold, 'value'):
                hold = float(account.hold.value)
        
        total = available + hold
        
        if total > 0.00001:
            print(f"\n{currency}:")
            print(f"  Available: {available:.8f}")
            if hold > 0:
                print(f"  On Hold: {hold:.8f}")
            print(f"  Total: {total:.8f}")
            
            # Get USD value
            if currency in ['USD', 'USDC']:
                usd_value = total
            else:
                try:
                    import requests
                    url = f"https://api.coinbase.com/v2/exchange-rates?currency={currency}"
                    resp = requests.get(url, timeout=5)
                    data = resp.json()
                    price = float(data['data']['rates']['USD'])
                    usd_value = total * price
                    print(f"  Value: ${usd_value:.2f}")
                except:
                    usd_value = 0
            
            total_value += usd_value
            
    except Exception as e:
        print(f"Error with account: {e}")

print("\n" + "=" * 70)
print(f"💎 TOTAL PORTFOLIO VALUE: ${total_value:.2f}")

# Check if orders went through
print("\n⚠️ IMPORTANT NOTES:")
print("  • Orders may take 5-10 seconds to settle")
print("  • USD from sells might be 'on hold' briefly")
print("  • Check again in 30 seconds if USD not showing")