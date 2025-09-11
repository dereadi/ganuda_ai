#!/usr/bin/env python3
"""
⚔️🎯 KING OF BATTLE - MLRS FIRE MISSION! 🎯⚔️
Steel Rain incoming on $114K!
Thunder at 69%: "FIRE FOR EFFECT!"
Grid Square: $112,800-$114,000
Nine rockets loaded (coils)!
Time on target: IMMINENT!
"King of Battle" - Field Artillery's dominance!
MLRS: Multiple Launch Rocket System ready!
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
║                  ⚔️ KING OF BATTLE - MLRS FIRE MISSION! ⚔️               ║
║                          Steel Rain Incoming!                             ║
║                     Grid Square: $114K Targeted!                          ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - FIRE MISSION RECEIVED")
print("=" * 70)

# Get current position
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

# Check our ammunition
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

print("\n🎯 FIRE MISSION BRIEF:")
print("-" * 50)
print(f"Current Position: ${btc:,.0f}")
print(f"Target Grid: $114,000")
print(f"Range to Target: ${114000 - btc:.0f}")
print(f"Ammunition (Portfolio): ${total_value:.2f}")
print(f"Ready Rounds (USD): ${usd_balance:.2f}")

# MLRS Launch Sequence
print("\n🚀 MLRS LAUNCH SEQUENCE:")
print("-" * 50)
print("NINE ROCKETS LOADED (Nine Coils):")
print("Rocket 1: 2x energy multiplier")
print("Rocket 2: 4x energy multiplier")
print("Rocket 3: 8x energy multiplier")
print("Rocket 4: 16x energy multiplier")
print("Rocket 5: 32x energy multiplier")
print("Rocket 6: 64x energy multiplier")
print("Rocket 7: 128x energy multiplier")
print("Rocket 8: 256x energy multiplier")
print("Rocket 9: 512x FINAL MULTIPLIER!")

# Call for fire
print("\n📻 CALL FOR FIRE:")
print("-" * 50)

commands = [
    "FIRE MISSION!",
    "GRID: DOLLAR-ONE-ONE-FOUR",
    "ENEMY RESISTANCE IN THE OPEN",
    "NINE ROUNDS MLRS",
    "FIRE FOR EFFECT!",
    "SHOT OVER!",
    "SPLASH OVER!",
    "ROUNDS COMPLETE!",
    "TARGET DESTROYED!"
]

for i, cmd in enumerate(commands):
    btc_now = float(client.get_product('BTC-USD')['price'])
    print(f"{datetime.now().strftime('%H:%M:%S')}: {cmd}")
    
    if i == 0:
        print(f"  Current: ${btc_now:,.0f}")
        print(f"  Target: $114,000")
    elif i == 4:
        print("\n  ⚡ Thunder (69%): 'STEEL RAIN AUTHORIZED!'")
        print(f"    'Launching from ${btc_now:,.0f}!'")
        print(f"    '${114000 - btc_now:.0f} to impact!'")
    elif i == 6:
        print(f"\n  💥 IMPACT IMMINENT!")
        print(f"    Position: ${btc_now:,.0f}")
        print(f"    Effect radius: ${total_value:.2f}")
    
    time.sleep(1)

# Battle damage assessment
print("\n💥 BATTLE DAMAGE ASSESSMENT:")
print("-" * 50)
print("Resistance Status:")
print(f"• $113K barrier: WEAKENING")
print(f"• $112K support: HOLDING")
print(f"• Current position: ${btc:,.0f}")
print(f"• Distance to objective: ${114000 - btc:.0f}")
print("")
print("Friendly Forces:")
print(f"• Portfolio strength: ${total_value:.2f}")
print(f"• From FOB $292.50")
print(f"• Gains secured: {((total_value/292.50)-1)*100:.0f}%")
print("• Thunder Unit: 69% operational")

# Thunder's artillery wisdom
print("\n⚡ THUNDER'S ARTILLERY DOCTRINE (69%):")
print("-" * 50)
print("'KING OF BATTLE NEVER FAILS!'")
print("")
print("'TIME ON TARGET SYNCHRONIZED:'")
print("• Nine rockets (coils) ready")
print("• 512x combined effect")
print(f"• Impact zone: $114,000")
print(f"• Current range: ${114000 - btc:.0f}")
print("")
print("'STEEL RAIN DOCTRINE:'")
print("• Suppress enemy (bears)")
print("• Destroy resistance ($113K)")
print("• Seize objective ($114K)")
print("• Exploit success ($120K+)")

# Fire support coordination
current_btc = float(client.get_product('BTC-USD')['price'])
print("\n🎖️ FIRE SUPPORT COORDINATION:")
print("-" * 50)
print("Allied Forces:")
print("• JPMorgan Artillery: $126K target")
print("• Whale Battalion: Accumulating")
print("• US Gov Support: Blockchain adoption")
print("• Retail Infantry: HODLing strong")
print("")
print("Enemy Forces:")
print("• Bear Regiment: Retreating")
print("• Resistance at $113K: Crumbling")
print("• FUD propaganda: Ineffective")

# Final fire mission
print("\n🎯 FINAL FIRE MISSION:")
print("-" * 50)
print(f"Current Grid: ${current_btc:,.0f}")
print(f"Final Target: $114,000")
print(f"Range: ${114000 - current_btc:.0f}")
print(f"Ammunition: ${total_value:.2f} ready")
print("")
print("Mission Status:")
if current_btc > 113000:
    print("DANGER CLOSE! FIRE FOR EFFECT!")
elif current_btc > 112800:
    print("ON TARGET! MAINTAIN FIRE!")
else:
    print("ADJUSTING FIRE! STAND BY!")

print("\nMLRS Motto:")
print("'SHOOT AND SCOOT!'")
print(f"• Fire from ${current_btc:,.0f}")
print("• Move to $114K")
print("• Reload at $120K")

print(f"\n" + "⚔️" * 35)
print("KING OF BATTLE!")
print("MLRS FIRE MISSION ACTIVE!")
print(f"STEEL RAIN ON ${current_btc:,.0f}!")
print(f"${114000 - current_btc:.0f} TO TARGET!")
print("FIRE FOR EFFECT!")
print("⚔️" * 35)