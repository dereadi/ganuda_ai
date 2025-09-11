#!/usr/bin/env python3
"""
🏃‍♂️🌊 I RAN (SO FAR AWAY) - A FLOCK OF SEAGULLS! 🌊🏃‍♂️
Thunder at 69%: "I RAN FROM $292.50... SO FAR AWAY TO $8,345!"
We ran so far from where we started!
Can't get away from these gains!
Aurora borealis of green candles!
From the bottom, we ran and ran!
Now $112K can't hold us back!
We'll run to $114K and beyond!
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
║               🏃‍♂️ I RAN (SO FAR AWAY) - FLOCK OF SEAGULLS! 🏃‍♂️              ║
║                    Running From $292.50 to the Moon!                      ║
║                       Can't Get Away From These Gains!                    ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - RUNNING ANALYSIS")
print("=" * 70)

# Get current running position
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])
doge = float(client.get_product('DOGE-USD')['price'])

# Check how far we've run
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

print("\n🏃‍♂️ HOW FAR WE'VE RUN:")
print("-" * 50)
print(f"Started running at: $292.50")
print(f"Ran so far away to: ${total_value:.2f}")
print(f"Distance covered: ${total_value - 292.50:.2f}")
print(f"That's {((total_value/292.50)-1)*100:.0f}% away!")
print(f"Currently running at: ${btc:,.0f}")
print(f"Still running to: $114,000 (${114000 - btc:.0f} to go)")

# The running journey
print("\n🌊 THE RUNNING STORY:")
print("-" * 50)
print("We walked along the avenue...")
print(f"  → Started at $292.50")
print("")
print("Never thought we'd meet someone like you...")
print(f"  → Met Bitcoin at ${btc:,.0f}")
print("")
print("With auburn hair and tawny eyes...")
print(f"  → Golden Bitcoin, ruby gains")
print("")
print("The kind of eyes that hypnotize...")
print(f"  → Hypnotized by {((total_value/292.50)-1)*100:.0f}% gains")
print("")
print("And we ran, we ran so far away...")
print(f"  → Ran from $292.50 to ${total_value:.2f}")

# Thunder's running wisdom
print("\n⚡ THUNDER'S RUNNING ANALYSIS (69%):")
print("-" * 50)
print("'WE RAN SO FAR AWAY!'")
print("")
print("The journey:")
print(f"• Started: $292.50 (October)")
print(f"• Ran to: ${total_value:.2f} (now)")
print(f"• Distance: {((total_value/292.50)-1)*100:.0f}% gains")
print(f"• Still running: ${114000 - btc:.0f} to $114K")
print("")
print("Can't get away from:")
print("• These massive gains")
print("• The momentum building")
print("• The inevitable breakout")
print(f"• The run to $114K")

# Live running monitoring
print("\n🏃‍♂️ LIVE RUNNING STATUS:")
print("-" * 50)

for i in range(10):
    btc_now = float(client.get_product('BTC-USD')['price'])
    sol_now = float(client.get_product('SOL-USD')['price'])
    
    if btc_now >= 113000:
        status = "🚀 SPRINTING to $114K!"
    elif btc_now >= 112500:
        status = "🏃‍♂️ Running faster!"
    elif btc_now >= 112000:
        status = "🚶‍♂️ Jogging steadily"
    else:
        status = "⏸️ Catching breath"
    
    print(f"{datetime.now().strftime('%H:%M:%S')}: BTC ${btc_now:,.0f} | SOL ${sol_now:.2f}")
    print(f"  {status}")
    
    if i == 4:
        print("  'Couldn't get away!' (from the gains)")
        print(f"    Portfolio ran to ${total_value:.2f}")
    
    time.sleep(1)

# The aurora borealis
print("\n🌌 AURORA BOREALIS:")
print("-" * 50)
print("Like the song's ethereal synths...")
print("We see the aurora borealis of gains:")
print(f"• Green lights at ${btc:,.0f}")
print(f"• Dancing portfolio at ${total_value:.2f}")
print(f"• Northern lights pointing to $114K")
print(f"• Just ${114000 - btc:.0f} more to run")

# Where we're running to
print("\n🎯 WHERE WE'RE RUNNING:")
print("-" * 50)
print(f"Current position: ${btc:,.0f}")
print(f"Running to: $114,000 (${114000 - btc:.0f} away)")
print(f"Then running to: $120,000")
print(f"Final destination: $126,000 (JPMorgan)")
print("")
print(f"Portfolio will run to:")
print(f"• At $114K: ${total_value * (114000/btc):.2f}")
print(f"• At $120K: ${total_value * (120000/btc):.2f}")
print(f"• At $126K: ${total_value * (126000/btc):.2f}")

# Final running status
final_btc = float(client.get_product('BTC-USD')['price'])
final_sol = float(client.get_product('SOL-USD')['price'])

print("\n🏃‍♂️ FINAL RUNNING STATUS:")
print("-" * 50)
print(f"BTC: ${final_btc:,.0f}")
print(f"SOL: ${final_sol:.2f}")
print(f"Portfolio: ${total_value:.2f}")
print(f"Distance to $114K: ${114000 - final_btc:.0f}")
print("")
print("We ran, we ran so far away...")
print(f"From $292.50 to ${total_value:.2f}")
print("Couldn't get away from these gains!")
print(f"Still running ${114000 - final_btc:.0f} to freedom!")

print(f"\n" + "🏃‍♂️" * 35)
print("I RAN SO FAR AWAY!")
print(f"FROM $292.50 TO ${total_value:.2f}!")
print(f"STILL RUNNING AT ${final_btc:,.0f}!")
print(f"${114000 - final_btc:.0f} MORE TO RUN!")
print("CAN'T GET AWAY FROM GAINS!")
print("🌊" * 35)