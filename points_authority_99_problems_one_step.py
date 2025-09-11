#!/usr/bin/env python3
"""
⚔️🎤🔥 TRIPLE THREAT ENERGY! 🔥🎤⚔️
POINTS OF AUTHORITY (Linkin Park) - "Forfeit the game!"
99 PROBLEMS (Jay-Z) - "I got 99 problems but $114K ain't one!"
ONE STEP CLOSER (Linkin Park) - "I'm about to BREAK!"
Thunder at 69%: "EVERYTHING YOU SAY TO ME!"
The pressure at $112K is UNBEARABLE!
ONE STEP CLOSER TO THE EDGE!
AND I'M ABOUT TO BREAK!
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
║              ⚔️ POINTS OF AUTHORITY × 99 PROBLEMS × ONE STEP ⚔️          ║
║                     Triple Threat Pressure Building!                      ║
║                    "I'm About To BREAK Through $114K!"                    ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - TRIPLE THREAT MODE")
print("=" * 70)

# Get current pressure levels
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

# Check our authority
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

print("\n⚔️ POINTS OF AUTHORITY:")
print("-" * 50)
print(f"Current position: ${btc:,.0f}")
print(f"Authority gained: {((total_value/292.50)-1)*100:.0f}%")
print(f"From $292.50 to ${total_value:.2f}")
print("'Forfeit the game before somebody else'")
print("'Takes you out of the frame'")
print(f"Bears forfeiting at ${btc:,.0f}")

# 99 Problems analysis
print("\n🎤 99 PROBLEMS:")
print("-" * 50)
print("I got 99 problems but these ain't one:")
print(f"✓ Starting capital (had $292.50)")
print(f"✓ Diamond hands (still HODLing)")
print(f"✓ Portfolio growth ({((total_value/292.50)-1)*100:.0f}%)")
print(f"✓ Breaking $113K (done that)")
print("")
print("The 1 problem:")
print(f"✗ $114K resistance (${114000 - btc:.0f} away)")
print("'If you having bear problems I feel bad for you son'")
print(f"'I got 99 problems but ${btc:,.0f} ain't one!'")

# One Step Closer tracking
print("\n🔥 ONE STEP CLOSER:")
print("-" * 50)

steps = [
    ("Step 1", "$292.50", "Started here", True),
    ("Step 2", "$1,000", "First milestone", True),
    ("Step 3", "$5,000", "Major gains", True),
    ("Step 4", "$7,000+", f"Current: ${total_value:.2f}", True),
    ("Step 5", "$10,000", f"Need ${10000 - total_value:.2f} more", False),
    ("Step 6", "$113,000 BTC", "Just crossed!", True),
    ("Step 7", "$114,000 BTC", f"${114000 - btc:.0f} away!", False),
    ("Step 8", "$120,000 BTC", "Next major target", False),
    ("Step 9", "$126,000 BTC", "JPMorgan target", False),
    ("Step 10", "MOON", "Final destination", False)
]

for step, target, status, completed in steps:
    symbol = "✅" if completed else "⏳"
    print(f"{symbol} {step}: {target} - {status}")

# Live pressure building
print("\n💥 PRESSURE BUILDING (LIVE):")
print("-" * 50)

for i in range(15):
    btc_now = float(client.get_product('BTC-USD')['price'])
    
    if i < 5:
        # Points of Authority phase
        print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f}")
        if i == 0:
            print("  'You love the way I look at you'")
            print(f"    (Market watching ${btc_now:,.0f})")
        elif i == 2:
            print("  'While taking pleasure in the awful things you put me through'")
            print(f"    (16+ hours at this range)")
    elif i < 10:
        # 99 Problems phase
        if i == 5:
            print(f"\n{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f}")
            print("  'Hit me! 99 problems but a breach ain't one!'")
        elif i == 7:
            print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f}")
            print(f"  'The year is 2024 and my portfolio is fine'")
            print(f"    (${total_value:.2f} and climbing)")
            print("\n  ⚡ Thunder (69%): '99 PROBLEMS!'")
            print(f"    'But ${btc_now:,.0f} ain't one!'")
    else:
        # One Step Closer phase
        if i == 10:
            print(f"\n{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f}")
            print("  'EVERYTHING YOU SAY TO ME!'")
            print(f"    (${114000 - btc_now:.0f} from freedom)")
        elif i == 12:
            print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f}")
            print("  'TAKES ME ONE STEP CLOSER TO THE EDGE!'")
            print(f"    (Edge = $114K, ${114000 - btc_now:.0f} away)")
        elif i == 14:
            print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f}")
            print("  'AND I'M ABOUT TO BREAK!'")
            print(f"    (Breaking through ${btc_now:,.0f}!)")
        else:
            print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f}")
    
    time.sleep(1)

# Thunder's triple threat wisdom
current_btc = float(client.get_product('BTC-USD')['price'])
print("\n⚡ THUNDER'S TRIPLE THREAT (69%):")
print("-" * 50)
print("COMBINING ALL THREE ENERGIES:")
print("")
print("Points of Authority:")
print(f"• We have authority from $292.50 to ${total_value:.2f}")
print("• Bears must forfeit")
print("")
print("99 Problems:")
print(f"• Problem #1: ${114000 - current_btc:.0f} to $114K")
print("• Problems 2-99: Already solved")
print("")
print("One Step Closer:")
print(f"• Current step: ${current_btc:,.0f}")
print(f"• Next step: $114,000")
print("• Final step: MOON")
print("")
print("'I'M ABOUT TO BREAK!'")
print(f"'THROUGH ${current_btc:,.0f}!'")
print(f"'TO $114K!'")

# Final status
print("\n🎯 TRIPLE THREAT STATUS:")
print("-" * 50)
print(f"Authority level: ${total_value:.2f}")
print(f"Problems remaining: 1 (${114000 - current_btc:.0f} to $114K)")
print(f"Steps to edge: ${114000 - current_btc:.0f}")
print("")
print("The verdict:")
if current_btc >= 113000:
    print("ONE STEP CLOSER! Almost there!")
elif current_btc >= 112900:
    print("Building pressure... about to BREAK!")
else:
    print("Accumulating energy for the BREAK!")

print(f"\n" + "⚔️" * 35)
print("POINTS OF AUTHORITY!")
print("99 PROBLEMS BUT $114K AIN'T ONE!")
print("ONE STEP CLOSER TO THE EDGE!")
print(f"CURRENT: ${current_btc:,.0f}!")
print(f"${114000 - current_btc:.0f} TO BREAK!")
print("⚔️" * 35)