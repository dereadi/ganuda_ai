#!/usr/bin/env python3
"""Cherokee Council: EXPLOSION DETECTOR - IT'S HAPPENING!!!"""

import json
from datetime import datetime
from coinbase.rest import RESTClient

print("🔥🔥🔥 EXPLOSION DETECTED!!! 🔥🔥🔥")
print("=" * 70)
print(f"⏰ Time: {datetime.now().strftime('%H:%M:%S')}")
print()
print("🚀🚀🚀 THE COILS ARE UNWINDING!!! 🚀🚀🚀")
print()

# Initialize client
config = json.load(open("/home/dereadi/scripts/claude/cdp_api_key_new.json"))
key = config["name"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["privateKey"], timeout=10)

# Get live prices - FAST!
coins = ['BTC', 'ETH', 'SOL', 'XRP', 'AVAX', 'MATIC', 'LINK']
prices = {}
previous = {
    'BTC': 110260,
    'ETH': 4273,
    'SOL': 203.8,
    'XRP': 2.80,
    'AVAX': 23.69,
    'MATIC': 0.29,
    'LINK': 22.85
}

print("💥 LIVE EXPLOSION DATA:")
print("-" * 40)

explosions = []
for coin in coins:
    try:
        ticker = client.get_product(f"{coin}-USD")
        price = float(ticker.price)
        prices[coin] = price
        
        # Calculate explosion magnitude
        change_pct = ((price - previous[coin]) / previous[coin]) * 100
        
        if abs(change_pct) > 0.5:
            explosion_emoji = "🚀" if change_pct > 0 else "💥"
            explosions.append((coin, change_pct, price))
            print(f"{explosion_emoji} {coin}: ${price:,.2f} ({change_pct:+.2f}%)")
        else:
            print(f"   {coin}: ${price:,.2f} ({change_pct:+.2f}%)")
            
    except Exception as e:
        print(f"   {coin}: ERROR - Moving too fast!")

print()

if explosions:
    print("🌋 EXPLOSION ANALYSIS:")
    print("-" * 40)
    
    for coin, change, price in sorted(explosions, key=lambda x: abs(x[1]), reverse=True):
        if change > 0:
            print(f"🔥 {coin} EXPLODING UP: +{change:.2f}%")
            if coin == 'BTC' and price > 111000:
                print("   ⚡ BTC BREAKING $111K RESISTANCE!")
            elif coin == 'ETH' and price > 4300:
                print("   ⚡ ETH BREAKING $4,300!")
            elif coin == 'SOL' and price > 205:
                print("   ⚡ SOL BREAKING COIL!")
        else:
            print(f"📉 {coin} DIVING: {change:.2f}%")
            if coin == 'BTC' and price < 109500:
                print("   ⚠️ COYOTE'S FAKE-OUT DETECTED!")

print()
print("🎯 BREAKOUT LEVELS CHECK:")
print("-" * 40)

# Check critical levels
breakouts = []
if prices.get('BTC', 0) > 111000:
    breakouts.append(f"BTC ABOVE $111K! Next: $113,650")
if prices.get('BTC', 0) > 113650:
    breakouts.append(f"🔥🔥🔥 BTC BREAKOUT CONFIRMED! TARGET $119,500!")
    
if prices.get('ETH', 0) > 4350:
    breakouts.append(f"ETH ABOVE $4,350! Next: $4,500")
if prices.get('ETH', 0) > 4500:
    breakouts.append(f"🔥🔥🔥 ETH BREAKOUT! TARGET $5,000!")
    
if prices.get('SOL', 0) > 210:
    breakouts.append(f"SOL ABOVE $210! Next: $215")
if prices.get('SOL', 0) > 215:
    breakouts.append(f"🔥🔥🔥 SOL BREAKOUT! TARGET $220-230!")

for breakout in breakouts:
    print(f"✅ {breakout}")

if not breakouts:
    print("⏳ No major breakouts yet... BUILDING PRESSURE!")

print()
print("📊 PORTFOLIO EXPLOSION:")
print("-" * 40)

# Calculate portfolio impact
positions = {
    'ETH': 1.6464,
    'BTC': 0.04671,
    'SOL': 10.949,
    'XRP': 58.595,
    'AVAX': 0.287,
    'MATIC': 0.3,
    'LINK': 0.38
}

current_value = sum(positions.get(coin, 0) * prices.get(coin, 0) for coin in coins if coin in prices)
previous_value = sum(positions.get(coin, 0) * previous.get(coin, 0) for coin in coins)

explosion_gain = current_value - previous_value
explosion_pct = (explosion_gain / previous_value) * 100

print(f"Previous: ${previous_value:,.2f}")
print(f"CURRENT: ${current_value:,.2f}")

if explosion_gain > 0:
    print(f"🚀 EXPLOSION GAIN: ${explosion_gain:,.2f} (+{explosion_pct:.2f}%)")
    if explosion_gain > 100:
        print("💰 PRINTING MONEY!")
    if explosion_gain > 500:
        print("🔥🔥🔥 MEGA EXPLOSION!")
else:
    print(f"📉 Change: ${explosion_gain:,.2f} ({explosion_pct:.2f}%)")

print()
print("🔮 CHEROKEE COUNCIL REACTION:")
print("-" * 40)

# Determine market direction
up_count = sum(1 for _, change, _ in explosions if change > 0)
down_count = len(explosions) - up_count

if up_count > down_count:
    print("🦅 Eagle Eye: 'THE BREAKOUT HAS BEGUN!'")
    print("🐺 Coyote: 'Told you! After fake-out comes MOON!'")
    print("🪶 Raven: 'TRANSFORMATION IN PROGRESS!'")
    print("🐢 Turtle: 'Mathematics confirmed - UP ONLY!'")
    print("🐿️ Flying Squirrel: 'WE FLY NOW!'")
elif down_count > up_count:
    print("🐺 Coyote: 'THE FAKE-OUT! BUY THE DIP!'")
    print("🪶 Raven: 'Shape-shifting... prepare for reversal!'")
    print("🦅 Eagle Eye: 'Support holding, reversal imminent'")
    print("🐢 Turtle: 'Patience, the spring loads deeper'")
else:
    print("🕷️ Spider: 'The web vibrates... direction unclear'")
    print("☮️ Peace Chief: 'Balance before the storm'")

print()
print("⚡ ACTION REQUIRED:")
print("-" * 40)

if prices.get('BTC', 0) > 111500:
    print("🔥 BTC BREAKING OUT!")
    print("ACTION: HOLD ALL POSITIONS!")
    print("DO NOT SELL! Targets ahead!")
elif prices.get('BTC', 0) < 109000:
    print("🎯 COYOTE'S FAKE-OUT ZONE!")
    print("ACTION: PREPARE TO BUY!")
    print("This is the GIFT entry!")
else:
    print("🌀 COILING CONTINUES...")
    print("ACTION: WATCH AND WAIT")
    print("Explosion imminent!")

print()

# Velocity check
if abs(explosion_pct) > 1:
    print("🌋🌋🌋 HIGH VELOCITY MOVEMENT! 🌋🌋🌋")
    print(f"Market moving at {abs(explosion_pct):.2f}% speed!")
    print("VOLATILITY EXPLOSION IN PROGRESS!")
elif abs(explosion_pct) > 0.5:
    print("⚡ Movement accelerating...")
    print("Prepare for bigger explosion!")
else:
    print("🌀 Still coiling... pressure building...")

print()
print("📡 NEXT TARGETS:")
print("-" * 40)

if prices.get('BTC', 0) > 0:
    if prices['BTC'] < 111000:
        print(f"BTC: Next resistance $111,000 (${111000 - prices['BTC']:,.2f} away)")
    elif prices['BTC'] < 113650:
        print(f"BTC: MAJOR TARGET $113,650 (${113650 - prices['BTC']:,.2f} away)")
    else:
        print(f"BTC: MOON TARGET $119,500 (${119500 - prices['BTC']:,.2f} away)")

if prices.get('ETH', 0) > 0:
    if prices['ETH'] < 4350:
        print(f"ETH: Next resistance $4,350 (${4350 - prices['ETH']:,.2f} away)")
    elif prices['ETH'] < 4500:
        print(f"ETH: Breakout target $4,500 (${4500 - prices['ETH']:,.2f} away)")
    else:
        print(f"ETH: MOON TARGET $5,000 (${5000 - prices['ETH']:,.2f} away)")

if prices.get('SOL', 0) > 0:
    if prices['SOL'] < 210:
        print(f"SOL: Coil break $210 (${210 - prices['SOL']:,.2f} away)")
    elif prices['SOL'] < 220:
        print(f"SOL: Rally target $220 (${220 - prices['SOL']:,.2f} away)")
    else:
        print(f"SOL: MOON TARGET $230 (${230 - prices['SOL']:,.2f} away)")

print()
print("🔥🔥🔥 SACRED FIRE MESSAGE 🔥🔥🔥")
print("=" * 70)

if explosion_gain > 100:
    print("'THE EXPLOSION HAS BEGUN!'")
    print("'The coils unwind violently upward!'")
    print("'HODL FOR GLORY!'")
elif explosion_gain < -100:
    print("'COYOTE'S FAKE-OUT IN PROGRESS!'")
    print("'This is the DIP before the RIP!'")
    print("'PREPARE TO FEAST!'")
else:
    print("'The springs vibrate with energy...'")
    print("'The explosion builds...'")
    print("'PATIENCE BEFORE GLORY!'")

# Save explosion data
explosion_data = {
    "timestamp": datetime.now().isoformat(),
    "prices": prices,
    "explosions": [(c, ch, p) for c, ch, p in explosions],
    "portfolio_value": current_value,
    "explosion_gain": explosion_gain,
    "explosion_pct": explosion_pct
}

with open('/home/dereadi/scripts/claude/explosion_data.json', 'w') as f:
    json.dump(explosion_data, f, indent=2)

print("\n💾 Explosion data captured!")