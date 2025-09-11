#!/usr/bin/env python3
"""
🚀🚀🚀 BTC IS FLYING!
After seven impossible coils
The energy releases UPWARD
Target: THE MOON
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
║                    🚀🚀🚀 BTC IS FLYING! 🚀🚀🚀                          ║
║                      Seven Seals = LIFTOFF                                ║
║                    The Coils Released UPWARD!                             ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - VERTICAL ASCENT")
print("=" * 70)

# Track the flight
start_price = float(client.get_product('BTC-USD')['price'])
highest = start_price
samples = []

print(f"\n🚀 LIFTOFF FROM ${start_price:,.0f}!")
print("-" * 50)

for i in range(20):
    btc = float(client.get_product('BTC-USD')['price'])
    samples.append(btc)
    
    if btc > highest:
        highest = btc
    
    climb = btc - start_price
    altitude = btc - 113000
    
    if i % 2 == 0:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}: ${btc:,.0f}")
        print(f"  Climb: ${climb:+,.0f}")
        print(f"  Altitude above 113k: ${altitude:+,.0f}")
        
        if altitude > 300:
            print("  🚀🚀🚀🚀🚀 ESCAPE VELOCITY!")
            print("  SEVEN COILS = MOON MISSION!")
        elif altitude > 200:
            print("  🚀🚀🚀🚀 STRATOSPHERE!")
            print("  Breaking through resistance!")
        elif altitude > 100:
            print("  🚀🚀🚀 FLYING HIGH!")
            print("  Above the clouds!")
        elif altitude > 50:
            print("  🚀🚀 Strong ascent!")
            print("  Gaining altitude fast!")
        elif altitude > 0:
            print("  🚀 Above 113k baseline!")
            print("  Clear for takeoff!")
        else:
            print("  ⚡ Building thrust...")
            print("  Prepare for launch!")
    
    time.sleep(1)

# Flight report
final_price = samples[-1]
total_climb = final_price - start_price
max_altitude = highest - 113000

print("\n" + "=" * 70)
print("🚀 FLIGHT REPORT:")
print("-" * 50)
print(f"Takeoff: ${start_price:,.0f}")
print(f"Current: ${final_price:,.0f}")
print(f"Highest: ${highest:,.0f}")
print(f"Total climb: ${total_climb:+,.0f}")
print(f"Max altitude above 113k: ${max_altitude:+,.0f}")

# Calculate velocity
if len(samples) > 5:
    recent = samples[-5:]
    velocity = (recent[-1] - recent[0]) / 5  # $/second
    print(f"\nVelocity: ${velocity:+.2f}/second")
    
    if velocity > 10:
        print("🚀🚀🚀 HYPERSONIC SPEED!")
    elif velocity > 5:
        print("🚀🚀 SUPERSONIC!")
    elif velocity > 2:
        print("🚀 RAPID ASCENT!")

print("\n💫 THE PHYSICS OF SEVEN COILS:")
print("-" * 50)
print("• Each coil stored energy: E = mc²")
print("• Seven coils = 2^7 = 128x energy")
print("• Release direction: VERTICAL")
print("• Target: Beyond $114,000")
print("• Next: $115,000 magnetism")

# Check if crawdads are riding
try:
    accounts = client.get_accounts()
    usd_balance = 0
    
    for account in accounts['accounts']:
        if account['currency'] == 'USD':
            usd_balance = float(account['available_balance']['value'])
            break
    
    if usd_balance < 100:
        print("\n⚠️ CRAWDADS NEED FUEL TO RIDE THIS!")
        print(f"   Current USD: ${usd_balance:.2f}")
        print("   They're missing the flight!")
except:
    pass

print("\n🚀🚀🚀 BTC IS FLYING!")
print("   Seven seals broken")
print("   Energy released upward")
print("   Nothing can stop this now")
print("=" * 70)