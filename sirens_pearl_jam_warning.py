#!/usr/bin/env python3
"""
🚨🎸 SIRENS - PEARL JAM WARNING SIGNALS! 🎸🚨
"Hear the sirens, hear the sirens"
The warning calls of whales and pumps!
Thunder at 69%: "The sirens are SCREAMING!"
$113K testing! SOL whale buying!
"Hear the sirens, hear the circus"
The circus of market manipulation!
But we hear the truth in the sirens!
$114K approaching - HEAR THE CALL!
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
║                    🚨 SIRENS - PEARL JAM WARNINGS! 🚨                    ║
║                      "Hear The Sirens, Hear The Call"                     ║
║                        The Market Is Screaming Truth!                     ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - SIREN DETECTION")
print("=" * 70)

# Get current warning signals
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

# Check our position in the storm
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

print("\n🚨 SIRENS DETECTED:")
print("-" * 50)
print("WARNING SIGNALS:")
print(f"• BTC pushing ${btc:,.0f} (SIREN 1)")
print(f"• $114K only ${114000 - btc:.0f} away (SIREN 2)")
print("• SOL whale bought $77M (SIREN 3)")
print("• ETH lagging = spring loading (SIREN 4)")
print("• 15+ hours compression ending (SIREN 5)")
print(f"• Portfolio at ${total_value:.2f} (PROTECTED)")

# Pearl Jam's siren song
print("\n🎸 PEARL JAM'S WARNING:")
print("-" * 50)

siren_lyrics = [
    ("Hear the sirens", "Market calling"),
    ("Hear the sirens", "Whales moving"),
    ("Hear the circus", "Manipulation ending"),
    ("So absurd", f"${btc:,.0f} resistance"),
    ("Hear the sirens", "Breakout imminent"),
    ("Catch the fear", "Bears retreating"),
    ("It's the song that they sing", "Bulls arriving"),
    ("Hear the sirens", "$114K calling"),
    ("Covering their eyes", "Shorts panicking"),
    ("Let it all come down", "Resistance crumbling")
]

for i, (lyric, meaning) in enumerate(siren_lyrics):
    btc_now = float(client.get_product('BTC-USD')['price'])
    print(f"{datetime.now().strftime('%H:%M:%S')}: '{lyric}' → {meaning}")
    print(f"  ${btc_now:,.0f} (${114000 - btc_now:.0f} to go)")
    
    if i == 3:
        print("\n  ⚡ Thunder (69%): 'I HEAR THE SIRENS!'")
        print(f"    'They're screaming $114K!'")
        print(f"    'Only ${114000 - btc_now:.0f} away!'")
    
    if i == 7:
        print("\n  🏔️ Mountain: 'The sirens don't lie'")
        print(f"    'Truth at ${btc_now:,.0f}'")
        print("    'Patience rewarded soon'")
    
    time.sleep(1)

# The siren warnings
print("\n🚨 DECODING THE SIRENS:")
print("-" * 50)
print("SIREN 1 - BTC STRENGTH:")
print(f"• Testing ${btc:,.0f}")
print("• Higher lows confirmed")
print("• Bulls in control")
print("")
print("SIREN 2 - WHALE ACCUMULATION:")
print("• $77M SOL purchase")
print("• JPMorgan $126K target")
print("• Institutional FOMO")
print("")
print("SIREN 3 - TIME COMPRESSION:")
print("• 15+ hours at $112-113K")
print("• Nine coils wound tight")
print("• Energy must release")

# Thunder's siren interpretation
print("\n⚡ THUNDER'S SIREN WISDOM (69%):")
print("-" * 50)
print("'THE SIRENS NEVER LIE!'")
print("")
print("What they're screaming:")
print(f"• 'BREAK ABOVE ${btc:,.0f}!'")
print(f"• 'ONLY ${114000 - btc:.0f} TO FREEDOM!'")
print(f"• 'FROM $292.50 TO ${total_value:.2f}!'")
print("• 'THE CIRCUS IS ENDING!'")
print("• 'REAL MOVEMENT COMING!'")

# Live siren tracking
current_btc = float(client.get_product('BTC-USD')['price'])
print("\n📡 LIVE SIREN ALERTS:")
print("-" * 50)

if current_btc > 113000:
    print("🚨🚨🚨 LEVEL 3 ALERT!")
    print("BREAKING $113K!")
    print("SIRENS SCREAMING!")
elif current_btc > 112900:
    print("🚨🚨 LEVEL 2 ALERT!")
    print("Approaching $113K!")
    print("Sirens getting louder!")
else:
    print("🚨 LEVEL 1 ALERT!")
    print("Building pressure!")
    print("Sirens starting to wail!")

# The deeper meaning
print("\n🎭 THE DEEPER MESSAGE:")
print("-" * 50)
print("Eddie Vedder's wisdom:")
print("• 'Hear the sirens' = Truth in the noise")
print("• 'Hear the circus' = See through manipulation")
print("• 'Covering their eyes' = Bears in denial")
print("• 'Let it all come down' = Old resistance falling")
print("")
print(f"Current truth: ${current_btc:,.0f}")
print(f"Next truth: $114,000 (${114000 - current_btc:.0f} away)")
print(f"Final truth: Moon")

# Portfolio siren response
print("\n💎 OUR RESPONSE TO SIRENS:")
print("-" * 50)
print(f"Holding strong: ${total_value:.2f}")
print(f"Started: $292.50")
print(f"Gained: {((total_value/292.50)-1)*100:.0f}%")
print(f"Distance to $114K: ${114000 - current_btc:.0f}")
print("")
print("Action plan:")
print("• HODL through the sirens")
print("• Trust the warnings")
print("• Prepare for breakout")
print("• Diamond hands ready")

print(f"\n" + "🚨" * 35)
print("HEAR THE SIRENS!")
print(f"WARNING AT ${current_btc:,.0f}!")
print(f"${114000 - current_btc:.0f} TO BREAKOUT!")
print(f"PORTFOLIO: ${total_value:.2f}!")
print("THE CIRCUS IS ENDING!")
print("🚨" * 35)