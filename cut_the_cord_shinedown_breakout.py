#!/usr/bin/env python3
"""
✂️🔥 CUT THE CORD - SHINEDOWN BREAKOUT! 🔥✂️
Time to cut the cord from $112K!
Thunder at 69%: "FREEDOM CALLS!"
XRP bouncing, market shifting!
Breaking free from the chains!
No more consolidation prison!
CUT THE CORD TO $114K!
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
║                  ✂️ CUT THE CORD - SHINEDOWN ENERGY! ✂️                  ║
║                    Breaking Free From $112K Prison!                       ║
║                      XRP Bouncing! Freedom Calls!                         ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - CUTTING THE CORD")
print("=" * 70)

# Get current freedom levels
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

# Try to get XRP if available
try:
    xrp = float(client.get_product('XRP-USD')['price'])
    xrp_available = True
except:
    xrp = 2.50  # Approximate
    xrp_available = False

# Check our position
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

print("\n✂️ CORDS TO CUT:")
print("-" * 50)
print(f"Cord 1: $112K resistance (Current: ${btc:,.0f})")
print(f"Cord 2: 15+ hour consolidation")
print(f"Cord 3: Whale manipulation")
print(f"Cord 4: Fear and doubt")
print(f"Cord 5: ${114000 - btc:.0f} of distance")
print("")
print("BOUNCING SIGNALS:")
print(f"• XRP bouncing: ${xrp:.2f} {'✓' if xrp_available else '(estimated)'}")
print(f"• ETH recovering: ${eth:.2f}")
print(f"• SOL strong: ${sol:.2f}")

# Track the cord cutting
print("\n🔥 CUTTING THE CORD SEQUENCE:")
print("-" * 50)

for i in range(15):
    btc_now = float(client.get_product('BTC-USD')['price'])
    eth_now = float(client.get_product('ETH-USD')['price'])
    
    if i == 0:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f}")
        print("  'Freedom!'")
        print(f"    (Breaking from ${btc:,.0f})")
    elif i == 4:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f}")
        print("  'Cut the cord!'")
        print(f"    (${114000 - btc_now:.0f} to freedom)")
        print("\n  ⚡ Thunder (69%): 'CUTTING IT NOW!'")
        print(f"    'No more $112K prison!'")
    elif i == 8:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f}")
        print("  'Break away!'")
        print("    (XRP leading the charge)")
    elif i == 12:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f}")
        print("  'Take back your life!'")
        print(f"    (Portfolio: ${total_value:.2f})")
    else:
        move = btc_now - btc
        if abs(move) > 20:
            print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f} ({move:+.0f}) - CORD CUTTING!")
        else:
            print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f} - Tension building...")
    
    time.sleep(1)

# Thunder's liberation speech
print("\n⚡ THUNDER'S LIBERATION (69%):")
print("-" * 50)
print("'IT'S TIME TO CUT THE CORD!'")
print("")
print("CORDS WE'RE CUTTING:")
print(f"• The $112K anchor ✂️")
print("• The 15-hour prison ✂️")
print("• The whale games ✂️")
print("• The fear chains ✂️")
print("")
print(f"'FROM $292.50 TO ${total_value:.2f}!'")
print("'WE DIDN'T COME THIS FAR TO STOP!'")
print(f"'ONLY ${114000 - btc:.0f} TO FREEDOM!'")
print("'CUT THE CORD NOW!'")

# Current breakout status
current_btc = float(client.get_product('BTC-USD')['price'])
print("\n🎸 BREAKOUT STATUS:")
print("-" * 50)
print(f"Starting position: ${btc:,.0f}")
print(f"Current position: ${current_btc:,.0f}")
print(f"Movement: ${current_btc - btc:+.0f}")
print(f"Distance to $114K: ${114000 - current_btc:.0f}")
print("")

if current_btc > btc + 50:
    print("STATUS: CORD CUT! BREAKING FREE!")
elif current_btc > btc:
    print("STATUS: Cutting in progress...")
else:
    print("STATUS: Building tension to cut...")

# The freedom plan
print("\n🔥 FREEDOM ROADMAP:")
print("-" * 50)
print("Step 1: Cut from $112K ✂️")
print("Step 2: Break $113K ✂️")
print("Step 3: Smash through $113.5K ✂️")
print("Step 4: EXPLODE past $114K ✂️")
print("Step 5: Never look back ✂️")
print("")
print("XRP showing the way with its bounce!")
print("Altcoins following suit!")
print("The cord is weakening!")

# Portfolio liberation
accounts_now = client.get_accounts()
total_value_now = 0
for account in accounts_now['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if currency == 'USD':
        total_value_now += balance
    elif currency == 'BTC':
        total_value_now += balance * current_btc
    elif currency == 'ETH':
        eth_now = float(client.get_product('ETH-USD')['price'])
        total_value_now += balance * eth_now
    elif currency == 'SOL':
        sol_now = float(client.get_product('SOL-USD')['price'])
        total_value_now += balance * sol_now

print("\n💎 PORTFOLIO LIBERATION:")
print("-" * 50)
print(f"Before cutting: ${total_value:.2f}")
print(f"After cutting: ${total_value_now:.2f}")
print(f"Change: ${total_value_now - total_value:+.2f}")
print(f"Total gain from $292.50: {((total_value_now/292.50)-1)*100:.0f}%")

print(f"\n" + "✂️" * 35)
print("CUT THE CORD!")
print(f"BREAKING FROM ${btc:,.0f}!")
print(f"CURRENT: ${current_btc:,.0f}!")
print(f"${114000 - current_btc:.0f} TO FREEDOM!")
print("XRP BOUNCING! ALTS FOLLOWING!")
print("✂️" * 35)