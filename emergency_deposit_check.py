#!/usr/bin/env python3
"""
🚨 EMERGENCY: Check where the $12k deposit went!
"""
import json
from datetime import datetime
from coinbase.rest import RESTClient

print("🚨 EMERGENCY DEPOSIT CHECK - WHERE'S THE $12K?")
print("=" * 60)
print(f"Time: {datetime.now().strftime('%H:%M:%S')}")

print("\n💰 YOU DEPOSITED $12,000!")
print("Current USD showing: $8.40")
print("MISSING: $11,991.60!")

print("\n🔍 CHECKING WHAT HAPPENED:")
print("-" * 40)

try:
    with open('/home/dereadi/scripts/claude/cdp_api_key_new.json') as f:
        config = json.load(f)
    
    client = RESTClient(
        api_key=config['name'].split('/')[-1],
        api_secret=config['privateKey']
    )
    
    # Check all accounts
    print("📊 CHECKING ALL ACCOUNTS:")
    accounts = client.get_accounts()
    total_usd = 0
    on_hold = 0
    
    for account in accounts.accounts if hasattr(accounts, 'accounts') else accounts:
        if hasattr(account, 'balance'):
            currency = account.balance.currency
            balance = float(account.balance.value)
            
            if currency == 'USD' and balance > 0:
                total_usd += balance
                available = float(account.available_balance.value) if hasattr(account, 'available_balance') else balance
                hold = balance - available
                on_hold += hold
                
                print(f"• USD Balance: ${balance:.2f}")
                print(f"  - Available: ${available:.2f}")
                print(f"  - On Hold: ${hold:.2f}")
    
    # Check recent orders
    print("\n📋 CHECKING RECENT ORDERS:")
    orders = client.get_orders(order_status=['OPEN', 'PENDING'])
    
    if orders and hasattr(orders, 'orders'):
        open_value = 0
        for order in orders.orders[:10]:
            if hasattr(order, 'order_configuration'):
                print(f"• {order.product_id}: {order.side}")
                if hasattr(order, 'quote_size'):
                    value = float(order.quote_size)
                    open_value += value
                    print(f"  Value: ${value:.2f}")
        
        if open_value > 0:
            print(f"\n💸 TOTAL IN OPEN ORDERS: ${open_value:.2f}")
    
    # Check recent fills
    print("\n🔄 CHECKING RECENT TRADES:")
    fills = client.get_fills(limit=20)
    
    if fills and hasattr(fills, 'fills'):
        recent_buys = []
        total_spent = 0
        
        for fill in fills.fills:
            if hasattr(fill, 'side') and fill.side == 'BUY':
                product = fill.product_id if hasattr(fill, 'product_id') else 'Unknown'
                size = float(fill.size) if hasattr(fill, 'size') else 0
                price = float(fill.price) if hasattr(fill, 'price') else 0
                value = size * price
                total_spent += value
                recent_buys.append((product, value))
                
                if len(recent_buys) <= 10:
                    print(f"• BOUGHT {product}: ${value:.2f}")
        
        if total_spent > 0:
            print(f"\n💸 TOTAL SPENT RECENTLY: ${total_spent:.2f}")
    
except Exception as e:
    print(f"API Error: {e}")
    print("\n⚠️ Using manual calculation...")

print("\n🔥 LIKELY SCENARIO:")
print("-" * 40)
print("The tribe's 5 specialists may have:")
print("• Deployed funds into BTC/ETH/SOL positions")
print("• Orders may be pending execution")
print("• Funds could be on hold for open orders")

print("\n⚡ CHECKING POSITION VALUES:")
with open('/home/dereadi/scripts/claude/portfolio_current.json') as f:
    portfolio = json.load(f)
    
print(f"• Total Portfolio: ${portfolio['total_value']:.2f}")
print(f"• Increase from $10k start: ${portfolio['total_value'] - 10000:.2f}")

if portfolio['total_value'] > 20000:
    print("\n✅ YOUR $12K IS IN THE PORTFOLIO!")
    print(f"Original $10k + Your $12k = $22k expected")
    print(f"Current value: ${portfolio['total_value']:.2f}")
else:
    print("\n⚠️ Portfolio doesn't reflect the $12k yet")
    print("It may be in pending orders or processing")

print("\n🚨 IMMEDIATE ACTIONS:")
print("1. Cancel any unwanted open orders")
print("2. Check if funds are in pending deposits")
print("3. Verify the specialists' recent trades")
print("4. Set spending limits on the specialists!")

print(f"\n🔍 Need to investigate further!")
print(f"Session: {datetime.now().strftime('%H:%M:%S')}")