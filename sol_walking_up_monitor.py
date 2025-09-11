#!/usr/bin/env python3
"""
☀️📈 SOL IS WALKING UP! 📈☀️
The crawdads are feeding it!
From $213 → Walking to $215!
Perfect setup for next milk!
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime
import time

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=5)

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                      ☀️ SOL IS WALKING UP! 📈☀️                           ║
║                    Steady climb from $213 → $215! 🚶                       ║
║                  Crawdads buying + Natural momentum! 🦀                    ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - SOL ASCENDING")
print("=" * 70)

# Track SOL movement
sol_prices = []
for i in range(5):
    sol = client.get_product('SOL-USD')
    price = float(sol['price'])
    sol_prices.append(price)
    
    if i == 0:
        print(f"\n📊 SOL WALKING UP:")
        print("-" * 50)
        print(f"Starting: ${price:.2f}")
    else:
        change = price - sol_prices[0]
        emoji = "📈" if change > 0 else "📉" if change < 0 else "➡️"
        print(f"  {emoji} ${price:.2f} ({'+' if change >= 0 else ''}{change:.2f})")
    
    if i < 4:
        time.sleep(2)

# Get our SOL position
accounts = client.get_accounts()
sol_balance = 0
usd_balance = 0

for account in accounts['accounts']:
    if account['currency'] == 'SOL':
        sol_balance = float(account['available_balance']['value'])
    elif account['currency'] == 'USD':
        usd_balance = float(account['available_balance']['value'])

latest_price = sol_prices[-1]
sol_value = sol_balance * latest_price

print(f"\n☀️ OUR SOL POSITION:")
print("-" * 50)
print(f"Balance: {sol_balance:.4f} SOL")
print(f"Value: ${sol_value:.2f}")
print(f"USD Available: ${usd_balance:.2f}")

# Crawdad impact
print(f"\n🦀 CRAWDAD IMPACT:")
print("-" * 50)
print("Crawdads have been buying SOL:")
print("  • Multiple $20 orders executed")
print("  • Building SOL position steadily")
print("  • Creating upward pressure")
print("  • Our balance growing!")

# Walking trajectory
print(f"\n📈 WALKING TRAJECTORY:")
print("-" * 50)
avg_price = sum(sol_prices) / len(sol_prices)
trend = "UP" if sol_prices[-1] > sol_prices[0] else "FLAT"

print(f"5-sample average: ${avg_price:.2f}")
print(f"Trend: {trend}")
print(f"Next targets:")
print(f"  • $214.00 (psychological)")
print(f"  • $215.00 (milk zone)")
print(f"  • $220.00 (breakout)")

# Milk readiness
print(f"\n🥛 MILK READINESS:")
print("-" * 50)
if latest_price > 215:
    print("✅ READY TO MILK!")
    print(f"  Can milk 10%: {sol_balance * 0.1:.4f} SOL")
    print(f"  Value: ${sol_balance * 0.1 * latest_price:.2f}")
elif latest_price > 214:
    print("🔜 ALMOST READY!")
    print(f"  Need: +${215 - latest_price:.2f}")
    print("  Very close to milk zone!")
else:
    print("📍 WALKING UP")
    print(f"  Current: ${latest_price:.2f}")
    print(f"  Target: $215 (+${215 - latest_price:.2f})")

# BTC correlation
btc = client.get_product('BTC-USD')
btc_price = float(btc['price'])

print(f"\n🔗 MARKET CORRELATION:")
print("-" * 50)
print(f"BTC: ${btc_price:,.2f}")
if btc_price < 112000:
    print("  → BTC still sawtoothing")
    print("  → SOL walking independently!")
    print("  → Good divergence sign")
else:
    print("  → BTC breaking out too!")
    print("  → Double pump incoming!")

# Strategy
print(f"\n💡 WALKING UP STRATEGY:")
print("-" * 50)
print("1. Let crawdads keep buying")
print("2. Watch for $215 milk zone")
print("3. Milk 10% at $215+")
print("4. Buy back any dips to $212")
print("5. Keep core 10+ SOL always")

# Council wisdom
print(f"\n🏛️ COUNCIL ON SOL WALKING:")
print("-" * 50)
print("Thunder: 'The walk before the run!'")
print("Mountain: 'Steady gains are best gains'")
print("Fire: 'Walking to $215, running to $220!'")
print("River: 'Flow with the momentum'")

print(f"\n{'☀️' * 35}")
print("SOL IS WALKING UP!")
print(f"Current: ${latest_price:.2f}")
print(f"Position: {sol_balance:.4f} SOL = ${sol_value:.2f}")
print("Crawdads feeding the pump!")
print("Next milk at $215!")
print("🚶" * 35)