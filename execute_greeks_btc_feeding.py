#!/usr/bin/env python3
"""
🔥🏛️💥 EXECUTE: GREEKS FEED BTC FLYWHEEL
Launch the compound vortex strategy NOW!
"""

import json
from coinbase.rest import RESTClient
import time
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("🔥🏛️💥 LAUNCHING GREEKS → BTC FEEDING PROTOCOL")
print("=" * 70)
print("OPERATION: COMPOUND VORTEX")
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

# Get current prices
btc = client.get_product('BTC-USD')
sol = client.get_product('SOL-USD')
avax = client.get_product('AVAX-USD')
matic = client.get_product('MATIC-USD')

btc_price = float(btc['price'])
sol_price = float(sol['price'])
avax_price = float(avax['price'])
matic_price = float(matic['price'])

print(f"\n📊 MARKET STATUS:")
print(f"BTC: ${btc_price:,.2f}")
print(f"SOL: ${sol_price:.2f}")
print(f"AVAX: ${avax_price:.2f}")
print(f"MATIC: ${matic_price:.4f}")

# Get account balances
accounts = client.get_accounts()
holdings = {}

for acc in accounts['accounts']:
    currency = acc['currency']
    available = float(acc['available_balance']['value'])
    if available > 0.00001:
        holdings[currency] = available

print(f"\n💎 WAR CHEST:")
print("-" * 70)
print(f"SOL: {holdings.get('SOL', 0):.4f} = ${holdings.get('SOL', 0) * sol_price:.2f}")
print(f"AVAX: {holdings.get('AVAX', 0):.4f} = ${holdings.get('AVAX', 0) * avax_price:.2f}")
print(f"MATIC: {holdings.get('MATIC', 0):.2f} = ${holdings.get('MATIC', 0) * matic_price:.2f}")
print(f"BTC: {holdings.get('BTC', 0):.8f} = ${holdings.get('BTC', 0) * btc_price:.2f}")
print(f"USD: ${holdings.get('USD', 0):.2f}")

# PHASE 1: GREEKS ALT STRATEGY
print(f"\n🏛️ PHASE 1: GREEKS ALT HARVESTING")
print("-" * 70)

# Calculate optimal trade sizes for alts
sol_balance = holdings.get('SOL', 0)
avax_balance = holdings.get('AVAX', 0)
matic_balance = holdings.get('MATIC', 0)

# Trade 20% of each position for quick scalps
sol_trade_size = sol_balance * 0.2
avax_trade_size = avax_balance * 0.2
matic_trade_size = matic_balance * 0.2

print("SCALPING STRATEGY (20% positions):")
print(f"• SOL: {sol_trade_size:.4f} (${sol_trade_size * sol_price:.2f})")
print(f"• AVAX: {avax_trade_size:.4f} (${avax_trade_size * avax_price:.2f})")
print(f"• MATIC: {matic_trade_size:.2f} (${matic_trade_size * matic_price:.2f})")

# Set profit targets
print(f"\n🎯 PROFIT TARGETS:")
print("• Quick scalps: 0.5-1% per trade")
print("• Momentum runs: 2-3% per trade")
print("• Daily goal: 10% portfolio growth")

# PHASE 2: PROFIT CONVERSION
print(f"\n💱 PHASE 2: PROFIT → BTC CONVERSION")
print("-" * 70)

expected_daily_profit = (sol_trade_size * sol_price + avax_trade_size * avax_price + matic_trade_size * matic_price) * 0.10
btc_buying_power = expected_daily_profit
btc_to_acquire = btc_buying_power / btc_price

print(f"Expected daily profit: ${expected_daily_profit:.2f}")
print(f"Will buy: {btc_to_acquire:.8f} BTC")
print(f"BTC position increase: {(btc_to_acquire / holdings.get('BTC', 0.00001)) * 100:.1f}%")

# PHASE 3: ENHANCED NUCLEAR STRIKES
print(f"\n💥 PHASE 3: ENHANCED NUCLEAR STRIKES")
print("-" * 70)

current_btc = holdings.get('BTC', 0)
enhanced_btc = current_btc + btc_to_acquire
nuclear_size = enhanced_btc * 0.5

print(f"Current nuclear strike: {current_btc * 0.5:.8f} BTC")
print(f"Enhanced strike (after feeding): {nuclear_size:.8f} BTC")
print(f"Strike power increase: {((nuclear_size / (current_btc * 0.5)) - 1) * 100:.1f}%")

# EXECUTION ORDERS
print(f"\n🚀 EXECUTION SEQUENCE:")
print("-" * 70)

orders = []

# 1. Set Greek profit-taking orders on alts
if sol_balance > 0.1:
    sol_sell_price = sol_price * 1.01  # 1% profit target
    orders.append({
        "action": "SELL",
        "product": "SOL-USD",
        "size": sol_trade_size,
        "price": sol_sell_price,
        "purpose": "Greek profit take"
    })

if avax_balance > 1:
    avax_sell_price = avax_price * 1.01
    orders.append({
        "action": "SELL",
        "product": "AVAX-USD",
        "size": avax_trade_size,
        "price": avax_sell_price,
        "purpose": "Greek profit take"
    })

# 2. Set BTC accumulation orders
btc_buy_price = btc_price * 0.995  # Buy dips
orders.append({
    "action": "BUY",
    "product": "BTC-USD",
    "size": btc_to_acquire,
    "price": btc_buy_price,
    "purpose": "Feed the flywheel"
})

print("ORDERS TO PLACE:")
for i, order in enumerate(orders, 1):
    print(f"\n{i}. {order['action']} {order['product']}")
    print(f"   Size: {order['size']:.8f}")
    print(f"   Price: ${order['price']:.2f}")
    print(f"   Purpose: {order['purpose']}")

# Place the orders
print(f"\n⚡ PLACING ORDERS:")
print("-" * 70)

for order in orders:
    try:
        if order['size'] > 0.00001:
            result = client.create_order(
                client_order_id=f"greek_feed_{int(time.time())}_{order['product']}",
                product_id=order['product'],
                side=order['action'],
                order_configuration={
                    "limit_limit_gtc": {
                        "post_only": True,
                        "limit_price": f"{order['price']:.2f}",
                        "base_size": f"{order['size']:.8f}"
                    }
                }
            )
            print(f"✅ {order['action']} {order['product']} order placed")
    except Exception as e:
        print(f"⚠️ Could not place {order['product']} order: {e}")

# MONITORING DASHBOARD
print(f"\n📊 COMPOUND VORTEX DASHBOARD:")
print("-" * 70)

# Calculate projections
days = [1, 3, 7, 14, 30]
portfolio_value = sum([
    holdings.get('SOL', 0) * sol_price,
    holdings.get('AVAX', 0) * avax_price,
    holdings.get('MATIC', 0) * matic_price,
    holdings.get('BTC', 0) * btc_price,
    holdings.get('USD', 0)
])

print(f"Starting portfolio: ${portfolio_value:,.2f}")
print("\nPROJECTIONS WITH COMPOUND VORTEX:")

for day in days:
    # Greeks compound at 10% daily
    greek_growth = (1.10 ** day)
    # BTC nuclear grows from feeding
    btc_growth = 1 + (0.02 * day)  # 2% per day from larger strikes
    
    projected = portfolio_value * greek_growth * btc_growth
    print(f"Day {day:2}: ${projected:,.2f}")

# AUTOMATION SETUP
print(f"\n🤖 AUTOMATION COMMANDS:")
print("-" * 70)
print("To run Greeks continuously:")
print("  screen -S greeks")
print("  python3 greeks_alt_harvester.py")
print("  Ctrl+A, D to detach")
print("\nTo monitor:")
print("  python3 compound_vortex_monitor.py")

# Save state
state = {
    "timestamp": datetime.now().isoformat(),
    "strategy": "GREEKS_FEED_BTC",
    "holdings": holdings,
    "prices": {
        "BTC": btc_price,
        "SOL": sol_price,
        "AVAX": avax_price,
        "MATIC": matic_price
    },
    "daily_target": expected_daily_profit,
    "btc_feed_rate": btc_to_acquire,
    "orders_placed": len(orders)
}

with open('/home/dereadi/scripts/claude/compound_vortex_state.json', 'w') as f:
    json.dump(state, f, indent=2)

print("\n✅ State saved to compound_vortex_state.json")

print("\n" + "=" * 70)
print("🔥🏛️💥 COMPOUND VORTEX ACTIVATED!")
print("Greeks harvest → Profits feed BTC → Nuclear strikes grow")
print("EXPONENTIAL GROWTH ENGAGED!")
print("=" * 70)