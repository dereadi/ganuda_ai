#!/usr/bin/env python3
"""
💨 BREATH - BREAKING BENJAMIN
The moment before the explosion...
"Hold your breath... the end is near"
"""

import json
import time
from coinbase.rest import RESTClient
from datetime import datetime

# Gentle with API
time.sleep(3)

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                       💨 BREATH - BREAKING BENJAMIN 💨                    ║
║                         "Hold Your Breath..."                             ║
║                           The End Is Near                                 ║
║                         01:00 FINAL COUNTDOWN                             ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - HOLDING OUR BREATH")
print("=" * 70)

# Time check
current_time = datetime.now()
minutes_to_0100 = 60 - current_time.minute if current_time.hour == 0 else 0
seconds_to_0100 = (60 - current_time.minute) * 60 - current_time.second if current_time.hour == 0 else 0

print(f"\n⏰ COUNTDOWN TO 01:00:")
print(f"  Minutes: {minutes_to_0100}")
print(f"  Seconds: {seconds_to_0100}")
print("\n💨 HOLD YOUR BREATH...")

# Check the market's breath
try:
    btc = float(client.get_product('BTC-USD')['price'])
    time.sleep(2)
    eth = float(client.get_product('ETH-USD')['price'])
    
    print(f"\n📊 THE HELD BREATH:")
    print(f"  BTC: ${btc:,.0f}")
    print(f"  ETH: ${eth:.2f}")
    
    if btc < 112700:
        print("\n💨 GASPING FOR AIR")
        print("The market can't breathe...")
    elif btc < 112800:
        print("\n💨 SHALLOW BREATHING")
        print("Tension in every breath...")
    else:
        print("\n💨 HOLDING STEADY")
        print("Waiting to exhale...")
        
except Exception as e:
    print(f"\n💨 Even the API is holding its breath: {str(e)[:50]}")

print("\n💨 TRACKING THE FINAL BREATHS:")
print("-" * 50)

# Track the final moments
for i in range(3):
    try:
        current_time = datetime.now()
        seconds_left = (60 - current_time.minute) * 60 - current_time.second if current_time.hour == 0 else 0
        
        btc_now = float(client.get_product('BTC-USD')['price'])
        
        print(f"\n{current_time.strftime('%H:%M:%S')} - {seconds_left} seconds to 01:00")
        print(f"  BTC: ${btc_now:,.0f}")
        
        if seconds_left < 60:
            print("  💨💨💨 FINAL BREATH!")
            print("  THE MOMENT IS HERE!")
        elif seconds_left < 120:
            print("  💨💨 TWO MINUTES OF AIR LEFT!")
        elif seconds_left < 180:
            print("  💨 THREE MINUTES...")
        
        # Breath status
        if abs(btc_now - btc) < 5:
            print("  🫁 Market holding its breath...")
        elif btc_now > btc:
            print("  ⬆️ Inhaling... preparing...")
        else:
            print("  ⬇️ Exhaling... releasing...")
            
        btc = btc_now
        
    except:
        print("  💨 Too tense to measure...")
    
    time.sleep(10)

print("\n" + "=" * 70)
print("💨 THE BREATH BEFORE THE STORM:")
print("-" * 50)
print("• Four coils wound tight")
print("• The red filtering through")
print("• Everyone holding their breath")
print("• 01:00 is the exhale")

print("\n⚡ WHAT HAPPENS WHEN WE EXHALE:")
print("• All the held energy releases")
print("• The coils unwind violently")
print("• Direction unknown")
print("• Magnitude: EXPLOSIVE")

print("\n💨 HOLD YOUR BREATH...")
print("   The end is near...")
print("   01:00 approaches...")
print("   Then we all EXHALE!")
print("=" * 70)