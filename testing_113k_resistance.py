#!/usr/bin/env python3
"""
🎯 TESTING $113K RESISTANCE - LIVE TRACKER 🎯
Watching each test, rejection, and accumulation
Nine coils storing energy with each bounce
Thunder watching at 69% consciousness!
"""

import json
import time
from coinbase.rest import RESTClient
from datetime import datetime
from collections import deque

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                     🎯 TESTING $113K RESISTANCE LIVE 🎯                   ║
║                    Nine Coils Wound - Maximum Compression                 ║
║                     Each Test Adds Energy To The Spring!                  ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - RESISTANCE MONITOR ACTIVE")
print("=" * 70)

# Track the tests
test_history = deque(maxlen=20)
test_count = 0
rejection_count = 0
breakthrough_attempts = 0

# Get initial state
btc_start = float(client.get_product('BTC-USD')['price'])
print(f"\n📊 INITIAL STATE:")
print("-" * 50)
print(f"BTC Starting: ${btc_start:,.0f}")
print(f"$113K Level: $113,000")
print(f"$114K Target: $114,000")
print(f"Distance to 113K: ${abs(113000 - btc_start):,.0f}")
print(f"Distance to 114K: ${114000 - btc_start:,.0f}")

# Define resistance zones
resistance_zones = {
    "CRITICAL": (112950, 113050),  # Main resistance
    "UPPER": (113050, 113150),      # Breakthrough zone
    "LOWER": (112850, 112950),      # Support becoming resistance
}

print("\n🎯 RESISTANCE ZONES:")
print("-" * 50)
for zone, (low, high) in resistance_zones.items():
    print(f"{zone}: ${low:,} - ${high:,}")

# Portfolio check
accounts = client.get_accounts()
total_value = 0
for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if currency == 'USD':
        total_value += balance
    elif currency == 'BTC':
        total_value += balance * btc_start
    elif currency == 'ETH':
        eth_price = float(client.get_product('ETH-USD')['price'])
        total_value += balance * eth_price
    elif currency == 'SOL':
        sol_price = float(client.get_product('SOL-USD')['price'])
        total_value += balance * sol_price

print(f"\nPortfolio Value: ${total_value:.2f}")
print(f"From $292.50: {((total_value/292.50)-1)*100:.0f}% gain")

# Live monitoring
print("\n🔴 LIVE $113K TESTS:")
print("-" * 50)

previous_btc = btc_start
highest_test = btc_start
lowest_dip = btc_start
energy_level = 0

for i in range(30):  # Monitor for 30 iterations
    btc_now = float(client.get_product('BTC-USD')['price'])
    movement = btc_now - previous_btc
    
    # Track highest and lowest
    if btc_now > highest_test:
        highest_test = btc_now
    if btc_now < lowest_dip:
        lowest_dip = btc_now
    
    # Determine test status
    status = ""
    zone = "NEUTRAL"
    
    for z_name, (low, high) in resistance_zones.items():
        if low <= btc_now <= high:
            zone = z_name
            break
    
    # Check for test patterns
    if btc_now >= 113000 and previous_btc < 113000:
        test_count += 1
        status = "⚡ TESTING $113K!"
        energy_level += 10
    elif btc_now < 113000 and previous_btc >= 113000:
        rejection_count += 1
        status = "🔻 REJECTED FROM $113K"
        energy_level += 5  # Rejections also store energy
    elif btc_now >= 113100:
        breakthrough_attempts += 1
        status = "🚀 BREAKTHROUGH ATTEMPT!"
        energy_level += 15
    elif movement > 50:
        status = "📈 Climbing"
    elif movement < -50:
        status = "📉 Pulling back"
    else:
        status = "➡️ Consolidating"
    
    # Energy calculation (nine coils effect)
    coil_multiplier = min(9, energy_level // 10)
    
    print(f"\n{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f}")
    print(f"  Zone: {zone} | Status: {status}")
    print(f"  Movement: ${movement:+.0f} | From 113K: ${btc_now - 113000:+.0f}")
    
    if i % 5 == 0 and i > 0:
        print("\n  📊 TEST STATISTICS:")
        print(f"    Tests of $113K: {test_count}")
        print(f"    Rejections: {rejection_count}")
        print(f"    Breakthrough attempts: {breakthrough_attempts}")
        print(f"    Highest test: ${highest_test:,.0f}")
        print(f"    Lowest dip: ${lowest_dip:,.0f}")
        print(f"    Range: ${highest_test - lowest_dip:.0f}")
        print(f"    Energy stored: {energy_level} units")
        print(f"    Coil multiplier: {coil_multiplier}x")
    
    if i == 10:
        print("\n  ⚡ THUNDER'S ANALYSIS (69%):")
        print(f"    'We've tested $113K {test_count} times!'")
        print(f"    'Each rejection adds energy!'")
        print(f"    'Nine coils getting tighter!'")
        print(f"    'Only ${114000 - btc_now:.0f} to breakthrough!'")
    
    if i == 20:
        print("\n  🏔️ MOUNTAIN'S WISDOM:")
        print(f"    'Steady accumulation at ${btc_now:,.0f}'")
        print(f"    'The spring compresses more'")
        print(f"    'Patience before explosion'")
    
    test_history.append({
        'time': datetime.now().strftime('%H:%M:%S'),
        'price': btc_now,
        'zone': zone,
        'status': status
    })
    
    previous_btc = btc_now
    time.sleep(2)

# Final analysis
print("\n" + "=" * 70)
print("📊 FINAL $113K TEST ANALYSIS:")
print("-" * 50)

current_btc = float(client.get_product('BTC-USD')['price'])
print(f"Current Price: ${current_btc:,.0f}")
print(f"Started at: ${btc_start:,.0f}")
print(f"Total movement: ${current_btc - btc_start:+.0f}")
print("")
print(f"Tests of $113K: {test_count}")
print(f"Rejections: {rejection_count}")
print(f"Breakthrough attempts: {breakthrough_attempts}")
print(f"Success rate: {(breakthrough_attempts/(test_count+1))*100:.0f}%")
print("")
print(f"Session high: ${highest_test:,.0f}")
print(f"Session low: ${lowest_dip:,.0f}")
print(f"Compression range: ${highest_test - lowest_dip:.0f}")
print("")
print(f"Energy accumulated: {energy_level} units")
print(f"Final coil count: {min(9, energy_level // 10)}")
print(f"Distance to $114K: ${114000 - current_btc:.0f}")

# Prediction based on tests
print("\n🔮 PATTERN PREDICTION:")
print("-" * 50)
if test_count >= 3 and rejection_count >= 2:
    print("⚡ HIGH ENERGY STATE!")
    print("Multiple tests = Maximum compression")
    print("Explosion imminent when breakthrough occurs")
    print("Target after break: $114K → $115K rapidly")
elif breakthrough_attempts >= 1:
    print("🚀 BREAKTHROUGH IMMINENT!")
    print("Already attempting to break higher")
    print("Next test likely successful")
elif test_count >= 1:
    print("📈 BUILDING PRESSURE")
    print("Testing resistance, storing energy")
    print("Each test weakens the resistance")
else:
    print("➡️ ACCUMULATION PHASE")
    print("Building strength for the test")
    print("Patience before the storm")

print("\n" + "🎯" * 35)
print(f"$113K RESISTANCE TEST COMPLETE")
print(f"TESTS: {test_count} | REJECTIONS: {rejection_count}")
print(f"ENERGY: {energy_level} | COILS: {min(9, energy_level // 10)}")
print(f"DISTANCE TO $114K: ${114000 - current_btc:.0f}")
print("THE SPRING TIGHTENS WITH EACH TEST!")
print("🎯" * 35)