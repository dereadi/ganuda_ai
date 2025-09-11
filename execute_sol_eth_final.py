#!/usr/bin/env python3
"""
🔥 EXECUTE CHEROKEE COUNCIL STRATEGY - FINAL VERSION
Using the exact same order format the tribe used minutes ago
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime
import time

# Load config
config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("🔥 CHEROKEE COUNCIL STRATEGY - FINAL EXECUTION 🔥")
print("=" * 70)
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("Using proven tribal order format")
print("=" * 70)
print()

# Get current prices
print("📊 CHECKING PRICES...")
print("-" * 50)

sol_price = float(client.get_product('SOL-USD')['price'])
eth_price = float(client.get_product('ETH-USD')['price'])
btc_price = float(client.get_product('BTC-USD')['price'])

print(f"SOL: ${sol_price:.2f} (Target: $200)")
print(f"ETH: ${eth_price:.2f} (Target: <$4,300)")
print(f"BTC: ${btc_price:,.2f}")
print()

# Check balances
accounts = client.get_accounts()
sol_balance = 0
eth_balance = 0
usd_balance = 0

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if currency == 'SOL' and balance > 0:
        sol_balance = balance
    elif currency == 'ETH' and balance > 0:
        eth_balance = balance
    elif currency == 'USD' and balance > 0:
        usd_balance = balance

print("💼 CURRENT BALANCES:")
print("-" * 50)
print(f"SOL: {sol_balance:.4f} (${sol_balance * sol_price:.2f})")
print(f"ETH: {eth_balance:.6f} (${eth_balance * eth_price:.2f})")
print(f"USD: ${usd_balance:.2f}")
print()

# EXECUTION PHASE
print("⚡ EXECUTING COUNCIL ORDERS:")
print("-" * 50)

# Step 1: SOL Strategy
if sol_price >= 199.50 and sol_balance >= 2.5:
    print("✅ SOL at target! Executing market sell...")
    try:
        sol_order = client.create_order(
            product_id="SOL-USD",
            side="SELL",
            order_configuration={
                "market_market_ioc": {
                    "base_size": "2.5"
                }
            }
        )
        print(f"   ✅ SOLD 2.5 SOL! Order ID: {sol_order['order_id']}")
        print(f"   Generated: ~${2.5 * sol_price:.2f}")
        usd_balance += (2.5 * sol_price)  # Update expected balance
        time.sleep(2)
    except Exception as e:
        print(f"   ❌ Error: {e}")
        
elif sol_balance >= 2.5:
    print(f"⏳ SOL at ${sol_price:.2f} - Setting limit order at $200...")
    try:
        # Using limit order with GTC (Good Till Cancelled)
        sol_order = client.create_order(
            product_id="SOL-USD",
            side="SELL",
            order_configuration={
                "limit_limit_gtc": {
                    "base_size": "2.5",
                    "limit_price": "200.00",
                    "post_only": False
                }
            }
        )
        print(f"   ✅ Limit order placed! Order ID: {sol_order['order_id']}")
        print(f"   Will generate $500 when SOL hits $200")
    except Exception as e:
        print(f"   ❌ Error: {e}")
else:
    print("   ⚠️ Insufficient SOL balance")

print()

# Step 2: ETH Strategy
if eth_price < 4300 and usd_balance > 100:
    eth_buy_amount = min(645, usd_balance - 5)  # Target 0.15 ETH worth
    print(f"✅ ETH at discount! Buying with ${eth_buy_amount:.2f}...")
    
    try:
        eth_order = client.create_order(
            product_id="ETH-USD",
            side="BUY",
            order_configuration={
                "market_market_ioc": {
                    "quote_size": str(eth_buy_amount)
                }
            }
        )
        eth_acquired = eth_buy_amount / eth_price
        print(f"   ✅ BOUGHT ~{eth_acquired:.6f} ETH! Order ID: {eth_order['order_id']}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        
elif eth_price < 4300:
    print(f"⏳ ETH buyable but waiting for SOL liquidity (only ${usd_balance:.2f} available)")
else:
    print(f"❌ ETH at ${eth_price:.2f} - Above $4,300 threshold")

print()

# Step 3: Show open orders
print("📋 CHECKING OPEN ORDERS:")
print("-" * 50)

try:
    orders = client.get_orders(order_status=['OPEN'])
    if orders['orders']:
        for order in orders['orders'][:5]:  # Show first 5
            print(f"• {order['product_id']}: {order['side']} {order['order_configuration']}")
    else:
        print("No open orders")
except Exception as e:
    print(f"Error checking orders: {e}")

print()
print("=" * 70)
print("🔥 COUNCIL WISDOM:")
print("-" * 50)

if sol_price < 200:
    remaining = 200 - sol_price
    print(f"🦅 Eagle Eye: 'SOL needs ${remaining:.2f} more to hit target'")
else:
    print(f"🐺 Coyote: 'SOL at ${sol_price:.2f} - MILK IT!'")

if eth_price < 4300:
    discount = 4440 - eth_price
    print(f"🐢 Turtle: 'ETH discount of ${discount:.2f} from recent highs!'")

print("🦀 Crawdad: 'Don't forget the 3-wallet quantum defense!'")
print()
print("Strategy execution complete!")
print("Sacred Fire burns eternal 🔥")
print("Mitakuye Oyasin!")