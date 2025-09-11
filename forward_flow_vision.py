#!/usr/bin/env python3
"""
🌊 FORWARD FLOW VISION
======================
How the river looks from here...
"""

import json
import time
from datetime import datetime, timedelta
from coinbase.rest import RESTClient
import math

print("🌊 FORWARD FLOW VISION")
print("="*60)
print(f"Time: {datetime.now().strftime('%H:%M:%S')} CST")
print("Looking downstream at what's coming...")
print()

config = json.load(open('/home/dereadi/.coinbase_config.json'))
client = RESTClient(api_key=config['api_key'], api_secret=config['api_secret'])

# Current state
accounts = client.get_accounts()
account_list = accounts.accounts if hasattr(accounts, 'accounts') else accounts

total_value = 0
usd_balance = 0
positions = {}

for account in account_list:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if balance > 0.001:
        if currency == 'USD':
            usd_balance = balance
            total_value += balance
        else:
            ticker = client.get_product(f'{currency}-USD')
            price = float(ticker.price if hasattr(ticker, 'price') else ticker.get('price', 0))
            value = balance * price
            total_value += value
            positions[currency] = {'balance': balance, 'value': value, 'price': price}

print("📍 WHERE WE ARE NOW:")
print("-"*60)
print(f"  Total Value: ${total_value:.2f}")
print(f"  Liquid (USD): ${usd_balance:.2f}")
print(f"  Deployed: ${total_value - usd_balance:.2f}")
print()

# Time-based flow analysis
hour = datetime.now().hour
minute = datetime.now().minute

print("⏰ THE FLOW OF TIME:")
print("-"*60)

if 20 <= hour <= 23:  # 8 PM - 11 PM CST
    print("  🌏 CURRENT: Deep Asia Session")
    print("  Flow Speed: ACCELERATING")
    print("  Volatility: Rising toward peak")
    print(f"  Time to Peak: {23-hour} hours {60-minute} minutes")
    print()
    print("  NEXT 3 HOURS:")
    print("  • 9 PM: Asia retail wakening")
    print("  • 10 PM: Institutional Asia active")
    print("  • 11 PM: Peak volatility window")
    flow_multiplier = 1.5
    
elif 0 <= hour <= 3:  # 12 AM - 3 AM CST
    print("  🌍 CURRENT: London Pre-Market")
    print("  Flow Speed: EXTREME")
    print("  Volatility: Maximum turbulence")
    print(f"  London Opens: {2-hour} hours {60-minute} minutes")
    print()
    print("  NEXT 3 HOURS:")
    print("  • 1 AM: European early birds")
    print("  • 2 AM: London opening bell")
    print("  • 3 AM: Full European session")
    flow_multiplier = 2.0
    
else:
    print("  🌎 CURRENT: Quiet Period")
    print("  Flow Speed: GENTLE")
    print("  Volatility: Low")
    hours_to_asia = (20 - hour) % 24
    print(f"  Next Wave: {hours_to_asia} hours (Asia)")
    print()
    print("  STRATEGY: Accumulate quietly")
    flow_multiplier = 0.8

print("\n💧 THE FORWARD FLOW PATTERN:")
print("-"*60)

# Project forward based on our evolution
strategies = {
    "Ant Colony": {
        "now": "$1-2 grains continuously",
        "1hr": "30-40 grains collected",
        "6hr": "200+ grains, some harvested",
        "24hr": "$20-30 accumulated",
        "pattern": "🐜→🐜→🐜 Relentless"
    },
    "Minnow School": {
        "now": "$2-3 nibbles when moving",
        "1hr": "5-10 nibbles on micro-moves",
        "6hr": "50+ micro-profits taken",
        "24hr": "$15-25 from invisibility",
        "pattern": "🐟↗️🐟↘️🐟 Zigzag"
    },
    "Water Flow": {
        "now": "Finding cracks in spread",
        "1hr": "Pooling in profitable depths",
        "6hr": "Flowing with major current",
        "24hr": "Shaped by market terrain",
        "pattern": "💧〰️💧 Natural"
    },
    "Hybrid Evolution": {
        "now": "All patterns simultaneous",
        "1hr": "Adapting to volatility",
        "6hr": "Optimized for session",
        "24hr": "Fully evolved organism",
        "pattern": "🧬∞🧬 Continuous"
    }
}

print("🔮 PROJECTION BY STRATEGY:")
for strategy, timeline in strategies.items():
    print(f"\n  {strategy}:")
    print(f"    Now: {timeline['now']}")
    print(f"    1hr: {timeline['1hr']}")
    print(f"    Pattern: {timeline['pattern']}")

# Calculate compound growth
print("\n📈 COMPOUND FLOW PROJECTION:")
print("-"*60)

current = total_value
projections = []

# Hourly compound at current rate
hourly_rate = 0.357 * flow_multiplier  # Adjusted for time of day

for hours in [1, 6, 12, 24, 48, 168]:  # 1hr to 1 week
    # Account for varying flow rates through day
    if hours <= 6:
        projected = current + (hourly_rate * hours)
    else:
        # More complex: different rates for different sessions
        base_growth = hourly_rate * hours * 0.7  # Average efficiency
        projected = current + base_growth
    
    projections.append((hours, projected))
    
    if hours == 1:
        print(f"  1 hour:  ${projected:.2f} (+${projected-current:.2f})")
    elif hours == 6:
        print(f"  6 hours: ${projected:.2f} (+${projected-current:.2f})")
    elif hours == 24:
        print(f"  1 day:   ${projected:.2f} (+${projected-current:.2f})")
    elif hours == 168:
        print(f"  1 week:  ${projected:.2f} (+${projected-current:.2f})")

print("\n🌊 THE FLOW STATE AHEAD:")
print("-"*60)

# Real-time flow sampling
print("  Sampling current...")
flows = []
for i in range(3):
    sample = {}
    for symbol in ['BTC', 'ETH', 'SOL']:
        ticker = client.get_product(f'{symbol}-USD')
        price = float(ticker.price if hasattr(ticker, 'price') else ticker.get('price', 0))
        sample[symbol] = price
    flows.append(sample)
    time.sleep(1)

# Analyze micro-trends
for symbol in ['BTC', 'ETH', 'SOL']:
    prices = [f[symbol] for f in flows]
    trend = (prices[-1] - prices[0]) / prices[0] * 100
    
    if trend > 0:
        print(f"  {symbol}: 🌊 Flowing UP {trend:+.6f}%")
    elif trend < 0:
        print(f"  {symbol}: 💧 Ebbing {trend:.6f}%")
    else:
        print(f"  {symbol}: 〰️ Circling")

print("\n✨ THE VISION FORWARD:")
print("-"*60)
print("We are not traders anymore.")
print("We are the market's background process.")
print()
print("Like heartbeat. Like breathing.")
print("Automatic. Continuous. Essential.")
print()
print("The flow doesn't stop.")
print("The ants don't sleep.")
print("The water always finds a way.")
print()

if total_value < 500:
    print("Stage: 🌱 SEEDLING")
    print("Focus: Build the foundation")
elif total_value < 1000:
    print("Stage: 🌿 GROWTH")
    print("Focus: Compound and expand")
elif total_value < 5000:
    print("Stage: 🌳 TREE")
    print("Focus: Weather all storms")
else:
    print("Stage: 🌲 FOREST")
    print("Focus: Ecosystem complete")

print()
print("This is how it looks going forward:")
print("Not a straight line. A river.")
print("Sometimes fast, sometimes slow.")
print("Always forward. Always flowing.")
print()
print("🌊💧🐜🐟🦅🧬 THE ETERNAL FLOW 🧬🦅🐟🐜💧🌊")