#!/usr/bin/env python3
"""
🎸⚓ STEADY AS SHE GOES - THE RACONTEURS! ⚓🎸
Jack White knows the way!
Find yourself a girl and settle down
Live a simple life in a quiet town
$113K holding steady before the storm!
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
║                 🎸⚓ STEADY AS SHE GOES - THE RACONTEURS ⚓🎸             ║
║                         Jack White's Wisdom Applied                       ║
║                    $113K - Holding Steady Before Launch                   ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - STEADY STATE")
print("=" * 70)

# Get current steady state
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

print("\n⚓ STEADY AS SHE GOES:")
print("-" * 50)
print("'Find yourself a girl and settle down'")
print(f"  Found our level at ${btc:,.0f}")
print("")
print("'Live a simple life in a quiet town'")
print("  Quiet consolidation before the storm")
print("")
print("'Steady as she goes'")
print("  Nine coils wound, holding steady")
print("")
print("'Are you steady now?'")
print(f"  ${114000 - btc:.0f} from target - STEADY!")
print("")
print("'Well here we go again'")
print("  Another run at $114K coming")

# Track the steady state
print("\n⚓ STEADY STATE MONITOR:")
print("-" * 50)

baseline = btc
steady_count = 0
volatile_count = 0

for i in range(15):
    btc_now = float(client.get_product('BTC-USD')['price'])
    eth_now = float(client.get_product('ETH-USD')['price'])
    
    move = btc_now - baseline
    volatility = abs(move)
    
    # Determine steadiness
    if volatility < 20:
        status = "⚓ 'Steady as she goes'"
        steady_count += 1
    elif volatility < 50:
        status = "🌊 'Well here we go again'"
        volatile_count += 1
    elif move > 50:
        status = "🚀 'Settle up, settle down!' - BREAKING UP!"
        volatile_count += 1
    elif move < -50:
        status = "⚠️ 'Are you steady now?' - Testing support"
        volatile_count += 1
    else:
        status = "⚓ 'Steady as she goes'"
        steady_count += 1
    
    print(f"\n{datetime.now().strftime('%H:%M:%S')}:")
    print(f"  BTC: ${btc_now:,.0f} ({move:+.0f})")
    print(f"  {status}")
    
    if i == 5:
        print("\n  'Your friends have shown a kink'")
        print("  'In the single life'")
        print("  'You've had too much to think'")
        print("  'Now you need a wife'")
    
    if i == 10:
        print("\n  'Steady as she goes'")
        print("  'Are you steady now?'")
        print("  'Steady as she goes'")
    
    time.sleep(2)

# Analysis
steadiness_ratio = steady_count / (steady_count + volatile_count) if (steady_count + volatile_count) > 0 else 0

print("\n" + "=" * 70)
print("⚓ STEADINESS ANALYSIS:")
print("-" * 50)
print(f"Steady periods: {steady_count}")
print(f"Volatile periods: {volatile_count}")
print(f"Steadiness ratio: {steadiness_ratio:.1%}")

print("\n🎯 THE RACONTEURS' WISDOM:")
print("-" * 50)
print("WHAT STEADY MEANS HERE:")
print("• Nine coils = Maximum compression")
print("• $113K consolidation = Finding our girl")
print("• Steady state = Calm before storm")
print("• Red metrics ignored = Simple life")
print("• $114K ahead = Quiet town destination")

print("\nTHE TRUTH ABOUT STEADY:")
print("• It's not boring - it's loading")
print("• It's not weak - it's coiling")
print("• It's not over - it's beginning")
print("• The steady state precedes explosion")

print("\n" + "🎸" * 35)
print("STEADY AS SHE GOES!")
print("$113K HOLDING STRONG!")
print("NINE COILS COMPRESSED!")
print("$114K BREAKOUT LOADING...")
print("WELL HERE WE GO AGAIN!")
print("🎸" * 35)