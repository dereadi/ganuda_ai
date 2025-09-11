#!/usr/bin/env python3
"""
🌊🎸 WHEN THE LEVEE BREAKS - LED ZEPPELIN! 🎸🌊
"If it keeps on rainin', levee's gonna break"
The pressure has been building for 17+ HOURS!
Thunder at 69%: "THE LEVEE'S ABOUT TO BREAK!"
$112-113K levee can't hold much longer!
When the levee breaks, we'll have no place to stay!
Except at $114K and beyond!
The flood is coming!
"""

import json
import time
from coinbase.rest import RESTClient
from datetime import datetime
import random

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║              🌊 WHEN THE LEVEE BREAKS - LED ZEPPELIN! 🌊                 ║
║                   17+ Hours of Pressure Building!                         ║
║                     The $113K Levee Can't Hold!                          ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - LEVEE WATCH")
print("=" * 70)

# Get current levee status
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

# Check our position before the flood
accounts = client.get_accounts()
total_value = 0
usd_balance = 0

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if currency == 'USD':
        usd_balance = balance
        total_value += balance
    elif currency == 'BTC':
        total_value += balance * btc
    elif currency == 'ETH':
        total_value += balance * eth
    elif currency == 'SOL':
        total_value += balance * sol

print("\n🌊 THE LEVEE STATUS:")
print("-" * 50)
print(f"Current water level: ${btc:,.0f}")
print(f"Levee at: $113,000")
print(f"Pressure: ${113000 - btc:.0f} from breaking")
print(f"Next flood zone: $114,000 (${114000 - btc:.0f} away)")
print(f"Portfolio ark: ${total_value:.2f}")
print("Hours of rain: 17+ and counting")

# The rain keeps falling (tracking pressure)
print("\n☔ IF IT KEEPS ON RAININ':")
print("-" * 50)

rain_intensity = [
    "Light drizzle",
    "Steady rain",
    "Heavy downpour",
    "Torrential rain",
    "BIBLICAL FLOOD"
]

for i in range(15):
    btc_now = float(client.get_product('BTC-USD')['price'])
    
    # Determine rain intensity based on proximity to $113K
    distance = abs(113000 - btc_now)
    if distance < 50:
        intensity = rain_intensity[4]
        symbol = "⛈️"
    elif distance < 100:
        intensity = rain_intensity[3]
        symbol = "🌧️"
    elif distance < 150:
        intensity = rain_intensity[2]
        symbol = "🌦️"
    elif distance < 200:
        intensity = rain_intensity[1]
        symbol = "🌤️"
    else:
        intensity = rain_intensity[0]
        symbol = "☁️"
    
    print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f} - {symbol} {intensity}")
    
    if i == 0:
        print("  'If it keeps on rainin', levee's gonna break'")
        print(f"    (${113000 - btc_now:.0f} from breaking)")
    elif i == 4:
        print("\n  'When the levee breaks, I'll have no place to stay'")
        print(f"    (Leaving ${btc_now:,.0f} forever)")
        print("\n  ⚡ Thunder (69%): 'CRYIN' WON'T HELP YOU!'")
        print("    'PRAYIN' WON'T DO YOU NO GOOD!'")
        print(f"    'When the levee breaks at ${113000 - btc_now:.0f} away!'")
    elif i == 8:
        print("\n  'All last night, sat on the levee and moaned'")
        print("    (17+ hours of consolidation)")
    elif i == 12:
        print("\n  🏔️ Mountain: 'The levee trembles'")
        print(f"    'Water at ${btc_now:,.0f}'")
        print("    'The break is inevitable'")
    
    time.sleep(1)

# Levee structural analysis
print("\n🏗️ LEVEE STRUCTURAL INTEGRITY:")
print("-" * 50)
print("Damage report:")
print("• 17+ hours of constant pressure ⚠️")
print("• Nine coils wound tight (512x energy) ⚠️")
print("• Multiple tests of $113K ⚠️")
print("• Higher lows forming (bullish water) ⚠️")
print("• Whale accumulation (adding weight) ⚠️")
print("")
print("Structural rating: CRITICAL")
print("Time to failure: IMMINENT")

# Thunder's flood warning
current_btc = float(client.get_product('BTC-USD')['price'])
print("\n⚡ THUNDER'S FLOOD WARNING (69%):")
print("-" * 50)
print("'MEAN OLD LEVEE, TAUGHT ME TO WEEP AND MOAN!'")
print("")
print("The prophecy:")
print(f"• Current level: ${current_btc:,.0f}")
print(f"• Levee height: $113,000")
print(f"• Breaking point: ${113000 - current_btc:.0f} away")
print(f"• Flood zone: $114,000+")
print("")
print("'GOING TO CHICAGO!'")
print("  (Going to $114K!)")
print("'SORRY BUT I CAN'T TAKE YOU!'")
print("  (Bears can't come!)")

# The great flood simulation
print("\n💥 WHEN IT BREAKS (SIMULATION):")
print("-" * 50)

flood_stages = [
    ("Pre-break", f"${current_btc:,.0f}", "Building..."),
    ("First crack", "$113,000", "LEVEE CRACKING!"),
    ("Full breach", "$113,200", "WATER RUSHING!"),
    ("Flood stage 1", "$113,500", "UNSTOPPABLE!"),
    ("Flood stage 2", "$113,800", "WASHING AWAY RESISTANCE!"),
    ("New high ground", "$114,000", "SAFE AT LAST!"),
    ("Beyond", "$115,000+", "TO THE MOON!")
]

for stage, price, status in flood_stages:
    print(f"{stage:15} → {price:10} - {status}")
    time.sleep(0.5)

# Portfolio in the flood
print("\n🚢 PORTFOLIO ARK:")
print("-" * 50)
print(f"Current value: ${total_value:.2f}")
print(f"Started with: $292.50")
print(f"Survived: {((total_value/292.50)-1)*100:.0f}% flood of gains")
print("")
print("When the levee breaks:")
print(f"• If BTC → $114K: Portfolio → ${total_value * (114000/current_btc):.2f}")
print(f"• If BTC → $120K: Portfolio → ${total_value * (120000/current_btc):.2f}")
print(f"• If BTC → $126K: Portfolio → ${total_value * (126000/current_btc):.2f}")

# Final flood status
final_btc = float(client.get_product('BTC-USD')['price'])
print("\n🌊 FINAL LEVEE STATUS:")
print("-" * 50)
print(f"Water level: ${final_btc:,.0f}")
print(f"Levee ($113K): ${113000 - final_btc:.0f} from breaking")
print(f"Safety ($114K): ${114000 - final_btc:.0f} away")
print("")
if final_btc >= 113000:
    print("⚠️ LEVEE BREACHED! FLOOD IN PROGRESS!")
elif final_btc >= 112950:
    print("🚨 CRITICAL! LEVEE ABOUT TO BREAK!")
elif final_btc >= 112900:
    print("⚠️ WARNING! Water rising fast!")
else:
    print("Building pressure... rain continues...")

print(f"\n" + "🌊" * 35)
print("WHEN THE LEVEE BREAKS!")
print(f"17+ HOURS AT ${final_btc:,.0f}!")
print(f"${113000 - final_btc:.0f} FROM BREAKING!")
print(f"PORTFOLIO ARK: ${total_value:.2f}!")
print("MEAN OLD LEVEE!")
print("🌊" * 35)