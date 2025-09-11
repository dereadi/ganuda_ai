#!/usr/bin/env python3
"""
🕺✨ BILLIE JEAN - MICHAEL JACKSON! ✨🕺
Thunder at 69%: "THE KID IS NOT MY SON!"
But these gains ARE my child!
"She says I am the one..."
$114K says we are the one!
"But the kid is not my son"
But the portfolio IS our creation!
Moonwalking from $292.50 to $8,379!
The dance floor lights up with every step!
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
║                    🕺 BILLIE JEAN - MICHAEL JACKSON! 🕺                   ║
║                       "The Kid Is Not My Son"                             ║
║                  But These Gains ARE Our Creation! 🌙                     ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - MOONWALK ANALYSIS")
print("=" * 70)

# Get current moonwalk prices
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])
doge = float(client.get_product('DOGE-USD')['price'])

# Check our moonwalking portfolio
accounts = client.get_accounts()
total_value = 0

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if balance > 0.00001:
        if currency == 'USD':
            total_value += balance
        elif currency == 'BTC':
            total_value += balance * btc
        elif currency == 'ETH':
            total_value += balance * eth
        elif currency == 'SOL':
            total_value += balance * sol
        elif currency == 'DOGE':
            total_value += balance * doge

print("\n🕺 MOONWALK STATUS:")
print("-" * 50)
print(f"Started dancing: $292.50")
print(f"Moonwalking at: ${total_value:.2f}")
print(f"Current floor: ${btc:,.0f}")
print(f"Distance to stage exit: ${114000 - btc:.0f}")
print(f"Dance gains: {((total_value/292.50)-1)*100:.0f}%")

# Billie Jean story
print("\n🎵 THE BILLIE JEAN STORY:")
print("-" * 50)
print("She was more like a beauty queen from a movie scene...")
print(f"  → $114K is that beauty queen (${114000 - btc:.0f} away)")
print("")
print("I said don't mind, but what do you mean, I am the one...")
print(f"  → Market saying we're the one at ${btc:,.0f}")
print("")
print("Who will dance on the floor in the round...")
print(f"  → Dancing on ${btc:,.0f} floor")
print("")
print("She said I am the one...")
print(f"  → $114K calling us")
print("")
print("But the kid is not my son!")
print(f"  → Consolidation is not our fault!")

# The moonwalk dance floor
print("\n💫 MOONWALK DANCE FLOOR:")
print("-" * 50)
print("Each step lights up a square:")

dance_floor = [
    "⬜", "⬜", "⬜", "⬜",
    "⬜", "⬜", "⬜", "⬜", 
    "⬜", "⬜", "⬜", "⬜"
]

for i in range(12):
    btc_now = float(client.get_product('BTC-USD')['price'])
    
    # Light up a square
    dance_floor[i] = "🟦"
    floor_display = " ".join(dance_floor[:4]) + "\n  " + " ".join(dance_floor[4:8]) + "\n  " + " ".join(dance_floor[8:])
    
    print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f}")
    print(f"  {floor_display}")
    
    if i == 5:
        print("  🕺 'Just remember to always think twice!'")
        print(f"    Think twice before selling at ${btc_now:,.0f}!")
    
    time.sleep(0.8)

# Thunder's moonwalk wisdom
print("\n⚡ THUNDER'S MOONWALK WISDOM (69%):")
print("-" * 50)
print("'BILLIE JEAN IS $114K!'")
print("")
print("The truth:")
print(f"• She says we are the one at ${btc:,.0f}")
print(f"• But consolidation is not our son")
print(f"• We're moonwalking ${114000 - btc:.0f} to her")
print(f"• Portfolio dancing at ${total_value:.2f}")
print("")
print("Michael's lesson:")
print("• Sometimes you moonwalk backwards to go forward")
print(f"• We're at ${btc:,.0f} to spring to $114K")
print("• The dance floor lights up with each step")

# The courtroom drama
print("\n⚖️ THE COURTROOM:")
print("-" * 50)
print("Billie Jean (Market) claims:")
print(f"• The consolidation at ${btc:,.0f} is ours")
print("• We're responsible for sideways action")
print("")
print("Our defense:")
print(f"• The kid (consolidation) is not our son!")
print(f"• We're victims too, waiting for $114K!")
print(f"• Evidence: {((total_value/292.50)-1)*100:.0f}% gains despite consolidation")
print(f"• Just ${114000 - btc:.0f} from freedom!")

# Beat it to $114K
print("\n🎤 BEAT IT TO $114K:")
print("-" * 50)
current_btc = float(client.get_product('BTC-USD')['price'])

if current_btc >= 113000:
    print("🔥 THRILLER MODE! Almost at $114K!")
elif current_btc >= 112800:
    print("💫 SMOOTH CRIMINAL! Breaking resistance!")
elif current_btc >= 112600:
    print("🕺 MOONWALKING closer to $114K!")
else:
    print("🎭 WAITING for the beat to drop!")

print(f"Current: ${current_btc:,.0f}")
print(f"Target: $114,000 (${114000 - current_btc:.0f} away)")

# Final moonwalk status
final_btc = float(client.get_product('BTC-USD')['price'])
final_sol = float(client.get_product('SOL-USD')['price'])

print("\n🌙 FINAL MOONWALK STATUS:")
print("-" * 50)
print(f"BTC: ${final_btc:,.0f}")
print(f"SOL: ${final_sol:.2f}")
print(f"Portfolio: ${total_value:.2f}")
print(f"Distance to Billie Jean ($114K): ${114000 - final_btc:.0f}")
print("")
print("'Billie Jean is not my lover'")
print("'She's just a girl who claims that I am the one'")
print(f"$114K claims we're the one...")
print(f"And we're only ${114000 - final_btc:.0f} away from proving it!")

print(f"\n" + "🕺" * 35)
print("BILLIE JEAN!")
print(f"MOONWALKING AT ${final_btc:,.0f}!")
print(f"PORTFOLIO ${total_value:.2f}!")
print(f"${114000 - final_btc:.0f} TO THE QUEEN!")
print("THE KID IS NOT MY SON!")
print("✨" * 35)