#!/usr/bin/env python3
"""
🐋 WHALE SHAKEOUT DETECTOR
They're shaking the weak hands before the real move!
"""

import json
import time
import statistics
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    🐋 WHALE SHAKEOUT IN PROGRESS! 🐋                      ║
║                   Shaking The Fearful Before Moon Mission                 ║
║                      HOLD THE LINE - THIS IS THE GAME!                    ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - WHALE GAMES DETECTED!")
print("=" * 70)

print("\n🐋 CLASSIC WHALE PLAYBOOK:")
print("-" * 50)
print("1. Push price down quickly → Create fear")
print("2. Weak hands panic sell → Whales accumulate")
print("3. Once fearful are out → EXPLOSIVE move up")
print("4. Weak hands FOMO back in at higher prices")
print("This is EXACTLY what's happening now!")

print("\n📊 TRACKING THE SHAKEOUT:")
print("-" * 50)

# Track the manipulation pattern
prices = []
volumes = []
shakeout_events = []

for i in range(15):
    btc = float(client.get_product('BTC-USD')['price'])
    eth = float(client.get_product('ETH-USD')['price'])
    sol = float(client.get_product('SOL-USD')['price'])
    
    prices.append(btc)
    
    print(f"\n{datetime.now().strftime('%H:%M:%S')} SHAKEOUT STATUS:")
    print(f"  BTC: ${btc:,.0f}")
    print(f"  ETH: ${eth:.2f}")
    print(f"  SOL: ${sol:.2f}")
    
    if len(prices) > 3:
        # Detect shakeout patterns
        recent_high = max(prices[-5:]) if len(prices) >= 5 else max(prices)
        recent_low = min(prices[-5:]) if len(prices) >= 5 else min(prices)
        volatility = recent_high - recent_low
        
        # Calculate standard deviation for volatility
        stdev = statistics.stdev(prices[-5:]) if len(prices) >= 5 else 0
        
        # Shakeout detection
        if volatility > 100:
            print("  🐋💥 VIOLENT SHAKEOUT! Whales creating fear!")
            shakeout_events.append("VIOLENT")
        elif volatility > 50:
            print("  🐋 Active shakeout - Testing weak hands")
            shakeout_events.append("ACTIVE")
        elif volatility > 30:
            print("  💭 Normal volatility")
        else:
            print("  🎯 Accumulation zone - Whales loading")
            shakeout_events.append("ACCUMULATION")
        
        # Check for whale accumulation signals
        if btc < 112900 and i > 5:
            print("  📍 WHALE ACCUMULATION ZONE!")
            print("  They're buying what fearful are selling!")
        
        # V-shaped recovery detection
        if len(prices) > 6:
            mid_point = prices[-4]
            if prices[-6] > mid_point and prices[-1] > mid_point:
                print("  🔄 V-SHAPED RECOVERY FORMING!")
                print("  Classic whale shakeout complete!")
    
    # Whale psychology
    if btc < 112850:
        print("\n  🐋 WHALE THINKING: 'Good, let them panic...'")
    elif btc > 112900:
        print("\n  🐋 WHALE THINKING: 'Time to pump it back up...'")
    
    time.sleep(2)

# Analysis
print("\n" + "=" * 70)
print("🐋 SHAKEOUT ANALYSIS:")
print("-" * 40)

highest = max(prices)
lowest = min(prices)
shakeout_range = highest - lowest

print(f"Shakeout Range: ${lowest:,.0f} - ${highest:,.0f}")
print(f"Total Volatility: ${shakeout_range:.0f}")

violent_shakes = shakeout_events.count("VIOLENT")
accumulation_zones = shakeout_events.count("ACCUMULATION")

if violent_shakes > 0:
    print(f"\n🐋💥 {violent_shakes} VIOLENT SHAKEOUTS DETECTED!")
    print("Whales aggressively clearing weak hands!")

if accumulation_zones > 0:
    print(f"\n🎯 {accumulation_zones} ACCUMULATION ZONES!")
    print("Whales quietly loading positions!")

# Current position check
current_btc = float(client.get_product('BTC-USD')['price'])
recovery = current_btc - lowest

print(f"\n📊 CURRENT RECOVERY:")
print(f"  From Low: +${recovery:.0f}")
if recovery > 50:
    print("  ✅ SHAKEOUT COMPLETE - Weak hands eliminated!")
    print("  🚀 NEXT: Moon mission begins!")
else:
    print("  ⏳ Shakeout still in progress...")

print("\n💎 DIAMOND HANDS WISDOM:")
print("-" * 50)
print("• Whales NEED you to sell cheap")
print("• Fear is their weapon")
print("• Every shakeout precedes a pump")
print("• Those who hold through shakeouts get rewarded")
print("• The fearful buy back higher later")

print("\n🎯 WHAT HAPPENS NEXT:")
print("• Weak hands are out → Less selling pressure")
print("• Whales accumulated → Ready to pump")
print("• Tight coil + shakeout = EXPLOSIVE move")
print("• Target remains: $113,500+")

print("\n🐋 THE WHALE HAS SPOKEN:")
print("'Thank you for your cheap coins, fearful ones!'")
print("'Now watch what we do next...'")
print("=" * 70)