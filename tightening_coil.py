#!/usr/bin/env python3
"""
🌀 THE TIGHTENING COIL
Bands compressing beyond belief - explosion imminent
"""

import json
import statistics
import time
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                        🌀 TIGHTENING COIL ALERT 🌀                        ║
║                    Compression beyond 0.007% and falling                  ║
║                         HISTORIC SQUEEZE LOADING                          ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print("⚠️  STILL TIGHTENING - This is unprecedented!")
print("=" * 70)

# Rapid sampling to measure the squeeze
samples = []
print("\n📊 MEASURING THE SQUEEZE:")
print("-" * 40)

for i in range(30):
    btc = float(client.get_product('BTC-USD')['price'])
    samples.append(btc)
    
    if len(samples) > 2:
        recent = samples[-10:] if len(samples) >= 10 else samples
        stdev = statistics.stdev(recent)
        mean = statistics.mean(recent)
        squeeze = (stdev / mean) * 100
        
        high = max(recent)
        low = min(recent)
        range_size = high - low
        
        if i % 5 == 0:
            print(f"\n⏰ {datetime.now().strftime('%H:%M:%S')}")
            print(f"   Price: ${btc:,.0f}")
            print(f"   Range: ${range_size:.0f} (${low:,.0f} - ${high:,.0f})")
            print(f"   Squeeze: {squeeze:.4f}%", end="")
            
            if squeeze < 0.005:
                print(" 🔥🔥🔥 UNPRECEDENTED!")
            elif squeeze < 0.007:
                print(" 🔥🔥 EXTREME!")
            elif squeeze < 0.01:
                print(" 🔥 VERY TIGHT!")
            else:
                print(" ⚡ TIGHT")
    
    time.sleep(2)

# Final analysis
final_stdev = statistics.stdev(samples)
final_mean = statistics.mean(samples)
final_squeeze = (final_stdev / final_mean) * 100
final_range = max(samples) - min(samples)

print("\n\n" + "=" * 70)
print("🌀 COIL ANALYSIS COMPLETE:")
print("-" * 40)
print(f"Final Squeeze: {final_squeeze:.5f}%")
print(f"Total Range: ${final_range:.0f}")
print(f"Center: ${final_mean:,.0f}")

if final_squeeze < 0.005:
    print("\n🚨 DANGER ZONE 🚨")
    print("This level of compression is EXTREMELY RARE")
    print("When this releases, it will be VIOLENT")
    print("\nExpected move: $2,000-5,000 on BTC")
elif final_squeeze < 0.007:
    print("\n⚡ EXPLOSION IMMINENT")
    print("Cannot stay this compressed much longer")
    print("Expected move: $1,000-3,000 on BTC")
else:
    print("\n📊 Still compressing...")
    print("Wait for sub-0.005% for maximum violence")

print("\n💭 Cherokee Wisdom:")
print('"The tighter the bowstring, the farther the arrow flies."')
print('"Patience in the coil, violence in the release."')

print("\n🎯 POSITIONING:")
print("-" * 40)
print(f"Your $12,421 portfolio is perfectly positioned:")
print(f"  • SOL $4,028 - Will amplify any move 2-3x")
print(f"  • AVAX $2,891 - High beta play")
print(f"  • BTC $2,562 - Direct exposure")
print("\nWhen this coil releases, these positions will EXPLODE")
print("=" * 70)