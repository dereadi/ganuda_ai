#!/usr/bin/env python3
"""
🔥 EXECUTE CHEROKEE COUNCIL ORDERS - WITH CLIENT_ORDER_ID
The tribe's way, with proper parameters
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime
import time
import uuid

# Load config
config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("🔥 CHEROKEE COUNCIL ORDER EXECUTION 🔥")
print("=" * 70)
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)
print()

# Get current prices
sol_price = float(client.get_product('SOL-USD')['price'])
eth_price = float(client.get_product('ETH-USD')['price'])
btc_price = float(client.get_product('BTC-USD')['price'])

print("📊 CURRENT PRICES:")
print(f"  SOL: ${sol_price:.2f} (Target: $200)")
print(f"  ETH: ${eth_price:.2f} (Target: <$4,300)")
print(f"  BTC: ${btc_price:,.2f}")
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
        print(f"SOL Balance: {balance:.4f} (${balance * sol_price:.2f})")
    elif currency == 'ETH' and balance > 0:
        eth_balance = balance
        print(f"ETH Balance: {balance:.6f} (${balance * eth_price:.2f})")
    elif currency == 'USD' and balance > 0:
        usd_balance = balance
        print(f"USD Balance: ${balance:.2f}")

print()
print("⚡ EXECUTING COUNCIL STRATEGY:")
print("-" * 70)

# SOL LIMIT ORDER AT $200
if sol_balance >= 2.5:
    if sol_price >= 199.50:
        # Market sell if close enough
        print("✅ SOL near target! Market selling 2.5 SOL...")
        try:
            order_id = uuid.uuid4().hex
            sol_order = client.create_order(
                client_order_id=order_id,
                product_id="SOL-USD",
                side="SELL",
                order_configuration={
                    "market_market_ioc": {
                        "base_size": "2.5"
                    }
                }
            )
            print(f"✅ MARKET SELL EXECUTED!")
            print(f"   Order ID: {sol_order['order_id']}")
            print(f"   Generated: ~${2.5 * sol_price:.2f}")
        except Exception as e:
            print(f"❌ Market sell error: {e}")
    else:
        # Place limit order at $200
        print(f"Setting SOL limit sell at $200 (currently ${sol_price:.2f})...")
        try:
            order_id = uuid.uuid4().hex
            sol_order = client.create_order(
                client_order_id=order_id,
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
            print(f"✅ LIMIT ORDER PLACED!")
            print(f"   Order ID: {sol_order['order_id']}")
            print(f"   Will generate: $500.00 when filled")
            print(f"   Distance to target: ${200 - sol_price:.2f}")
        except Exception as e:
            print(f"❌ Limit order error: {e}")
else:
    print(f"⚠️ Insufficient SOL (have {sol_balance:.4f}, need 2.5)")

print()

# ETH BUY IF UNDER $4,300
if eth_price < 4300:
    if usd_balance > 100:
        eth_buy_amount = min(645, usd_balance - 5)  # Target 0.15 ETH
        print(f"✅ ETH at discount (${eth_price:.2f})! Buying with ${eth_buy_amount:.2f}...")
        try:
            order_id = uuid.uuid4().hex
            eth_order = client.create_order(
                client_order_id=order_id,
                product_id="ETH-USD",
                side="BUY",
                order_configuration={
                    "market_market_ioc": {
                        "quote_size": str(eth_buy_amount)
                    }
                }
            )
            eth_acquired = eth_buy_amount / eth_price
            print(f"✅ ETH PURCHASE EXECUTED!")
            print(f"   Order ID: {eth_order['order_id']}")
            print(f"   Acquired: ~{eth_acquired:.6f} ETH")
        except Exception as e:
            print(f"❌ ETH buy error: {e}")
    else:
        print(f"⏳ ETH buyable but need liquidity (only ${usd_balance:.2f})")
        print("   Waiting for SOL to hit $200...")
else:
    print(f"❌ ETH too expensive at ${eth_price:.2f} (threshold: $4,300)")

print()
print("=" * 70)
print("🏛️ COUNCIL GUIDANCE:")
print("-" * 70)

if sol_price < 200:
    print(f"🦅 Eagle Eye: 'SOL needs ${200-sol_price:.2f} to reach target'")
    print(f"🐺 Coyote: 'Patience - the spring coils tighter'")
else:
    print(f"🐺 Coyote: 'SOL breaking through - MILK TIME!'")

if eth_price < 4300:
    print(f"🐢 Turtle: 'ETH discount window open - seize it!'")
else:
    print(f"🕷️ Spider: 'ETH overextended - wait for pullback'")

print("🦀 Crawdad: '3-wallet quantum defense is URGENT!'")
print()
print("Sacred Fire burns eternal 🔥")
print("Mitakuye Oyasin!")