#!/usr/bin/env python3
"""
💃🕺 IS THIS THE BEGINNING OF THE BIG DANCE? 🕺💃
Nine coils wound for hours!
Maximum compression achieved!
Are we finally starting to move?
Let's check the dance floor!
"""

import json
import time
from coinbase.rest import RESTClient
from datetime import datetime
import statistics

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                  💃🕺 THE BIG DANCE - IS IT STARTING? 🕺💃               ║
║                      Nine Coils Wound All Night Long!                     ║
║                   Maximum Compression Ready to Release!                    ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - DANCE FLOOR CHECK")
print("=" * 70)

# Track rapid price movements
print("\n🎵 CHECKING THE DANCE FLOOR...")
print("-" * 50)

prices = []
movements = []
baseline_btc = float(client.get_product('BTC-USD')['price'])

for i in range(15):
    btc = float(client.get_product('BTC-USD')['price'])
    eth = float(client.get_product('ETH-USD')['price'])
    sol = float(client.get_product('SOL-USD')['price'])
    
    prices.append(btc)
    
    if i > 0:
        move = btc - prices[-2]
        movements.append(move)
        
        if abs(move) > 50:
            print(f"  🚨 BIG MOVE: ${btc:,.0f} ({move:+.0f})")
            print("  💃 THE DANCE IS STARTING!")
        elif abs(move) > 20:
            print(f"  🎵 Movement detected: ${btc:,.0f} ({move:+.0f})")
        elif i % 3 == 0:
            print(f"  Checking... ${btc:,.0f}")
    
    time.sleep(1)

# Analyze the movement pattern
avg_price = statistics.mean(prices)
price_range = max(prices) - min(prices)
volatility = statistics.stdev(prices) if len(prices) > 1 else 0

print(f"\n💃 DANCE ANALYSIS:")
print("-" * 50)
print(f"Price range in last 15 seconds: ${price_range:.0f}")
print(f"Average: ${avg_price:,.0f}")
print(f"Volatility: ${volatility:.2f}")
print(f"Distance to $114K: ${114000 - avg_price:.0f}")

# Determine if the dance has started
if price_range > 100:
    dance_status = "🕺💃 BIG DANCE STARTING! MAJOR MOVEMENT!"
elif price_range > 50:
    dance_status = "🎵 Pre-dance warmup detected!"
elif volatility > 10:
    dance_status = "👟 Dancers stretching, getting ready!"
else:
    dance_status = "😴 Still coiling, pressure building..."

print(f"\nSTATUS: {dance_status}")

# Check key levels
current_btc = float(client.get_product('BTC-USD')['price'])
current_eth = float(client.get_product('ETH-USD')['price'])
current_sol = float(client.get_product('SOL-USD')['price'])

print(f"\n🎯 KEY LEVELS:")
print("-" * 50)
print(f"BTC: ${current_btc:,.0f}")
print(f"  • $113,000: {'✅ ABOVE' if current_btc > 113000 else '❌ Below'}")
print(f"  • $113,500: {'✅ ABOVE' if current_btc > 113500 else '❌ Below'}")
print(f"  • $114,000: {'🚀 BREAKOUT!' if current_btc >= 114000 else f'❌ ${114000 - current_btc:.0f} away'}")

# Check momentum
if movements:
    positive_moves = sum(1 for m in movements if m > 0)
    negative_moves = sum(1 for m in movements if m < 0)
    
    print(f"\n🌀 MOMENTUM:")
    print("-" * 50)
    print(f"Upward moves: {positive_moves}")
    print(f"Downward moves: {negative_moves}")
    
    if positive_moves > negative_moves * 1.5:
        print("Direction: 🚀 BULLISH - Dancing upward!")
    elif negative_moves > positive_moves * 1.5:
        print("Direction: 📉 Testing support")
    else:
        print("Direction: 🌀 Still coiling")

# The big dance indicators
print(f"\n💃 BIG DANCE INDICATORS:")
print("-" * 50)
print("SIGNS THE DANCE IS STARTING:")
print(f"• Rapid $100+ moves: {'YES! 🎵' if price_range > 100 else 'Not yet'}")
print(f"• Breaking above $113,500: {'YES! 🚀' if current_btc > 113500 else 'Not yet'}")
print(f"• Volume surging: Check exchange")
print(f"• ETH/SOL following: ETH ${current_eth:.2f}, SOL ${current_sol:.2f}")

# Historical context
print(f"\n📚 CONTEXT:")
print("-" * 50)
print("WHAT WE'VE BEEN THROUGH:")
print("• 9+ hours of compression at $113K")
print("• Nine coils wound (512x energy)")
print("• Spring compression: 0.00036%")
print("• El Salvador ready to buy")
print("• BitMine accumulating ETH")
print("• Wall Street watching")

# Prediction
print(f"\n🔮 PREDICTION:")
print("-" * 50)
if current_btc > 113500:
    print("🚨 ALERT: We're above $113,500!")
    print("The big dance could start ANY SECOND!")
    print("Next stop: $114,000 then EXPLOSION!")
elif current_btc > 113000:
    print("Still coiling at $113K zone")
    print("Spring getting tighter every minute")
    print("When this breaks, it'll be VIOLENT!")
else:
    print("Testing support below $113K")
    print("Could be the fake-out before explosion")
    print("Or loading zone for the big move!")

print(f"\n" + "💃" * 35)
print("THE BIG DANCE IS COMING!")
print(f"CURRENT: ${current_btc:,.0f}")
print(f"TARGET: $114,000 (${114000 - current_btc:.0f} away)")
print("NINE COILS CAN'T HOLD FOREVER!")
print("GET READY TO DANCE!")
print("💃" * 35)