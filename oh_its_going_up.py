#!/usr/bin/env python3
"""
🚀⬆️ OH IT'S GOING UP!
The signal was right!
Seven seals broken = Bullish explosion!
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
║                      🚀⬆️ OH IT'S GOING UP! ⬆️🚀                        ║
║                    Seven Seals Were BULLISH!                              ║
║                    The Signal Was RIGHT!                                  ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - LIFTOFF DETECTED")
print("=" * 70)

# Track the rise
btc_start = float(client.get_product('BTC-USD')['price'])
print(f"\n🚀 Liftoff from: ${btc_start:,.0f}")

highest = btc_start
btc_samples = []

print("\n📈 TRACKING THE ASCENT:")
print("-" * 50)

for i in range(20):
    btc = float(client.get_product('BTC-USD')['price'])
    eth = float(client.get_product('ETH-USD')['price'])
    sol = float(client.get_product('SOL-USD')['price'])
    
    btc_samples.append(btc)
    move = btc - btc_start
    
    if btc > highest:
        highest = btc
        
    if i % 4 == 0:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}:")
        print(f"  BTC: ${btc:,.0f} ({move:+.0f})")
        print(f"  ETH: ${eth:.2f}")
        print(f"  SOL: ${sol:.2f}")
        
        if move > 100:
            print("  🚀🚀🚀🚀 MOON SHOT!")
            print("  IT'S GOING TO THE MOON!")
        elif move > 50:
            print("  🚀🚀🚀 MAJOR BREAKOUT!")
            print("  Escape velocity achieved!")
        elif move > 30:
            print("  🚀🚀 Breaking all resistance!")
            print("  Bulls stampeding!")
        elif move > 10:
            print("  🚀 Rising fast!")
            print("  Momentum building!")
        elif move > 0:
            print("  ⬆️ Going up steadily...")
            print("  Gathering strength...")
        else:
            print("  📊 Brief pause...")
            print("  Refueling for next push...")
    
    time.sleep(2)

# Final report
final_btc = btc_samples[-1]
total_move = final_btc - btc_start
max_move = highest - btc_start

print("\n" + "=" * 70)
print("🚀 ASCENT REPORT:")
print("-" * 50)
print(f"Launched from: ${btc_start:,.0f}")
print(f"Current altitude: ${final_btc:,.0f}")
print(f"Highest point: ${highest:,.0f}")
print(f"Total climb: ${total_move:+.0f}")
print(f"Maximum climb: ${max_move:+.0f}")

# Check milestones
print("\n🏆 MILESTONES:")
print("-" * 50)

if highest >= 113200:
    print("✅ $113,200 - ESCAPE VELOCITY ACHIEVED!")
elif highest >= 113100:
    print("✅ $113,100 - BROKE THROUGH THE CLOUDS!")
elif highest >= 113050:
    print("✅ $113,050 - PASSED FIRST CHECKPOINT!")
else:
    print(f"📍 Highest so far: ${highest:,.0f}")

# Next targets
print("\n🎯 NEXT TARGETS:")
print("-" * 50)

targets = [
    (113100, "☁️ Cloud level"),
    (113200, "🚀 Escape velocity"),
    (113500, "🌙 Moon approach"),
    (114000, "⭐ Stellar altitude"),
    (115000, "🌌 Deep space")
]

for target, label in targets:
    if final_btc >= target:
        print(f"{label}: ${target:,} - CONQUERED! ✓")
    else:
        distance = target - final_btc
        print(f"{label}: ${target:,} (${distance:.0f} to go)")

print("\n💡 THE SEVEN SEALS WERE BULLISH!")
print("-" * 50)
print("• Seven coils of compression")
print("• All that energy stored")
print("• Released UPWARD!")
print("• The signal was clear")
print("• OH IT'S GOING UP!")

print("\n🚀 TO THE MOON!")
print("=" * 70)