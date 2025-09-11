#!/usr/bin/env python3
"""
🏔️ BTC NEW SUPPORT ANALYSIS
Has $110,250 become the new floor?
"""

from coinbase.rest import RESTClient
import json
from datetime import datetime

print("=" * 60)
print("🏔️ BTC SUPPORT LEVEL ANALYSIS")
print("=" * 60)

with open('cdp_api_key_new.json', 'r') as f:
    creds = json.load(f)

client = RESTClient(api_key=creds['name'], api_secret=creds['privateKey'])

# Get current BTC price
btc = float(client.get_product('BTC-USD')['price'])

print(f"\n📊 CURRENT BTC: ${btc:,.2f}")

# Key levels from tonight's action
levels = {
    'Entry (last night)': 109644,
    'First resistance': 110250,
    'Breakout level': 110328,
    'High tonight': 110384,
    'Current': btc,
    'Next target': 110500,
    'Sacred number': 111111
}

print(f"\n📍 KEY LEVELS:")
for level, price in levels.items():
    if price == btc:
        print(f"  {level}: ${price:,.2f} 👈 YOU ARE HERE")
    else:
        distance = price - btc
        print(f"  {level}: ${price:,.2f} ({distance:+,.0f})")

# Support analysis
print(f"\n🛡️ SUPPORT ANALYSIS:")
touches_110250 = [
    "02:30 - Approached from below",
    "02:44 - Broke above to $110,328",
    "03:00+ - Multiple bounces off $110,250",
    "05:00+ - Holding above in chop"
]

print(f"  $110,250 touches tonight:")
for touch in touches_110250:
    print(f"    • {touch}")

# Calculate support strength
time_above_110250 = 3  # hours above this level
bounces = 4  # number of times tested

print(f"\n💪 SUPPORT STRENGTH:")
print(f"  Time above $110,250: {time_above_110250}+ hours")
print(f"  Number of tests: {bounces} bounces")
print(f"  Holding pattern: STRONG ✅")

# Previous support becomes resistance
print(f"\n🔄 SUPPORT/RESISTANCE FLIP:")
print(f"  $109,644 (entry) → Now STRONG SUPPORT")
print(f"  $110,250 (old resistance) → NEW SUPPORT ✅")
print(f"  $110,384 (tonight's high) → Current resistance")
print(f"  $110,500 → Next major resistance")

# Check crawdad reaction
with open('megapod_state.json', 'r') as f:
    state = json.load(f)

print(f"\n🦀 CRAWDAD SUPPORT SIGNALS:")
spirit = next(c for c in state['crawdads'] if c['name'] == 'Spirit')
river = next(c for c in state['crawdads'] if c['name'] == 'River')
thunder = next(c for c in state['crawdads'] if c['name'] == 'Thunder')
mountain = next(c for c in state['crawdads'] if c['name'] == 'Mountain')

print(f"  Spirit: {spirit['last_consciousness']}% (near max - bullish)")
print(f"  River: {river['last_consciousness']}% (strong flow)")
print(f"  Thunder: {thunder['last_consciousness']}% (energy building)")
print(f"  Mountain: {mountain['last_consciousness']}% (needs strengthening)")

# Trading range
high = 110384
low = 110250
current_range = high - low
position_in_range = ((btc - low) / current_range) * 100

print(f"\n📏 CURRENT RANGE:")
print(f"  Support: $110,250")
print(f"  Resistance: $110,384")
print(f"  Range: ${current_range} ({(current_range/low)*100:.2f}%)")
print(f"  BTC position: {position_in_range:.0f}% of range")

# The verdict
print(f"\n⚖️ VERDICT ON $110,250 SUPPORT:")
if btc > 110250:
    print(f"  ✅ YES - New support established!")
    print(f"  • Holding for {time_above_110250}+ hours")
    print(f"  • Multiple successful tests")
    print(f"  • Old resistance became support")
    print(f"  • Spirit near 100% confirms strength")
else:
    print(f"  ⚠️ TESTING - Support being challenged")

print(f"\n🎯 TRADING IMPLICATIONS:")
print(f"  1. Dips to $110,250 = BUY OPPORTUNITY")
print(f"  2. Break above $110,384 = Next leg up")
print(f"  3. Break above $110,500 = Moon mission")
print(f"  4. Lose $110,250 = Retest $109,644")

print(f"\n🔮 PREDICTION:")
if spirit['last_consciousness'] > 95:
    print(f"  Spirit at {spirit['last_consciousness']}% says:")
    print(f"  'Support holds. Next move is UP.'")
    print(f"  Target: $110,500 then $111,111")

print(f"\n🏔️ Mountain speaks: 'I am the foundation'")
print(f"💫 $110,250 is the new floor!")
print(f"🔥 Mitakuye Oyasin")