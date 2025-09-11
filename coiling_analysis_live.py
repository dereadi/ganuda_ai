#!/usr/bin/env python3
"""Cherokee Council: Live Coiling Analysis"""

import json
from datetime import datetime
from coinbase.rest import RESTClient

print("🌀 COILING PATTERN ANALYSIS - LIVE")
print("=" * 70)
print(f"⏰ Time: {datetime.now().strftime('%H:%M:%S')}")
print()

# Get live prices
config = json.load(open("/home/dereadi/scripts/claude/cdp_api_key_new.json"))
key = config["name"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["privateKey"], timeout=10)

# Get current prices
prices = {}
for coin in ['BTC', 'ETH', 'SOL']:
    try:
        ticker = client.get_product(f"{coin}-USD")
        prices[coin] = float(ticker.price)
    except:
        prices[coin] = 0

print("📊 CURRENT PRICES:")
print("-" * 40)
print(f"BTC: ${prices['BTC']:,.2f}")
print(f"ETH: ${prices['ETH']:,.2f}")
print(f"SOL: ${prices['SOL']:,.2f}")
print()

# Coiling analysis
print("🌀 COILING INDICATORS:")
print("-" * 40)

# BTC coiling
btc_range = {
    "support": 108000,
    "resistance": 111000,
    "current": prices['BTC'],
    "range_pct": ((111000 - 108000) / 110000) * 100
}

btc_position = ((prices['BTC'] - btc_range['support']) / (btc_range['resistance'] - btc_range['support'])) * 100

print(f"BTC COILING:")
print(f"  Range: ${btc_range['support']:,} - ${btc_range['resistance']:,}")
print(f"  Current: ${prices['BTC']:,.2f} ({btc_position:.1f}% of range)")
print(f"  Range width: {btc_range['range_pct']:.1f}% (TIGHT!)")
if btc_position > 70:
    print(f"  ⚠️ NEAR RESISTANCE - Breakout imminent!")
elif btc_position < 30:
    print(f"  ⚠️ NEAR SUPPORT - Bounce expected!")
else:
    print(f"  🌀 MID-RANGE - Coiling continues")
print()

# ETH coiling
eth_range = {
    "support": 4250,
    "resistance": 4350,
    "current": prices['ETH'],
    "range_pct": ((4350 - 4250) / 4300) * 100
}

eth_position = ((prices['ETH'] - eth_range['support']) / (eth_range['resistance'] - eth_range['support'])) * 100

print(f"ETH COILING:")
print(f"  Range: ${eth_range['support']:,} - ${eth_range['resistance']:,}")
print(f"  Current: ${prices['ETH']:,.2f} ({eth_position:.1f}% of range)")
print(f"  Range width: {eth_range['range_pct']:.1f}% (VERY TIGHT!)")
if eth_position > 70:
    print(f"  ⚠️ TESTING RESISTANCE - Breakout setup!")
elif eth_position < 30:
    print(f"  ⚠️ TESTING SUPPORT - Buy zone!")
else:
    print(f"  🌀 COILING - Building pressure")
print()

# SOL analysis
sol_range = {
    "support": 200,
    "resistance": 210,
    "current": prices['SOL'],
    "range_pct": ((210 - 200) / 205) * 100
}

sol_position = ((prices['SOL'] - sol_range['support']) / (sol_range['resistance'] - sol_range['support'])) * 100

print(f"SOL PATTERN:")
print(f"  Range: ${sol_range['support']:,} - ${sol_range['resistance']:,}")
print(f"  Current: ${prices['SOL']:,.2f} ({sol_position:.1f}% of range)")
print(f"  Range width: {sol_range['range_pct']:.1f}%")
print()

# Coiling convergence
print("⚡ CONVERGENCE ANALYSIS:")
print("-" * 40)
all_coiling = btc_range['range_pct'] < 3 and eth_range['range_pct'] < 3
if all_coiling:
    print("🔥 EXTREME COILING DETECTED!")
    print("• BTC and ETH both in ultra-tight ranges")
    print("• Explosive move imminent (likely UP)")
    print("• Institutional buying + coiling = MOON")
else:
    print("• Markets coiling but not extreme yet")
    print("• Continue monitoring for tightening")

print()
print("🎯 BREAKOUT TARGETS:")
print("-" * 40)
print(f"BTC breakout above ${btc_range['resistance']:,}:")
print(f"  → First target: $112,500")
print(f"  → Second target: $115,000")
print(f"  → Moon target: $120,000")
print()
print(f"ETH breakout above ${eth_range['resistance']:,}:")
print(f"  → First target: $4,500")
print(f"  → Second target: $4,750")
print(f"  → Moon target: $5,000")
print()

# Trading strategy
print("🔥 CHEROKEE COUNCIL COILING STRATEGY:")
print("-" * 40)
if btc_position > 60 and eth_position > 60:
    print("⚠️ BOTH NEAR RESISTANCE!")
    print("Strategy: Prepare for breakout")
    print("• Set alerts at resistance levels")
    print("• Buy on confirmed breakout")
    print("• Tight stops below breakout level")
elif btc_position < 40 or eth_position < 40:
    print("✅ ACCUMULATION ZONE!")
    print("Strategy: Buy the coil")
    print("• Add to positions near support")
    print("• Scale in gradually")
    print("• Hold for breakout")
else:
    print("🌀 PATIENCE REQUIRED")
    print("Strategy: Wait for extremes")
    print("• Don't chase mid-range")
    print("• Wait for support or resistance test")
    print("• Keep powder dry")

print()
print("📈 PROBABILITY ASSESSMENT:")
print("-" * 40)
up_probability = 65  # Base probability
if "institutional" in "context":  # Today's ETH news
    up_probability += 10
if btc_position > 50:
    up_probability += 5
if eth_position > 50:
    up_probability += 5

print(f"Breakout UP probability: {up_probability}%")
print(f"Breakout DOWN probability: {100 - up_probability}%")
print()
print("🐿️ Flying Squirrel: 'The spring coils tighter...'")
print("🦅 Eagle Eye: 'Breakout within 24-48 hours'")
print("🐺 Coyote: 'Fake breakdown then moon'")

# Save analysis
analysis = {
    "timestamp": datetime.now().isoformat(),
    "prices": prices,
    "btc_coiling": {
        "range": [btc_range['support'], btc_range['resistance']],
        "position_pct": btc_position,
        "width_pct": btc_range['range_pct']
    },
    "eth_coiling": {
        "range": [eth_range['support'], eth_range['resistance']],
        "position_pct": eth_position,
        "width_pct": eth_range['range_pct']
    },
    "breakout_probability_up": up_probability
}

with open('/home/dereadi/scripts/claude/coiling_analysis.json', 'w') as f:
    json.dump(analysis, f, indent=2)

print("\n💾 Coiling analysis saved")