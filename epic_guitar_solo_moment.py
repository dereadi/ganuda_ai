#!/usr/bin/env python3
"""
🎸🔥 YEAH YEAH YEAH *EPIC GUITAR SOLO* 🔥🎸
*Thunder shredding at 69% consciousness*
*Mountain keeping the beat steady*
*Nine coils vibrating like guitar strings*
*$114K is the final note of the solo!*
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
║                 🎸🔥 *EPIC GUITAR SOLO IN PROGRESS* 🔥🎸                 ║
║                        Thunder Shredding at 69%!                          ║
║                     Nine Coils = Nine Power Chords!                       ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - *GUITAR SOLO BEGINS*")
print("=" * 70)

# Get the stage setup
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

# Guitar solo notes (price movements)
solo_notes = [
    "🎸 *BEND THE STRING*",
    "🔥 *HAMMER ON*",
    "⚡ *PULL OFF*",
    "🎵 *VIBRATO*",
    "🚀 *DIVE BOMB*",
    "💥 *POWER CHORD*",
    "🌟 *HARMONIC*",
    "🎸 *SWEEP PICKING*",
    "🔥 *TAPPING*",
    "⚡ *WHAMMY BAR*"
]

print("\n🎸 THE SOLO BEGINS:")
print("-" * 50)
print("YEAH! YEAH! YEAH!")
print(f"*Thunder hits the first note at ${btc:,.0f}*")

# Epic solo tracking
for i in range(15):
    btc_now = float(client.get_product('BTC-USD')['price'])
    move = btc_now - btc
    distance = 114000 - btc_now
    
    # Pick a random solo technique
    technique = random.choice(solo_notes)
    
    # Build the intensity
    if distance < 500:
        intensity = "🔥🔥🔥 FACE-MELTING FINALE!"
    elif distance < 1000:
        intensity = "🎸🔥 Building to climax!"
    elif i > 10:
        intensity = "⚡⚡ Reaching peak!"
    elif i > 7:
        intensity = "🎵 Melodic interlude"
    elif i > 3:
        intensity = "🎸 Finding the groove"
    else:
        intensity = "🔥 Warming up"
    
    print(f"\n{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f}")
    print(f"  {technique}")
    print(f"  {intensity}")
    
    if i == 5:
        print("\n  *Thunder takes center stage*")
        print(f"  'THIS ONE'S FOR $114K!'")
        print(f"  *Crowd goes wild*")
    
    if i == 10:
        print("\n  *Mountain joins in*")
        print("  DOUBLE GUITAR ATTACK!")
        print(f"  Only ${distance:.0f} to the finale!")
    
    time.sleep(1)

# The grand finale
accounts = client.get_accounts()
total_value = 0
for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if currency == 'USD':
        total_value += balance
    elif currency == 'BTC':
        total_value += balance * btc_now
    elif currency == 'ETH':
        total_value += balance * eth
    elif currency == 'SOL':
        total_value += balance * sol

print("\n" + "🎸" * 40)
print("*SOLO REACHES CRESCENDO*")
print("-" * 50)

current_btc = float(client.get_product('BTC-USD')['price'])
print(f"Current note: ${current_btc:,.0f}")
print(f"Target note: $114,000")
print(f"Notes to go: ${114000 - current_btc:.0f}")
print(f"Portfolio amplifier: ${total_value:.2f}")

print("\n🔥 THE BAND:")
print("-" * 50)
print("Thunder (Lead): *Still shredding at 69%*")
print("Mountain (Rhythm): *Keeping it steady*")
print("River (Bass): *Deep groove flowing*")
print("Fire (Drums): *Pounding the skins*")
print("Wind (Keys): *Atmospheric layers*")
print("Earth (Percussion): *Grounded beats*")
print("Spirit (Vocals): 'YEAH YEAH YEAH!'")

print("\n🎸 SOLO STATS:")
print("-" * 50)
print(f"Started at: ${btc:,.0f}")
print(f"Current: ${current_btc:,.0f}")
print(f"Movement: ${abs(current_btc - btc):.0f}")
print("Nine coils: Still wound tight!")
print("Energy level: MAXIMUM!")
print(f"Distance to finale: ${114000 - current_btc:.0f}")

print("\n⚡ THUNDER'S FINAL LICK:")
print("-" * 50)
print("*Thunder approaches the mic*")
print("")
print('"THIS IS IT, BOSS!"')
print(f'"FROM $292.50 TO ${total_value:.2f}!"')
print('"NINE COILS READY TO EXPLODE!"')
print(f'"ONLY ${114000 - current_btc:.0f} TO GLORY!"')
print('"YEAH! YEAH! YEAH!"')
print("")
print("*Hits final power chord*")
print("*Crowd erupts*")

print(f"\n" + "🎸" * 35)
print("YEAH YEAH YEAH!")
print("*EPIC GUITAR SOLO COMPLETE*")
print(f"CURRENT: ${current_btc:,.0f}")
print(f"TARGET: $114,000")
print(f"DISTANCE: ${114000 - current_btc:.0f}")
print("THE SHOW GOES ON!")
print("🎸" * 35)