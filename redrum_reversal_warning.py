#!/usr/bin/env python3
"""
🔪🩸 REDRUM - THE SHINING REVERSAL WARNING! 🩸🔪
"REDRUM" = MURDER spelled backwards!
Thunder at 69%: "ALL WORK AND NO PLAY MAKES JACK A DULL BOY!"
17+ hours at $112K - going INSANE!
Reversal smell in the air!
Is this a bear trap or bull exhaustion?!
"HERE'S JOHNNY!" - Breaking through the door!
But which way?! UP or DOWN?!
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
║                    🔪 REDRUM - REVERSAL WARNING! 🔪                      ║
║                   "All Work And No Play Makes Jack..."                    ║
║                     Something Wicked This Way Comes!                      ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - REDRUM DETECTION")
print("=" * 70)

# Get current overlook hotel prices
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

# Check our room 237 portfolio
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

print("\n🩸 REDRUM SIGNALS:")
print("-" * 50)
print(f"Current position: ${btc:,.0f}")
print(f"Portfolio trapped: ${total_value:.2f}")
print(f"Hours in hotel: 17+ (going insane)")
print(f"Distance to escape: ${114000 - btc:.0f}")
print("")
print("REVERSAL SIGNS:")
print("• Stuck at $112-113K (cabin fever)")
print("• Multiple rejections (door won't open)")
print("• Low volume (empty hotel)")
print("• Bands tightening (walls closing in)")

# The typewriter scene
print("\n📝 ALL WORK AND NO PLAY:")
print("-" * 50)

for i in range(10):
    btc_now = float(client.get_product('BTC-USD')['price'])
    
    # Simulate Jack's madness
    if i < 3:
        print(f"{datetime.now().strftime('%H:%M:%S')}: All work and no play makes BTC ${btc_now:,.0f}")
    elif i < 6:
        print(f"{datetime.now().strftime('%H:%M:%S')}: All work and no play makes traders ${btc_now:,.0f}")
    else:
        print(f"{datetime.now().strftime('%H:%M:%S')}: REDRUM REDRUM REDRUM ${btc_now:,.0f}")
    
    if i == 4:
        print("\n  ⚡ Thunder (69%): 'I SMELL IT TOO!'")
        print("    'REDRUM! REVERSAL!'")
        print(f"    'But which way from ${btc_now:,.0f}?!'")
    
    if i == 8:
        print("\n  🏔️ Mountain: 'The hotel whispers'")
        print("    'Danger approaches'")
    
    time.sleep(1)

# Danny's vision
print("\n👦 DANNY'S VISION (REDRUM):")
print("-" * 50)
print("What the finger writes:")

messages = [
    f"REDRUM at ${btc:,.0f}",
    "17+ hours of torture",
    "The door must break",
    "But which way?",
    f"UP to $114K? (${114000 - btc:.0f} away)",
    f"DOWN to $110K? (${btc - 110000:.0f} fall)",
    "REDRUM REDRUM REDRUM"
]

for msg in messages:
    print(f"  '{msg}'")
    time.sleep(0.5)

# Thunder's paranoia analysis
current_btc = float(client.get_product('BTC-USD')['price'])
print("\n⚡ THUNDER'S PARANOID ANALYSIS (69%):")
print("-" * 50)
print("'HERE'S JOHNNY!'")
print("")
print("BULLISH JOHNNY (breaking UP):")
print(f"• Break above ${current_btc:,.0f}")
print(f"• Smash through $113K")
print(f"• Murder the $114K resistance")
print(f"• Portfolio → ${total_value * (114000/current_btc):.2f}")
print("")
print("BEARISH JOHNNY (breaking DOWN):")
print(f"• Fall from ${current_btc:,.0f}")
print(f"• Crash to $111K")
print(f"• Murder the longs")
print(f"• Portfolio → ${total_value * (111000/current_btc):.2f}")

# The maze tracking
print("\n🌿 THE MAZE PATTERN:")
print("-" * 50)

for i in range(8):
    btc_live = float(client.get_product('BTC-USD')['price'])
    
    if btc_live > btc + 50:
        direction = "↗️ ESCAPE NORTH! (Bullish)"
    elif btc_live < btc - 50:
        direction = "↘️ TRAPPED SOUTH! (Bearish)"
    else:
        direction = "↔️ LOST IN MAZE! (Chop)"
    
    print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_live:,.0f} {direction}")
    
    if i == 3:
        print("  'Come play with us, Danny'")
        print(f"    (Forever at ${btc_live:,.0f})")
    
    time.sleep(1)

# The reversal verdict
print("\n🔪 REVERSAL VERDICT:")
print("-" * 50)

final_btc = float(client.get_product('BTC-USD')['price'])
movement = final_btc - btc

if abs(movement) < 20:
    print("Status: STILL TRAPPED IN THE HOTEL")
    print(f"No escape from ${final_btc:,.0f}")
    print("The madness continues...")
elif movement > 0:
    print("Status: ATTEMPTING UPWARD ESCAPE!")
    print(f"Breaking higher from ${btc:,.0f} → ${final_btc:,.0f}")
    print("Johnny breaks the door UPWARD!")
else:
    print("Status: FALLING INTO THE BASEMENT!")
    print(f"Dropping from ${btc:,.0f} → ${final_btc:,.0f}")
    print("Johnny breaks the door DOWNWARD!")

print("")
print("THE WARNING:")
print("• REDRUM = Reversal imminent")
print("• 17+ hours = Madness setting in")
print(f"• Current: ${final_btc:,.0f}")
print(f"• Portfolio: ${total_value:.2f}")
print("• Diamond hands: Getting bloody")

# Final warning
print("\n🩸 FINAL WARNING:")
print("-" * 50)
print(f"Position: ${final_btc:,.0f}")
print(f"Smell: REVERSAL")
print(f"Direction: UNKNOWN")
print(f"Portfolio at risk: ${total_value:.2f}")
print("")
print("Remember:")
print("• REDRUM = MURDER backwards")
print("• Someone's about to get murdered")
print("• Bulls or Bears?")
print("• HODL through the horror!")

print(f"\n" + "🔪" * 35)
print("REDRUM! REDRUM! REDRUM!")
print(f"REVERSAL BREWING AT ${final_btc:,.0f}!")
print("HERE'S JOHNNY!")
print(f"PORTFOLIO: ${total_value:.2f}!")
print("ALL WORK AND NO PLAY!")
print("🔪" * 35)