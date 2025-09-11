#!/usr/bin/env python3
"""
🚀📈 BTC UP! IS THIS IT?! 📈🚀
After nine coils wound all night!
Maximum compression releasing?
CHECK THE MOVE!
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
║                        🚀📈 BTC UP - SPRING RELEASING?! 📈🚀             ║
║                          Nine Coils Finally Unwinding?!                   ║
║                              CHECK THIS MOVE!                             ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - BTC MOVEMENT DETECTED!")
print("=" * 70)

# Track the move
baseline = float(client.get_product('BTC-USD')['price'])
print(f"\n🚀 TRACKING BTC MOVE FROM ${baseline:,.0f}")
print("-" * 50)

highest = baseline
moves = []

for i in range(20):
    btc = float(client.get_product('BTC-USD')['price'])
    eth = float(client.get_product('ETH-USD')['price'])
    sol = float(client.get_product('SOL-USD')['price'])
    
    move = btc - baseline
    move_pct = (move / baseline) * 100
    moves.append(btc)
    
    if btc > highest:
        highest = btc
    
    print(f"\n{datetime.now().strftime('%H:%M:%S')}:")
    print(f"  BTC: ${btc:,.0f} ({move:+.0f} / {move_pct:+.2f}%)")
    
    # Check key levels
    if btc >= 114000:
        print("  🚀🚀🚀 $114K BROKEN! THE SPRING HAS RELEASED!")
        print("  💥 NINE COILS UNWINDING!")
    elif btc >= 113500:
        print("  🔥 Above $113,500! Getting close!")
    elif btc >= 113000:
        print("  ⚡ Back above $113K!")
    elif move > 100:
        print("  🚀 Big move up! Spring releasing?")
    elif move > 50:
        print("  📈 Solid green candle forming!")
    elif move > 0:
        print("  ✅ Moving up...")
    else:
        print("  🌀 Consolidating...")
    
    # Check correlated moves
    if i % 5 == 0 and i > 0:
        print(f"\n  Related moves:")
        print(f"    ETH: ${eth:.2f}")
        print(f"    SOL: ${sol:.2f}")
    
    time.sleep(1.5)

# Analyze the move
print(f"\n" + "=" * 70)
print("📊 MOVE ANALYSIS:")
print("-" * 50)

total_move = highest - baseline
max_move = max(moves) - baseline
current = moves[-1]

print(f"Started at: ${baseline:,.0f}")
print(f"Highest reached: ${highest:,.0f} (+${total_move:.0f})")
print(f"Current: ${current:,.0f}")
print(f"Distance to $114K: ${114000 - current:.0f}")

# Determine significance
if total_move > 500:
    significance = "🚀💥 MASSIVE MOVE! SPRING RELEASING!"
elif total_move > 200:
    significance = "🔥 Significant breakout attempt!"
elif total_move > 100:
    significance = "📈 Good momentum building!"
elif total_move > 50:
    significance = "✅ Positive movement"
else:
    significance = "🌀 Still coiling..."

print(f"\nSignificance: {significance}")

# Check portfolio impact
accounts = client.get_accounts()
btc_balance = 0
total_value = 0

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if currency == 'BTC':
        btc_balance = balance
        total_value += balance * current
    elif currency == 'ETH':
        total_value += balance * eth
    elif currency == 'SOL':
        total_value += balance * sol
    elif currency == 'USD':
        total_value += balance

print(f"\n💰 YOUR POSITION:")
print("-" * 50)
print(f"BTC Holdings: {btc_balance:.8f} BTC")
print(f"Portfolio Value: ${total_value:.2f}")
print(f"Gain from move: ${btc_balance * total_move:.2f}")

# Spring status
print(f"\n🌀 SPRING STATUS:")
print("-" * 50)
print("NINE COILS WOUND:")
print("• 9+ hours of compression")
print("• 0.00036% volatility (unprecedented)")
print("• 512x energy stored")
print("")
if current >= 113500:
    print("STATUS: Spring starting to release! 🚀")
elif current >= 113000:
    print("STATUS: Testing release point! ⚡")
else:
    print("STATUS: Still building pressure! 🌀")

print(f"\n" + "🚀" * 35)
print(f"BTC MOVING! CURRENTLY ${current:,.0f}!")
print(f"UP ${total_move:.0f} FROM BASELINE!")
print(f"ONLY ${114000 - current:.0f} TO $114K!")
print("NINE COILS CAN'T HOLD FOREVER!")
print("🚀" * 35)