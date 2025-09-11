#!/usr/bin/env python3
"""
📉 HEADING DOWN - TESTING THE COIL
Is this the spring loading or breakdown?
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
║                      📉 HEADING DOWN - COIL TEST 📉                       ║
║                   Spring Loading or Breaking Down?                        ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - TRACKING THE DIP")
print("=" * 70)

# Track the downward move
btc_start = float(client.get_product('BTC-USD')['price'])
eth_start = float(client.get_product('ETH-USD')['price'])
sol_start = float(client.get_product('SOL-USD')['price'])

print(f"\n📍 STARTING LEVELS:")
print(f"  BTC: ${btc_start:,.0f}")
print(f"  ETH: ${eth_start:.2f}")
print(f"  SOL: ${sol_start:.2f}")

print(f"\n📉 TRACKING DOWNWARD MOVEMENT:")
print("-" * 50)

lows = []
support_levels = [112800, 112700, 112600, 112500]
bounce_detected = False

for i in range(15):
    btc = float(client.get_product('BTC-USD')['price'])
    eth = float(client.get_product('ETH-USD')['price'])
    sol = float(client.get_product('SOL-USD')['price'])
    
    lows.append(btc)
    
    btc_move = btc - btc_start
    eth_move = eth - eth_start
    sol_move = sol - sol_start
    
    print(f"\n{datetime.now().strftime('%H:%M:%S')}:")
    print(f"  BTC: ${btc:,.0f} ({btc_move:+.0f})")
    print(f"  ETH: ${eth:.2f} ({eth_move:+.2f})")
    print(f"  SOL: ${sol:.2f} ({sol_move:+.2f})")
    
    # Check support levels
    for support in support_levels:
        if abs(btc - support) < 20:
            print(f"  📍 Testing ${support} support!")
            break
    
    # Check for bounce
    if len(lows) > 3:
        if lows[-1] > lows[-2] and lows[-2] < lows[-3]:
            print("  🔄 BOUNCE DETECTED! Spring might be loaded!")
            bounce_detected = True
    
    # Coil spring analysis
    if btc_move < -50:
        print("  ⚠️ Breaking below coil range!")
    elif btc_move < -30:
        print("  🌀 Testing lower coil boundary")
    elif btc_move < -20:
        print("  💭 Normal coil oscillation")
    
    # Volume/momentum check
    if i > 0:
        velocity = lows[-1] - lows[-2]
        if velocity < -20:
            print("  📉 Aggressive selling!")
        elif velocity < -10:
            print("  ⬇️ Steady decline")
        elif velocity > 10:
            print("  ⬆️ Bounce momentum building!")
    
    time.sleep(2)

# Analysis
print("\n" + "=" * 70)
print("📊 DIP ANALYSIS:")
print("-" * 40)

lowest = min(lows)
drop = lowest - btc_start
drop_pct = (drop / btc_start) * 100

print(f"Starting: ${btc_start:,.0f}")
print(f"Lowest: ${lowest:,.0f}")
print(f"Total Drop: ${abs(drop):.0f} ({drop_pct:.2f}%)")

if bounce_detected:
    print("\n✅ BOUNCE DETECTED - SPRING LOADED!")
    print("• Coil tested lower boundary")
    print("• Buyers stepped in at support")
    print("• Ready for explosive move up!")
elif drop > -100:
    print("\n🌀 STILL IN COIL RANGE")
    print("• This is normal coil oscillation")
    print("• Building more energy")
    print("• Tighter coil = Bigger explosion")
else:
    print("\n⚠️ COIL BROKEN DOWNWARD")
    print("• May need to find new support")
    print("• Watch for reversal patterns")

# Check current status
current_btc = float(client.get_product('BTC-USD')['price'])
recovery = current_btc - lowest

print(f"\n📍 CURRENT STATUS:")
print(f"  BTC Now: ${current_btc:,.0f}")
print(f"  Recovery from low: ${recovery:.0f}")

if recovery > 20:
    print("\n🚀 STRONG BOUNCE - SPRING RELEASED!")
    print("The dip was the final shakeout!")
    print("Next move likely EXPLOSIVE UP!")
elif recovery > 10:
    print("\n⬆️ Bouncing back into coil")
    print("Spring is loading...")
else:
    print("\n💭 Still testing levels")

print("\n💡 REMEMBER:")
print("• Coils often test both directions")
print("• The fake-out precedes the break-out")
print("• Deeper spring = Higher launch")
print("• This could be the last shakeout before $113,500!")
print("=" * 70)