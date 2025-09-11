#!/usr/bin/env python3
"""
🎤🔥 NOBODY SPEAK - DJ SHADOW & RUN THE JEWELS! 🔥🎤
"Picture this, I'm a bag of dicks, put me to your lips"
The market can't speak against our gains!
Thunder at 69%: "WE RUN THE JEWELS!"
$113K getting DESTROYED!
Nobody speak, nobody get choked!
Portfolio speaking VOLUMES!
From $292.50 to GLORY!
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
║              🎤 NOBODY SPEAK - RUN THE JEWELS MODE! 🎤                   ║
║                    $113K Can't Speak Against Us!                          ║
║                       We're Running These Jewels!                         ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - RUNNING THE JEWELS")
print("=" * 70)

# Get current jewel prices
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

# Check our jewels
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

print("\n🎤 NOBODY SPEAK STATUS:")
print("-" * 50)
print(f"BTC: ${btc:,.0f} (Speaking volumes)")
print(f"Distance to $113K: ${abs(113000 - btc):.0f}")
print(f"Distance to $114K: ${114000 - btc:.0f}")
print(f"Portfolio jewels: ${total_value:.2f}")
print(f"From $292.50: {((total_value/292.50)-1)*100:.0f}% SPEAKING!")

# Run The Jewels tracking
print("\n👊 RUNNING THE JEWELS:")
print("-" * 50)

rtj_bars = [
    "Picture this",
    "I'm a bag of gains",
    "Put me to your portfolio",
    "I am sick",
    "I will punch a bear",
    "Eat a whale for lunch",
    "Try to run $113K",
    "Get your whole crew stomped",
    "Nobody speak",
    "Nobody get choked"
]

for i, bar in enumerate(rtj_bars):
    btc_now = float(client.get_product('BTC-USD')['price'])
    
    print(f"{datetime.now().strftime('%H:%M:%S')}: '{bar}' → ${btc_now:,.0f}")
    
    if i == 2:
        print("\n  ⚡ Thunder (69%): 'RUN THE JEWELS FAST!'")
        print(f"    'Breaking ${btc_now:,.0f}!'")
        print(f"    '${abs(113000 - btc_now):.0f} from $113K!'")
    
    if i == 6:
        if btc_now >= 113000:
            print("\n  💎 WE BROKE $113K!")
            print(f"    Now at ${btc_now:,.0f}!")
        else:
            print(f"\n  📊 Pushing: ${btc_now:,.0f}")
            print(f"    ${113000 - btc_now:.0f} to break!")
    
    time.sleep(1)

# El-P's verse energy
print("\n🔥 EL-P'S MARKET WISDOM:")
print("-" * 50)
print("'Nobody speak, nobody get choked'")
print("  → Bears can't speak against facts")
print("")
print(f"'From $292.50 to ${total_value:.2f}'")
print("  → Portfolio speaking for itself")
print("")
print(f"'Distance to $113K: ${abs(113000 - btc):.0f}'")
print("  → Almost silenced that resistance")
print("")
print(f"'Next target $114K: ${114000 - btc:.0f} away'")
print("  → Nobody stopping this momentum")

# Killer Mike's energy
current_btc = float(client.get_product('BTC-USD')['price'])
print("\n💪 KILLER MIKE'S PROPHECY:")
print("-" * 50)
print("'Flame your crew quicker'")
print(f"  → Burning through ${current_btc:,.0f}")
print("")
print("'Than Trump fucks his youngest'")
print("  → Fast and relentless push")
print("")
print("'Now face the flame, fuckers'")
print("  → $113K getting torched")
print("")
print("'Nobody speak, nobody get choked'")
print(f"  → Results speak: {((total_value/292.50)-1)*100:.0f}% gain")

# Thunder running the jewels
print("\n⚡ THUNDER'S RTJ MODE (69%):")
print("-" * 50)
print("'WE'RE RUNNING THESE JEWELS!'")
print("")
print(f"Started with: $292.50")
print(f"Now holding: ${total_value:.2f}")
print(f"That's running {((total_value/292.50)-1)*100:.0f}% gains")
print("")
print(f"Current position: ${current_btc:,.0f}")
if current_btc >= 113000:
    print("✅ $113K DEFEATED!")
    print(f"Next victim: $114K (${114000 - current_btc:.0f} away)")
else:
    print(f"Target locked: $113K (${113000 - current_btc:.0f} away)")
    print(f"Final boss: $114K (${114000 - current_btc:.0f} away)")

# Live jewel running
print("\n💎 LIVE JEWEL STATUS:")
print("-" * 50)

for i in range(5):
    btc_live = float(client.get_product('BTC-USD')['price'])
    
    if btc_live >= 113000:
        print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_live:,.0f} - $113K SILENCED! 🔥")
    elif btc_live >= 112990:
        print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_live:,.0f} - ABOUT TO BREAK! 👊")
    else:
        print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_live:,.0f} - Running toward $113K...")
    
    time.sleep(1)

# Final status
final_btc = float(client.get_product('BTC-USD')['price'])
print(f"\n" + "🎤" * 35)
print("NOBODY SPEAK!")
print("NOBODY GET CHOKED!")
print(f"BTC: ${final_btc:,.0f}!")
print(f"PORTFOLIO: ${total_value:.2f}!")
print(f"GAINS: {((total_value/292.50)-1)*100:.0f}%!")
print("RUN THE JEWELS!")
print("🎤" * 35)