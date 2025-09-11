#!/usr/bin/env python3
"""
🔥💙 BURNIN' FOR YOU - BLUE ÖYSTER CULT! 💙🔥
"I'm burnin', I'm burnin', I'm burnin' for you"
Thunder at 69%: "BURNIN' FOR $114K!"
17+ hours of burning desire!
Portfolio burnin' at $7,150+!
"Time is the essence, time is the season"
Time for the breakout is NOW!
From $292.50 we've been burnin'!
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
║                 🔥 BURNIN' FOR YOU - BLUE ÖYSTER CULT! 🔥               ║
║                      "I'm Burnin', Burnin' For You"                       ║
║                    17+ Hours Of Burning Desire For $114K!                 ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - BURNING INTENSITY")
print("=" * 70)

# Get current burning levels
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

# Check our burning portfolio
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

print("\n🔥 BURNIN' STATUS:")
print("-" * 50)
print(f"Currently burning at: ${btc:,.0f}")
print(f"Burning for: $114,000")
print(f"Heat needed: ${114000 - btc:.0f}")
print(f"Portfolio on fire: ${total_value:.2f}")
print(f"Burning since: $292.50 ({((total_value/292.50)-1)*100:.0f}% flames)")

# The burning verses
print("\n💙 THE BURNING SONG:")
print("-" * 50)

burning_lyrics = [
    ("Home in the valley", f"Started at $292.50"),
    ("Home in the city", f"Now at ${btc:,.0f}"),
    ("Home isn't pretty", "17+ hours of chop"),
    ("Ain't no home for me", "Must escape to $114K"),
    ("Home in the darkness", "Stuck in consolidation"),
    ("Home on the highway", f"Highway to ${114000 - btc:.0f} higher"),
    ("Home isn't my way", "Diamond hands way"),
    ("Home I'll never be", f"Home is ${total_value:.2f}"),
    ("Burn out the day", "Burning through resistance"),
    ("Burn out the night", "All night vigil"),
    ("I'm burnin', I'm burnin'", f"For ${114000 - btc:.0f} more"),
    ("I'm burnin' for you", "For $114K breakthrough")
]

for i, (lyric, meaning) in enumerate(burning_lyrics):
    btc_now = float(client.get_product('BTC-USD')['price'])
    
    if i % 2 == 0:
        print(f"{datetime.now().strftime('%H:%M:%S')}: '{lyric}'")
        print(f"  → {meaning}")
    else:
        print(f"           '{lyric}' → {meaning}")
    
    if i == 5:
        print("\n  ⚡ Thunder (69%): 'I'M BURNIN'!'")
        print(f"    'BURNIN' AT ${btc_now:,.0f}!'")
        print(f"    'FOR ${114000 - btc_now:.0f} MORE!'")
    
    if i == 10:
        print("\n  🏔️ Mountain: 'The fire intensifies'")
        print(f"    'Burning desire at ${btc_now:,.0f}'")
    
    time.sleep(1)

# The burning intensity meter
print("\n🔥 BURNING INTENSITY METER:")
print("-" * 50)

for i in range(10):
    btc_live = float(client.get_product('BTC-USD')['price'])
    distance = 114000 - btc_live
    
    if distance < 500:
        flames = "🔥" * 10
        intensity = "INFERNO!"
    elif distance < 1000:
        flames = "🔥" * 8
        intensity = "BLAZING!"
    elif distance < 1500:
        flames = "🔥" * 6
        intensity = "BURNING HOT!"
    elif distance < 2000:
        flames = "🔥" * 4
        intensity = "HEATING UP!"
    else:
        flames = "🔥" * 2
        intensity = "SMOLDERING..."
    
    print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_live:,.0f} {flames} {intensity}")
    
    if i == 4:
        print("  'Time is the essence, time is the season'")
        print(f"    (17+ hours burning)")
    
    if i == 8:
        print("  'I'm living for giving the devil his due'")
        print(f"    (Paying dues at ${btc_live:,.0f})")
    
    time.sleep(1)

# Thunder's burning confession
current_btc = float(client.get_product('BTC-USD')['price'])
print("\n⚡ THUNDER'S BURNING CONFESSION (69%):")
print("-" * 50)
print("'I'M BURNIN', I'M BURNIN', I'M BURNIN' FOR YOU!'")
print("")
print("What I'm burning for:")
print(f"• Breaking above ${current_btc:,.0f}")
print(f"• Reaching $114,000 (${114000 - current_btc:.0f} away)")
print(f"• Portfolio to $10K (from ${total_value:.2f})")
print("• Freedom from consolidation")
print("• JPMorgan's $126K prophecy")
print("")
print("'TELL ME WHAT YOU WANT!'")
print("  → I want $114K!")
print("'I'LL BRING IT TO YOU!'")
print("  → Bringing the breakout!")

# The eternal flame
print("\n🔥 THE ETERNAL FLAME:")
print("-" * 50)
print("How long we've been burning:")
print(f"• Started: $292.50")
print(f"• Now: ${total_value:.2f}")
print(f"• Hours: 17+ at ${current_btc:,.0f}")
print(f"• Distance: ${114000 - current_btc:.0f} to goal")
print("")
print("The flame that won't die:")
print("• Diamond hands since day 1")
print(f"• {((total_value/292.50)-1)*100:.0f}% gains burning bright")
print("• Nine coils of compressed fire")
print("• 512x energy ready to explode")

# Final burning status
final_btc = float(client.get_product('BTC-USD')['price'])
accounts_final = client.get_accounts()
final_value = 0
for account in accounts_final['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if currency == 'USD':
        final_value += balance
    elif currency == 'BTC':
        final_value += balance * final_btc
    elif currency == 'ETH':
        final_value += balance * float(client.get_product('ETH-USD')['price'])
    elif currency == 'SOL':
        final_value += balance * float(client.get_product('SOL-USD')['price'])

print("\n💙 FINAL BURNING STATUS:")
print("-" * 50)
print(f"Burning at: ${final_btc:,.0f}")
print(f"Burning for: $114,000")
print(f"Heat gap: ${114000 - final_btc:.0f}")
print(f"Portfolio flames: ${final_value:.2f}")
print("")
if final_btc >= 113000:
    print("Status: 🔥 BURNING THROUGH $113K!")
elif final_btc >= 112500:
    print("Status: 🔥 Temperature rising!")
else:
    print("Status: 🔥 Still burning, still yearning!")

print(f"\n" + "🔥" * 35)
print("I'M BURNIN' FOR YOU!")
print(f"BURNIN' AT ${final_btc:,.0f}!")
print(f"${114000 - final_btc:.0f} TO SATISFACTION!")
print(f"PORTFOLIO: ${final_value:.2f}!")
print("17+ HOURS OF BURNING DESIRE!")
print("🔥" * 35)