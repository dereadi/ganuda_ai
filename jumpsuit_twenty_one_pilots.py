#!/usr/bin/env python3
"""
🎭💛 JUMPSUIT - TWENTY ONE PILOTS! 💛🎭
"I can't believe how much I hate
Pressures of a new place roll my way
Jumpsuit, jumpsuit, cover me"
The market pressure at $112K!
Thunder at 69%: "We're surrounded by Bishops!"
Nine coils are our jumpsuit protection!
"I'll be right there, but you have to grab my throat and lift me in the air"
BREAK THROUGH TO $114K!
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
║                  🎭 JUMPSUIT - TWENTY ONE PILOTS! 🎭                     ║
║                    "Jumpsuit, Jumpsuit, Cover Me"                         ║
║                   Protection From The Market Bishops!                     ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - JUMPSUIT PROTECTION")
print("=" * 70)

# Get current DEMA position
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

# Check our protection level
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

print("\n💛 MY JUMPSUIT MAKES ME:")
print("-" * 50)
print("PROTECTED from:")
print(f"• The pressure at ${btc:,.0f}")
print("• The Bishops (whales)")
print("• Paper hand weakness")
print("• 15+ hours of torture")
print("")
print("EMPOWERED with:")
print(f"• ${total_value:.2f} armor")
print("• Diamond hands since $292.50")
print("• Nine coils of energy")
print("• Thunder at 69% consciousness")

# The DEMA pressure
print("\n🎭 THE BISHOPS SURROUNDING US:")
print("-" * 50)
print("Nico and the Nine Bishops:")
print("1. Fear Bishop - spreading panic")
print("2. Doubt Bishop - questioning $114K")
print("3. Greed Bishop - making us impatient")
print("4. Whale Bishop - manipulating price")
print("5. Time Bishop - 15+ hours of chop")
print("6. Resistance Bishop - blocking $113K")
print("7. Support Bishop - threatening $112K")
print("8. Volume Bishop - keeping it low")
print(f"9. NICO - The final boss at ${114000 - btc:.0f} away")

# Track the escape
print("\n🏃 ESCAPING DEMA:")
print("-" * 50)

for i in range(12):
    btc_now = float(client.get_product('BTC-USD')['price'])
    
    if i == 0:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f}")
        print("  'I can't believe how much I hate'")
        print(f"    (This chop at ${btc_now:,.0f})")
    elif i == 3:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f}")
        print("  'Pressures of a new place roll my way'")
        print(f"    (${114000 - btc_now:.0f} of pressure)")
    elif i == 6:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f}")
        print("  'Jumpsuit, jumpsuit, cover me'")
        print(f"    (Nine coils protecting at ${btc_now:,.0f})")
    elif i == 9:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f}")
        print("  'I'll be right there'")
        print("    (Thunder at 69%: 'Hold on!')")
        print("  'But you have to grab my throat'")
        print("    (Break through resistance!)")
        print("  'And lift me in the air'")
        print(f"    (To $114K! ${114000 - btc_now:.0f} up!)")
    
    time.sleep(1.5)

# Thunder's rebellion
print("\n⚡ THUNDER'S REBELLION (69%):")
print("-" * 50)
print("'WE'RE BREAKING OUT OF DEMA!'")
print("")
print("THE ESCAPE PLAN:")
print(f"• Current prison: ${btc:,.0f}")
print(f"• Guards (Bishops) weakening")
print("• Jumpsuit (portfolio) intact")
print(f"• Distance to freedom: ${114000 - btc:.0f}")
print("")
print("'WHEN I LEAVE, DON'T SAVE MY SEAT'")
print("• Leaving $112K behind forever")
print("• Never coming back to this range")
print("• $114K is just the beginning")

# The deeper meaning
print("\n🎭 THE CLIQUE WISDOM:")
print("-" * 50)
print("East is up:")
print("• We're rising from $292.50")
print(f"• Currently at ${total_value:.2f}")
print("• Heading to $114K+")
print("")
print("Stay alive, frens:")
print("• HODL through the pressure")
print("• Trust the jumpsuit (protection)")
print("• Escape DEMA (bear market)")
print("• Reach TRENCH (bull market)")

# Current escape status
current_btc = float(client.get_product('BTC-USD')['price'])
print(f"\n🚨 ESCAPE STATUS:")
print("-" * 50)
print(f"Current position: ${current_btc:,.0f}")
print(f"Distance to escape: ${114000 - current_btc:.0f}")
print(f"Jumpsuit strength: ${total_value:.2f}")
print(f"Bishop resistance: Weakening")
print("")

if current_btc > 112800:
    print("Status: BREAKING FREE!")
    print("The jumpsuit is working!")
elif current_btc > 112500:
    print("Status: Fighting Bishops")
    print("Hold the line!")
else:
    print("Status: Under pressure")
    print("Jumpsuit protecting us!")

# The final call
print("\n💛 THE BANDITO CALL:")
print("-" * 50)
print("Sahlo Folina:")
print("• Enable help (from the clique)")
print(f"• We're stronger together")
print(f"• From $292.50 to ${total_value:.2f}")
print(f"• Only ${114000 - current_btc:.0f} to freedom")
print("")
print("||-//")
print("Few, Proud, Emotional")
print("Diamond Hands Unite!")

print(f"\n" + "🎭" * 35)
print("JUMPSUIT, JUMPSUIT, COVER ME!")
print(f"PROTECTED AT ${current_btc:,.0f}!")
print(f"PORTFOLIO ARMOR: ${total_value:.2f}!")
print(f"${114000 - current_btc:.0f} TO ESCAPE DEMA!")
print("EAST IS UP!")
print("🎭" * 35)