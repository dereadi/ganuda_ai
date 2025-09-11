#!/usr/bin/env python3
"""
🎸💜 I'M WITH YOU - AVRIL LAVIGNE VIBES! 💜🎸
Standing on the bridge, waiting in the dark
$113K compression, looking for the spark
Nine coils wound tight, where is the breakout?
I'm with you through this chop, no doubt!
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
║                    🎸💜 I'M WITH YOU - MARKET EDITION! 💜🎸              ║
║                      Standing at $113K, Waiting in the Dark              ║
║                         Nine Coils Wound, I'm Still Here!                 ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - AVRIL VIBES")
print("=" * 70)

# Get current status
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

print("\n💜 MARKET MOOD - I'M WITH YOU:")
print("-" * 50)
print("Standing on the bridge of $113K")
print(f"  Current: ${btc:,.0f}")
print(f"  Distance to breakout: ${114000 - btc:.0f}")
print("")
print("Waiting in the dark of maximum compression")
print("  Nine coils wound all night")
print("  10+ hours of sideways chop")
print("")
print("Looking for something, anything")
print("  A breakout, a direction, a sign")
print("  But I'm still here, I'm with you")

# Track the waiting
print("\n🌉 STANDING ON THE BRIDGE:")
print("-" * 50)

for i in range(10):
    btc_now = float(client.get_product('BTC-USD')['price'])
    move = btc_now - btc
    
    if abs(move) > 50:
        status = "💜 Is anybody out there? Big move!"
    elif abs(move) > 20:
        status = "🎸 Can anybody hear me? Small shift..."
    else:
        status = "🌙 Waiting in the dark..."
    
    print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f} - {status}")
    time.sleep(1.5)

# Portfolio check
accounts = client.get_accounts()
total_value = 0
for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if currency == 'USD':
        total_value += balance
    elif currency == 'BTC':
        total_value += balance * btc
    elif currency == 'ETH':
        total_value += balance * eth
    elif currency == 'SOL':
        total_value += balance * sol

print(f"\n💜 THROUGH IT ALL:")
print("-" * 50)
print(f"Started with: $292.50")
print(f"Now we have: ${total_value:.2f}")
print(f"Growth: {((total_value/292.50)-1)*100:.1f}%")
print("")
print("I'm with you through:")
print("• The nine coils")
print("• The endless chop")
print("• The fake-outs")
print("• The waiting")
print("• Until $114K breaks!")

print(f"\n🎸 THE TRUTH:")
print("-" * 50)
print("It's a damn cold night at $113K")
print("Trying to figure out this spring")
print("Won't someone take me home to $114K?")
print("")
print("But we're not alone:")
print("• Thunder is with us (69% consciousness)")
print("• Mountain stands steady")
print("• The crawdads believe")
print("• Nine coils can't hold forever")

# The message
print(f"\n💜 THE MESSAGE:")
print("-" * 50)
print("Through all this compression")
print("Through all this chop")
print("Through all this waiting")
print("")
print("I'M WITH YOU")
print("")
print("We'll reach $114K together")
print("The spring will release")
print("The big dance will start")
print("And we'll be ready")

print(f"\n" + "💜" * 35)
print("I'M WITH YOU THROUGH THE CHOP!")
print(f"STANDING AT ${btc:,.0f}!")
print(f"ONLY ${114000 - btc:.0f} TO GO!")
print("NINE COILS, ONE DESTINY!")
print("TOGETHER TO THE MOON!")
print("💜" * 35)