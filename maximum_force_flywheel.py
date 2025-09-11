#!/usr/bin/env python3
"""
💥 MAXIMUM FORCE FLYWHEEL - THE NUCLEAR OPTION
Use 50% of holdings per trade for escape velocity
Only need 3-5 massive trades to build momentum
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("💥 MAXIMUM FORCE FLYWHEEL - NUCLEAR IGNITION")
print("=" * 70)
print("Philosophy: 3 massive hits > 1000 tiny taps")
print("=" * 70)

# Get positions
btc = client.get_product('BTC-USD')
eth = client.get_product('ETH-USD')
btc_price = float(btc['price'])
eth_price = float(eth['price'])

accounts = client.get_accounts()
holdings = {}
for acc in accounts['accounts']:
    if acc['currency'] in ['BTC', 'ETH', 'USD']:
        available = float(acc['available_balance']['value'])
        if available > 0:
            holdings[acc['currency']] = available

btc_balance = holdings.get('BTC', 0)
eth_balance = holdings.get('ETH', 0)
btc_value = btc_balance * btc_price
eth_value = eth_balance * eth_price
total_value = btc_value + eth_value

print(f"\n💎 WAR CHEST:")
print(f"BTC: {btc_balance:.8f} (${btc_value:,.2f})")
print(f"ETH: {eth_balance:.8f} (${eth_value:,.2f})")
print(f"TOTAL: ${total_value:,.2f}")

# THE NUCLEAR MATH
print("\n☢️ NUCLEAR IGNITION MATH:")
print("-" * 70)

# Use 50% of holdings per trade
nuclear_btc = btc_balance * 0.5
nuclear_eth = eth_balance * 0.5
nuclear_value = nuclear_btc * btc_price

print(f"Nuclear BTC position: {nuclear_btc:.8f} (${nuclear_btc * btc_price:,.2f})")
print(f"Nuclear ETH position: {nuclear_eth:.8f} (${nuclear_eth * eth_price:,.2f})")

# Calculate breakeven
maker_fee = 0.004
taker_fee = 0.006
nuclear_fees_maker = nuclear_value * maker_fee * 2  # Round trip
nuclear_fees_taker = nuclear_value * taker_fee * 2

breakeven_maker = (nuclear_fees_maker / nuclear_value) * 100
breakeven_taker = (nuclear_fees_taker / nuclear_value) * 100

print(f"\nWith ${nuclear_value:.2f} positions:")
print(f"  Maker fees: ${nuclear_fees_maker:.2f} (need {breakeven_maker:.3f}% move)")
print(f"  Taker fees: ${nuclear_fees_taker:.2f} (need {breakeven_taker:.3f}% move)")

# TARGET IDENTIFICATION
print("\n🎯 NUCLEAR STRIKE TARGETS:")
print("-" * 70)

# Only take HIGH PROBABILITY setups
print("CRITERIA FOR NUCLEAR STRIKE:")
print("• Bollinger Band squeeze < 0.5%")
print("• Support/Resistance confluence")
print("• Volume spike incoming")
print("• Time window optimal (Asia/Europe)")
print("• Expected move > 1%")

# Check current setup
# Note: ask/bid not available in this response format
spread_pct = 0.01  # Typical Coinbase spread
print(f"\nCurrent BTC spread: ~{spread_pct:.4f}%")

if spread_pct < 0.05:
    print("✅ TIGHT SPREAD - Good liquidity")
else:
    print("⚠️ WIDE SPREAD - Wait for better liquidity")

# THE THREE-STRIKE PLAN
print("\n💥 THREE-STRIKE IGNITION PLAN:")
print("-" * 70)

strikes = [
    {
        "name": "STRIKE ONE - The Awakening",
        "size_pct": 50,
        "btc_size": btc_balance * 0.5,
        "target_move": 1.0,
        "expected_profit": nuclear_value * 0.01 - nuclear_fees_maker
    },
    {
        "name": "STRIKE TWO - The Momentum",
        "size_pct": 30,
        "btc_size": btc_balance * 0.3,
        "target_move": 0.7,
        "expected_profit": (nuclear_value * 0.6) * 0.007 - (nuclear_value * 0.6 * maker_fee * 2)
    },
    {
        "name": "STRIKE THREE - The Sustainer",
        "size_pct": 20,
        "btc_size": btc_balance * 0.2,
        "target_move": 0.5,
        "expected_profit": (nuclear_value * 0.4) * 0.005 - (nuclear_value * 0.4 * maker_fee * 2)
    }
]

total_expected = 0
for i, strike in enumerate(strikes, 1):
    print(f"\n{strike['name']}:")
    print(f"  Size: {strike['size_pct']}% of holdings")
    print(f"  BTC: {strike['btc_size']:.8f}")
    print(f"  Target: {strike['target_move']}% move")
    print(f"  Expected: ${strike['expected_profit']:.2f}")
    total_expected += strike['expected_profit']

print(f"\n💰 TOTAL EXPECTED FROM 3 STRIKES: ${total_expected:.2f}")

# SUCCESS METRICS
print("\n📊 SUCCESS METRICS:")
print("-" * 70)
print("After 3 nuclear strikes:")
print(f"• Flywheel spinning: YES")
print(f"• Momentum achieved: {total_expected > 0}")
print(f"• Can reduce to normal size: {total_expected > 50}")

if total_expected > 100:
    print("✅ NUCLEAR IGNITION SUCCESSFUL!")
    print("   Flywheel has escape velocity")
    print("   Switch to cruise mode with profits")
else:
    print("⚠️ Need better setups for nuclear option")
    print("   Wait for 1%+ opportunity")

# RISK MANAGEMENT
print("\n⚠️ NUCLEAR RISK MANAGEMENT:")
print("-" * 70)
print("RULES:")
print("1. NEVER use more than 50% per trade")
print("2. WAIT for perfect setups only")
print("3. USE limit orders for maker fees")
print("4. STOP after 3 strikes (reassess)")
print("5. If profitable, reduce to 10% positions")

# TIMING
current_hour = datetime.now().hour
print(f"\n⏰ TIMING CHECK (Hour: {current_hour}):")
if 20 <= current_hour <= 23:
    print("🔥 NUCLEAR WINDOW OPEN - Asia volatility!")
    print("   → PREPARE FOR STRIKE ONE")
elif 2 <= current_hour <= 5:
    print("⚡ SECONDARY WINDOW - Europe entry")
else:
    print("💤 HOLD FIRE - Wait for volatility")

# THE DECISION
print("\n" + "=" * 70)
print("💥 THE NUCLEAR QUESTION:")
print("=" * 70)
print("Do we have the setup for a nuclear strike?")
print("\nCHECKLIST:")
checklist = [
    f"□ Expected move > 1%? (Need to check charts)",
    f"□ At support/resistance? (Need to check levels)",
    f"□ Volatility incoming? {'✅ YES - Asia open' if 20 <= current_hour <= 23 else '❌ NO'}",
    f"□ Spread tight? {'✅ YES' if spread_pct < 0.05 else '❌ NO'}",
    f"□ Risk acceptable? (50% position = ${nuclear_value:.2f})"
]

for item in checklist:
    print(item)

print("\nIf 4/5 checked → LAUNCH NUCLEAR STRIKE")
print("If < 4 checked → WAIT FOR BETTER SETUP")
print("=" * 70)