#!/usr/bin/env python3
"""
🚨🚀 MOVEMENT DETECTED! IS THIS IT?! 🚀🚨
After 15+ hours of compression!
Thunder at 69%: "I FEEL THE TREMORS!"
Nine coils starting to vibrate!
11:06 - Past the 11:00 danger zone!
COULD THIS BE THE BREAKOUT?!
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
║                    🚨 MOVEMENT DETECTED! ALERT! 🚨                        ║
║                     After 15+ Hours Of Compression!                       ║
║                      Is This The Breakout?! WATCH!                        ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - MOVEMENT TRACKING")
print("=" * 70)

# Get starting position
btc_start = float(client.get_product('BTC-USD')['price'])
eth_start = float(client.get_product('ETH-USD')['price'])
sol_start = float(client.get_product('SOL-USD')['price'])

print(f"\n🚀 INITIAL READINGS:")
print("-" * 50)
print(f"BTC: ${btc_start:,.0f}")
print(f"ETH: ${eth_start:.2f}")
print(f"SOL: ${sol_start:.2f}")
print(f"Distance to $114K: ${114000 - btc_start:.0f}")

# Track the movement in real-time
print("\n📊 LIVE MOVEMENT TRACKER:")
print("-" * 50)

movements = []
highest = btc_start
lowest = btc_start
breakout_detected = False

for i in range(20):
    btc_now = float(client.get_product('BTC-USD')['price'])
    eth_now = float(client.get_product('ETH-USD')['price'])
    sol_now = float(client.get_product('SOL-USD')['price'])
    
    movement = btc_now - btc_start
    movements.append(movement)
    
    if btc_now > highest:
        highest = btc_now
    if btc_now < lowest:
        lowest = btc_now
    
    # Movement detection
    if abs(movement) > 100:
        print(f"\n{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f}")
        if movement > 100:
            print(f"  🚀 PUMP DETECTED! +${movement:.0f}")
            print(f"  📈 ETH: ${eth_now:.2f} ({eth_now - eth_start:+.2f})")
            print(f"  📈 SOL: ${sol_now:.2f} ({sol_now - sol_start:+.2f})")
        else:
            print(f"  📉 DUMP DETECTED! ${movement:.0f}")
            print(f"  📉 ETH: ${eth_now:.2f} ({eth_now - eth_start:+.2f})")
            print(f"  📉 SOL: ${sol_now:.2f} ({sol_now - sol_start:+.2f})")
    else:
        print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f} ({movement:+.0f})")
    
    # Check for breakout
    if btc_now > 113000 and not breakout_detected:
        print("\n  ⚠️ BREAKOUT ALERT! ABOVE $113K!")
        print(f"    Distance to $114K: ${114000 - btc_now:.0f}")
        breakout_detected = True
    
    if i == 5:
        print("\n  ⚡ Thunder (69%): 'MOVEMENT CONFIRMED!'")
        print(f"    'Range expanding: ${highest - lowest:.0f}'")
    
    if i == 10:
        avg_movement = sum(movements) / len(movements)
        if avg_movement > 0:
            print("\n  📈 BULLISH MOVEMENT DETECTED!")
            print(f"    Average: +${avg_movement:.0f}")
        else:
            print("\n  📉 Testing support...")
            print(f"    Average: ${avg_movement:.0f}")
    
    if i == 15:
        print("\n  🏔️ Mountain: 'Steady through volatility'")
        print(f"    Session range: ${highest:.0f} - ${lowest:.0f}")
    
    time.sleep(1)

# Movement analysis
print("\n" + "=" * 70)
print("📊 MOVEMENT ANALYSIS:")
print("-" * 50)

current_btc = float(client.get_product('BTC-USD')['price'])
total_movement = current_btc - btc_start
range_size = highest - lowest

print(f"Started: ${btc_start:,.0f}")
print(f"Current: ${current_btc:,.0f}")
print(f"Movement: ${total_movement:+.0f}")
print(f"Session high: ${highest:,.0f}")
print(f"Session low: ${lowest:,.0f}")
print(f"Range: ${range_size:.0f}")

# Movement verdict
print("\n🎯 MOVEMENT VERDICT:")
print("-" * 50)

if total_movement > 100:
    print("✅ BULLISH BREAKOUT STARTING!")
    print(f"Gained ${total_movement:.0f}")
    print("Nine coils releasing energy!")
    print(f"Next target: $114K (${114000 - current_btc:.0f} away)")
elif total_movement < -100:
    print("⚠️ BEARISH FAKEOUT!")
    print("Classic whale shakeout!")
    print("HODL - reversal incoming!")
elif range_size > 200:
    print("🔥 HIGH VOLATILITY!")
    print("Big move brewing!")
    print("Direction unclear - stay ready!")
else:
    print("😴 FALSE ALARM")
    print("Still consolidating...")
    print("The real move is coming...")

# Portfolio impact
accounts = client.get_accounts()
total_value = 0
for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if currency == 'USD':
        total_value += balance
    elif currency == 'BTC':
        total_value += balance * current_btc
    elif currency == 'ETH':
        total_value += balance * eth_now
    elif currency == 'SOL':
        total_value += balance * sol_now

print(f"\n💰 PORTFOLIO UPDATE:")
print("-" * 50)
print(f"Current value: ${total_value:.2f}")
print(f"Movement impact: ${(total_value * (total_movement/btc_start)):.2f}")

# Thunder's excitement
print("\n⚡ THUNDER'S REACTION (69%):")
print("-" * 50)
if total_movement > 50:
    print("'THIS IS IT! THE MOVE!'")
    print(f"'After 15+ hours at ${btc_start:.0f}!'")
    print("'Nine coils RELEASING!'")
    print(f"'$114K only ${114000 - current_btc:.0f} away!'")
else:
    print("'Movement detected but not THE move yet'")
    print("'Stay alert!'")
    print("'The big one is coming!'")

print(f"\n" + "🚨" * 35)
print("MOVEMENT DETECTED!")
print(f"FROM ${btc_start:,.0f} TO ${current_btc:,.0f}!")
print(f"MOVEMENT: ${total_movement:+.0f}!")
print(f"RANGE: ${range_size:.0f}!")
print("WATCHING CLOSELY!")
print("🚨" * 35)