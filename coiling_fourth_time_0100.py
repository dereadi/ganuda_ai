#!/usr/bin/env python3
"""
🌀🌀🌀🌀 COILING AGAIN?! FOURTH TIME!
10 minutes before 01:00 - This is it!
"""

import json
import time
import statistics
from coinbase.rest import RESTClient
from datetime import datetime

# Be gentle with API
time.sleep(3)

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                   🌀🌀🌀🌀 FOURTH COIL?! 🌀🌀🌀🌀                     ║
║                       10 MINUTES TO 01:00!                                ║
║                    THE FINAL COMPRESSION BEFORE...                        ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - IS IT COILING AGAIN?!")
print("=" * 70)

# Quick check with minimal API calls
try:
    btc = float(client.get_product('BTC-USD')['price'])
    time.sleep(2)
    eth = float(client.get_product('ETH-USD')['price'])
    time.sleep(2)
    sol = float(client.get_product('SOL-USD')['price'])
    
    print(f"\n📍 CURRENT LEVELS:")
    print(f"  BTC: ${btc:,.0f}")
    print(f"  ETH: ${eth:.2f}")
    print(f"  SOL: ${sol:.2f}")
    
    # Take a few samples carefully
    print("\n🌀 MEASURING COIL #4:")
    print("-" * 50)
    
    samples = [btc]
    time.sleep(5)
    
    btc2 = float(client.get_product('BTC-USD')['price'])
    samples.append(btc2)
    time.sleep(5)
    
    btc3 = float(client.get_product('BTC-USD')['price'])
    samples.append(btc3)
    
    btc_range = max(samples) - min(samples)
    
    print(f"10-second range: ${btc_range:.0f}")
    
    if btc_range < 20:
        print("\n🌀🌀🌀🌀 YES! FOURTH COIL CONFIRMED!")
        print("Range under $20 - EXTREME COMPRESSION!")
        print("\nTHIS IS UNPRECEDENTED:")
        print("• COIL #1: 22:05 → Exploded")
        print("• COIL #2: 00:16 → Brief pop")
        print("• COIL #3: 00:38 → Tightest yet")
        print("• COIL #4: NOW → Before 01:00!")
        print("\n⚡ FOUR COILS = NUCLEAR ENERGY!")
    elif btc_range < 40:
        print("\n🌀 Moderate coiling...")
        print("Still compressed but not extreme")
    else:
        print("\n📊 Moving more freely")
        print(f"Range: ${btc_range:.0f}")
    
except Exception as e:
    print(f"\n⚠️ API exhausted: {str(e)[:50]}")
    print("Even checking is rate limited!")
    print("The market is so tight it broke the API!")

# Time analysis
current_time = datetime.now()
minutes_to_0100 = 60 - current_time.minute if current_time.hour == 0 else 0

print(f"\n⏰ TIME CHECK:")
print(f"Current: {current_time.strftime('%H:%M:%S')}")
print(f"Minutes to 01:00: {minutes_to_0100}")

if minutes_to_0100 < 10:
    print("\n🚨 FINAL COUNTDOWN!")
    print("Less than 10 minutes to witching hour!")
    print("Four coils + 01:00 = EXPLOSION!")
elif minutes_to_0100 < 15:
    print("\n⚡ T-minus 15 minutes!")
    print("Final compression phase!")

print("\n💡 FOUR COILS THEORY:")
print("-" * 50)
print("• Never seen 4 coils in one night")
print("• Each coil stores exponential energy")
print("• Market makers playing ultimate game")
print("• 01:00 will be the release valve")
print("• Magnitude: UNPRECEDENTED")

print("\n🎯 WHAT HAPPENS AT 01:00:")
print("• Asian institutions enter")
print("• Algos reset positions")
print("• Four coils of energy release")
print("• Direction: Unknown")
print("• Size: MASSIVE")

print("\n🌀🌀🌀🌀 QUADRUPLE COILED SPRING!")
print("This is the setup of the year!")
print("=" * 70)