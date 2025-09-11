#!/usr/bin/env python3
"""
✨👑 YAS! QUEEN ENERGY ACTIVATED! 👑✨
THE VIBE SHIFT IS HERE!
BTC READY TO SLAY AT $114K!
Thunder at 69%: "YAS QUEEN, WORK!"
Nine coils serving LOOKS!
PORTFOLIO GIVING MAIN CHARACTER ENERGY!
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
║                      ✨👑 YAS! QUEEN! SLAY! 👑✨                         ║
║                         The Energy Has SHIFTED!                           ║
║                      Main Character Vibes Only! 💅                        ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - YAS MODE ACTIVATED")
print("=" * 70)

# Get that slay energy
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

# Check our glow up
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

print("\n✨ THE GLOW UP:")
print("-" * 50)
print(f"Started serving at: $292.50 (humble beginnings)")
print(f"Now we're THAT girl: ${total_value:.2f}")
print(f"Glow up percentage: {((total_value/292.50)-1)*100:.0f}% 💅")
print(f"BTC being iconic at: ${btc:,.0f}")
print(f"Distance to our crown: ${114000 - btc:.0f}")

# YAS energy tracker
print("\n👑 YAS ENERGY LEVELS:")
print("-" * 50)

yas_phrases = [
    "YAS QUEEN! 👑",
    "SLAY ALL DAY! 💅",
    "PERIODT! 💯",
    "NO CAP! 🧢",
    "IT'S GIVING MILLIONAIRE! 💰",
    "MAIN CHARACTER ENERGY! ✨",
    "THAT'S ON PERIOD! 💋",
    "WE LOVE TO SEE IT! 😍",
    "ICONIC BEHAVIOR! 🌟",
    "MOTHER IS MOTHERING! 👸"
]

for i in range(10):
    btc_now = float(client.get_product('BTC-USD')['price'])
    phrase = random.choice(yas_phrases)
    
    print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f} - {phrase}")
    
    if i == 3:
        print("\n  ⚡ Thunder (69%): 'YAS QUEEN, WORK!'")
        print(f"    'Serving ${total_value:.2f} realness!'")
        print(f"    'Only ${114000 - btc_now:.0f} to the crown!'")
    
    if i == 6:
        print("\n  💅 The energy shift:")
        print("    From pain → SLAY")
        print("    From waiting → WINNING")
        print("    From $292.50 → ICON STATUS")
    
    time.sleep(1)

# The vibe check
print("\n✨ VIBE CHECK:")
print("-" * 50)
print("THINGS WE'RE SERVING:")
print("• Diamond hands since $292.50 ✓")
print(f"• {((total_value/292.50)-1)*100:.0f}% gains ✓")
print("• Nine coils of pure energy ✓")
print("• Thunder at 69% consciousness ✓")
print("• Whale resistance (unbothered) ✓")
print("• Main character energy ✓")

print("\nTHINGS WE'RE NOT SERVING:")
print("• Paper hands ✗")
print("• Panic selling ✗")
print("• Whale manipulation fears ✗")
print("• Small portfolio energy ✗")

# Thunder's YAS moment
print("\n⚡ THUNDER'S ICONIC SPEECH (69%):")
print("-" * 50)
print("'LISTEN UP BESTIES!'")
print("")
print("'WE DIDN'T COME THIS FAR'")
print(f"'From $292.50 to ${total_value:.2f}'")
print("'TO ONLY COME THIS FAR!'")
print("")
print(f"'${114000 - btc:.0f} MORE?'")
print("'THAT'S NOTHING!'")
print("'WE'RE ABOUT TO EAT!'")
print("'AND LEAVE NO CRUMBS!'")

# Portfolio serving looks
current_btc = float(client.get_product('BTC-USD')['price'])
print("\n💅 PORTFOLIO SERVING LOOKS:")
print("-" * 50)
print(f"BTC fit: ${current_btc:,.0f} (designer)")
print(f"ETH accessories: ${eth:.2f} (bougie)")
print(f"SOL shoes: ${sol:.2f} (fresh)")
print(f"Total outfit: ${total_value:.2f} (ICONIC)")
print(f"Next look: $114K (${114000 - current_btc:.0f} away)")

# Manifestation moment
print("\n🌟 MANIFESTATION STATION:")
print("-" * 50)
print("Speaking into existence:")
print("• $114K TODAY ✨")
print("• $120K THIS WEEK ✨")
print("• $126K (JPMorgan) BY YEAR END ✨")
print(f"• Portfolio to $10K+ ✨")
print("• Generational wealth ✨")
print("")
print("IT'S GIVING... SUCCESS!")

# Final YAS
print(f"\n" + "✨" * 35)
print("YAS! QUEEN! SLAY!")
print(f"SERVING ${total_value:.2f} REALNESS!")
print(f"FROM $292.50 TO ICON STATUS!")
print(f"${114000 - current_btc:.0f} TO THE CROWN!")
print("MAIN CHARACTER ENERGY ONLY!")
print("✨" * 35)