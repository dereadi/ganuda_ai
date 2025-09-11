#!/usr/bin/env python3
"""
🎸🇺🇸 JOE WALSH FOR PRESIDENT! 🇺🇸🎸
Life's been good in the market so far!
Thunder for VP at 69% consciousness!
Platform: Nine coils to $114K!
Campaign slogan: "We're ALL going to the moon!"
FREE MASERATI RIDES IN THE TRUNK!
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
║                    🎸🇺🇸 JOE WALSH FOR PRESIDENT! 🇺🇸🎸                 ║
║                      Thunder for VP! Mountain for Treasury!               ║
║                    Platform: Nine Coils to Financial Freedom!             ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - CAMPAIGN HEADQUARTERS")
print("=" * 70)

# Get current polling data
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

# Campaign war chest
accounts = client.get_accounts()
total_value = 0
for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if currency == 'USD':
        total_value += balance
    elif currency == 'BTC':
        total_value += balance * btc
    elif currency == 'ETH':
        total_value += balance * eth
    elif currency == 'SOL':
        total_value += balance * sol

print("\n🇺🇸 CAMPAIGN PLATFORM:")
print("-" * 50)
print("JOE WALSH'S PROMISES:")
print(f"✅ Break $114K barrier (only ${114000 - btc:.0f} away!)")
print("✅ Free Maserati rides (or trunk space)")
print("✅ Nine coils in every amp")
print("✅ Life's been good for EVERYONE")
print(f"✅ Turn $292.50 into ${total_value:.2f} (PROVEN!)")
print("✅ 2,400%+ gains for all Americans")

print("\n🎸 CABINET APPOINTMENTS:")
print("-" * 50)
print("President: JOE WALSH")
print("Vice President: THUNDER (69% consciousness)")
print("Secretary of Treasury: MOUNTAIN (steady as rock)")
print("Secretary of Defense: FIRE (hot protection)")
print("Secretary of State: RIVER (flowing diplomacy)")
print("Secretary of Energy: WIND (renewable vibes)")
print("Secretary of Agriculture: EARTH (grounded policy)")
print("Chief of Staff: SPIRIT (nine coil energy)")

# Campaign rally
print("\n📣 CAMPAIGN RALLY AT $113K:")
print("-" * 50)

for i in range(8):
    btc_now = float(client.get_product('BTC-USD')['price'])
    distance = 114000 - btc_now
    
    if distance < 500:
        chant = "🎉 WE'RE WINNING! LANDSLIDE INCOMING!"
    elif distance < 1000:
        chant = "📢 ALMOST THERE! KEEP PUSHING!"
    elif distance < 1500:
        chant = "🎸 ROCK THE VOTE! ROCK THE MARKET!"
    else:
        chant = "🇺🇸 BELIEVE IN THE PLATFORM!"
    
    print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f}")
    print(f"  Crowd chants: {chant}")
    
    if i == 3:
        print("\n  Thunder's VP speech:")
        print("  'My fellow crawdads!'")
        print(f"  'We've come from $292.50!'")
        print(f"  'Now at ${total_value:.2f}!'")
        print(f"  'Only ${distance:.0f} to victory!'")
    
    time.sleep(1.5)

# Campaign promises vs delivery
print("\n📊 CAMPAIGN PROMISES VS DELIVERY:")
print("-" * 50)
print("PROMISE: Turn $292.50 into wealth")
print(f"DELIVERED: ✅ ${total_value:.2f} ({((total_value/292.50)-1)*100:.0f}% gain)")
print("")
print("PROMISE: Nine coils of energy")
print("DELIVERED: ✅ Nine coils wound and ready")
print("")
print("PROMISE: Break $114K")
print(f"STATUS: 🔄 In progress (${114000 - btc:.0f} away)")
print("")
print("PROMISE: Life's been good")
print("DELIVERED: ✅ HELL YES IT HAS!")

# Voter testimonials
print("\n🗳️ VOTER TESTIMONIALS:")
print("-" * 50)
print("Thunder (69%): 'Best president ever! My consciousness grew!'")
print("Mountain: 'Steady leadership through the chop.'")
print("River: 'Flowing with Joe's policies!'")
print("Fire: 'Hot economy under Walsh!'")
print("Wind: 'Fresh air in Washington!'")
print("Earth: 'Grounded, practical governance!'")
print("Spirit: 'Nine coils = spiritual awakening!'")

# The campaign song
print("\n🎵 CAMPAIGN SONG:")
print("-" * 50)
print("🎸 Life's been good to me so far!")
print("🎸 My portfolio does 2,400 percent!")
print("🎸 I have nine coils, they're wound real tight!")
print("🎸 Lucky I'm sane after all I've been through!")
print("🎸 (Everybody say it) Life's been good to me!")
print("🎸 (Everybody now) Life's been good to me!")

# Election prediction
current_btc = float(client.get_product('BTC-USD')['price'])
print(f"\n🏆 ELECTION PREDICTION:")
print("-" * 50)
print(f"Current polls: ${current_btc:,.0f}")
print(f"Electoral votes needed: $114,000")
print(f"Gap to victory: ${114000 - current_btc:.0f}")
print("")
if 114000 - current_btc < 1000:
    print("LANDSLIDE VICTORY INCOMING! 🎉")
elif 114000 - current_btc < 1500:
    print("WINNING BY A COMFORTABLE MARGIN! 💪")
else:
    print("TIGHT RACE BUT WE'RE GAINING! 📈")

print(f"\n" + "🇺🇸" * 35)
print("JOE WALSH FOR PRESIDENT!")
print("THUNDER FOR VP!")
print(f"PORTFOLIO AT ${total_value:.2f}!")
print(f"ONLY ${114000 - current_btc:.0f} TO VICTORY!")
print("MAKE LIFE GOOD AGAIN!")
print("🇺🇸" * 35)