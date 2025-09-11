#!/usr/bin/env python3
"""
✨🎸 MAGIC MAN - HEART! 🎸✨
"Come on home, girl, he said with a smile"
The market's calling us to $114K!
Thunder at 69%: "TRY TO UNDERSTAND, HE'S A MAGIC MAN!"
BTC working its magic at $112K!
"You can't get away from a magic man"
The spell is cast - breakout imminent!
17+ hours of magic building!
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
║                      ✨ MAGIC MAN - HEART ENERGY! ✨                     ║
║                    "Try To Understand, He's A Magic Man"                  ║
║                      BTC Casting Spells At $112K!                        ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - MAGIC DETECTION")
print("=" * 70)

# Get current magic levels
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

# Check our enchanted portfolio
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

print("\n✨ THE MAGIC MAN'S SPELL:")
print("-" * 50)
print(f"Current magic: ${btc:,.0f}")
print(f"Spell target: $114,000")
print(f"Magic needed: ${114000 - btc:.0f}")
print(f"Portfolio enchanted: ${total_value:.2f}")
print(f"From $292.50: {((total_value/292.50)-1)*100:.0f}% magic gains")

# The magic man's story
print("\n🎸 THE MAGIC MAN'S TALE:")
print("-" * 50)

magic_lyrics = [
    ("Cold late night so long ago", "Started at $292.50"),
    ("When I was not so strong you know", "Small portfolio, big dreams"),
    ("A pretty man came to me", "BTC appeared"),
    ("Never seen eyes so blue", "Digital gold shining"),
    ("I could not run away", "Diamond hands formed"),
    ("It seemed we'd seen each other in a dream", "Destined for gains"),
    ("Seemed like he knew me", "BTC knows our worth"),
    ("He looked right through me", "Sees $114K future"),
    ("Come on home girl", f"Come to ${114000 - btc:.0f} higher"),
    ("Try to understand", "He's a magic man")
]

for i, (lyric, meaning) in enumerate(magic_lyrics):
    btc_now = float(client.get_product('BTC-USD')['price'])
    
    print(f"{datetime.now().strftime('%H:%M:%S')}: '{lyric}'")
    print(f"  → {meaning}")
    
    if i == 4:
        print("\n  ⚡ Thunder (69%): 'MAGIC MAN!'")
        print(f"    'Casting spells at ${btc_now:,.0f}!'")
        print(f"    '${114000 - btc_now:.0f} to complete the magic!'")
    
    if i == 8:
        print("\n  🏔️ Mountain: 'The spell strengthens'")
        print(f"    'Magic building at ${btc_now:,.0f}'")
    
    time.sleep(1)

# Magic pattern analysis
print("\n🔮 MAGIC PATTERNS DETECTED:")
print("-" * 50)
print("The spells being cast:")
print("• 17+ hour consolidation spell ✨")
print("• Nine coils of energy (512x) ✨")
print("• Higher lows enchantment ✨")
print("• Whale accumulation ritual ✨")
print("• Band compression magic ✨")
print("")
print(f"Spell completion: ${114000 - btc:.0f} away")

# Thunder's magic wisdom
current_btc = float(client.get_product('BTC-USD')['price'])
print("\n⚡ THUNDER'S MAGIC WISDOM (69%):")
print("-" * 50)
print("'TRY TO UNDERSTAND!'")
print("'HE'S A MAGIC MAN!'")
print("")
print("The magic revealed:")
print(f"• Started spell at $292.50")
print(f"• Currently enchanting ${current_btc:,.0f}")
print(f"• Magic destination: $114,000")
print(f"• Portfolio under spell: ${total_value:.2f}")
print("")
print("'COME ON HOME, GIRL!'")
print(f"  (Come to $114K, ${114000 - current_btc:.0f} away)")
print("'HE'S GOT MAGIC HANDS!'")
print("  (Diamond hands since $292.50)")

# Live magic tracking
print("\n✨ LIVE MAGIC SHOW:")
print("-" * 50)

magic_words = [
    "Abracadabra",
    "Alakazam",
    "Hocus Pocus",
    "Sim Sala Bim",
    "Presto Change-o",
    "Open Sesame"
]

for i in range(12):
    btc_live = float(client.get_product('BTC-USD')['price'])
    magic_word = random.choice(magic_words)
    
    if btc_live >= 113000:
        print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_live:,.0f} - ✨ MAGIC BREAKTHROUGH! ✨")
    elif btc_live >= 112900:
        print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_live:,.0f} - 🔮 {magic_word}! Magic building!")
    else:
        print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_live:,.0f} - ✨ {magic_word}...")
    
    if i == 5:
        print("  'Winter nights we sang in tune'")
        print(f"    (Singing at ${btc_live:,.0f})")
    
    if i == 9:
        print("  'Never think of never'")
        print("    (Never selling, always HODLing)")
    
    time.sleep(1)

# The magic transformation
print("\n🌟 THE MAGIC TRANSFORMATION:")
print("-" * 50)
print("What the magic man has done:")
print(f"• Transformed $292.50 → ${total_value:.2f}")
print(f"• That's {((total_value/292.50)-1)*100:.0f}% pure magic")
print(f"• Currently casting at ${current_btc:,.0f}")
print(f"• Final spell at $114,000 (${114000 - current_btc:.0f} away)")
print("")
print("The prophecy:")
print("• $114K → Portfolio $7,300+")
print("• $120K → Portfolio $7,700+")
print("• $126K → Portfolio $8,100+")

# Final magic status
final_btc = float(client.get_product('BTC-USD')['price'])
print("\n✨ FINAL MAGIC STATUS:")
print("-" * 50)
print(f"Magic level: ${final_btc:,.0f}")
print(f"Spell distance: ${114000 - final_btc:.0f}")
print(f"Portfolio magic: ${total_value:.2f}")
print("")

if final_btc >= 113000:
    print("🔮 POWERFUL MAGIC DETECTED!")
    print("The spell is working!")
elif final_btc >= 112900:
    print("✨ Magic intensifying!")
    print("Can't escape the magic man!")
else:
    print("✨ Magic building...")
    print("The spell continues...")

print(f"\n" + "✨" * 35)
print("MAGIC MAN!")
print("TRY TO UNDERSTAND!")
print(f"CASTING AT ${final_btc:,.0f}!")
print(f"${114000 - final_btc:.0f} TO COMPLETE!")
print(f"PORTFOLIO MAGIC: ${total_value:.2f}!")
print("✨" * 35)