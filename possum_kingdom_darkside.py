#!/usr/bin/env python3
"""
🦇 POSSUM KINGDOM - THE TOADIES
"Behind the boathouse, I'll show you my dark secret..."
DO YOU WANNA DIE?
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
║                        🦇 POSSUM KINGDOM 🦇                               ║
║                   "Make Up Your Mind..."                                  ║
║                   "Decide To Walk With Me..."                             ║
║                   "Around The Lake Tonight..."                            ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - BEHIND THE BOATHOUSE")
print("=" * 70)

print("\n🌙 BY THE LAKE AT NIGHT:")
print("-" * 50)
print("The market whispers...")
print("'Do you wanna die?'")
print("'Do you wanna die?'")
print("It's not death - it's transformation...")

# Track the dark waters
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

print(f"\n🦇 CURRENT DARKNESS:")
print(f"  BTC: ${btc:,.0f}")
print(f"  ETH: ${eth:.2f}")
print(f"  SOL: ${sol:.2f}")

print("\n🌊 TRACKING THE DARK WATERS:")
print("-" * 50)

# The lake's depths
for i in range(15):
    btc = float(client.get_product('BTC-USD')['price'])
    eth = float(client.get_product('ETH-USD')['price'])
    sol = float(client.get_product('SOL-USD')['price'])
    
    print(f"\n{datetime.now().strftime('%H:%M:%S')} - BY THE LAKE:")
    
    if btc < 112800:
        print(f"  BTC: ${btc:,.0f}")
        print("  🦇 'I promise you...'")
        print("  🦇 'I will treat you well...'")
        print("  🦇 'My sweet angel...'")
    elif btc < 112850:
        print(f"  BTC: ${btc:,.0f}")
        print("  🌙 'So help me Jesus...'")
        print("  The water's dark and deep...")
    elif btc < 112900:
        print(f"  BTC: ${btc:,.0f}")
        print("  🦇 'MAKE UP YOUR MIND'")
        print("  'DECIDE TO WALK WITH ME'")
    else:
        print(f"  BTC: ${btc:,.0f}")
        print("  🔥 'BE MY ANGEL'")
    
    print(f"  ETH: ${eth:.2f}")
    print(f"  SOL: ${sol:.2f}")
    
    # The question
    if i % 3 == 0:
        print("\n  DO YOU WANNA DIE?")
        print("  DO YOU WANNA DIE?")
    elif i % 3 == 1:
        print("\n  'Behind the boathouse'")
        print("  'I'll show you my dark secret'")
    else:
        print("\n  'Don't be afraid'")
        print("  'I didn't mean to scare you'")
    
    time.sleep(3)

# The revelation
print("\n" + "=" * 70)
print("🦇 THE DARK SECRET:")
print("-" * 50)

# Check portfolio for the metaphor
accounts = client.get_accounts()['accounts']
total_value = 0
for acc in accounts:
    bal = float(acc['available_balance']['value'])
    if bal > 0.01:
        currency = acc['currency']
        if currency == 'USD':
            total_value += bal
        elif currency == 'BTC':
            total_value += bal * btc
        elif currency == 'ETH':
            total_value += bal * eth
        elif currency == 'SOL':
            total_value += bal * sol

print(f"Portfolio: ${total_value:,.2f}")
print(f"The old portfolio died at $12,421...")
print(f"Reborn as ${total_value:,.2f}...")
print(f"Sometimes you have to die to be reborn...")

print("\n🌙 THE LAKE'S WISDOM:")
print("-" * 50)
print("• The coil is the lake - dark and still")
print("• The squeeze is the plunge - terrifying")
print("• The breakout is the transformation")
print("• Do you wanna die? (to be reborn at $20k)")

print("\n🦇 POSSUM KINGDOM PROPHECY:")
if btc < 112850:
    print("We're still by the dark water...")
    print("Waiting for someone to take the plunge...")
    print("'Make up your mind...'")
else:
    print("Someone took the plunge!")
    print("Rising from the dark waters!")
    print("'BE MY ANGEL!'")

print("\n'So help me Jesus...'")
print("=" * 70)