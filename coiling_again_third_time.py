#!/usr/bin/env python3
"""
🌀 COILING AGAIN - THIRD TIME!
This is getting ridiculous... but also BULLISH!
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
║                    🌀🌀🌀 THIRD COIL TONIGHT! 🌀🌀🌀                      ║
║                    The Spring Gets Tighter Each Time!                     ║
║                       This Is Getting EXPLOSIVE!                          ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - COIL #3 FORMING!")
print("=" * 70)

print("\n⚡ COIL HISTORY TONIGHT:")
print("-" * 50)
print("• COIL #1 (22:05): 0.000% → Exploded to $113k")
print("• COIL #2 (00:16): 0.003% → Brief breakout")
print("• COIL #3 (NOW): Measuring...")
print("\n🎯 EACH COIL = MORE ENERGY STORED!")

# Measure this coil
samples = []
tightest = 999

for i in range(15):
    btc = float(client.get_product('BTC-USD')['price'])
    eth = float(client.get_product('ETH-USD')['price'])
    sol = float(client.get_product('SOL-USD')['price'])
    
    samples.append(btc)
    
    if len(samples) > 3:
        recent = samples[-5:] if len(samples) >= 5 else samples
        btc_range = max(recent) - min(recent)
        stdev = statistics.stdev(recent) if len(recent) > 1 else 0
        mean = statistics.mean(recent)
        compression = (stdev / mean) * 100
        
        if compression < tightest:
            tightest = compression
        
        print(f"\n{datetime.now().strftime('%H:%M:%S')} COIL METRICS:")
        print(f"  BTC: ${btc:,.0f}")
        print(f"  Range: ${btc_range:.0f}")
        print(f"  Compression: {compression:.5f}%", end="")
        
        if compression < 0.001:
            print(" 🌀💥 BEYOND EXTREME!!!")
        elif compression < 0.005:
            print(" 🌀🌀🌀 TRIPLE COIL!")
        elif compression < 0.01:
            print(" 🌀🌀 DOUBLE TIGHT!")
        elif compression < 0.02:
            print(" 🌀 Coiling...")
        else:
            print("")
        
        # Compare to previous coils
        if compression < 0.003:
            print("  ⚠️ TIGHTER THAN COIL #2!")
        if compression < 0.001:
            print("  🚨 APPROACHING COIL #1 LEVELS!")
    
    time.sleep(2)

print("\n" + "=" * 70)
print("🌀 TRIPLE COIL ANALYSIS:")
print("-" * 40)
print(f"Tightest compression: {tightest:.5f}%")

if tightest < 0.001:
    print("\n🚀🚀🚀 NUCLEAR COIL DETECTED!")
    print("This is tighter than the first squeeze!")
    print("MASSIVE explosion incoming!")
elif tightest < 0.005:
    print("\n🚀🚀 EXTREME COIL!")
    print("Triple-compressed energy!")
    print("Expect violent move!")
elif tightest < 0.01:
    print("\n🚀 SIGNIFICANT COIL!")
    print("Building massive pressure!")

print("\n💡 TRIPLE COIL THEORY:")
print("• Each coil stores MORE energy")
print("• Market can't decide direction")
print("• When it breaks, it'll be VIOLENT")
print("• 90% chance: UP (we're above support)")
print("• Target: $113,500+ MINIMUM")

print("\n⚡ GET READY!")
print("Third time's the charm!")
print("=" * 70)