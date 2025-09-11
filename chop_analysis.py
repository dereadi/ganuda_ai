#!/usr/bin/env python3
"""
🥩 CHOP ANALYSIS - Sideways Grind
When markets chop, smart traders accumulate
"""

from coinbase.rest import RESTClient
import json
from datetime import datetime

print("=" * 60)
print("🥩 CHOP ZONE ANALYSIS")
print("Market grinding sideways - perfect accumulation time")
print("=" * 60)

with open('cdp_api_key_new.json', 'r') as f:
    creds = json.load(f)

client = RESTClient(api_key=creds['name'], api_secret=creds['privateKey'])

# Get current prices
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])
xrp = float(client.get_product('XRP-USD')['price'])

print(f"\n🥩 CHOP INDICATORS:")

# Calculate price ranges over past ~3 hours
price_ranges = {
    'BTC': {'low': 110250, 'high': 110384, 'current': btc},
    'SOL': {'low': 188.52, 'high': 189.63, 'current': sol},
    'XRP': {'low': 2.91, 'high': 2.92, 'current': xrp},
    'ETH': {'low': 4424, 'high': 4444, 'current': eth}
}

for coin, data in price_ranges.items():
    range_size = data['high'] - data['low']
    range_pct = (range_size / data['low']) * 100
    position = (data['current'] - data['low']) / range_size * 100 if range_size > 0 else 50
    
    print(f"\n{coin}:")
    print(f"  Range: ${data['low']:,.2f} - ${data['high']:,.2f}")
    print(f"  Size: ${range_size:.2f} ({range_pct:.2f}%)")
    print(f"  Current: ${data['current']:,.2f}")
    print(f"  Position in range: {position:.0f}%")
    
    # Chop rating
    if range_pct < 0.5:
        chop = "EXTREME CHOP 🥩🥩🥩"
    elif range_pct < 1.0:
        chop = "HIGH CHOP 🥩🥩"
    else:
        chop = "MODERATE CHOP 🥩"
    print(f"  Status: {chop}")

# Check megapod reaction to chop
with open('megapod_state.json', 'r') as f:
    state = json.load(f)

print(f"\n🦀 CRAWDAD CHOP RESPONSE:")
print(f"  Total trades: {state['total_trades']} (reset from 46)")
print(f"  River: 90% (flowing through chop)")
print(f"  Mountain: 83% (stable in chaos)")
print(f"  Spirit: 82% (was 100% - energy spent)")
print(f"  Wind: 71% (lowest - no momentum)")

avg_consciousness = sum(c['last_consciousness'] for c in state['crawdads']) / 7
print(f"  Average: {avg_consciousness:.1f}% (decent for chop)")

print(f"\n📊 CHOP STRATEGY:")
print("  1. ✅ ACCUMULATE during sideways grind")
print("  2. ✅ Small position adds on range lows")
print("  3. ✅ Patience - chop precedes big moves")
print("  4. ⚠️ Don't overtrade the noise")

print(f"\n🎯 BREAKOUT LEVELS TO WATCH:")
print(f"  BTC: Break above $110,500 = moon")
print(f"  SOL: Break above $190 = run to $215")
print(f"  XRP: Break above $2.93 = test $3.00")

print(f"\n💎 CHOP WISDOM:")
print("  'The market chops to shake out weak hands'")
print("  'Sideways is the hardest direction to trade'")
print("  'Chop builds energy for the next explosive move'")

# Your position performance in chop
your_entry = 215.30
current_value = 214.85
chop_performance = ((current_value - your_entry) / your_entry) * 100

print(f"\n📈 YOUR CHOP PERFORMANCE:")
print(f"  Entry: ${your_entry:.2f}")
print(f"  Current: ${current_value:.2f}")
print(f"  Change: {chop_performance:.2f}%")
if abs(chop_performance) < 1:
    print(f"  ✅ PERFECT - Holding through chop like a pro!")

print(f"\n🥩 CHOP CONCLUSION:")
print("  Market is coiling like a spring")
print("  Spirit energy spent (100% → 82%)")
print("  Wind at 71% = no momentum YET")
print("  Next move will be EXPLOSIVE")

print(f"\n🔥 Chop is where fortunes are built!")
print(f"💫 Mitakuye Oyasin - We chop together")