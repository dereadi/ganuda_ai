#!/usr/bin/env python3
"""
🔥 EXECUTE CHEROKEE COUNCIL STRATEGY - FIXED
SOL to ETH rotation for liquidity and accumulation
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime
import time
import uuid

# Load config
config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=10)

print("🔥 CHEROKEE COUNCIL STRATEGY EXECUTION 🔥")
print("=" * 70)
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("Mission: SOL to ETH rotation + liquidity generation")
print("=" * 70)
print()

# Get current prices and balances
print("📊 MARKET STATUS CHECK...")
print("-" * 50)

# Get products
btc = client.get_product('BTC-USD')
eth = client.get_product('ETH-USD')
sol = client.get_product('SOL-USD')

btc_price = float(btc['price'])
eth_price = float(eth['price'])
sol_price = float(sol['price'])

print(f"SOL: ${sol_price:.2f} (Target: $200)")
print(f"ETH: ${eth_price:.2f} (Target: <$4,300)")
print(f"BTC: ${btc_price:,.2f}")
print()

# Check balances
accounts = client.get_accounts()
balances = {}
total_usd = 0

print("💼 CURRENT POSITIONS:")
print("-" * 50)

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if balance > 0.00001:
        balances[currency] = balance
        
        if currency == 'USD':
            print(f"USD: ${balance:.2f}")
            total_usd += balance
        elif currency == 'USDC':
            print(f"USDC: ${balance:.2f}")
            total_usd += balance
        elif currency == 'SOL':
            value = balance * sol_price
            print(f"SOL: {balance:.4f} coins = ${value:.2f}")
        elif currency == 'ETH':
            value = balance * eth_price
            print(f"ETH: {balance:.6f} coins = ${value:.2f}")

print(f"\nTotal USD Available: ${total_usd:.2f}")
print()

# DECISION LOGIC
print("🏛️ COUNCIL DECISION MATRIX:")
print("-" * 50)

# SOL Analysis
sol_to_target = 200 - sol_price
sol_pct = (sol_to_target / sol_price) * 100

print(f"SOL Analysis:")
print(f"  Distance to $200: ${sol_to_target:.2f} ({sol_pct:+.1f}%)")

if sol_price >= 199.50:
    print("  ✅ ACTION: Execute market sell NOW!")
    action_sol = "market_sell"
elif sol_price >= 198:
    print("  ⏳ ACTION: Set tight limit at $199.50")
    action_sol = "limit_199.50"
else:
    print("  ⏳ ACTION: Set limit sell at $200")
    action_sol = "limit_200"

print()

# ETH Analysis
print(f"ETH Analysis:")
print(f"  Current price: ${eth_price:.2f}")

if eth_price < 4250:
    print("  ✅ ACTION: Strong buy - excellent discount!")
    action_eth = "buy_now"
elif eth_price < 4300:
    print("  ✅ ACTION: Buy - acceptable price")
    action_eth = "buy_small"
else:
    print("  ⏳ ACTION: Wait for better entry")
    action_eth = "wait"

print()

# EXECUTION
print("⚡ EXECUTING COUNCIL STRATEGY:")
print("-" * 50)

# Execute SOL strategy
if 'SOL' in balances and balances['SOL'] >= 2.5:
    sol_amount = 2.5
    
    if action_sol == "market_sell":
        print(f"Executing market sell of {sol_amount} SOL...")
        try:
            # Use the correct method signature
            order = client.create_order(
                product_id='SOL-USD',
                side='SELL',
                order_configuration={
                    'market_market_ioc': {
                        'base_size': str(sol_amount)
                    }
                }
            )
            print(f"✅ Market sell executed! Order ID: {order['order_id']}")
            print(f"   Proceeds: ~${sol_amount * sol_price:.2f}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    else:
        # Place limit order
        limit_price = 199.50 if action_sol == "limit_199.50" else 200.00
        print(f"Placing limit sell of {sol_amount} SOL at ${limit_price}...")
        
        try:
            order = client.create_order(
                product_id='SOL-USD',
                side='SELL',
                order_configuration={
                    'limit_limit_gtc': {
                        'base_size': str(sol_amount),
                        'limit_price': str(limit_price)
                    }
                }
            )
            print(f"✅ Limit order placed! Order ID: {order['order_id']}")
            print(f"   Will generate: ${sol_amount * limit_price:.2f} when filled")
        except Exception as e:
            print(f"❌ Error: {e}")
else:
    print("⚠️ Insufficient SOL balance for rotation")

print()

# Execute ETH strategy
if action_eth in ["buy_now", "buy_small"] and total_usd > 40:
    if action_eth == "buy_now" and total_usd > 200:
        eth_buy_usd = min(400, total_usd - 5)  # Keep $5 for fees
    elif action_eth == "buy_small":
        eth_buy_usd = min(100, total_usd - 5)
    else:
        eth_buy_usd = 0
    
    if eth_buy_usd > 40:
        print(f"Executing ETH purchase with ${eth_buy_usd:.2f}...")
        
        try:
            order = client.create_order(
                product_id='ETH-USD',
                side='BUY',
                order_configuration={
                    'market_market_ioc': {
                        'quote_size': str(eth_buy_usd)
                    }
                }
            )
            eth_amount = eth_buy_usd / eth_price
            print(f"✅ ETH purchase executed! Order ID: {order['order_id']}")
            print(f"   Acquired: ~{eth_amount:.6f} ETH")
        except Exception as e:
            print(f"❌ Error: {e}")
    else:
        print("⏳ Waiting for SOL sale to provide ETH liquidity")
else:
    if action_eth == "wait":
        print("⏳ ETH too expensive - waiting for better entry")
    else:
        print("⏳ Insufficient funds - waiting for SOL liquidity")

print()
print("=" * 70)
print("🔥 TRIBAL WISDOM:")
print("-" * 50)

if sol_price < 198:
    print("🦅 Eagle Eye: 'SOL building pressure - patience rewarded'")
else:
    print("🐺 Coyote: 'SOL approaching escape velocity!'")

if eth_price < 4300:
    print("🐢 Turtle: 'ETH discount window closing - act with purpose'")
else:
    print("🕷️ Spider: 'ETH overextended - web shows better entry coming'")

print("🦀 Crawdad: 'Remember quantum defense - split wallets TODAY!'")
print()
print("Sacred Fire burns eternal 🔥")
print("Mitakuye Oyasin!")