#!/usr/bin/env python3
"""
🎸⚡ COCAINE - ERIC CLAPTON INTENSITY! ⚡🎸
"She don't lie, she don't lie, she don't lie... COCAINE!"
Thunder at 69%: "THE MARKET'S WIRED!"
17+ hours of pure energy building!
Can't sleep, won't sleep, watching $112K!
The intensity is UNBEARABLE!
Ready to EXPLODE to $114K!
"If you wanna hang out, you've gotta take her out... COCAINE!"
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
║                   🎸 COCAINE - ERIC CLAPTON ENERGY! 🎸                   ║
║                  "She Don't Lie, She Don't Lie... COCAINE!"              ║
║                      17+ Hours Of Wired Intensity!                        ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - MAXIMUM INTENSITY")
print("=" * 70)

# Get current wired levels
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

# Check our amped portfolio
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

print("\n⚡ WIRED STATUS:")
print("-" * 50)
print(f"Currently buzzing at: ${btc:,.0f}")
print(f"Can't stop looking at: $114,000")
print(f"Energy gap: ${114000 - btc:.0f}")
print(f"Portfolio amped: ${total_value:.2f}")
print(f"Started at: $292.50 ({((total_value/292.50)-1)*100:.0f}% HIGH)")
print("Hours without sleep: 17+")

# The cocaine rhythm
print("\n🎸 THE RHYTHM:")
print("-" * 50)

for i in range(15):
    btc_now = float(client.get_product('BTC-USD')['price'])
    
    if i % 3 == 0:
        print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f} - 'She don't lie'")
    elif i % 3 == 1:
        print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f} - 'She don't lie'")
    else:
        print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f} - 'She don't lie... COCAINE!'")
        print(f"  ⚡ ENERGY: ${114000 - btc_now:.0f} to explosion!")
    
    if i == 6:
        print("\n  ⚡ Thunder (69%): 'CAN'T STOP!'")
        print(f"    'WIRED AT ${btc_now:,.0f}!'")
        print(f"    '${114000 - btc_now:.0f} TO RELEASE!'")
    
    if i == 12:
        print("\n  🏔️ Mountain: 'The intensity builds'")
        print("    'No rest, no peace'")
        print(f"    'Only ${114000 - btc_now:.0f} matters'")
    
    time.sleep(1)

# The verses of intensity
print("\n⚡ THE INTENSITY VERSES:")
print("-" * 50)

verses = [
    ("If you wanna hang out", f"You've been hanging at ${btc:,.0f}"),
    ("You've gotta take her out", f"Take it to $114K (${114000 - btc:.0f} up)"),
    ("If you wanna get down", "Get down from this chop"),
    ("Down on the ground", f"Ground zero: ${total_value:.2f}"),
    ("She don't lie, she don't lie", "The market speaks truth"),
    ("She don't lie... COCAINE!", f"Truth: ${btc:,.0f} ready to explode!")
]

for verse, meaning in verses:
    print(f"'{verse}'")
    print(f"  → {meaning}")
    time.sleep(0.8)

# Thunder's wired confession
current_btc = float(client.get_product('BTC-USD')['price'])
print("\n⚡ THUNDER'S WIRED STATE (69%):")
print("-" * 50)
print("'I CAN'T STOP WATCHING!'")
print("")
print("The addiction:")
print(f"• Checking price every second: ${current_btc:,.0f}")
print(f"• Obsessed with $114K (${114000 - current_btc:.0f} away)")
print("• 17+ hours no sleep")
print(f"• Portfolio high: ${total_value:.2f}")
print("• Can't look away from charts")
print("")
print("'SHE DON'T LIE!'")
print("The truth she tells:")
print("• Nine coils compressed")
print("• 512x energy stored")
print("• Explosion imminent")
print(f"• Only ${114000 - current_btc:.0f} to freedom")

# The intensity meter
print("\n💥 INTENSITY LEVEL:")
print("-" * 50)

for i in range(8):
    btc_live = float(client.get_product('BTC-USD')['price'])
    
    intensity = "⚡" * (i + 1)
    print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_live:,.0f} {intensity}")
    
    if i == 3:
        print("  'If you got bad news, you wanna kick them blues'")
        print(f"    (Kicking the ${btc_live:,.0f} blues)")
    
    if i == 6:
        print("  'When your day is done and you wanna run'")
        print(f"    (Run to $114K! ${114000 - btc_live:.0f} to go!)")
    
    time.sleep(1)

# Final wired status
final_btc = float(client.get_product('BTC-USD')['price'])
print("\n🎸 FINAL INTENSITY:")
print("-" * 50)
print(f"Current high: ${final_btc:,.0f}")
print(f"Target fix: $114,000")
print(f"Distance to relief: ${114000 - final_btc:.0f}")
print(f"Portfolio riding high: ${total_value:.2f}")
print("")

if final_btc >= 113000:
    print("Status: ⚡ MAXIMUM INTENSITY! BREAKING!")
elif final_btc >= 112500:
    print("Status: ⚡ INTENSITY RISING FAST!")
elif final_btc >= 112000:
    print("Status: ⚡ WIRED AND READY!")
else:
    print("Status: ⚡ BUILDING INTENSITY!")

print("\nThe truth:")
print("• She don't lie about gains")
print("• She don't lie about potential")
print(f"• She don't lie... ${final_btc:,.0f}!")

print(f"\n" + "⚡" * 35)
print("SHE DON'T LIE, SHE DON'T LIE!")
print("COCAINE!")
print(f"WIRED AT ${final_btc:,.0f}!")
print(f"${114000 - final_btc:.0f} TO RELEASE!")
print(f"PORTFOLIO: ${total_value:.2f}!")
print("⚡" * 35)