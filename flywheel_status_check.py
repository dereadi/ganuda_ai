#!/usr/bin/env python3
"""
🔥 FLYWHEEL STATUS CHECK
Monitor the nuclear strike and momentum build
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("🔥 FLYWHEEL STATUS CHECK")
print("=" * 70)
print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
print("=" * 70)

# Get current prices
btc = client.get_product('BTC-USD')
eth = client.get_product('ETH-USD')
btc_price = float(btc['price'])
eth_price = float(eth['price'])

print(f"\n📊 MARKET:")
print(f"BTC: ${btc_price:,.2f}")
print(f"ETH: ${eth_price:,.2f}")

# Check our nuclear strike orders
print(f"\n💥 NUCLEAR STRIKE STATUS:")
print("-" * 70)

strike_levels = [
    {"price": 109921.90, "size": 0.00276674, "name": "STRIKE 1A"},
    {"price": 110251.01, "size": 0.00276674, "name": "STRIKE 1B"},
    {"price": 110580.12, "size": 0.00368899, "name": "STRIKE 1C"}
]

closest_distance = float('inf')
closest_strike = None

for strike in strike_levels:
    distance = strike['price'] - btc_price
    distance_pct = (distance / btc_price) * 100
    
    if distance < closest_distance:
        closest_distance = distance
        closest_strike = strike
    
    if distance > 0:
        print(f"{strike['name']}: ${strike['price']:.2f} ({distance_pct:+.3f}% away)")
        
        # Visual progress bar
        progress = max(0, min(100, (1 - distance_pct/1) * 100))
        bar_length = 30
        filled = int(bar_length * progress / 100)
        bar = '█' * filled + '░' * (bar_length - filled)
        print(f"  Progress: [{bar}] {progress:.1f}%")
    else:
        print(f"{strike['name']}: ✅ SHOULD BE FILLED!")

# Momentum calculation
print(f"\n⚡ FLYWHEEL MOMENTUM:")
print("-" * 70)

if closest_distance < 100:
    print("🔥 IGNITION IMMINENT!")
    print(f"Only ${closest_distance:.2f} to first strike")
    print("Flywheel about to receive MAXIMUM FORCE")
elif closest_distance < 500:
    print("⚡ APPROACHING IGNITION")
    print(f"${closest_distance:.2f} to go")
    print("Building pressure...")
else:
    print("⏳ WAITING FOR IGNITION")
    print(f"${closest_distance:.2f} to first strike")

# Success metrics
print(f"\n📈 SUCCESS METRICS:")
print("-" * 70)

total_strike_value = sum(s['price'] * s['size'] for s in strike_levels)
print(f"Total strike value: ${total_strike_value:,.2f}")

if btc_price > 109921.90:
    print("✅ STRIKE ONE ACTIVE - Flywheel spinning!")
    momentum = "BUILDING"
elif closest_distance < 100:
    print("⚡ Pre-ignition - Maximum energy ready")
    momentum = "LOADING"
else:
    print("⏳ Armed and waiting")
    momentum = "POTENTIAL"

print(f"Momentum state: {momentum}")

# The plan
print(f"\n🎯 THE PLAN:")
print("-" * 70)
print("1. Wait for BTC to hit $109,922 (STRIKE ONE)")
print("2. Sell orders execute automatically")
print("3. Place buy orders 1% lower for profit")
print("4. Use profits for STRIKE TWO")
print("5. Flywheel achieves escape velocity")

print("\n" + "=" * 70)
print("🔥 SACRED FIRE BURNS BRIGHT")
print(f"Distance to ignition: ${closest_distance:.2f}")
print("=" * 70)