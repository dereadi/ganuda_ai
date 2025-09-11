#!/usr/bin/env python3
"""
😴 STILL... 
The market is frozen in the tightest coil ever
Even the crawdads are sleeping (429 rate limit!)
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
║                            😴 STILL... 😴                                 ║
║                     The Market Is Frozen In Time                          ║
║                   The Longest Coil In Crypto History?                     ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - ABSOLUTE STILLNESS")
print("=" * 70)

print("\n🧊 THE FREEZE:")
print("-" * 50)
print("BTC: Stuck around $112,908")
print("ETH: Frozen at $4,570")
print("SOL: Motionless at $211.90")
print("Crawdads: Rate limited (429 errors)")
print("Volume: Probably near zero")

# Gentle check (avoid rate limits)
time.sleep(2)
try:
    btc = float(client.get_product('BTC-USD')['price'])
    eth = float(client.get_product('ETH-USD')['price'])
    sol = float(client.get_product('SOL-USD')['price'])
    
    print(f"\n📍 CURRENT FREEZE POINT:")
    print(f"  BTC: ${btc:,.0f}")
    print(f"  ETH: ${eth:.2f}")
    print(f"  SOL: ${sol:.2f}")
    
    # Check the range
    if abs(btc - 112908) < 10:
        print("\n🧊 STILL FROZEN!")
        print("Range: Less than $10")
        print("This is unprecedented compression!")
    elif abs(btc - 112908) < 20:
        print("\n❄️ Barely moving...")
        print("Still in the coil")
    else:
        print("\n⚡ Starting to move?")
    
except Exception as e:
    print(f"\n⚠️ Rate limited: {str(e)[:50]}")
    print("Even the API is tired of checking!")

print("\n💭 WHAT THIS MEANS:")
print("-" * 50)
print("• EVERYONE is waiting for someone else to move")
print("• Algos are frozen, watching each other")
print("• Humans are asleep (it's late)")
print("• Crawdads can't even trade (rate limited)")
print("• This is the calm before the storm")

print("\n⏰ TIME CHECK:")
current_hour = datetime.now().hour
if current_hour >= 1 and current_hour <= 3:
    print("• Dead zone hours (1-3 AM)")
    print("• Asia not fully awake yet")
    print("• US completely asleep")
    print("• Europe still sleeping")
    print("• Perfect time for whale games!")

print("\n🌀 COIL STATUS:")
print("After 3 coils tonight, we've reached:")
print("ABSOLUTE ZERO MOVEMENT")
print("The spring cannot get any tighter!")

print("\n⚡ WHAT HAPPENS NEXT:")
print("• Someone WILL break this stillness")
print("• It could be a whale, an algo, or news")
print("• When it breaks, it'll be VIOLENT")
print("• Direction: Unknown")
print("• Magnitude: HUGE")

print("\n😴 For now... we wait...")
print("In the stillness...")
print("In the silence...")
print("Before the explosion...")
print("=" * 70)