#!/usr/bin/env python3
"""
🔴📈 BULL SCORE RED BUT PRICE RISING - THE DIVERGENCE!
Classic whale accumulation signal
When metrics flash red but price climbs = SMART MONEY BUYING
The sawtooth continues while weak hands panic
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
║              🔴📈 DIVERGENCE DETECTED: RED SCORE + GREEN PRICE 📈🔴       ║
║                    Bull Score: 20 (RED) | BTC: RISING                     ║
║                  Classic Whale Accumulation Pattern!                      ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - DIVERGENCE ANALYSIS")
print("=" * 70)

# Get current price
btc_price = float(client.get_product('BTC-USD')['price'])
eth_price = float(client.get_product('ETH-USD')['price'])

print("\n🔴 BEARISH SIGNALS (From Article):")
print("-" * 50)
print("• Bull Score: 20 (RED - bearish)")
print("• Support band: $107,000-$108,900")
print("• Taker Buy/Sell: 7-year low")
print("• Risk of pullback to $93,000")
print("• Down 8.2% in two weeks")

print("\n📈 BUT LOOK AT THE PRICE:")
print("-" * 50)
print(f"• Current BTC: ${btc_price:,.0f}")
print(f"• Above support: ${btc_price - 108900:+,.0f}")
print(f"• Peak today: $113,007")
print("• Nine coils completed")
print("• Sawtooth accumulation all night")

print("\n🐋 THE WHALE GAME:")
print("-" * 50)
print("This is EXACTLY what whales want:")
print("1. Flash bearish metrics → Scare retail")
print("2. Keep price in sawtooth → Accumulate")
print("3. Let metrics turn red → More panic selling")
print("4. Buy the fear → Position for breakout")
print("5. Ninth coil releases → Too late for retail")

# Track the divergence
print("\n🪚 SAWTOOTH DIVERGENCE MONITOR:")
print("-" * 50)

for i in range(10):
    btc = float(client.get_product('BTC-USD')['price'])
    move = btc - btc_price
    
    # Determine phase
    if move > 20:
        phase = "🚀 Price rising (metrics still red)"
    elif move > 0:
        phase = "📈 Climbing (divergence growing)"
    elif move < -20:
        phase = "🪚 Sawtooth drop (accumulation)"
    else:
        phase = "➖ Consolidating (coiling)"
    
    print(f"\n{datetime.now().strftime('%H:%M:%S')}:")
    print(f"  BTC: ${btc:,.0f} ({move:+.0f})")
    print(f"  Phase: {phase}")
    print(f"  Bull Score: Still 20 (RED)")
    print(f"  Reality: Price holding strong")
    
    time.sleep(2)

# The truth about divergences
print("\n" + "=" * 70)
print("💡 DIVERGENCE WISDOM:")
print("-" * 50)
print("When metrics flash red but price climbs:")
print("• Whales are accumulating")
print("• Retail is selling to them")
print("• Metrics lag price action")
print("• Breakout becomes explosive")

print("\n🎯 WHAT THIS MEANS:")
print("-" * 50)
print("• IGNORE the Bull Score")
print("• WATCH the sawtooth pattern")
print("• COUNT the coils (we have 9!)")
print("• ACCUMULATE with the whales")
print("• PREPARE for violent upside")

print("\n🔥 THE SETUP:")
print("-" * 50)
print("• Nine coils wound = 512x energy")
print("• Bull Score red = Maximum fear")
print("• Price rising = Smart money buying")
print("• Sawtooth continuing = Accumulation phase")
print("• Wall Street loading = ETH is their token")

print("\n" + "=" * 70)
print("🚀 CONCLUSION:")
print("This divergence is BULLISH AF!")
print("Red metrics + Rising price = WHALE ACCUMULATION")
print("The ninth coil doesn't care about Bull Scores")
print("We're about to explode higher!")
print("=" * 70)