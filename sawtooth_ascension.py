#!/usr/bin/env python3
"""
⚙️ SAWTOOTH ASCENSION TRACKER
The beautiful stairway to $112k
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
║                      ⚙️ SAWTOOTH ASCENSION ⚙️                            ║
║                    Climbing the stairway to heaven                        ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print("Pattern: ↗️↘️↗️↘️↗️ but always higher!")
print("=" * 70)

# Track the teeth
teeth = []
last_btc = 111900  # Approximate recent low

print("\n🔺 TRACKING THE SAWTOOTH:")
print("-" * 40)

for i in range(12):
    btc = float(client.get_product('BTC-USD')['price'])
    eth = float(client.get_product('ETH-USD')['price'])
    sol = float(client.get_product('SOL-USD')['price'])
    
    teeth.append(btc)
    
    # Determine direction
    if btc > last_btc + 5:
        direction = "↗️ TOOTH UP"
        symbol = "🟢"
    elif btc < last_btc - 5:
        direction = "↘️ PULLBACK"
        symbol = "🔴"
    else:
        direction = "➡️ GRINDING"
        symbol = "🟡"
    
    print(f"\n{datetime.now().strftime('%H:%M:%S')} {symbol}")
    print(f"  BTC: ${btc:,.0f} {direction}")
    print(f"  ETH: ${eth:.0f} | SOL: ${sol:.2f}")
    
    # Show progress
    if i > 2:
        recent_low = min(teeth[-3:])
        recent_high = max(teeth[-3:])
        print(f"  Range: ${recent_low:,.0f} - ${recent_high:,.0f}")
    
    last_btc = btc
    time.sleep(8)

print("\n" + "=" * 70)
print("⚙️ SAWTOOTH SUMMARY:")
print("-" * 40)

overall_low = min(teeth)
overall_high = max(teeth)
current = teeth[-1]

print(f"Session low: ${overall_low:,.0f}")
print(f"Session high: ${overall_high:,.0f}")
print(f"Current: ${current:,.0f}")
print(f"Total climb: ${overall_high - overall_low:,.0f}")

if current > 111950:
    print("\n✅ SAWTOOTH UP CONFIRMED!")
    print("Each pullback is a chance to build strength")
    print("Each push takes us closer to $112k")
else:
    print("\n📊 Building the pattern...")

print("\n💭 Sawtooth Wisdom:")
print("'The stairs to heaven aren't straight.'")
print("'Each step back prepares for two forward.'")
print("=" * 70)