#!/usr/bin/env python3
"""
🛹🎵 KICK, PUSH - LUPE FIASCO MOMENTUM! 🎵🛹
"He was a skater boy, said 'see you later, boy'"
But this is our story - kick, push, coast to $114K!
Thunder at 69%: "KICK PUSH THROUGH $113K!"
We're skating through resistance!
First got on the board at $292.50!
Now we're kick pushing to GLORY!
Coast... coast... to the MOON!
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
║                   🛹 KICK, PUSH - LUPE FIASCO VIBES! 🛹                  ║
║                      Skating Through Resistance!                          ║
║                    First Day on Board: $292.50                           ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - KICK PUSH MODE")
print("=" * 70)

# Get current skateboard position
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

# Check our skateboard value
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

print("\n🛹 OUR SKATEBOARD JOURNEY:")
print("-" * 50)
print(f"First day (started): $292.50")
print(f"Now we're skating at: ${total_value:.2f}")
print(f"That's a {((total_value/292.50)-1)*100:.0f}% ollie!")
print(f"Current position: ${btc:,.0f}")
print(f"Distance to $114K: ${114000 - btc:.0f}")

# The kick push sequence
print("\n🎵 KICK, PUSH, COAST:")
print("-" * 50)

for i in range(20):
    btc_now = float(client.get_product('BTC-USD')['price'])
    eth_now = float(client.get_product('ETH-USD')['price'])
    
    if i % 3 == 0:
        action = "KICK"
        symbol = "🦶"
    elif i % 3 == 1:
        action = "PUSH"
        symbol = "💪"
    else:
        action = "COAST"
        symbol = "🌊"
    
    print(f"{datetime.now().strftime('%H:%M:%S')}: {symbol} {action} → ${btc_now:,.0f}")
    
    if i == 0:
        print("  'First got on the board at $292.50'")
    elif i == 3:
        print(f"  'Now we're at ${btc_now:,.0f}'")
        print(f"  'Only ${114000 - btc_now:.0f} to go'")
    elif i == 6:
        print("\n  ⚡ Thunder (69%): 'KICK PUSH!'")
        print(f"    'Through ${btc_now:,.0f}!'")
        print("    'Never falling off!'")
    elif i == 9:
        print(f"  'From the first kick at $292.50'")
        print(f"  'To this moment at ${btc_now:,.0f}'")
    elif i == 12:
        print("\n  🏔️ Mountain: 'Steady on the board'")
        print("    'Balance through the chop'")
    elif i == 15:
        if btc_now >= 113000:
            print(f"\n  🎯 LANDED THE $113K TRICK!")
            print(f"    Next trick: $114K (${114000 - btc_now:.0f} away)")
    elif i == 18:
        print(f"  'Portfolio cruising at ${total_value:.2f}'")
    
    time.sleep(1)

# Lupe's story parallel
current_btc = float(client.get_product('BTC-USD')['price'])
print("\n📖 THE LUPE PARALLEL:")
print("-" * 50)
print("His story:")
print("• Started with just a board")
print("• Learned to kick, push")
print("• Fell down, got back up")
print("• Eventually mastered the streets")
print("")
print("Our story:")
print(f"• Started with $292.50")
print(f"• Learned to HODL through chop")
print(f"• Survived dips and fakeouts")
print(f"• Now skating at ${total_value:.2f}")
print(f"• Mastering ${current_btc:,.0f}")

# Thunder's skate wisdom
print("\n⚡ THUNDER'S SKATE WISDOM (69%):")
print("-" * 50)
print("'KICK PUSH COAST!'")
print("")
print("The technique:")
print(f"• KICK from $292.50")
print(f"• PUSH through ${current_btc:,.0f}")
print(f"• COAST to $114K (${114000 - current_btc:.0f} away)")
print("")
print("'We didn't just walk here'")
print("'We SKATED through:'")
print("• 16+ hours of consolidation")
print("• Whale manipulations")
print("• Fear and doubt")
print(f"• Now at {((total_value/292.50)-1)*100:.0f}% gains!")

# Current skate status
print("\n🛹 SKATE STATUS:")
print("-" * 50)
print(f"Board position: ${current_btc:,.0f}")
print(f"Portfolio balance: ${total_value:.2f}")
print(f"Distance to next spot: ${114000 - current_btc:.0f}")
print("")

if current_btc >= 113500:
    print("Status: FLYING! Halfway to $114K!")
elif current_btc >= 113000:
    print("Status: CRUISING past $113K!")
elif current_btc >= 112900:
    print("Status: Building speed...")
else:
    print("Status: Setting up the approach...")

# The final coast
print("\n🌊 THE FINAL COAST:")
print("-" * 50)
print("Where we're going:")
print(f"• Current: ${current_btc:,.0f}")
print(f"• Next stop: $114,000")
print(f"• Then: $120,000")
print(f"• Finally: MOON")
print("")
print("How we get there:")
print("• KICK (accumulate)")
print("• PUSH (HODL)")
print("• COAST (profit)")

# Live skating
print("\n🛹 LIVE SKATE SESSION:")
print("-" * 50)

for i in range(5):
    btc_live = float(client.get_product('BTC-USD')['price'])
    
    if i == 0:
        print(f"{datetime.now().strftime('%H:%M:%S')}: Starting at ${btc_live:,.0f}")
    elif i == 2:
        print(f"{datetime.now().strftime('%H:%M:%S')}: Kick, push → ${btc_live:,.0f}")
    elif i == 4:
        print(f"{datetime.now().strftime('%H:%M:%S')}: Coasting at ${btc_live:,.0f}")
        print(f"  Distance to $114K: ${114000 - btc_live:.0f}")
    else:
        print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_live:,.0f}")
    
    time.sleep(1)

final_btc = float(client.get_product('BTC-USD')['price'])
print(f"\n" + "🛹" * 35)
print("KICK, PUSH, COAST!")
print(f"FROM $292.50 TO ${total_value:.2f}!")
print(f"CURRENTLY AT ${final_btc:,.0f}!")
print(f"${114000 - final_btc:.0f} TO $114K!")
print("NEVER FALLING OFF!")
print("🛹" * 35)