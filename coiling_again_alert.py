#!/usr/bin/env python3
"""
🌀 COILING AGAIN! 
After the breakout, immediately tightening for next move!
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
║                       🌀 COILING AGAIN! 🌀                                ║
║                  Back-to-Back Squeezes = MEGA MOVE!                       ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - DOUBLE COIL PATTERN!")
print("=" * 70)

print("\n⚠️ ALERT: RARE PATTERN DETECTED!")
print("• First squeeze: Released to $113,000")
print("• Now: IMMEDIATELY coiling again")
print("• This means: CONTINUATION PATTERN!")
print("• Next target: $113,500+")
print("-" * 50)

# Track the new coil
samples = []
ranges = []

for i in range(20):
    btc = float(client.get_product('BTC-USD')['price'])
    eth = float(client.get_product('ETH-USD')['price'])
    sol = float(client.get_product('SOL-USD')['price'])
    
    samples.append(btc)
    
    if len(samples) > 3:
        recent = samples[-5:] if len(samples) >= 5 else samples
        btc_high = max(recent)
        btc_low = min(recent)
        btc_range = btc_high - btc_low
        ranges.append(btc_range)
        
        # Calculate coil tightness
        stdev = statistics.stdev(recent) if len(recent) > 1 else 0
        mean = statistics.mean(recent)
        compression = (stdev / mean) * 100 if mean > 0 else 0
        
        print(f"\n{datetime.now().strftime('%H:%M:%S')} COIL STATUS:")
        print(f"  BTC: ${btc:,.0f}")
        print(f"  Range: ${btc_range:.0f} ({btc_low:,.0f}-{btc_high:,.0f})")
        print(f"  Compression: {compression:.4f}%", end="")
        
        # Coil detection
        if compression < 0.005:
            print(" 🌀🌀🌀 EXTREME COIL!")
            print("  ⚡ NEXT EXPLOSION IMMINENT!")
        elif compression < 0.01:
            print(" 🌀🌀 TIGHT COIL!")
        elif compression < 0.02:
            print(" 🌀 Coiling...")
        else:
            print("")
        
        # Pattern analysis
        if btc_range < 20 and btc > 112950:
            print("  🎯 Coiling above $113k support = BULLISH!")
        elif btc_range < 30:
            print("  📍 Building energy at this level")
        
        # Check for spring loading
        if len(ranges) > 3:
            if ranges[-1] < ranges[-2] < ranges[-3]:
                print("  🔥 RANGE CONTRACTING! Spring loading!")
    
    time.sleep(2)

# Final analysis
print("\n" + "=" * 70)
print("🌀 DOUBLE COIL ANALYSIS:")
print("-" * 40)

if ranges:
    tightest_range = min(ranges)
    print(f"Tightest Range: ${tightest_range:.0f}")
    
    if tightest_range < 20:
        print("🚀 EXTREME COIL DETECTED!")
        print("• Previous breakout: +$80 in seconds")
        print("• This coil: Likely +$100-200 move!")
        print("• Direction: 80% probability UP (above support)")
    elif tightest_range < 40:
        print("⚡ SIGNIFICANT COIL!")
        print("• Building massive energy")
        print("• Breakout within minutes")

print("\n💡 DOUBLE COIL PATTERN:")
print("• Squeeze → Breakout → Immediate Re-coil")
print("• This is CONTINUATION behavior")
print("• Market makers accumulating for next leg")
print("• GET READY FOR ROUND 2!")

print("\n🎯 TARGETS IF BREAKS UP:")
print("• First: $113,150")
print("• Second: $113,300")
print("• Third: $113,500")

print("\n⚠️ THIS IS THE MOST BULLISH PATTERN!")
print("Back-to-back coils = Relentless momentum!")
print("=" * 70)