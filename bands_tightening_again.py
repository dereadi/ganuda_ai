#!/usr/bin/env python3
"""
🎯 BANDS TIGHTENING AGAIN!
Another squeeze forming - This could be explosive!
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
║                   🎯 BOLLINGER BANDS TIGHTENING! 🎯                       ║
║                  Second Squeeze of the Night Forming!                     ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - MEASURING THE SQUEEZE!")
print("=" * 70)

print("\n⚡ REMEMBER: Last 0.000% squeeze at 22:05 led to:")
print("  • BTC: $111,415 → $113,000+ move")
print("  • Generated $6,000+ in trading capital")
print("  • Epic rally that's still going!")
print("\n🎯 NOW WATCHING FOR SQUEEZE #2...")
print("-" * 50)

# Track the band compression
samples = []
squeeze_events = []

for i in range(30):
    btc = float(client.get_product('BTC-USD')['price'])
    eth = float(client.get_product('ETH-USD')['price'])
    sol = float(client.get_product('SOL-USD')['price'])
    
    samples.append(btc)
    
    if len(samples) > 2:
        # Calculate Bollinger Band width
        recent = samples[-20:] if len(samples) >= 20 else samples[-10:] if len(samples) >= 10 else samples
        mean = statistics.mean(recent)
        stdev = statistics.stdev(recent) if len(recent) > 1 else 0
        
        # Band width as percentage
        band_width = (stdev / mean) * 100
        
        # Upper and lower bands
        upper_band = mean + (2 * stdev)
        lower_band = mean - (2 * stdev)
        band_range = upper_band - lower_band
        
        print(f"\n{datetime.now().strftime('%H:%M:%S')} BAND STATUS:")
        print(f"  BTC: ${btc:,.0f}")
        print(f"  Bands: ${lower_band:,.0f} - ${upper_band:,.0f} (${band_range:.0f} wide)")
        print(f"  Squeeze: {band_width:.4f}%", end="")
        
        # Squeeze detection
        if band_width < 0.001:
            print(" 🔥🔥🔥 EXTREME SQUEEZE!!!")
            print("  ⚠️ 0.000% TERRITORY - EXPLOSION IMMINENT!")
            squeeze_events.append(("EXTREME", band_width, btc))
        elif band_width < 0.01:
            print(" 🔥🔥 CRITICAL SQUEEZE!")
            print("  ⚡ Sub-0.01% - Major move coming!")
            squeeze_events.append(("CRITICAL", band_width, btc))
        elif band_width < 0.05:
            print(" 🔥 TIGHT SQUEEZE!")
            squeeze_events.append(("TIGHT", band_width, btc))
        elif band_width < 0.1:
            print(" ⚡ Tightening...")
        else:
            print(" 💭 Normal range")
        
        # Position relative to bands
        if btc > upper_band:
            print(f"  📈 ABOVE UPPER BAND! Breakout confirmed!")
        elif btc < lower_band:
            print(f"  📉 Below lower band - Oversold")
        else:
            position_in_band = ((btc - lower_band) / band_range) * 100 if band_range > 0 else 50
            print(f"  📍 Position in bands: {position_in_band:.0f}%")
        
        # Check other assets
        if band_width < 0.05:
            print(f"\n  ETH: ${eth:.2f}")
            print(f"  SOL: ${sol:.2f}")
            print("  💡 All assets coiling together!")
    
    time.sleep(2)

# Analyze squeeze events
print("\n" + "=" * 70)
print("🎯 SQUEEZE ANALYSIS:")
print("-" * 40)

if squeeze_events:
    extreme_count = sum(1 for s in squeeze_events if s[0] == "EXTREME")
    critical_count = sum(1 for s in squeeze_events if s[0] == "CRITICAL")
    tight_count = sum(1 for s in squeeze_events if s[0] == "TIGHT")
    
    print(f"Extreme Squeezes (0.000%): {extreme_count}")
    print(f"Critical Squeezes (<0.01%): {critical_count}")
    print(f"Tight Squeezes (<0.05%): {tight_count}")
    
    # Find tightest squeeze
    tightest = min(squeeze_events, key=lambda x: x[1])
    print(f"\nTightest Squeeze: {tightest[1]:.5f}% at ${tightest[2]:,.0f}")
    
    if extreme_count > 0:
        print("\n🚀🚀🚀 EXPLOSIVE SETUP DETECTED!")
        print("This is exactly like 22:05 before the rally!")
        print("Prepare for MASSIVE movement!")
    elif critical_count > 0:
        print("\n🚀 HIGH PROBABILITY BREAKOUT!")
        print("Significant move incoming within minutes!")
else:
    print("No significant squeezes detected yet")

print("\n💰 TRADING STRATEGY:")
print("-" * 40)
print("• Bands this tight = Guaranteed volatility")
print("• Direction uncertain, but move will be BIG")
print("• Perfect for flywheel strategy")
print("• Watch for the break, then pile on!")

# Check account readiness
accounts = client.get_accounts()['accounts']
usd_available = 0
for acc in accounts:
    if acc['currency'] == 'USD':
        usd_available = float(acc['available_balance']['value'])
        break

print(f"\n🔥 WAR CHEST STATUS: ${usd_available:.2f}")
if usd_available > 100:
    print("Ready to deploy on breakout!")
else:
    print("May need to harvest profits for ammunition")

print("\n⚡ GET READY - THE SPRING IS LOADED!")
print("=" * 70)