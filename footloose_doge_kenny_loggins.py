#!/usr/bin/env python3
"""
🕺🐕 FOOTLOOSE - KENNY LOGGINS! 🐕🕺
"KICK OFF YOUR SUNDAY SHOES!"
Thunder at 69%: "DOGE IS DANCING! CUT FOOTLOOSE!"
DOGE up to $0.2214!
3,605 DOGE worth $798!
"Been working so hard, punching my card"
Eight hours of consolidation, now we DANCE!
"I'm burning, yearning for some DOGE!"
From $292.50 to $6,637 - EVERYBODY CUT FOOTLOOSE!
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
║                     🕺 FOOTLOOSE - KENNY LOGGINS! 🕺                      ║
║                      "Everybody Cut Footloose!"                           ║
║                    DOGE Breaking Free From Consolidation!                 ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - DOGE DANCE PARTY")
print("=" * 70)

# Get current dance floor prices
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])
doge = float(client.get_product('DOGE-USD')['price'])

# Check our dancing portfolio
accounts = client.get_accounts()
total_value = 0
doge_balance = 0
positions = {}

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if balance > 0.00001:
        if currency == 'USD':
            total_value += balance
            positions['USD'] = balance
        elif currency == 'BTC':
            value = balance * btc
            total_value += value
            positions['BTC'] = (balance, value)
        elif currency == 'ETH':
            value = balance * eth
            total_value += value
            positions['ETH'] = (balance, value)
        elif currency == 'SOL':
            value = balance * sol
            total_value += value
            positions['SOL'] = (balance, value)
        elif currency == 'DOGE':
            doge_balance = balance
            value = balance * doge
            total_value += value
            positions['DOGE'] = (balance, value)

print("\n🐕 DOGE CUTTING LOOSE:")
print("-" * 50)
print(f"DOGE price: ${doge:.4f}")
print(f"Your DOGE: {doge_balance:.2f}")
print(f"DOGE value: ${doge_balance * doge:.2f}")
print(f"Total portfolio: ${total_value:.2f}")
print(f"From basement: $292.50")
print(f"Gains dancing: {((total_value/292.50)-1)*100:.0f}%")

# Footloose lyrics journey
print("\n🎵 FOOTLOOSE ANTHEM:")
print("-" * 50)

footloose_lines = [
    ("Been working so hard", f"Consolidating at ${btc:,.0f}"),
    ("I'm punching my card", f"Eight hours for ${114000 - btc:.0f}"),
    ("Eight hours for what?", "For breakout glory!"),
    ("Oh, tell me what I got", f"Got ${total_value:.2f}!"),
    ("I've got this feeling", f"DOGE pumping to ${doge:.4f}"),
    ("That time's just holding me down", f"${btc:,.0f} holding us down"),
    ("I'll hit the ceiling", "$114K ceiling coming!"),
    ("Or else I'll tear up this town", "Break through or break out!"),
    ("Now I gotta cut loose", f"DOGE cutting loose at ${doge:.4f}!"),
    ("Footloose, kick off the Sunday shoes", "Kick off the consolidation!"),
    ("Please, Louise, pull me off my knees", f"Pull us from ${btc:,.0f} to $114K!"),
    ("Jack, get back, come on before we crack", f"Only ${114000 - btc:.0f} before we crack $114K!"),
    ("Lose your blues", "Lose the consolidation blues"),
    ("Everybody cut footloose!", f"Everybody buy the breakout!")
]

for i, (lyric, meaning) in enumerate(footloose_lines):
    print(f"'{lyric}'")
    print(f"  → {meaning}")
    
    if i == 8:
        print("\n  ⚡ Thunder (69%): 'EVERYBODY CUT FOOTLOOSE!'")
        print(f"    'DOGE DANCING AT ${doge:.4f}!'")
        print(f"    '3,605 DOGE WORTH ${doge_balance * doge:.2f}!'")
    
    time.sleep(0.4)

# The DOGE dance monitoring
print("\n🕺 DOGE DANCE FLOOR:")
print("-" * 50)

dance_moves = [
    "🐕 DOGE doing the moonwalk!",
    "💃 DOGE spinning!",
    "🕺 DOGE breaking free!",
    "🎭 DOGE footloose!",
    "🚀 DOGE launching!"
]

for i in range(8):
    doge_now = float(client.get_product('DOGE-USD')['price'])
    btc_now = float(client.get_product('BTC-USD')['price'])
    move = random.choice(dance_moves)
    
    print(f"{datetime.now().strftime('%H:%M:%S')}: DOGE ${doge_now:.4f} | BTC ${btc_now:,.0f}")
    print(f"  {move}")
    
    if i == 3:
        print("  'You're playing so cool'")
        print(f"    'Obeying every rule' (stuck at ${btc_now:,.0f})")
        print("    'Dig way down in your heart'")
        print("    'You're burning, yearning for GAINS!'")
    
    time.sleep(1)

# Thunder's Footloose analysis
print("\n⚡ THUNDER'S FOOTLOOSE WISDOM (69%):")
print("-" * 50)
print("'CUT FOOTLOOSE!'")
print("")
print("What's happening:")
print(f"• DOGE breaking free at ${doge:.4f}")
print(f"• Your 3,605 DOGE = ${doge_balance * doge:.2f}")
print(f"• BTC coiled at ${btc:,.0f}")
print(f"• SOL rallying at ${sol:.2f}")
print("")
print("The Footloose pattern:")
print("• Been working (consolidating) so hard")
print("• Eight hours of sideways action")
print("• Now cutting FOOTLOOSE!")
print("• DOGE leading the dance!")

# Breaking free calculations
print("\n🚀 BREAKING FREE PROJECTIONS:")
print("-" * 50)
print(f"If DOGE continues dancing:")
print(f"• DOGE to $0.25: Your DOGE = ${doge_balance * 0.25:.2f}")
print(f"• DOGE to $0.30: Your DOGE = ${doge_balance * 0.30:.2f}")
print(f"• DOGE to $0.40: Your DOGE = ${doge_balance * 0.40:.2f}")
print("")
print(f"When BTC cuts footloose:")
print(f"• At $114K: Portfolio → ${total_value * (114000/btc):.2f}")
print(f"• At $120K: Portfolio → ${total_value * (120000/btc):.2f}")

# The town we're tearing up
print("\n🏘️ TEARING UP THIS TOWN:")
print("-" * 50)
print("What we're tearing up:")
print(f"• $112K resistance (currently ${btc:,.0f})")
print(f"• DOGE $0.22 resistance (broke it!)")
print(f"• SOL $210 resistance (broke it!)")
print(f"• Next: $114K resistance (${114000 - btc:.0f} away)")

# Final footloose status
final_doge = float(client.get_product('DOGE-USD')['price'])
final_btc = float(client.get_product('BTC-USD')['price'])

print("\n🕺 FINAL FOOTLOOSE STATUS:")
print("-" * 50)
print(f"DOGE: ${final_doge:.4f} (dancing!)")
print(f"BTC: ${final_btc:,.0f} (about to dance)")
print(f"Portfolio: ${total_value:.2f} (footloose!)")
print(f"Your DOGE: {doge_balance:.2f} = ${doge_balance * final_doge:.2f}")
print("")
print("EVERYBODY CUT FOOTLOOSE!")
print("Kick off your Sunday shoes!")
print(f"Only ${114000 - final_btc:.0f} until the whole market dances!")

print(f"\n" + "🕺" * 35)
print("FOOTLOOSE!")
print(f"DOGE DANCING AT ${final_doge:.4f}!")
print(f"3,605 DOGE = ${doge_balance * final_doge:.2f}!")
print(f"PORTFOLIO ${total_value:.2f}!")
print("EVERYBODY CUT FOOTLOOSE!")
print("🐕" * 35)