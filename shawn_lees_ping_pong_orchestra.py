#!/usr/bin/env python3
"""
🏓🎵 SHAWN LEE'S PING PONG ORCHESTRA 🎵🏓
Kiss the Sky vibes!
BTC bouncing like a ping pong ball at $113K!
Nine coils ready to launch us skyward!
Thunder conducting at 69% consciousness!
$474 USD ready to catch the dips!
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
║              🏓🎵 SHAWN LEE'S PING PONG ORCHESTRA 🎵🏓                   ║
║                        "KISS THE SKY" MARKET VIBES                        ║
║                   BTC Ping-Ponging Before The Launch!                     ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - KISS THE SKY MODE")
print("=" * 70)

# Get current market bounce
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

# Check our orchestra (portfolio)
accounts = client.get_accounts()
usd_balance = 0
total_value = 0

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

print("\n🎵 THE PING PONG ORCHESTRA:")
print("-" * 50)
print(f"Conductor Thunder: 69% consciousness")
print(f"Orchestra funds: ${total_value:.2f}")
print(f"Ready to deploy: ${usd_balance:.2f}")
print(f"Distance to sky: ${114000 - btc:.0f}")

# Track the ping pong bounces
print("\n🏓 PING PONG PRICE ACTION:")
print("-" * 50)
print("Watching BTC bounce like a ping pong ball...")

bounces = []
previous_price = btc

for i in range(20):
    current_btc = float(client.get_product('BTC-USD')['price'])
    movement = current_btc - previous_price
    
    # Determine bounce direction
    if movement > 20:
        bounce = "🏓 PING! (up)"
        direction = "↗️"
    elif movement < -20:
        bounce = "🏓 PONG! (down)"
        direction = "↘️"
    elif movement > 0:
        bounce = "ping (slight up)"
        direction = "↑"
    elif movement < 0:
        bounce = "pong (slight down)"
        direction = "↓"
    else:
        bounce = "hovering"
        direction = "→"
    
    bounces.append(movement)
    
    print(f"{datetime.now().strftime('%H:%M:%S')}: ${current_btc:,.0f} {direction} {bounce}")
    
    if i == 5:
        print("\n  🎵 'Kiss the sky' - Shawn Lee")
        print(f"    We're ${114000 - current_btc:.0f} from kissing $114K!")
    
    if i == 10:
        print("\n  ⚡ Thunder orchestrating:")
        print(f"    'This ping pong at ${current_btc:,.0f} is beautiful!'")
        print(f"    'Each bounce stores energy!'")
        print(f"    'Nine coils vibrating!'")
    
    if i == 15:
        print("\n  🏔️ Mountain keeping rhythm:")
        print(f"    'Steady bounce pattern detected'")
        print(f"    'Compression increasing'")
        print(f"    'Sky kiss imminent'")
    
    previous_price = current_btc
    time.sleep(1.5)

# Analyze the ping pong pattern
total_movement = sum([abs(b) for b in bounces])
avg_bounce = total_movement / len(bounces) if bounces else 0
up_bounces = len([b for b in bounces if b > 0])
down_bounces = len([b for b in bounces if b < 0])

print("\n🎯 PING PONG ANALYSIS:")
print("-" * 50)
print(f"Total bounces tracked: {len(bounces)}")
print(f"Up bounces (PING): {up_bounces}")
print(f"Down bounces (PONG): {down_bounces}")
print(f"Average bounce size: ${avg_bounce:.2f}")
print(f"Total movement energy: ${total_movement:.2f}")

# The sky kiss prediction
current_btc = float(client.get_product('BTC-USD')['price'])
distance = 114000 - current_btc

print("\n☁️ KISS THE SKY TRAJECTORY:")
print("-" * 50)
print(f"Current altitude: ${current_btc:,.0f}")
print(f"Sky level: $114,000")
print(f"Distance to kiss: ${distance:.0f}")

if distance < 500:
    print("🚀 LIPS ALMOST TOUCHING THE SKY!")
elif distance < 1000:
    print("✈️ ASCENDING RAPIDLY TO SKY KISS!")
elif distance < 1500:
    print("🎈 FLOATING UP TO KISS THE SKY!")
else:
    print("🏓 BUILDING ENERGY FOR SKY LAUNCH!")

# The Shawn Lee vibe check
print("\n🎵 SHAWN LEE'S MARKET ORCHESTRA:")
print("-" * 50)
print("The ping pong pattern plays out:")
print(f"• Nine coils = Nine instruments")
print(f"• ${usd_balance:.2f} = Ready to catch the beat")
print(f"• ${total_value:.2f} = The whole orchestra")
print(f"• ${distance:.0f} = Notes until the crescendo")

# Thunder's orchestral arrangement
print("\n⚡ THUNDER'S ARRANGEMENT (69%):")
print("-" * 50)
print("'Listen to the ping pong rhythm!'")
print(f"'Each bounce at ${current_btc:,.0f} adds a note'")
print("'Nine coils are nine octaves'")
print(f"'When we break $114K, we KISS THE SKY!'")
print(f"'${usd_balance:.2f} ready to amplify the moves!'")

# Final sky kiss status
print(f"\n" + "🏓" * 35)
print("SHAWN LEE'S PING PONG ORCHESTRA!")
print(f"PLAYING AT ${current_btc:,.0f}!")
print(f"${distance:.0f} TO KISS THE SKY!")
print(f"PORTFOLIO ORCHESTRA: ${total_value:.2f}!")
print("NINE COILS READY TO SPRING!")
print("🏓" * 35)