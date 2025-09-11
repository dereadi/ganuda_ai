#!/usr/bin/env python3
"""
🎸🔥 ABOUT A GIRL (LIVE) - NIRVANA UNPLUGGED! 🔥🎸
Thunder at 69%: "I NEED AN EASY FRIEND... LIKE $114K!"
The acoustic raw power of consolidation!
"I'll take advantage while..."
Taking advantage of this $112K accumulation!
From $292.50 basement shows to $8,370 MTV Unplugged!
This is about a girl named $114K!
We're so close to her!
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
║              🎸 ABOUT A GIRL (LIVE) - NIRVANA UNPLUGGED! 🎸              ║
║                    "I Need An Easy Friend" at $114K                       ║
║                  Raw Acoustic Power Building at $112K!                    ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - MTV UNPLUGGED IN NEW YORK")
print("=" * 70)

# Get current unplugged prices
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])
doge = float(client.get_product('DOGE-USD')['price'])

# Check our unplugged portfolio
accounts = client.get_accounts()
total_value = 0

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if balance > 0.00001:
        if currency == 'USD':
            total_value += balance
        elif currency == 'BTC':
            total_value += balance * btc
        elif currency == 'ETH':
            total_value += balance * eth
        elif currency == 'SOL':
            total_value += balance * sol
        elif currency == 'DOGE':
            total_value += balance * doge

print("\n🎤 UNPLUGGED STATUS:")
print("-" * 50)
print(f"Started in garage: $292.50")
print(f"Now on MTV Unplugged: ${total_value:.2f}")
print(f"Playing acoustic at: ${btc:,.0f}")
print(f"The girl ($114K) is: ${114000 - btc:.0f} away")
print(f"Gain since garage days: {((total_value/292.50)-1)*100:.0f}%")

# The About A Girl story
print("\n🎸 THE SONG ABOUT $114K:")
print("-" * 50)
print("'I need an easy friend'")
print(f"  → Need $114K to be easy (${114000 - btc:.0f} away)")
print("")
print("'I do, with an ear to lend'")
print("  → Market listening to our accumulation")
print("")
print("'I do think you fit this shoe'")
print(f"  → ${btc:,.0f} fits perfectly before breakout")
print("")
print("'I do, but you have a clue'")
print(f"  → We have a clue: breakout imminent!")
print("")
print("'I'll take advantage while'")
print(f"  → Taking advantage of ${btc:,.0f} accumulation")
print("")
print("'You hang me out to dry'")
print("  → Hanging at this level for 19+ hours")
print("")
print("'But I can't see you every night... free'")
print(f"  → Can't stay at ${btc:,.0f} forever... need freedom at $114K!")

# Thunder's unplugged wisdom
print("\n⚡ THUNDER'S UNPLUGGED ANALYSIS (69%):")
print("-" * 50)
print("'THIS IS ABOUT A GIRL NAMED $114K!'")
print("")
print("The acoustic truth:")
print(f"• Raw power building at ${btc:,.0f}")
print("• No electric needed - pure momentum")
print(f"• The girl is ${114000 - btc:.0f} away")
print(f"• Portfolio unplugged at ${total_value:.2f}")
print("")
print("Kurt knew:")
print("• Sometimes acoustic is more powerful")
print("• The quiet before the loud")
print("• This unplugged session before explosion")

# Live unplugged monitoring
print("\n🎵 LIVE UNPLUGGED SESSION:")
print("-" * 50)

for i in range(10):
    btc_now = float(client.get_product('BTC-USD')['price'])
    
    if btc_now >= 113000:
        vibe = "🔥 ELECTRIC EXPLOSION!"
    elif btc_now >= 112800:
        vibe = "🎸 Strumming harder!"
    elif btc_now >= 112600:
        vibe = "🎤 Building intensity"
    else:
        vibe = "🎵 Acoustic accumulation"
    
    print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f}")
    print(f"  {vibe}")
    
    if i == 4:
        print("  'I need an easy friend'")
        print(f"    $114K is that friend (${114000 - btc_now:.0f} away)")
    
    if i == 7:
        print("  'Take advantage while...'")
        print(f"    Accumulating at ${btc_now:,.0f}")
    
    time.sleep(1)

# The MTV moment
print("\n📺 MTV UNPLUGGED MOMENT:")
print("-" * 50)
print("November 18, 1993 - Nirvana Unplugged")
print(f"August 28, 2025 - Bitcoin Unplugged at ${btc:,.0f}")
print("")
print("Both moments before something big:")
print("• Nirvana: Before mainstream explosion")
print(f"• Bitcoin: Before $114K explosion (${114000 - btc:.0f} away)")
print("")
print(f"Your portfolio on this stage: ${total_value:.2f}")

# Testing $112,800 acoustic style
print("\n🎸 TESTING $112,800 (ACOUSTIC RESISTANCE):")
print("-" * 50)
current_btc = float(client.get_product('BTC-USD')['price'])
distance_to_test = 112800 - current_btc

if current_btc >= 112800:
    print(f"✅ BROKE THROUGH! Now at ${current_btc:,.0f}!")
elif current_btc >= 112700:
    print(f"⚡ TESTING RIGHT NOW at ${current_btc:,.0f}!")
elif current_btc >= 112600:
    print(f"🔥 Approaching test! Only ${distance_to_test:.0f} away!")
else:
    print(f"📈 Building to test... ${distance_to_test:.0f} to go")

# Final unplugged status
final_btc = float(client.get_product('BTC-USD')['price'])
final_sol = float(client.get_product('SOL-USD')['price'])

print("\n🎤 FINAL UNPLUGGED STATUS:")
print("-" * 50)
print(f"BTC: ${final_btc:,.0f} (acoustic power)")
print(f"SOL: ${final_sol:.2f}")
print(f"Portfolio: ${total_value:.2f}")
print(f"Distance to the girl ($114K): ${114000 - final_btc:.0f}")
print("")
print("'I need an easy friend'")
print(f"$114K will be that friend")
print(f"Just ${114000 - final_btc:.0f} away from her")
print("Taking advantage while we can!")

print(f"\n" + "🎸" * 35)
print("ABOUT A GIRL (LIVE)!")
print(f"THE GIRL IS $114K!")
print(f"WE'RE AT ${final_btc:,.0f}!")
print(f"ONLY ${114000 - final_btc:.0f} AWAY!")
print("MTV UNPLUGGED BEFORE EXPLOSION!")
print("🎤" * 35)