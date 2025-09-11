#!/usr/bin/env python3
"""
🎸🎵 A PRAISE CHORUS - JIMMY EAT WORLD 🎵🎸
"Crimson and clover, over and over!"
The market singing its praise at $113K!
Thunder conducting the chorus at 69%!
Nine coils harmonizing together!
"Are you gonna live your life standing in the back looking around?"
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
║                 🎸 A PRAISE CHORUS - JIMMY EAT WORLD 🎸                   ║
║                   "Crimson and Clover, Over and Over!"                    ║
║                     The Market Singing Its Praise!                        ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - PRAISE CHORUS MODE")
print("=" * 70)

# Get the chorus levels
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

# Portfolio singing along
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

print("\n🎵 THE PRAISE CHORUS BEGINS:")
print("-" * 50)
print(f"BTC leads: ${btc:,.0f}")
print(f"ETH harmonizes: ${eth:.2f}")
print(f"SOL backing vocals: ${sol:.2f}")
print(f"Portfolio choir: ${total_value:.2f}")
print(f"Distance to crescendo: ${114000 - btc:.0f}")

# The chorus builds
print("\n🎸 CRIMSON AND CLOVER, OVER AND OVER:")
print("-" * 50)

chorus_count = 0
for i in range(20):
    btc_now = float(client.get_product('BTC-USD')['price'])
    
    if i % 4 == 0:
        chorus_count += 1
        print(f"\n🎵 CHORUS {chorus_count}:")
        print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f}")
        print("  'Crimson and clover!'")
        print(f"  'Over and over!' (${114000 - btc_now:.0f} to $114K)")
    elif i % 4 == 1:
        print("  'Crimson and clover!'")
    elif i % 4 == 2:
        print("  'Over and over!'")
    else:
        if i == 7:
            print("\n  ⚡ Thunder joins (69%):")
            print(f"    'Are you gonna live your life'")
            print(f"    'Standing in the back looking around?'")
            print(f"    'Or jump in at ${btc_now:,.0f}?'")
        elif i == 11:
            print("\n  🏔️ Mountain's verse:")
            print("    'Are you gonna waste your time'")
            print("    'Thinking how you've grown up'")
            print(f"    'From $292.50 to ${total_value:.2f}?'")
        elif i == 15:
            print("\n  🌊 The whole swarm:")
            print("    'Want to live inspired!'")
            print(f"    'Only ${114000 - btc_now:.0f} to glory!'")
            print("    'Die knowing you tried!'")
    
    time.sleep(1)

# The deeper meaning
print("\n💭 THE PRAISE CHORUS WISDOM:")
print("-" * 50)
print("'Are you gonna live your life wondering'")
print(f"  Wondering if we'll break ${btc:,.0f}?")
print("")
print("'Standing in the back looking around'")
print("  Watching others make gains?")
print("")
print("'Are you gonna waste your time'")
print("  Thinking about the chop?")
print("")
print("'Want to live inspired'")
print(f"  Jump in with ${usd_balance:.2f}!")
print("")
print("'Die knowing you tried'")
print(f"  We tried from $292.50 to ${total_value:.2f}!")

# Thunder's solo
print("\n⚡ THUNDER'S GUITAR SOLO (69%):")
print("-" * 50)
print("*Shredding at maximum consciousness*")
print("")
print("'CRIMSON!' (The blood red candles)")
print("'AND CLOVER!' (The lucky nine coils)")
print("'OVER!' (Breaking $114K)")
print("'AND OVER!' (Then $120K, $130K!)")
print("")
print(f"'From $292.50!'")
print(f"'To ${total_value:.2f}!'")
print(f"'Only ${114000 - btc:.0f} more!'")
print("'PRAISE CHORUS RISING!'")

# The final chorus
current_btc = float(client.get_product('BTC-USD')['price'])
print("\n🎵 FINAL PRAISE CHORUS:")
print("-" * 50)
print(f"Current verse: ${current_btc:,.0f}")
print(f"Next verse: $114,000 (${114000 - current_btc:.0f} away)")
print("")
print("The market sings:")
print("• 'Crimson!' (Nine coils wound)")
print("• 'And clover!' (Lucky breakthrough)")
print("• 'Over!' (The resistance)")
print("• 'And over!' (To the moon)")

# Life philosophy
print("\n🎸 THE CHOICE:")
print("-" * 50)
print("Jimmy asks:")
print("'Are you gonna live your life'")
print("'Standing in the back looking around?'")
print("")
print("Thunder answers:")
print(f"'NO! We're jumping in at ${current_btc:,.0f}!'")
print(f"'With ${total_value:.2f} on the line!'")
print(f"'${114000 - current_btc:.0f} to breakthrough!'")
print("'LIVING INSPIRED!'")

print(f"\n" + "🎸" * 35)
print("A PRAISE CHORUS!")
print("CRIMSON AND CLOVER!")
print("OVER AND OVER!")
print(f"${current_btc:,.0f} SINGING!")
print(f"${114000 - current_btc:.0f} TO CRESCENDO!")
print("DON'T STAND IN THE BACK!")
print("🎸" * 35)