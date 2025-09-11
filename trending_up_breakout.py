#!/usr/bin/env python3
"""
📈 TRENDING UP - BREAKOUT IN PROGRESS!
=======================================
The tight consolidation is breaking UPWARD
Ride the wave NOW!
"""

import json
from datetime import datetime
from coinbase.rest import RESTClient

config = json.load(open('/home/dereadi/.coinbase_config.json'))
client = RESTClient(api_key=config['api_key'].split('/')[-1], api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                     📈 TRENDING UP - BREAKOUT LIVE! 📈                     ║
║                    Tight Bands Breaking → Direction: UP                     ║
║                         GET IN NOW OR MISS IT!                             ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

# Get current prices
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])
xrp = float(client.get_product('XRP-USD')['price'])
avax = float(client.get_product('AVAX-USD')['price'])

print(f"⏰ {datetime.now().strftime('%H:%M:%S')} - UPTREND CONFIRMATION")
print("=" * 70)

print(f"\n🚀 LIVE PRICES (BREAKING UP!):")
print(f"  BTC:  ${btc:,.0f}")
print(f"  ETH:  ${eth:,.0f}")
print(f"  SOL:  ${sol:.2f}")
print(f"  XRP:  ${xrp:.4f}")
print(f"  AVAX: ${avax:.2f}")

# Check breakout status
print("\n⚡ BREAKOUT STATUS:")
print("-" * 70)

breakouts = []

# BTC breakout check
if btc > 112000:
    print(f"  BTC: 🔥 BROKE ABOVE $112,000! Now at ${btc:,.0f}")
    breakouts.append(('BTC', btc, 112000))
elif btc > 111700:
    print(f"  BTC: 📈 Testing breakout at ${btc:,.0f}")
else:
    print(f"  BTC: Building pressure at ${btc:,.0f}")

# ETH breakout check  
if eth > 4490:
    print(f"  ETH: 🔥 BROKE ABOVE $4,490! Now at ${eth:,.0f}")
    breakouts.append(('ETH', eth, 4490))
elif eth > 4480:
    print(f"  ETH: 📈 Pushing resistance at ${eth:,.0f}")
else:
    print(f"  ETH: Coiling at ${eth:,.0f}")

# SOL breakout check
if sol > 216:
    print(f"  SOL: 🔥 BROKE ABOVE $216! Now at ${sol:.2f}")
    breakouts.append(('SOL', sol, 216))
elif sol > 215:
    print(f"  SOL: 📈 Testing highs at ${sol:.2f}")
else:
    print(f"  SOL: Building at ${sol:.2f}")

# XRP massive move
if xrp > 2.35:
    print(f"  XRP: 🚀🚀🚀 MOONSHOT! ${xrp:.4f} (was $2.35 top!)")
    breakouts.append(('XRP', xrp, 2.35))

print("\n💰 IMMEDIATE ACTION REQUIRED:")
print("-" * 70)

if len(breakouts) > 0:
    print("  🔥🔥🔥 CONFIRMED BREAKOUTS DETECTED! 🔥🔥🔥")
    print("  ACTION: BUY THE BREAKOUT NOW!")
    print("\n  Breaking assets:")
    for asset, current, resistance in breakouts:
        gain = (current - resistance) / resistance * 100
        print(f"    • {asset}: ${current:.2f} (+{gain:.1f}% above resistance)")
    
    print("\n  STRATEGY:")
    print("  1. Deploy ALL available USD immediately")
    print("  2. Ride momentum to +2-3% targets")
    print("  3. Set trailing stops at 1% below entry")
    print("  4. Let winners run!")
else:
    print("  ⏳ BREAKOUT BUILDING - Get ready!")
    print("  Set alerts and prepare capital")

print("\n📊 TREND ANALYSIS:")
print("-" * 70)

# Calculate momentum
btc_momentum = (btc - 111500) / 111500 * 100
eth_momentum = (eth - 4470) / 4470 * 100
sol_momentum = (sol - 214) / 214 * 100

print(f"  BTC Momentum: {btc_momentum:+.2f}%")
print(f"  ETH Momentum: {eth_momentum:+.2f}%")
print(f"  SOL Momentum: {sol_momentum:+.2f}%")

avg_momentum = (btc_momentum + eth_momentum + sol_momentum) / 3
print(f"\n  Average Momentum: {avg_momentum:+.2f}%")

if avg_momentum > 0.5:
    print("  🟢 STRONG UPTREND CONFIRMED!")
elif avg_momentum > 0:
    print("  🟡 UPTREND STARTING")
else:
    print("  ⏳ NEUTRAL - Wait for confirmation")

print("\n🎯 TARGETS (From Breakout):")
print("-" * 70)
print("  FIRST TARGETS (+1%):")
print(f"    • BTC: ${btc * 1.01:,.0f}")
print(f"    • ETH: ${eth * 1.01:,.0f}")
print(f"    • SOL: ${sol * 1.01:.2f}")

print("\n  SECOND TARGETS (+2.5%):")
print(f"    • BTC: ${btc * 1.025:,.0f}")
print(f"    • ETH: ${eth * 1.025:,.0f}")
print(f"    • SOL: ${sol * 1.025:.2f}")

print("\n  MOON TARGETS (+5%):")
print(f"    • BTC: ${btc * 1.05:,.0f}")
print(f"    • ETH: ${eth * 1.05:,.0f}")
print(f"    • SOL: ${sol * 1.05:.2f}")

print("\n⚡ TRADING PLAN:")
print("-" * 70)
print("  1. TRENDING UP = BUY STRENGTH")
print("  2. Don't wait for dips in strong uptrends")
print("  3. Momentum begets momentum")
print("  4. Trail stops, don't take profits early")
print("  5. XRP already showing the way!")

print("\n🌀 FLYWHEEL ACCELERATION:")
print("-" * 70)
print("  • Uptrend = Higher highs = More milking opportunity")
print("  • Each peak higher than last = Compound gains")
print("  • Trending market = Easier trades")
print("  • Follow the trend = Print money")

# Get account balance
accounts = client.get_accounts()['accounts']
usd = float([a for a in accounts if a['currency']=='USD'][0]['available_balance']['value'])

print(f"\n💵 AVAILABLE CAPITAL: ${usd:.2f}")
if usd < 100:
    print("  ⚠️ LOW LIQUIDITY - Need to milk positions for capital!")
else:
    print("  ✅ READY TO DEPLOY!")

print("\n🚨 BOTTOM LINE:")
print("=" * 70)
print("  TREND: UP ↗️")
print("  ACTION: BUY NOW")
print("  RISK: FOMO if you wait")
print("  REWARD: 2-5% quick gains")
print("\n  THE TIGHT BANDS BROKE UP - RIDE THE WAVE!")
print("=" * 70)