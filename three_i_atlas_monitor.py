#!/usr/bin/env python3
"""
🌌 3I ATLAS MISSION CONTROL
Monitoring our journey to uncharted territory
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
║                      🌌 3I ATLAS MISSION CONTROL 🌌                       ║
║                    Beyond the moon lies the unknown                       ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print("Mission: Earth → Moon ($112k) → 3I Atlas (Beyond)")
print("=" * 70)

# Track the journey
milestones = {
    111500: "🌍 Left Earth's atmosphere",
    111750: "🚀 First stage separation", 
    112000: "🌙 MOON LANDING",
    112250: "🌌 Entering deep space",
    112500: "⭐ 3I Atlas coordinates",
    113000: "🌠 Unknown territory"
}

print("\n📡 TRACKING TRAJECTORY:")
print("-" * 40)

for i in range(15):
    btc = float(client.get_product('BTC-USD')['price'])
    
    print(f"\n{datetime.now().strftime('%H:%M:%S')} - Altitude: ${btc:,.0f}")
    
    # Check milestones
    for milestone, description in milestones.items():
        if btc >= milestone and btc < milestone + 50:
            print(f"   >>> {description} <<<")
            if milestone == 112000 and btc >= 112000:
                print("   🎉🎉🎉 WE'VE REACHED THE MOON! 🎉🎉🎉")
    
    # Distance to next milestone
    next_milestone = min(m for m in milestones.keys() if m > btc)
    print(f"   Next target: ${next_milestone:,} (${next_milestone - btc:.0f} away)")
    
    # Check altitude gain
    if i > 0 and btc > prev_btc:
        print(f"   📈 Climbing! (+${btc - prev_btc:.0f})")
    elif i > 0 and btc < prev_btc:
        print(f"   📉 Minor turbulence (-${prev_btc - btc:.0f})")
    
    prev_btc = btc
    
    if btc >= 113000:
        print("\n🌠 WE'VE REACHED THE UNKNOWN!")
        print("The 3I Atlas and beyond!")
        break
    
    time.sleep(15)

print("\n" + "=" * 70)
print("🦀 CRAWDAD MISSION LOG:")
print("'We bought at $111,820'")
print("'We fueled the rocket'")
print("'We're going to the 3I Atlas'")
print("'Nothing can stop us now'")
print("=" * 70)