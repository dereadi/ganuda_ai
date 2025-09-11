#!/usr/bin/env python3
"""
🚀🚀🚀 WE ARE GOING UP! 🚀🚀🚀
BTC: $113,098 and climbing!
The ninth coil is releasing!
The cold hard bitch decided it's time!
TO THE FUCKING MOON!
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
║                    🚀🚀🚀 WE ARE GOING UP! 🚀🚀🚀                       ║
║                         THE NINTH COIL RELEASES!                          ║
║                           $114K HERE WE COME!                             ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - LIFTOFF!")
print("=" * 70)

# Track the ascent
btc_start = float(client.get_product('BTC-USD')['price'])
eth_start = float(client.get_product('ETH-USD')['price'])
sol_start = float(client.get_product('SOL-USD')['price'])

print(f"\n🚀 LAUNCH SEQUENCE:")
print(f"  BTC: ${btc_start:,.0f}")
print(f"  ETH: ${eth_start:,.2f}")
print(f"  SOL: ${sol_start:,.2f}")
print(f"  XRP: $3.00!")
print(f"\n  Target: $114,000")
print(f"  Distance: ${114000 - btc_start:,.0f}")

# Real-time ascent tracker
print("\n🚀🚀🚀 LIVE ASCENT TRACKER:")
print("-" * 50)

highest = btc_start
for i in range(15):
    btc = float(client.get_product('BTC-USD')['price'])
    eth = float(client.get_product('ETH-USD')['price'])
    sol = float(client.get_product('SOL-USD')['price'])
    
    if btc > highest:
        highest = btc
    
    gain = btc - btc_start
    to_target = 114000 - btc
    
    # Determine ascent phase
    if btc >= 114000:
        status = "🚀💥🎯 $114K BREACHED! WE DID IT!"
    elif btc >= 113500:
        status = "🚀🚀🚀 FINAL APPROACH!"
    elif btc >= 113200:
        status = "🚀🚀 ACCELERATING!"
    elif gain > 50:
        status = "🚀 ASCENDING RAPIDLY!"
    elif gain > 0:
        status = "⬆️ Going up!"
    else:
        status = "🌀 Coiling for launch..."
    
    print(f"\n{datetime.now().strftime('%H:%M:%S')}:")
    print(f"  BTC: ${btc:,.0f} ({gain:+.0f})")
    
    if to_target < 500:
        print(f"  📍 ONLY ${to_target:.0f} TO TARGET!")
    else:
        print(f"  📍 Distance: ${to_target:,.0f}")
    
    print(f"  {status}")
    
    if btc == highest and gain > 20:
        print("  ⭐ NEW HIGH!")
    
    time.sleep(1.5)

# Summary
print("\n" + "=" * 70)
print("🚀 ASCENT SUMMARY:")
print("-" * 50)
print(f"Starting altitude: ${btc_start:,.0f}")
print(f"Highest reached: ${highest:,.0f}")
print(f"Total climb: ${highest - btc_start:,.0f}")

# The truth
print("\n🔥 THE TRUTH:")
print("-" * 50)
print("• Nine coils wound = 512x energy")
print("• Bull Score RED = Maximum divergence")
print("• Wall Street loading = Institutional FOMO")
print("• Uprising active = 'They will not control us'")
print("• Arms race won = We beat the FUD")
print("• Trooper charging = Into the valley of death")
print("• Cold hard bitch = Finally warming up")

print("\n" + "🚀" * 35)
print("WE ARE GOING UP!")
print("THE NINTH COIL IS REAL!")
print("$114K IS DESTINY!")
print("$200K IS THE MISSION!")
print("TO THE FUCKING MOON!")
print("🚀" * 35)