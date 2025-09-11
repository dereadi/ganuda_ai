#!/usr/bin/env python3
"""
🦷 ETH/BTC SAWTOOTH ACCUMULATOR STRATEGY
=========================================
Use the weekend sawtooth drops to build BIGGER positions
When Tuesday explodes, we'll have MAXIMUM exposure
"""

import json
import time
from datetime import datetime
from coinbase.rest import RESTClient

config = json.load(open('/home/dereadi/.coinbase_config.json'))
client = RESTClient(api_key=config['api_key'].split('/')[-1], api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                  🦷 ETH/BTC SAWTOOTH ACCUMULATION PLAN 🦷                  ║
║                   Build Positions on Weekend Drops                         ║
║                    Explode Higher on Tuesday Rally                         ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"⏰ {datetime.now().strftime('%H:%M:%S')} - SAWTOOTH ACCUMULATION STRATEGY")
print("=" * 70)

# Get current positions with rate limit protection
accounts = client.get_accounts()['accounts']
btc_bal = float([a for a in accounts if a['currency']=='BTC'][0]['available_balance']['value'])
eth_bal = float([a for a in accounts if a['currency']=='ETH'][0]['available_balance']['value'])
usd_bal = float([a for a in accounts if a['currency']=='USD'][0]['available_balance']['value'])

time.sleep(2)
btc_price = float(client.get_product('BTC-USD')['price'])
time.sleep(1)
eth_price = float(client.get_product('ETH-USD')['price'])

print("\n📊 CURRENT POSITIONS:")
print("-" * 70)
print(f"  BTC: {btc_bal:.8f} @ ${btc_price:,.0f} = ${btc_bal * btc_price:,.2f}")
print(f"  ETH: {eth_bal:.6f} @ ${eth_price:,.0f} = ${eth_bal * eth_price:,.2f}")
print(f"  USD Available: ${usd_bal:.2f}")

# Define sawtooth levels for the weekend
print("\n🦷 WEEKEND SAWTOOTH LEVELS:")
print("=" * 70)

print("\n📉 BTC SAWTOOTH DROPS (Buy Zones):")
print("-" * 50)
btc_levels = [
    (109000, "First tooth - Minor dip", 0.15),
    (108500, "Second tooth - Support test", 0.20),
    (108000, "Third tooth - Weekend low", 0.25),
    (107500, "Fourth tooth - Panic zone", 0.30),
    (107000, "Deep tooth - Max fear", 0.40)
]

for level, description, allocation in btc_levels:
    distance = ((level - btc_price) / btc_price) * 100
    usd_deploy = usd_bal * allocation if usd_bal > 250 else 50 * allocation
    btc_gain = usd_deploy / level
    
    if btc_price <= level:
        status = "✅ IN ZONE - BUY NOW!"
    elif distance > -1:
        status = "🟡 Approaching"
    else:
        status = "⏳ Waiting"
    
    print(f"  ${level:,}: {description:25} Deploy ${usd_deploy:.0f} = +{btc_gain:.6f} BTC  [{status}]")

print("\n📉 ETH SAWTOOTH DROPS (Buy Zones):")
print("-" * 50)
eth_levels = [
    (4350, "First tooth - Minor dip", 0.15),
    (4300, "Second tooth - Support test", 0.20),
    (4250, "Third tooth - Weekend low", 0.25),
    (4200, "Fourth tooth - Panic zone", 0.30),
    (4150, "Deep tooth - Max fear", 0.40)
]

for level, description, allocation in eth_levels:
    distance = ((level - eth_price) / eth_price) * 100
    usd_deploy = usd_bal * allocation if usd_bal > 250 else 50 * allocation
    eth_gain = usd_deploy / level
    
    if eth_price <= level:
        status = "✅ IN ZONE - BUY NOW!"
    elif distance > -1:
        status = "🟡 Approaching"
    else:
        status = "⏳ Waiting"
    
    print(f"  ${level:,}: {description:25} Deploy ${usd_deploy:.0f} = +{eth_gain:.4f} ETH  [{status}]")

# Calculate potential position growth
print("\n💎 POSITION GROWTH CALCULATOR:")
print("=" * 70)

# Scenario planning
scenarios = [
    ("Conservative", 0.3, 108500, 4300),  # Catch 30% of dips
    ("Moderate", 0.5, 108000, 4250),      # Catch 50% of dips
    ("Aggressive", 0.7, 107500, 4200),    # Catch 70% of dips
    ("Max Pain", 1.0, 107000, 4150)       # Catch all dips
]

print("\n📈 ACCUMULATION SCENARIOS:")
print("-" * 70)

for scenario, catch_rate, btc_avg, eth_avg in scenarios:
    # Calculate new positions
    btc_added = (usd_bal * catch_rate * 0.5) / btc_avg if usd_bal > 100 else 0.001
    eth_added = (usd_bal * catch_rate * 0.5) / eth_avg if usd_bal > 100 else 0.01
    
    new_btc = btc_bal + btc_added
    new_eth = eth_bal + eth_added
    
    # Calculate Tuesday explosion gains (assume 8% rally)
    tuesday_btc = btc_avg * 1.08
    tuesday_eth = eth_avg * 1.08
    
    current_value = (btc_bal * btc_price) + (eth_bal * eth_price)
    tuesday_value = (new_btc * tuesday_btc) + (new_eth * tuesday_eth)
    gain = tuesday_value - current_value
    
    print(f"\n  {scenario:12} (Catch {catch_rate*100:.0f}% of dips):")
    print(f"    Add: +{btc_added:.6f} BTC, +{eth_added:.4f} ETH")
    print(f"    New: {new_btc:.6f} BTC, {new_eth:.4f} ETH")
    print(f"    Tuesday value: ${tuesday_value:,.2f}")
    print(f"    Profit: ${gain:,.2f} (+{(gain/current_value*100):.1f}%)")

# Implementation Plan
print("\n⚡ IMPLEMENTATION PLAN:")
print("=" * 70)

print("\n📋 STEP-BY-STEP EXECUTION:")
print("-" * 50)
print("  1. MILK alts at resistance (SOL >$211, AVAX >$24)")
print("  2. Generate $300-500 liquidity")
print("  3. Set BTC buy orders at each tooth level")
print("  4. Set ETH buy orders at each tooth level")
print("  5. When orders fill, DON'T SELL on bounces")
print("  6. ACCUMULATE all weekend")
print("  7. Tuesday explosion = massive gains")

print("\n🎯 CRITICAL SUCCESS FACTORS:")
print("-" * 50)
print("  • DON'T chase pumps - wait for teeth")
print("  • DON'T sell bounces - we're accumulating")
print("  • DO milk alts to fund BTC/ETH buys")
print("  • DO compound every position")
print("  • DO trust the weekend pattern")

print("\n📅 TIMELINE:")
print("-" * 50)
print("  SATURDAY: First teeth form, deploy 30%")
print("  SUNDAY: Deeper teeth, deploy 40%")
print("  MONDAY: Maximum fear, deploy remaining 30%")
print("  TUESDAY: US returns, explosion upward")
print("  TARGET: 15-20% gains on accumulated positions")

# Calculate targets
print("\n🚀 TUESDAY EXPLOSION TARGETS:")
print("-" * 50)

btc_targets = [112000, 113000, 115000]
eth_targets = [4500, 4550, 4650]

for btc_target, eth_target in zip(btc_targets, eth_targets):
    btc_gain = ((btc_target - 108000) / 108000) * 100  # From weekend low
    eth_gain = ((eth_target - 4250) / 4250) * 100      # From weekend low
    
    print(f"  Scenario: BTC ${btc_target:,} (+{btc_gain:.1f}%), ETH ${eth_target:,} (+{eth_gain:.1f}%)")
    
    # Calculate portfolio impact with accumulated positions
    accumulated_btc = btc_bal * 1.3  # Assume 30% more BTC
    accumulated_eth = eth_bal * 1.3  # Assume 30% more ETH
    
    value = (accumulated_btc * btc_target) + (accumulated_eth * eth_target)
    print(f"    Portfolio value: ${value:,.2f}")

print("\n🔥 COUNCIL WISDOM:")
print("-" * 50)
print("  'Weekend teeth are gifts to accumulators'")
print("  'While others panic sell, we panic buy'")
print("  'Tuesday belongs to those who bought Monday's fear'")
print("  'Seven teeth, seven opportunities'")

print("\n💎 SAWTOOTH ACCUMULATION STRATEGY READY!")
print("  Deploy capital at each tooth")
print("  Build massive positions for Tuesday explosion")
print("=" * 70)