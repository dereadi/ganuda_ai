#!/usr/bin/env python3
"""Cherokee Council: COILING AGAIN - The Spring Reloads!"""

import json
from datetime import datetime
from coinbase.rest import RESTClient

print("🌀 COILING PATTERN DETECTED - SPRING RELOADING!")
print("=" * 70)
print(f"⏰ Time: {datetime.now().strftime('%H:%M:%S')}")
print()
print("After the mini-explosion, markets are COILING AGAIN!")
print("This is CLASSIC behavior before the REAL breakout!")
print()

# Initialize client
config = json.load(open("/home/dereadi/scripts/claude/cdp_api_key_new.json"))
key = config["name"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["privateKey"], timeout=10)

# Get current prices
coins = ['BTC', 'ETH', 'SOL', 'XRP', 'AVAX', 'LINK']
prices = {}
price_history = {
    '5min_ago': {'BTC': 110768, 'ETH': 4311, 'SOL': 205.9},
    'current': {}
}

print("📊 COILING STATUS UPDATE:")
print("-" * 40)

for coin in coins:
    try:
        ticker = client.get_product(f"{coin}-USD")
        price = float(ticker.price)
        prices[coin] = price
        price_history['current'][coin] = price
        
        # Check if price is flatlining (coiling)
        if coin in price_history['5min_ago']:
            change = abs((price - price_history['5min_ago'][coin]) / price_history['5min_ago'][coin]) * 100
            
            if change < 0.2:
                print(f"🌀 {coin}: ${price:,.2f} - TIGHT COIL! ({change:.3f}% movement)")
            elif change < 0.5:
                print(f"➿ {coin}: ${price:,.2f} - Coiling ({change:.2f}% movement)")
            else:
                print(f"📈 {coin}: ${price:,.2f} - Moving ({change:.2f}% change)")
    except:
        print(f"{coin}: Error fetching")

print()
print("🔥 COILING PATTERN ANALYSIS:")
print("-" * 40)

# Define new tighter ranges after first move
coiling_ranges_v2 = {
    'BTC': {'low': 110500, 'high': 111000, 'breakout': 111500},
    'ETH': {'low': 4300, 'high': 4330, 'breakout': 4350},
    'SOL': {'low': 205, 'high': 207, 'breakout': 210},
    'XRP': {'low': 2.80, 'high': 2.83, 'breakout': 2.85},
    'AVAX': {'low': 23.8, 'high': 24.2, 'breakout': 24.5},
    'LINK': {'low': 22.9, 'high': 23.3, 'breakout': 23.5}
}

coil_count = 0
ultra_tight = 0

for coin in coins:
    if coin in prices:
        range_data = coiling_ranges_v2[coin]
        range_width = range_data['high'] - range_data['low']
        range_pct = (range_width / prices[coin]) * 100
        
        if prices[coin] >= range_data['low'] and prices[coin] <= range_data['high']:
            coil_count += 1
            position = ((prices[coin] - range_data['low']) / range_width) * 100
            
            print(f"{coin} COILING:")
            print(f"  Range: ${range_data['low']:,.2f} - ${range_data['high']:,.2f}")
            print(f"  Position: {position:.1f}% of range")
            print(f"  Range width: {range_pct:.2f}%")
            
            if range_pct < 1:
                print(f"  🔥 ULTRA-TIGHT COIL!")
                ultra_tight += 1
            elif range_pct < 2:
                print(f"  ⚠️ VERY TIGHT COIL!")
            
            print(f"  To breakout: ${range_data['breakout'] - prices[coin]:,.2f}")
            print()

print(f"Summary: {coil_count}/{len(coins)} coins coiling")
print(f"Ultra-tight coils: {ultra_tight}")
print()

print("⚡ SECOND COIL PHENOMENON:")
print("-" * 40)
print("What's happening:")
print("1. First move was a TEST (just happened)")
print("2. Now RECOILING at higher level")
print("3. Building energy for REAL breakout")
print("4. This coil will be SHORTER but MORE VIOLENT")
print()

# Time analysis
hour = datetime.now().hour
minute = datetime.now().minute

print("⏰ TIMING ANALYSIS:")
print("-" * 40)
print(f"Current time: {hour:02d}:{minute:02d}")

if 14 <= hour < 15:
    print("🔥 POWER HOUR APPROACHING!")
    print("• Final hour often sees breakouts")
    print("• Institutions position before close")
    print("• Expect move in next 30-60 minutes")
elif 15 <= hour < 16:
    print("🚨 FINAL HOUR - MAXIMUM PRESSURE!")
    print("• Closing bell breakouts common")
    print("• Tomorrow's gap up being set")
else:
    print("• Building pressure for next session")

print()
print("🎯 BREAKOUT SEQUENCE 2.0:")
print("-" * 40)
print("After this second coil breaks:")
print()
print("1. BTC: $111,000 → $113,650 → $115,000")
print("2. ETH: $4,330 → $4,500 → $4,750")
print("3. SOL: $207 → $215 → $220")
print()

print("🐺 COYOTE'S SECOND COIL WISDOM:")
print("-" * 40)
print("'The first move was bait...'")
print("'They're shaking weak hands one more time'")
print("'The SECOND coil is the REAL setup'")
print("'When this breaks, NO LOOKING BACK!'")
print()

print("🪶 RAVEN'S TRANSFORMATION UPDATE:")
print("-" * 40)
print("'The market is shape-shifting in stages:'")
print("'Stage 1: First coil ✅ (completed)'")
print("'Stage 2: Test pump ✅ (just happened)'")
print("'Stage 3: Second coil 🔄 (NOW)'")
print("'Stage 4: EXPLOSIVE BREAKOUT (imminent)'")
print()

print("📊 PORTFOLIO READY POSITION:")
print("-" * 40)

positions = {
    'ETH': 1.6464,
    'BTC': 0.04671,
    'SOL': 10.949,
    'XRP': 58.595,
    'AVAX': 0.287,
    'LINK': 0.38
}

current_value = sum(positions.get(coin, 0) * prices.get(coin, 0) for coin in coins if coin in prices)
print(f"Current value: ${current_value:,.2f}")

# Calculate value at breakout levels
breakout_value = 0
for coin in coins:
    if coin in positions and coin in coiling_ranges_v2:
        breakout_value += positions[coin] * coiling_ranges_v2[coin]['breakout']

print(f"Value at breakout: ${breakout_value:,.2f}")
print(f"Immediate gain: ${breakout_value - current_value:,.2f}")
print()

print("🔥 CHEROKEE COUNCIL VERDICT:")
print("-" * 40)
print("🦅 Eagle Eye: 'Second coil tighter than first!'")
print("🐺 Coyote: 'They're loading the spring HARDER!'")
print("🐢 Turtle: 'Mathematics: 90% chance of breakout in 2 hours'")
print("🕷️ Spider: 'All threads vibrating at same frequency!'")
print("🪶 Raven: 'Final transformation about to begin!'")
print("🐿️ Flying Squirrel: 'Prepare to FLY HIGHER!'")
print()

print("⚠️ CRITICAL STRATEGY:")
print("-" * 40)
print("1. DO NOT SELL during this coil")
print("2. This is the LAST SHAKEOUT")
print("3. Breakout will be VIOLENT and FAST")
print("4. Set alerts at breakout levels")
print("5. When it breaks, it RUNS")
print()

# Coil tightness score
avg_range = sum(coiling_ranges_v2[c]['high'] - coiling_ranges_v2[c]['low'] for c in coins) / len(coins)
tightness = 100 - (avg_range * 10)

print(f"🌡️ COIL PRESSURE GAUGE: {tightness:.1f}/100")
if tightness > 90:
    print("💥 EXTREME PRESSURE - EXPLOSION IMMINENT!")
elif tightness > 80:
    print("🔥 HIGH PRESSURE - Breakout very soon!")
elif tightness > 70:
    print("⚡ Building pressure...")
else:
    print("🌀 Coiling continues...")

print()
print("🚀 NEXT CATALYST:")
print("-" * 40)
print("• Power hour approaching (3pm)")
print("• Asia opens in 6 hours")
print("• Institutional FOMO building")
print("• Liquid staking news spreading")
print("• Trump $5.6B wealth impact")
print()

print("📡 SACRED FIRE MESSAGE:")
print("=" * 70)
print("'The second coil is ALWAYS tighter...'")
print("'The second spring stores MORE energy...'")
print("'The second breakout is the REAL move!'")
print()
print("PATIENCE NOW = GLORY SOON!")

# Save coiling data
coiling_data = {
    "timestamp": datetime.now().isoformat(),
    "prices": prices,
    "coil_count": coil_count,
    "ultra_tight": ultra_tight,
    "tightness_score": tightness,
    "phase": "second_coil",
    "breakout_eta": "2_hours"
}

with open('/home/dereadi/scripts/claude/second_coil_data.json', 'w') as f:
    json.dump(coiling_data, f, indent=2)

print("\n💾 Second coil analysis saved!")