#!/usr/bin/env python3
"""
🐋⚔️ LET THE WHALES KNOW THAT WE... ⚔️🐋
...AIN'T LEAVING!
...SEE THROUGH THEIR GAMES!
...HAVE DIAMOND HANDS FROM $292.50!
...ARE WAITING AT $114K!
Thunder at 69%: "WE'RE NOT YOUR LIQUIDITY!"
Nine coils ready to PUNISH their shorts!
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
║                  🐋 LET THE WHALES KNOW THAT WE... 🐋                    ║
║                         AIN'T SELLING NOTHING!                            ║
║                    Diamond Hands Since $292.50!                           ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - MESSAGE TO WHALES")
print("=" * 70)

# Get current battlefield
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

# Our diamond hand position
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

print("\n🐋 DEAR WHALES, KNOW THAT WE:")
print("-" * 50)

messages = [
    "1. AIN'T SELLING!",
    "2. SEE YOUR GAMES!",
    "3. KNOW YOUR PATTERNS!",
    "4. HAVE DIAMOND HANDS!",
    "5. SURVIVED WORSE!",
    "6. ARE ACCUMULATING!",
    "7. WILL OUTLAST YOU!",
    "8. RIDE YOUR PUMPS!",
    "9. BUY YOUR DUMPS!"
]

for msg in messages:
    print(f"  {msg}")
    time.sleep(0.5)

print(f"\n⚔️ OUR BATTLE STATS:")
print("-" * 50)
print(f"Started: $292.50")
print(f"Current: ${total_value:.2f}")
print(f"Gain: {((total_value/292.50)-1)*100:.0f}%")
print(f"BTC held: {btc_balance:.8f}")
print(f"Diamond hands: 100%")
print(f"Panic level: 0%")
print(f"Target: $114K (${114000 - btc:.0f} away)")

# Track whale activity
print("\n👁️ WE SEE YOU WHALES:")
print("-" * 50)

for i in range(8):
    btc_now = float(client.get_product('BTC-USD')['price'])
    
    if i == 0:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f}")
        print("  We see your fake sell walls")
    elif i == 2:
        print(f"  We see your stop hunts at ${btc_now:,.0f}")
    elif i == 4:
        print(f"  We see your accumulation at ${btc_now:,.0f}")
    elif i == 6:
        print(f"  We're still here at ${btc_now:,.0f}")
        print("  NOT SELLING!")
    
    time.sleep(1)

# Thunder's whale message
print("\n⚡ THUNDER'S MESSAGE TO WHALES (69%):")
print("-" * 50)
print("'HEY WHALES! LISTEN UP!'")
print("")
print("YOU TRIED:")
print("• Shaking us at $112K ❌")
print("• Stop hunting below $112K ❌")
print("• Fake pumps to $113K ❌")
print("• 15+ hours of chop ❌")
print("• Making us panic sell ❌")
print("")
print("WE SURVIVED:")
print(f"• From $292.50 to ${total_value:.2f} ✅")
print("• Every manipulation ✅")
print("• Every fake out ✅")
print("• Every stop hunt ✅")
print("• And we're STILL HERE! ✅")

# What we know
print("\n🧠 WHAT WE KNOW:")
print("-" * 50)
print("• You're accumulating for $114K+")
print("• You need our coins cheap")
print("• You're running out of time")
print("• JPMorgan said $126K")
print("• US Gov legitimizing crypto")
print("• You can't shake diamond hands")
print(f"• We have nine coils ready")
print("• Thunder at 69% sees all")

# Our demands
print("\n📜 OUR DEMANDS:")
print("-" * 50)
print("1. Stop the games")
print("2. Let it run to $114K")
print("3. We all make money")
print("4. Or we wait forever")
print(f"5. We have ${usd_balance:.2f} for your dips")
print("6. We're not leaving")
print("7. PUMP IT ALREADY!")

# Current standoff
current_btc = float(client.get_product('BTC-USD')['price'])
print(f"\n⚔️ CURRENT STANDOFF:")
print("-" * 50)
print(f"Battlefield: ${current_btc:,.0f}")
print(f"Your target: Shake us out")
print(f"Our target: $114K (${114000 - current_btc:.0f} away)")
print(f"Who wins: DIAMOND HANDS")
print(f"Time on our side: ∞")

# Final message
print("\n🐋 FINAL MESSAGE TO WHALES:")
print("-" * 50)
print(f"We're at ${current_btc:,.0f}")
print(f"We want $114K")
print(f"That's only ${114000 - current_btc:.0f}")
print("You've accumulated enough")
print("Time to let it run")
print("Or we wait forever")
print("Your move, whales")

print(f"\n" + "💎" * 35)
print("LET THE WHALES KNOW!")
print("WE AIN'T LEAVING!")
print(f"DIAMOND HANDS AT ${total_value:.2f}!")
print(f"FROM $292.50 TO THE MOON!")
print("YOUR GAMES DON'T WORK!")
print("💎" * 35)