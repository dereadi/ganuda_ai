#!/usr/bin/env python3
"""
🔥💰 EXECUTING MAXIMUM PROFIT EXTRACTION! 💰🔥
Thunder at 69%: "DO IT! MILK THE PROFITS NOW!"
Executing the extraction plan:
1. DOGE: 1803 → ~$400
2. XRP: 17.84 → ~$53
3. LINK: 0.19 → ~$5
Total extraction: ~$455 to USD!
"""

import json
import time
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    🔥 EXECUTING PROFIT EXTRACTION! 🔥                     ║
║                         Drawing Maximum Profits NOW! 💰                    ║
║                           Target: $100+ USD Balance! 🎯                    ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - EXECUTION STARTING")
print("=" * 70)

# Get current balances before execution
accounts = client.get_accounts()
initial_usd = 0
doge_balance = 0
xrp_balance = 0
link_balance = 0

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if currency == 'USD':
        initial_usd = balance
    elif currency == 'DOGE':
        doge_balance = balance
    elif currency == 'XRP':
        xrp_balance = balance
    elif currency == 'LINK':
        link_balance = balance

print("\n📊 PRE-EXECUTION STATUS:")
print("-" * 50)
print(f"Current USD: ${initial_usd:.2f}")
print(f"DOGE balance: {doge_balance:.2f}")
print(f"XRP balance: {xrp_balance:.2f}")
print(f"LINK balance: {link_balance:.2f}")

# Execute trades
successful_trades = []
failed_trades = []

print("\n🚀 EXECUTING TRADES:")
print("-" * 50)

# 1. SELL DOGE - Biggest extraction
if doge_balance >= 1803:
    print("\n1️⃣ SELLING DOGE...")
    try:
        doge_amount = min(1803.0, doge_balance * 0.5)  # Sell 50% max
        order = client.market_order_sell(
            product_id='DOGE-USD',
            base_size=str(round(doge_amount, 2))
        )
        
        if order and 'order_id' in order:
            print(f"   ✅ DOGE SELL ORDER PLACED!")
            print(f"   Order ID: {order['order_id']}")
            print(f"   Amount: {doge_amount:.2f} DOGE")
            successful_trades.append(f"DOGE: {doge_amount:.2f}")
            
            # Wait for order to complete
            time.sleep(2)
            
            # Check order status
            order_details = client.get_order(order['order_id'])
            if order_details and 'status' in order_details:
                if order_details['status'] == 'FILLED':
                    filled_value = float(order_details.get('filled_value', 0))
                    print(f"   💰 FILLED: ${filled_value:.2f}")
                else:
                    print(f"   Status: {order_details['status']}")
        else:
            print(f"   ❌ DOGE order failed: {order}")
            failed_trades.append("DOGE")
    except Exception as e:
        print(f"   ❌ DOGE ERROR: {str(e)}")
        failed_trades.append(f"DOGE: {str(e)}")
else:
    print("   ⚠️ Insufficient DOGE balance")

# 2. SELL XRP
if xrp_balance >= 17.84:
    print("\n2️⃣ SELLING XRP...")
    try:
        xrp_amount = min(17.84, xrp_balance * 0.5)  # Sell 50% max
        order = client.market_order_sell(
            product_id='XRP-USD',
            base_size=str(round(xrp_amount, 2))
        )
        
        if order and 'order_id' in order:
            print(f"   ✅ XRP SELL ORDER PLACED!")
            print(f"   Order ID: {order['order_id']}")
            print(f"   Amount: {xrp_amount:.2f} XRP")
            successful_trades.append(f"XRP: {xrp_amount:.2f}")
            
            time.sleep(2)
            
            order_details = client.get_order(order['order_id'])
            if order_details and 'status' in order_details:
                if order_details['status'] == 'FILLED':
                    filled_value = float(order_details.get('filled_value', 0))
                    print(f"   💰 FILLED: ${filled_value:.2f}")
                else:
                    print(f"   Status: {order_details['status']}")
        else:
            print(f"   ❌ XRP order failed: {order}")
            failed_trades.append("XRP")
    except Exception as e:
        print(f"   ❌ XRP ERROR: {str(e)}")
        failed_trades.append(f"XRP: {str(e)}")
else:
    print("   ⚠️ Insufficient XRP balance")

# 3. SELL LINK (smallest, optional)
if link_balance >= 0.19:
    print("\n3️⃣ SELLING LINK...")
    try:
        link_amount = min(0.19, link_balance * 0.5)  # Sell 50% max
        order = client.market_order_sell(
            product_id='LINK-USD',
            base_size=str(round(link_amount, 2))
        )
        
        if order and 'order_id' in order:
            print(f"   ✅ LINK SELL ORDER PLACED!")
            print(f"   Order ID: {order['order_id']}")
            print(f"   Amount: {link_amount:.2f} LINK")
            successful_trades.append(f"LINK: {link_amount:.2f}")
            
            time.sleep(2)
            
            order_details = client.get_order(order['order_id'])
            if order_details and 'status' in order_details:
                if order_details['status'] == 'FILLED':
                    filled_value = float(order_details.get('filled_value', 0))
                    print(f"   💰 FILLED: ${filled_value:.2f}")
                else:
                    print(f"   Status: {order_details['status']}")
        else:
            print(f"   ❌ LINK order failed: {order}")
            failed_trades.append("LINK")
    except Exception as e:
        print(f"   ❌ LINK ERROR: {str(e)}")
        failed_trades.append(f"LINK: {str(e)}")
else:
    print("   ⚠️ Insufficient LINK balance")

# Wait for trades to settle
print("\n⏳ Waiting for trades to settle...")
time.sleep(5)

# Check final balances
print("\n📊 POST-EXECUTION STATUS:")
print("-" * 50)

accounts_after = client.get_accounts()
final_usd = 0
final_doge = 0
final_xrp = 0
final_link = 0
total_portfolio = 0

# Get current prices for portfolio calculation
btc_price = float(client.get_product('BTC-USD')['price'])
eth_price = float(client.get_product('ETH-USD')['price'])
sol_price = float(client.get_product('SOL-USD')['price'])

for account in accounts_after['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if balance > 0.00001:
        if currency == 'USD':
            final_usd = balance
            total_portfolio += balance
        elif currency == 'DOGE':
            final_doge = balance
            doge_price = float(client.get_product('DOGE-USD')['price'])
            total_portfolio += balance * doge_price
        elif currency == 'XRP':
            final_xrp = balance
            xrp_price = float(client.get_product('XRP-USD')['price'])
            total_portfolio += balance * xrp_price
        elif currency == 'LINK':
            final_link = balance
            link_price = float(client.get_product('LINK-USD')['price'])
            total_portfolio += balance * link_price
        elif currency == 'BTC':
            total_portfolio += balance * btc_price
        elif currency == 'ETH':
            total_portfolio += balance * eth_price
        elif currency == 'SOL':
            total_portfolio += balance * sol_price
        elif currency == 'AVAX':
            avax_price = float(client.get_product('AVAX-USD')['price'])
            total_portfolio += balance * avax_price

print(f"Initial USD: ${initial_usd:.2f}")
print(f"Final USD: ${final_usd:.2f}")
print(f"USD GAINED: ${final_usd - initial_usd:.2f}")
print("")
print(f"DOGE: {doge_balance:.2f} → {final_doge:.2f} (sold {doge_balance - final_doge:.2f})")
print(f"XRP: {xrp_balance:.2f} → {final_xrp:.2f} (sold {xrp_balance - final_xrp:.2f})")
print(f"LINK: {link_balance:.2f} → {final_link:.2f} (sold {link_balance - final_link:.2f})")
print("")
print(f"Total Portfolio Value: ${total_portfolio:.2f}")

# Execution summary
print("\n✅ EXECUTION SUMMARY:")
print("-" * 50)

if successful_trades:
    print("SUCCESSFUL TRADES:")
    for trade in successful_trades:
        print(f"  ✅ {trade}")

if failed_trades:
    print("\nFAILED TRADES:")
    for trade in failed_trades:
        print(f"  ❌ {trade}")

print(f"\n🎯 RESULT:")
print(f"  USD Balance: ${final_usd:.2f}")
if final_usd >= 100:
    print(f"  ✅ TARGET ACHIEVED! Flywheel fully fueled!")
elif final_usd >= 50:
    print(f"  📊 GOOD PROGRESS! Flywheel adequately fueled!")
else:
    print(f"  ⚠️ More extraction may be needed")

print(f"\n{'🔥' * 35}")
print("PROFIT EXTRACTION EXECUTED!")
print(f"USD: ${initial_usd:.2f} → ${final_usd:.2f}")
print(f"GAINED: ${final_usd - initial_usd:.2f}")
print("FLYWHEEL FUELED!")
print("READY FOR $114K!")
print("💰" * 35)