#!/usr/bin/env python3
"""
🔥💃 HOT TO GO - CHAPPELL ROAN! 💃🔥
Thunder at 69%: "H-O-T-T-O-G-O COILING FOR EXPLOSION!"
You can take me hot to go!
The coil is tightening!
Snap your fingers, snap your neck!
BTC coiling at $112.5K!
Ready to explode to $114K!
The spring is loaded - HOT TO GO!
"""

import json
import time
from coinbase.rest import RESTClient
from datetime import datetime
import math

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                      🔥 HOT TO GO - CHAPPELL ROAN! 🔥                     ║
║                    BTC Coiling Like a Loaded Spring! 🌀                    ║
║                 "H-O-T-T-O-G-O" - Ready to EXPLODE! 💥                    ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - COILING ANALYSIS")
print("=" * 70)

# Get current prices
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

# Track the coil
print("\n💃 H-O-T-T-O-G-O SPELL IT OUT:")
print("-" * 50)
print(f"H - HOLDING at ${btc:,.0f}")
print(f"O - OSCILLATING in tight range")
print(f"T - TIGHTENING the coil")
print(f"T - TENSION building")
print(f"O - OPPORTUNITY incoming")
print(f"G - GO time at $114K!")
print(f"O - OUTBREAK imminent!")

# Check portfolio
accounts = client.get_accounts()
total_value = 0

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if balance > 0.00001:
        if currency == 'USD':
            total_value += balance
        elif currency == 'BTC':
            total_value += balance * btc
        elif currency == 'ETH':
            total_value += balance * eth
        elif currency == 'SOL':
            total_value += balance * sol
        else:
            try:
                price = float(client.get_product(f'{currency}-USD')['price'])
                total_value += balance * price
            except:
                pass

print("\n🌀 COILING STATUS:")
print("-" * 50)
print(f"BTC: ${btc:,.0f} - Coiled and loaded")
print(f"Portfolio: ${total_value:.2f}")
print(f"From $292.50: {((total_value/292.50)-1)*100:.0f}% gains")
print(f"Distance to explosion: ${114000 - btc:.0f}")

# Track the coil tightening
print("\n🔥 LIVE COIL MONITORING - HOT TO GO:")
print("-" * 50)

coil_high = btc
coil_low = btc
coil_range_history = []
previous_btc = btc

for i in range(12):
    btc_now = float(client.get_product('BTC-USD')['price'])
    sol_now = float(client.get_product('SOL-USD')['price'])
    
    # Update coil boundaries
    if btc_now > coil_high:
        coil_high = btc_now
    if btc_now < coil_low:
        coil_low = btc_now
    
    coil_range = coil_high - coil_low
    coil_range_history.append(coil_range)
    
    # Calculate coil tightness (lower = tighter)
    if coil_range < 50:
        tightness = "🌀🌀🌀 SUPER TIGHT!"
        action = "EXPLOSION IMMINENT!"
    elif coil_range < 100:
        tightness = "🌀🌀 Very tight"
        action = "Building pressure"
    elif coil_range < 200:
        tightness = "🌀 Tightening"
        action = "Coiling up"
    else:
        tightness = "⭕ Loose"
        action = "Gathering energy"
    
    print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f}")
    print(f"  Range: ${coil_range:.0f} | {tightness}")
    print(f"  Action: {action}")
    
    if i == 3:
        print("  💃 'Snap your fingers, snap your neck!'")
        print(f"     Coil snapping at ${btc_now:,.0f}!")
    
    if i == 6:
        print("  🔥 'You can take me hot to go!'")
        print(f"     Ready to go at ${btc_now:,.0f}!")
    
    if i == 9:
        print("  💥 'H-O-T-T-O-G-O!'")
        print(f"     Spelling out gains at {((total_value/292.50)-1)*100:.0f}%!")
    
    time.sleep(1.2)

# Calculate coil energy
print("\n⚡ COIL ENERGY PHYSICS:")
print("-" * 50)
avg_range = sum(coil_range_history) / len(coil_range_history) if coil_range_history else 100
compression_ratio = max(200 - avg_range, 0) / 200  # 0 to 1
stored_energy = compression_ratio ** 2 * 1000  # Quadratic energy storage

print(f"Average coil range: ${avg_range:.0f}")
print(f"Compression ratio: {compression_ratio * 100:.1f}%")
print(f"Stored energy: {stored_energy:.0f} units")
print(f"Explosion potential: ${stored_energy * 10:.0f} move")

if compression_ratio > 0.8:
    print("🚨 CRITICAL COMPRESSION - EXPLOSION ANY MOMENT!")
elif compression_ratio > 0.6:
    print("⚠️ HIGH COMPRESSION - Prepare for breakout!")
elif compression_ratio > 0.4:
    print("📊 MODERATE COMPRESSION - Building nicely")
else:
    print("📈 LOW COMPRESSION - Still gathering")

# Thunder's HOT TO GO wisdom
print("\n⚡ THUNDER'S HOT TO GO WISDOM (69%):")
print("-" * 50)
print("'THE COIL IS HOT TO GO!'")
print("")
print("Chappell Roan energy:")
print("• 'Snap your fingers' = Quick moves coming")
print("• 'Snap your neck' = Whiplash to $114K")
print("• 'Hot to go' = Ready RIGHT NOW")
print(f"• Current coil: ${coil_low:.0f} - ${coil_high:.0f}")
print("")
print("The dance:")
print("• Hands up (portfolio rising)")
print(f"• Spell it out (H-O-T = ${btc:,.0f})")
print("• Take me hot to go ($114K)")

# Breakout targets
print("\n🎯 BREAKOUT TARGETS WHEN COIL SNAPS:")
print("-" * 50)
print(f"Immediate: $113,000 ({113000 - btc:.0f} away)")
print(f"Primary: $114,000 ({114000 - btc:.0f} away)")
print(f"Secondary: $115,000 ({115000 - btc:.0f} away)")
print(f"Moon: $120,000 ({120000 - btc:.0f} away)")
print("")
print(f"Your portfolio at each level:")
print(f"• $113K: ${total_value * (113000/btc):.2f}")
print(f"• $114K: ${total_value * (114000/btc):.2f}")
print(f"• $115K: ${total_value * (115000/btc):.2f}")
print(f"• $120K: ${total_value * (120000/btc):.2f}")

# Dance instructions
print("\n💃 THE HOT TO GO DANCE:")
print("-" * 50)
print("When the coil breaks:")
print("1. Hands up - Portfolio explodes")
print("2. Spell it out - H-O-T-T-O-G-O")
print("3. Snap fingers - Quick profits")
print("4. Snap neck - Look at gains")
print("5. Take me hot to go - Ride to $114K")

# Final coil check
final_btc = float(client.get_product('BTC-USD')['price'])
final_sol = float(client.get_product('SOL-USD')['price'])
final_range = coil_high - coil_low

print("\n🔥 FINAL HOT TO GO STATUS:")
print("-" * 50)
print(f"BTC: ${final_btc:,.0f}")
print(f"SOL: ${final_sol:.2f}")
print(f"Coil range: ${final_range:.0f}")
print(f"Portfolio: ${total_value:.2f}")
print("")

if final_range < 100:
    print("🌀🌀🌀 COIL SUPER TIGHT - HOT TO GO!")
    print("EXPLOSION TO $114K IMMINENT!")
else:
    print(f"Coiling at ${final_btc:,.0f}")
    print("Building energy for breakout!")

print(f"\n{'🔥' * 35}")
print("H-O-T-T-O-G-O!")
print(f"COILED AT ${final_btc:,.0f}!")
print(f"READY TO EXPLODE!")
print("SNAP YOUR FINGERS!")
print("TAKE ME HOT TO GO!")
print("💃" * 35)