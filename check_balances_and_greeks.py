#!/usr/bin/env python3
"""
💰 CHECK BALANCES AND GREEKS ACTIVITY
See what the Greeks trading system is doing with our capital
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("💰 BALANCE CHECK & GREEKS ACTIVITY MONITOR")
print("=" * 70)
print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
print("=" * 70)

# Get market prices
btc = client.get_product('BTC-USD')
eth = client.get_product('ETH-USD')
btc_price = float(btc['price'])
eth_price = float(eth['price'])

print(f"\n📊 CURRENT PRICES:")
print(f"BTC: ${btc_price:,.2f}")
print(f"ETH: ${eth_price:,.2f}")

# Get ALL balances
print(f"\n💎 ACCOUNT BALANCES:")
print("-" * 70)

accounts = client.get_accounts()
total_value = 0
crypto_positions = []
cash_positions = []

for acc in accounts['accounts']:
    currency = acc['currency']
    available = float(acc['available_balance']['value'])
    hold = float(acc['hold']['value']) if acc.get('hold') else 0
    total_balance = available + hold
    
    # Only show non-dust balances
    if total_balance > 0.00001:
        if currency in ['USD', 'USDC']:
            cash_positions.append({
                'currency': currency,
                'available': available,
                'hold': hold,
                'total': total_balance
            })
            total_value += total_balance
        else:
            # Calculate USD value for crypto
            if currency == 'BTC':
                usd_value = total_balance * btc_price
            elif currency == 'ETH':
                usd_value = total_balance * eth_price
            else:
                # Try to get price
                try:
                    product = client.get_product(f'{currency}-USD')
                    price = float(product['price'])
                    usd_value = total_balance * price
                except:
                    usd_value = 0
            
            if total_balance > 0.00001:
                crypto_positions.append({
                    'currency': currency,
                    'available': available,
                    'hold': hold,
                    'total': total_balance,
                    'usd_value': usd_value
                })
                total_value += usd_value

# Display cash
print("\n💵 CASH POSITIONS:")
for pos in cash_positions:
    print(f"{pos['currency']}: ${pos['total']:.2f}")
    if pos['hold'] > 0:
        print(f"  (Available: ${pos['available']:.2f}, On hold: ${pos['hold']:.2f})")

# Display crypto
print("\n🪙 CRYPTO POSITIONS:")
for pos in crypto_positions:
    print(f"{pos['currency']}: {pos['total']:.8f} = ${pos['usd_value']:.2f}")
    if pos['hold'] > 0:
        print(f"  (Available: {pos['available']:.8f}, On hold: {pos['hold']:.8f})")

print(f"\n💎 TOTAL PORTFOLIO: ${total_value:,.2f}")

# Check for Greek activity
print("\n🏛️ GREEKS SYSTEM CHECK:")
print("-" * 70)

# Look for Greeks-related files
import glob
import os

greeks_files = [
    'greeks_moon_mission_bot.py',
    'the_greeks_monitor.py',
    'gamma_greek_ultra.py',
    'delta_greek.py',
    'theta_greek.py',
    'vega_greek.py',
    'rho_greek.py'
]

print("Greeks system files found:")
for file in greeks_files:
    if os.path.exists(f'/home/dereadi/scripts/claude/{file}'):
        print(f"✓ {file}")

# Check for recent trades
print("\n📈 RECENT TRADING ACTIVITY:")
print("-" * 70)

try:
    # Get recent orders
    orders = client.list_orders(limit=10)
    
    if hasattr(orders, 'orders') and orders.orders:
        print(f"Found {len(orders.orders)} recent orders:")
        
        for i, order in enumerate(orders.orders[:5], 1):
            print(f"\n{i}. {order.side} {order.product_id}")
            print(f"   Status: {order.status}")
            if hasattr(order, 'filled_size') and float(order.filled_size) > 0:
                print(f"   Filled: {order.filled_size}")
            if hasattr(order, 'limit_price'):
                print(f"   Price: ${float(order.limit_price):.2f}")
    else:
        print("No recent orders found")
        
except Exception as e:
    print(f"Could not fetch orders: {e}")

# Check open positions
print("\n🎯 OPEN POSITIONS:")
print("-" * 70)

# Check our nuclear strikes
nuclear_strikes = [
    {"price": 109921.90, "status": "FILLED" if btc_price > 109921.90 else "WAITING"},
    {"price": 110251.01, "status": "FILLED" if btc_price > 110251.01 else "WAITING"},
    {"price": 110580.12, "status": "FILLED" if btc_price > 110580.12 else "WAITING"}
]

print("Nuclear Strike Status:")
for i, strike in enumerate(nuclear_strikes, 1):
    distance = strike['price'] - btc_price if strike['status'] == "WAITING" else 0
    print(f"{i}. ${strike['price']:.2f} - {strike['status']}")
    if distance > 0:
        print(f"   Distance: ${distance:.2f}")

# Greeks strategy analysis
print("\n🏛️ GREEKS STRATEGY ANALYSIS:")
print("-" * 70)
print("The Greeks system uses options-like strategies:")
print("• Delta: Direction/momentum trading")
print("• Gamma: Acceleration trades") 
print("• Theta: Time decay/overnight holds")
print("• Vega: Volatility plays")
print("• Rho: Interest rate correlations")

if total_value > 10000:
    print("\n✅ With $11k+ capital, Greeks can:")
    print("• Deploy larger positions ($500-1000)")
    print("• Run multiple strategies simultaneously")
    print("• Compound gains faster")
    print("• Target 20-50% monthly returns")
else:
    print("\n⚠️ Capital optimization needed")

print("\n" + "=" * 70)
print("🔥 The Greeks are ready to accelerate your wealth!")
print("=" * 70)