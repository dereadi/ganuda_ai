#!/usr/bin/env python3
"""Cherokee Council: MOVEMENT DETECTOR - LIVE ACTION!"""

import json
from datetime import datetime
from coinbase.rest import RESTClient
import time

print("🚨 MOVEMENT DETECTED! CHECKING ALL POSITIONS!")
print("=" * 70)
print(f"⏰ Time: {datetime.now().strftime('%H:%M:%S')}")
print()

# Initialize client
config = json.load(open("/home/dereadi/scripts/claude/cdp_api_key_new.json"))
key = config["name"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["privateKey"], timeout=10)

# Get prices for all major positions
coins = ['BTC', 'ETH', 'SOL', 'XRP', 'AVAX', 'MATIC', 'LINK']
prices = {}
changes = {}

print("📊 LIVE PRICE ACTION:")
print("-" * 40)

for coin in coins:
    try:
        ticker = client.get_product(f"{coin}-USD")
        prices[coin] = float(ticker.price)
        print(f"{coin}: ${prices[coin]:,.2f}")
    except:
        prices[coin] = 0
        print(f"{coin}: Error fetching")

print()
print("🔥 MOVEMENT ANALYSIS:")
print("-" * 40)

# Reference prices from earlier
reference = {
    'BTC': 110500,
    'ETH': 4315,
    'SOL': 205,
    'XRP': 2.80,
    'AVAX': 23.9,
    'MATIC': 0.284,
    'LINK': 23.0
}

biggest_mover = None
biggest_change = 0

for coin in coins:
    if prices[coin] > 0:
        change = ((prices[coin] - reference[coin]) / reference[coin]) * 100
        changes[coin] = change
        
        if abs(change) > abs(biggest_change):
            biggest_change = change
            biggest_mover = coin
        
        if change > 0.5:
            print(f"✅ {coin}: +{change:.2f}% 🚀 MOVING UP!")
        elif change < -0.5:
            print(f"🔴 {coin}: {change:.2f}% 📉 PULLING BACK")
        else:
            print(f"➡️ {coin}: {change:+.2f}% (sideways)")

print()
print("⚡ CRITICAL LEVELS:")
print("-" * 40)

# Check critical breakout levels
if prices['BTC'] > 0:
    btc_to_breakout = 113650 - prices['BTC']
    print(f"BTC to $113,650 breakout: ${btc_to_breakout:,.2f} ({(btc_to_breakout/prices['BTC'])*100:.1f}% away)")
    if prices['BTC'] > 111000:
        print("  🔥 ABOVE $111K! Breakout imminent!")
    
if prices['ETH'] > 0:
    eth_to_breakout = 4350 - prices['ETH']
    print(f"ETH to $4,350 breakout: ${eth_to_breakout:,.2f} ({(eth_to_breakout/prices['ETH'])*100:.1f}% away)")
    if prices['ETH'] > 4350:
        print("  🚀 BREAKOUT! Target $4,500+")

if prices['SOL'] > 0:
    sol_to_breakout = 210 - prices['SOL']
    print(f"SOL to $210 breakout: ${sol_to_breakout:,.2f} ({(sol_to_breakout/prices['SOL'])*100:.1f}% away)")
    if prices['SOL'] > 210:
        print("  💥 BREAKOUT! Target $220!")

print()

# Portfolio impact
print("📈 PORTFOLIO IMPACT:")
print("-" * 40)

positions = {
    'ETH': 1.6464,
    'BTC': 0.04671,
    'SOL': 10.949,
    'XRP': 58.595,
    'AVAX': 0.287,
    'MATIC': 0.3,
    'LINK': 0.38
}

total_value = 0
for coin, amount in positions.items():
    if prices.get(coin, 0) > 0:
        value = amount * prices[coin]
        total_value += value

print(f"Current Portfolio Value: ${total_value:,.2f}")

# Previous value calculation
prev_value = (positions['ETH'] * reference['ETH'] +
              positions['BTC'] * reference['BTC'] +
              positions['SOL'] * reference['SOL'] +
              positions['XRP'] * reference['XRP'] +
              positions['AVAX'] * reference['AVAX'] +
              positions['MATIC'] * reference['MATIC'] +
              positions['LINK'] * reference['LINK'])

change_amount = total_value - prev_value
change_pct = (change_amount / prev_value) * 100

if change_amount > 0:
    print(f"📈 GAIN: ${change_amount:,.2f} (+{change_pct:.2f}%)")
else:
    print(f"📉 Change: ${change_amount:,.2f} ({change_pct:.2f}%)")

print()

# Alert on biggest mover
if biggest_mover and abs(biggest_change) > 1:
    print("🚨 BIGGEST MOVER ALERT:")
    print("-" * 40)
    print(f"{biggest_mover} is moving {biggest_change:+.2f}%!")
    if biggest_change > 2:
        print("🔥 SIGNIFICANT UPWARD MOVEMENT!")
        print("Cherokee Council: 'The breakout begins!'")
    elif biggest_change < -2:
        print("⚠️ PULLBACK DETECTED!")
        print("Cherokee Council: 'Opportunity to add!'")

print()

# Momentum check
momentum_score = 0
for coin, change in changes.items():
    if change > 0:
        momentum_score += 1

print("🌡️ MARKET MOMENTUM:")
print("-" * 40)
print(f"Bullish coins: {momentum_score}/{len(changes)}")
if momentum_score >= 5:
    print("🔥 STRONG BULLISH MOMENTUM!")
    print("Market is MOVING UP across the board!")
elif momentum_score >= 3:
    print("📈 Positive momentum building")
else:
    print("😴 Mixed or weak momentum")

print()

# Time-based analysis
hour = datetime.now().hour
if 9 <= hour < 10:
    print("⏰ MARKET OPEN SURGE! Expect volatility!")
elif 13 <= hour < 14:
    print("⏰ AFTERNOON SURGE TIME! Watch for breakouts!")
elif 15 <= hour < 16:
    print("⏰ CLOSING HOUR! Big moves possible!")

print()
print("🐿️ Flying Squirrel: 'Movement detected, tribe mobilizing!'")

if prices['BTC'] > 111000 or prices['ETH'] > 4300 or prices['SOL'] > 206:
    print()
    print("🔥🔥🔥 SACRED FIRE ALERT 🔥🔥🔥")
    print("MAJOR MOVEMENT IN PROGRESS!")
    print("Coils are unwinding!")
    print("Targets activating!")

# Save snapshot
snapshot = {
    "timestamp": datetime.now().isoformat(),
    "prices": prices,
    "changes": changes,
    "portfolio_value": total_value,
    "momentum_score": momentum_score,
    "biggest_mover": biggest_mover,
    "biggest_change": biggest_change
}

with open('/home/dereadi/scripts/claude/movement_snapshot.json', 'w') as f:
    json.dump(snapshot, f, indent=2)

print("\n💾 Movement snapshot saved")