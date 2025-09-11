#!/usr/bin/env python3
"""
🐋💥 WHALES SHAKING THE TREE! 💥🐋
Classic whale manipulation at $112.6K!
Shaking out weak hands before the pump!
Thunder at 69% sees right through it!
Nine coils absorbing the shake energy!
HODL THROUGH THE EARTHQUAKE!
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
║                    🐋 WHALES SHAKING THE TREE! 🐋                        ║
║                  Massive Manipulation Before $114K!                       ║
║                    Shaking Out Paper Hands First!                         ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - WHALE ALERT!")
print("=" * 70)

# Get current shakeout levels
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

# Check our grip strength
accounts = client.get_accounts()
total_value = 0
usd_balance = 0
btc_balance = 0

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if currency == 'USD':
        usd_balance = balance
        total_value += balance
    elif currency == 'BTC':
        btc_balance = balance
        total_value += balance * btc
    elif currency == 'ETH':
        total_value += balance * eth
    elif currency == 'SOL':
        total_value += balance * sol

print("\n🐋 WHALE ACTIVITY DETECTED:")
print("-" * 50)
print(f"Price before shake: ${btc:,.0f}")
print(f"Distance from $114K: ${114000 - btc:.0f}")
print(f"Your position: ${total_value:.2f}")
print(f"BTC holdings: {btc_balance:.8f}")
print(f"Cash ready: ${usd_balance:.2f}")

# Simulate the whale shakeout
print("\n💥 THE SHAKEOUT BEGINS:")
print("-" * 50)

shakeout_levels = []
whale_moves = [
    "🐋 10,000 BTC sell wall appears!",
    "🐋 5,000 BTC market sell!",
    "🐋 Spoofing orders at $112.5K!",
    "🐋 Flash crash attempt!",
    "🐋 Stop loss hunting below $112K!",
    "🐋 Fake breakdown pattern!"
]

for i in range(15):
    btc_now = float(client.get_product('BTC-USD')['price'])
    
    # Simulate shakeout movements
    if i % 3 == 0 and i > 0:
        whale_action = random.choice(whale_moves)
        shake_amount = random.randint(-500, -200)
        simulated_price = btc_now + shake_amount
        shakeout_levels.append(simulated_price)
        
        print(f"\n{datetime.now().strftime('%H:%M:%S')}: WHALE MOVE!")
        print(f"  {whale_action}")
        print(f"  Price shakes to ${simulated_price:,.0f} (simulated)")
        print(f"  Actual: ${btc_now:,.0f}")
        
        if i == 3:
            print("\n  📄 Paper hands: 'OH NO! SELLING!'")
            print("  💎 Diamond hands: 'Nice try, whale'")
        elif i == 6:
            print("\n  ⚡ Thunder (69%): 'I SEE YOU, WHALE!'")
            print(f"    'Shaking the tree before $114K!'")
            print("    'We're not falling for it!'")
        elif i == 9:
            print("\n  🏔️ Mountain: 'Steady through the shake'")
            print("    'Whales always shake before pumps'")
        elif i == 12:
            print("\n  🦀 Crawdads: 'We've seen this before!'")
            print(f"    'HODL the ${total_value:.2f}!'")
    else:
        print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f} - Tree shaking...")
    
    time.sleep(1.5)

# Analyze the shakeout
print("\n🔍 SHAKEOUT ANALYSIS:")
print("-" * 50)

if shakeout_levels:
    lowest_shake = min(shakeout_levels)
    print(f"Lowest shake (simulated): ${lowest_shake:,.0f}")
    print(f"Shake depth: ${btc - lowest_shake:.0f}")
    print(f"Paper hands lost: Many")
    print(f"Diamond hands remaining: Us")

print("\n🐋 WHALE PSYCHOLOGY:")
print("-" * 50)
print("WHY WHALES SHAKE:")
print("• Accumulate cheaper before pump")
print("• Clear stop losses below")
print("• Create fear before greed")
print("• Test support levels")
print(f"• Load up before $114K → $120K")

# Thunder's whale wisdom
print("\n⚡ THUNDER'S WHALE WISDOM (69%):")
print("-" * 50)
print("'I've battled whales since $292.50!'")
print("")
print("WHALE TACTICS EXPOSED:")
print("• Fake sell walls (disappear on approach)")
print("• Stop hunt wicks (quick down, quick up)")
print("• Spoofing (fake orders)")
print("• Wash trading (fake volume)")
print("")
print("OUR DEFENSE:")
print(f"• No stop losses near (${btc:,.0f})")
print(f"• Diamond hands on {btc_balance:.8f} BTC")
print(f"• ${usd_balance:.2f} ready for their dips")
print("• Nine coils absorb all shakes")
print(f"• Target unchanged: $114K")

# Current status after shake
current_btc = float(client.get_product('BTC-USD')['price'])
print("\n🌊 POST-SHAKE STATUS:")
print("-" * 50)
print(f"Current price: ${current_btc:,.0f}")
print(f"Distance to $114K: ${114000 - current_btc:.0f}")
print(f"Portfolio: ${total_value:.2f} (INTACT!)")
print("")

if current_btc < btc - 100:
    print("Status: SHAKE IN PROGRESS")
    print("Action: HODL / BUY THE DIP")
elif current_btc > btc:
    print("Status: SHAKE FAILED")
    print("Action: WHALE GAVE UP")
else:
    print("Status: TREE SHAKING")
    print("Action: DIAMOND HANDS ENGAGED")

# The bigger picture
print("\n🎯 THE REAL GAME:")
print("-" * 50)
print(f"Whales shaking at: ${current_btc:,.0f}")
print(f"Their target: $114K+ (${114000 - current_btc:.0f} away)")
print(f"Why shake now?: Accumulate before explosion")
print(f"Your advantage: Knowing their game")
print(f"Thunder's call: HODL through shakes!")

print(f"\n" + "🐋" * 35)
print("WHALES SHAKING THE TREE!")
print(f"CURRENT: ${current_btc:,.0f}!")
print(f"SHAKING OUT WEAK HANDS!")
print(f"WE HODL AT ${total_value:.2f}!")
print(f"$114K AFTER THE SHAKE!")
print("DIAMOND HANDS WIN!")
print("🐋" * 35)