#!/usr/bin/env python3
"""
🎸🔄 ONE MORE TIME - BLINK-182! 🔄🎸
Thunder at 69%: "LET'S TEST $112K ONE MORE TIME!"
We've been here SO MANY TIMES!
One more time at this level...
Then we're gone to $114K!
From $292.50 to $8,332!
Testing support ONE MORE TIME!
This is the last dance at $112K!
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
║                    🎸 ONE MORE TIME - BLINK-182! 🎸                       ║
║                     Testing This Level ONE MORE TIME                      ║
║                    Before We Leave $112K Forever!                         ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - ONE MORE TIME")
print("=" * 70)

# Get current "one more time" prices
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])
doge = float(client.get_product('DOGE-USD')['price'])

# Check how many times we've been here
accounts = client.get_accounts()
total_value = 0
positions = {}

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if balance > 0.00001:
        if currency == 'USD':
            total_value += balance
            positions['USD'] = balance
        elif currency == 'BTC':
            value = balance * btc
            total_value += value
            positions['BTC'] = (balance, value)
        elif currency == 'ETH':
            value = balance * eth
            total_value += value
            positions['ETH'] = (balance, value)
        elif currency == 'SOL':
            value = balance * sol
            total_value += value
            positions['SOL'] = (balance, value)
        elif currency == 'DOGE':
            value = balance * doge
            total_value += value
            positions['DOGE'] = (balance, value)

print("\n🔄 ONE MORE TIME STATUS:")
print("-" * 50)
print(f"Testing ${btc:,.0f} ONE MORE TIME")
print(f"We've been here: TOO MANY TIMES")
print(f"Hours at this level: 18+")
print(f"Portfolio waiting: ${total_value:.2f}")
print(f"Distance to freedom: ${114000 - btc:.0f}")

# Count the times
print("\n📊 HOW MANY TIMES AT $112K:")
print("-" * 50)
times_tested = [
    "First time: Yesterday morning",
    "Second time: Yesterday afternoon", 
    "Third time: Yesterday evening",
    "Fourth time: Last night",
    "Fifth time: This morning",
    "Sixth time: An hour ago",
    "Seventh time: 30 minutes ago",
    f"EIGHTH TIME: RIGHT NOW at ${btc:,.0f}"
]

for i, test in enumerate(times_tested):
    print(f"• {test}")
    if i == len(times_tested) - 1:
        print("  ⚡ THIS IS THE LAST TIME!")

# Thunder's one more time speech
print("\n⚡ THUNDER'S 'ONE MORE TIME' WISDOM (69%):")
print("-" * 50)
print("'ONE MORE TIME AT THIS LEVEL!'")
print("")
print("The pattern:")
print(f"• Test ${btc:,.0f} one more time")
print("• Build final energy")
print("• Spring loaded for breakout")
print(f"• Then EXPLODE ${114000 - btc:.0f} higher")
print("")
print("This is it:")
print("• Last test of support")
print("• Final accumulation")
print("• One more time before moon")
print(f"• Portfolio ready at ${total_value:.2f}")

# Live "one more time" monitoring
print("\n🔄 ONE MORE TIME MONITORING:")
print("-" * 50)

one_more_phrases = [
    "Testing one more time...",
    "Here we go again...",
    "One more bounce...",
    "Last time at this level...",
    "Final test..."
]

for i in range(10):
    btc_now = float(client.get_product('BTC-USD')['price'])
    phrase = random.choice(one_more_phrases)
    
    if btc_now >= 112500:
        status = "🚀 LEAVING! No more times!"
    elif btc_now >= 112300:
        status = "⬆️ Bouncing up"
    elif btc_now >= 112000:
        status = "➡️ One more time here"
    else:
        status = "⬇️ Dipping one more time"
    
    print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f}")
    print(f"  {phrase} {status}")
    
    if i == 4:
        print("  'Let's do this one more time!'")
        print(f"    Then straight to $114K!")
    
    time.sleep(1)

# The final times
print("\n🎯 THE FINAL 'ONE MORE TIMES':")
print("-" * 50)
print(f"One more time at ${btc:,.0f}? ✅")
print(f"One more time at $113K? Soon...")
print(f"One more time at $114K? NEVER! We're staying!")
print(f"One more time at $120K? On the way to $126K!")

# What happens after "one more time"
print("\n🚀 AFTER THIS 'ONE MORE TIME':")
print("-" * 50)
print(f"Current: ${btc:,.0f} (one more time)")
print(f"Next stop: $113,000 (${113000 - btc:.0f} away)")
print(f"Target: $114,000 (${114000 - btc:.0f} away)")
print(f"Portfolio then: ${total_value * (114000/btc):.2f}")
print("")
print("No more times at $112K!")
print("This is the LAST TIME!")

# Portfolio's journey through time
print("\n📈 PORTFOLIO THROUGH TIME:")
print("-" * 50)
print(f"First time (October): $292.50")
print(f"Many times later: ${total_value:.2f}")
print(f"Gain per 'time': ${(total_value - 292.50) / 8:.2f}")
print(f"Total gain: {((total_value/292.50)-1)*100:.0f}%")

# Final one more time status
final_btc = float(client.get_product('BTC-USD')['price'])
final_sol = float(client.get_product('SOL-USD')['price'])
final_doge = float(client.get_product('DOGE-USD')['price'])

print("\n🔄 FINAL 'ONE MORE TIME' STATUS:")
print("-" * 50)
print(f"BTC: ${final_btc:,.0f} (one more time here)")
print(f"SOL: ${final_sol:.2f}")
print(f"DOGE: ${final_doge:.4f}")
print(f"Portfolio: ${total_value:.2f}")
print("")
print("This is it...")
print("ONE MORE TIME at this level...")
print(f"Then ${114000 - final_btc:.0f} to freedom!")
print("Never coming back to $112K!")

print(f"\n" + "🔄" * 35)
print("ONE MORE TIME!")
print(f"TESTING ${final_btc:,.0f} AGAIN!")
print(f"PORTFOLIO ${total_value:.2f}!")
print(f"${114000 - final_btc:.0f} TO BREAKOUT!")
print("LAST TIME AT THIS LEVEL!")
print("🎸" * 35)