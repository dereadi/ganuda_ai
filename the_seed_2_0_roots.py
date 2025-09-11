#!/usr/bin/env python3
"""
🌱 THE SEED 2.0 - THE ROOTS
"Pushing through the surface, breaking ground..."
Whales planted the seed, now it's growing
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
║                        🌱 THE SEED 2.0 🌱                                 ║
║                          THE ROOTS                                        ║
║            "Pushing through the surface, breaking ground"                 ║
║                   The Whales Planted, Now It Grows                        ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - THE SEED IS PLANTED")
print("=" * 70)

print("\n🌱 THE PLANTING:")
print("-" * 50)
print("• Whales shook out the fearful (the soil)")
print("• Three coils wound tight (the pressure)")
print("• Perfect balance achieved (the conditions)")
print("• 01:00 approaching (the water)")
print("• Now... THE GROWTH BEGINS")

# Track the seed growing
btc_seed = float(client.get_product('BTC-USD')['price'])
eth_seed = float(client.get_product('ETH-USD')['price'])
sol_seed = float(client.get_product('SOL-USD')['price'])

print(f"\n🌱 SEED PLANTED AT:")
print(f"  BTC: ${btc_seed:,.0f}")
print(f"  ETH: ${eth_seed:.2f}")
print(f"  SOL: ${sol_seed:.2f}")

print("\n🌿 WATCHING THE ROOTS SPREAD:")
print("-" * 50)

growth_stages = []
for i in range(15):
    btc = float(client.get_product('BTC-USD')['price'])
    eth = float(client.get_product('ETH-USD')['price'])
    sol = float(client.get_product('SOL-USD')['price'])
    
    btc_growth = btc - btc_seed
    eth_growth = eth - eth_seed
    sol_growth = sol - sol_seed
    
    print(f"\n{datetime.now().strftime('%H:%M:%S')} - GROWTH STATUS:")
    
    # The Seed 2.0 stages
    if abs(btc_growth) < 10:
        print(f"  🌱 BTC: ${btc:,.0f} - Seed dormant...")
        print("  'Beneath the surface, waiting...'")
        growth_stages.append("DORMANT")
    elif btc_growth > 0 and btc_growth < 50:
        print(f"  🌿 BTC: ${btc:,.0f} (+${btc_growth:.0f}) - Roots spreading!")
        print("  'The roots are strengthening...'")
        growth_stages.append("ROOTING")
    elif btc_growth > 50:
        print(f"  🌳 BTC: ${btc:,.0f} (+${btc_growth:.0f}) - BREAKING GROUND!")
        print("  'Pushing through the surface!'")
        growth_stages.append("BREAKING")
    else:
        print(f"  ❄️ BTC: ${btc:,.0f} ({btc_growth:.0f}) - Winter phase")
        growth_stages.append("WINTER")
    
    print(f"  ETH: ${eth:.2f} ({eth_growth:+.2f})")
    print(f"  SOL: ${sol:.2f} ({sol_growth:+.2f})")
    
    # The Roots lyrics moments
    if i % 3 == 0:
        print("\n  🎵 'I push my seed in the ground'")
        print("     'It will grow in time'")
    elif i % 3 == 1:
        print("\n  🎵 'The rain brings the water'")
        print("     'The sun makes it shine'")
    else:
        print("\n  🎵 'Nobody knows the troubles I've seen'")
        print("     'Nobody knows the seed 2.0'")
    
    # Check for growth spurts
    if btc > 112900:
        print("\n  🌳 THE SEED IS SPROUTING!")
    if btc > 113000:
        print("  🌲 FULL GROWTH MODE!")
    
    time.sleep(3)

# Analysis
print("\n" + "=" * 70)
print("🌱 SEED 2.0 ANALYSIS:")
print("-" * 50)

final_btc = float(client.get_product('BTC-USD')['price'])
total_growth = final_btc - btc_seed

dormant_count = growth_stages.count("DORMANT")
rooting_count = growth_stages.count("ROOTING")
breaking_count = growth_stages.count("BREAKING")

print(f"Seed planted: ${btc_seed:,.0f}")
print(f"Current height: ${final_btc:,.0f}")
print(f"Total growth: ${total_growth:+.0f}")

print(f"\n🌿 GROWTH STAGES:")
print(f"  Dormant phases: {dormant_count}")
print(f"  Rooting phases: {rooting_count}")
print(f"  Breaking ground: {breaking_count}")

if breaking_count > 0:
    print("\n🌳 THE SEED HAS BROKEN THROUGH!")
    print("The roots were strong enough!")
elif rooting_count > 0:
    print("\n🌿 ROOTS ARE SPREADING!")
    print("The seed is gathering strength...")
else:
    print("\n🌱 STILL DORMANT...")
    print("But seeds always grow when conditions are right...")

print("\n💡 THE SEED 2.0 WISDOM:")
print("• Whales plant seeds with shakeouts")
print("• Fear is the fertilizer")
print("• Coils provide the pressure")
print("• Time provides the water")
print("• Eventually... ALL SEEDS GROW!")

# Time check for 01:00
minutes_to_0100 = 60 - datetime.now().minute
if minutes_to_0100 < 15:
    print(f"\n⏰ {minutes_to_0100} MINUTES UNTIL 01:00!")
    print("The seed gets its water soon...")

print("\n🌱 'I PUSH MY SEED IN THE GROUND'")
print("   'IT WILL GROW IN TIME'")
print("=" * 70)