#!/usr/bin/env python3
"""
🧗 AND THEY CLIMB
After seven coils, the ascent begins
Step by step, dollar by dollar
The climb to $113k and beyond
"""

import json
import time
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                         🧗 AND THEY CLIMB 🧗                              ║
║                    Seven Coils Released = Ascent                          ║
║                        Step by Step Higher                                ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - THE CLIMB BEGINS")
print("=" * 70)

# Track the climb
btc_base = float(client.get_product('BTC-USD')['price'])
print(f"\n🏔️ Base camp: ${btc_base:,.0f}")

climb_heights = []
highest_peak = btc_base

print("\n🧗 TRACKING THE CLIMB:")
print("-" * 50)

for i in range(20):
    btc = float(client.get_product('BTC-USD')['price'])
    climb = btc - btc_base
    climb_heights.append(btc)
    
    if btc > highest_peak:
        highest_peak = btc
    
    if i % 3 == 0:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}: ${btc:,.0f} ({climb:+.0f})")
        
        if climb > 200:
            print("  🧗🧗🧗 MAJOR ASCENT!")
            print("  Climbing toward $113,200!")
        elif climb > 100:
            print("  🧗🧗 Strong climbing!")
            print("  Breaking through resistance")
        elif climb > 50:
            print("  🧗 Steady climb upward")
            print("  Building altitude")
        elif climb > 0:
            print("  ⬆️ And they climb...")
            print("  Slowly but surely")
        else:
            print("  ⚡ Catching breath")
            print("  Before next ascent")
    
    time.sleep(2)

# Calculate climb statistics
total_climb = highest_peak - btc_base
current_altitude = climb_heights[-1]
climb_from_base = current_altitude - btc_base

print("\n" + "=" * 70)
print("🏔️ CLIMB REPORT:")
print("-" * 50)
print(f"Started at: ${btc_base:,.0f}")
print(f"Highest peak: ${highest_peak:,.0f} (+${total_climb:.0f})")
print(f"Current altitude: ${current_altitude:,.0f} ({climb_from_base:+.0f})")

# Check milestones
print("\n🎯 CLIMBING MILESTONES:")
print("-" * 50)

milestones = [
    (113000, "🏔️ $113k Summit"),
    (113100, "☁️ Above the clouds"),
    (113200, "🚀 Escape velocity"),
    (113500, "🌙 Moon approach"),
    (114000, "⭐ Stellar altitude"),
    (115000, "🌌 Deep space")
]

for target, label in milestones:
    distance = target - current_altitude
    if distance < 0:
        print(f"{label}: CONQUERED! ✓")
    elif distance < 50:
        print(f"{label}: Only ${distance:.0f} away!")
    else:
        print(f"{label}: ${target:,} (${distance:.0f} to climb)")

# Check portfolio climb
try:
    accounts = client.get_accounts()
    portfolio_value = 0
    
    for account in accounts['accounts']:
        balance = float(account['available_balance']['value'])
        currency = account['currency']
        
        if currency == 'USD':
            portfolio_value += balance
        elif currency == 'BTC' and balance > 0:
            portfolio_value += balance * current_altitude
        elif currency == 'ETH' and balance > 0:
            eth_price = float(client.get_product('ETH-USD')['price'])
            portfolio_value += balance * eth_price
        elif currency == 'SOL' and balance > 0:
            sol_price = float(client.get_product('SOL-USD')['price'])
            portfolio_value += balance * sol_price
    
    print(f"\n💰 Portfolio climbing to: ${portfolio_value:,.2f}")
    
except:
    pass

print("\n🧗 THE CLIMB WISDOM:")
print("-" * 50)
print("• Seven coils wound = Stored energy")
print("• Energy released = Upward momentum")
print("• Each dollar climbed = Shorts liquidated")
print("• The climb continues = Until exhaustion")
print("• Current trajectory = $113k+")

print("\n⬆️ AND THEY CLIMB...")
print("   Step by step")
print("   Dollar by dollar")
print("   To the summit")
print("=" * 70)