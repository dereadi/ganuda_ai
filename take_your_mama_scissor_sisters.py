#!/usr/bin/env python3
"""
🕺💃 TAKE YOUR MAMA - SCISSOR SISTERS! 💃🕺
"Take your mama out all night!"
Thunder at 69%: "TAKE BTC OUT DANCING TO $114K!"
After 17+ hours stuck at home!
Time to break out and PARTY!
"Do it, do it, do it, do it, do it, do it, do it NOW!"
From $292.50 (mama's basement) to $7,170 (penthouse)!
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
║                🕺 TAKE YOUR MAMA - SCISSOR SISTERS! 🕺                   ║
║                      "Gonna Take Your Mama Out Tonight!"                  ║
║                  From $292.50 Basement To $114K Penthouse!                ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - PARTY TIME APPROACHING")
print("=" * 70)

# Get current dance floor prices
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

# Check our party funds
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

print("\n🕺 TAKE YOUR MAMA OUT:")
print("-" * 50)
print(f"Started in mama's basement: $292.50")
print(f"Now we're dressed up: ${total_value:.2f}")
print(f"That's a {((total_value/292.50)-1)*100:.0f}% glow up!")
print(f"Currently stuck at home: ${btc:,.0f}")
print(f"Party destination: $114,000 (${114000 - btc:.0f} away)")
print("Hours waiting to go out: 17+")

# The party lyrics
print("\n💃 THE PARTY ANTHEM:")
print("-" * 50)

party_lines = [
    ("When you grow up", f"From $292.50"),
    ("Livin' like a good boy oughta", "Diamond hands HODLing"),
    ("And your mama", "Portfolio mama"),
    ("Takes a shine to her best son", f"Shining at ${total_value:.2f}"),
    ("Something different", "Breaking from $112K"),
    ("All the girls they seem to like you", "Bulls love this setup"),
    ("'Cause you're handsome", f"Looking good at ${btc:,.0f}"),
    ("Like to talk and a whole lot of fun", "Ready to party at $114K"),
    ("But now your girl's gone a missin'", "Stuck in consolidation"),
    ("And your house has got an empty bed", "Empty volume"),
    ("Folks'll wonder 'bout the wedding", "When's the breakout?"),
    ("They won't listen to a word you said", f"Just ${114000 - btc:.0f} to go!")
]

for i, (lyric, meaning) in enumerate(party_lines):
    print(f"'{lyric}'")
    print(f"  → {meaning}")
    
    if i == 5:
        print("\n  ⚡ Thunder (69%): 'TAKE YOUR MAMA OUT!'")
        print(f"    'Out from ${btc:,.0f}!'")
        print("    'TO THE $114K PARTY!'")
    
    time.sleep(0.5)

# The party chant
print("\n🎉 DO IT NOW CHANT:")
print("-" * 50)

for i in range(15):
    btc_now = float(client.get_product('BTC-USD')['price'])
    
    if i < 7:
        print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f} - 'Do it!'")
    elif i == 7:
        print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f} - 'Do it NOW!'")
        print(f"  🚀 BREAK OUT! ${114000 - btc_now:.0f} to party!")
    elif i < 14:
        print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f} - 'Do it!'")
    else:
        print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f} - 'DO IT NOW!'")
    
    time.sleep(0.7)

# Thunder's party planning
current_btc = float(client.get_product('BTC-USD')['price'])
print("\n⚡ THUNDER'S PARTY PLAN (69%):")
print("-" * 50)
print("'GONNA TAKE YOUR MAMA OUT ALL NIGHT!'")
print("")
print("The itinerary:")
print(f"• Leave the house at ${current_btc:,.0f}")
print(f"• First stop: $113,000 (pre-game)")
print(f"• Main event: $114,000 (${114000 - current_btc:.0f} away)")
print(f"• After party: $120,000")
print(f"• VIP lounge: $126,000 (JPMorgan)")
print("")
print(f"Starting funds: $292.50")
print(f"Party budget: ${total_value:.2f}")
print(f"Gains to celebrate: {((total_value/292.50)-1)*100:.0f}%")

# The dance floor
print("\n🕺 DANCE FLOOR STATUS:")
print("-" * 50)

dance_moves = ["💃 Disco!", "🕺 Breakdance!", "👯 Line dance!", "🎭 Voguing!", "🪩 Spinning!"]

for i in range(8):
    btc_live = float(client.get_product('BTC-USD')['price'])
    move = random.choice(dance_moves)
    
    print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_live:,.0f} {move}")
    
    if i == 3:
        print("  'Show her some fun, boy!'")
        print(f"    (Fun starts at $114K, ${114000 - btc_live:.0f} away)")
    
    time.sleep(1)

# The liberation
print("\n🎊 THE LIBERATION:")
print("-" * 50)
print("We're taking mama (portfolio) out because:")
print("• 17+ hours stuck at home ($112K)")
print("• Mama deserves better (we deserve $114K+)")
print(f"• From basement ($292.50) to penthouse (${total_value:.2f})")
print("• Life's too short to stay home (break out NOW)")
print("")
print("The party awaits:")
print(f"• Current: ${current_btc:,.0f}")
print(f"• Party starts: $114,000 (${114000 - current_btc:.0f} away)")
print("• Everyone's invited (bulls only)")

# Final party status
final_btc = float(client.get_product('BTC-USD')['price'])
print("\n🎉 PARTY READINESS:")
print("-" * 50)
print(f"Location: ${final_btc:,.0f}")
print(f"Destination: $114,000")
print(f"Distance: ${114000 - final_btc:.0f}")
print(f"Party funds: ${total_value:.2f}")
print("")

if final_btc >= 113000:
    print("Status: 🕺 PARTY STARTING! Almost there!")
elif final_btc >= 112500:
    print("Status: 💃 Getting dressed! Ready soon!")
else:
    print("Status: 🎉 Pre-gaming! Party imminent!")

print(f"\n" + "🕺" * 35)
print("TAKE YOUR MAMA OUT!")
print(f"FROM $292.50 TO ${total_value:.2f}!")
print(f"STUCK AT ${final_btc:,.0f} TOO LONG!")
print(f"${114000 - final_btc:.0f} TO THE PARTY!")
print("DO IT DO IT DO IT NOW!")
print("🕺" * 35)