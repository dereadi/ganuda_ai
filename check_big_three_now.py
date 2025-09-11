#!/usr/bin/env python3
"""
🔥 CHECK BIG THREE NOW - LIVE PRICE ACTION
===========================================
ETH, BTC, SOL - What's happening RIGHT NOW
"""

import json
from datetime import datetime
from coinbase.rest import RESTClient

config = json.load(open('/home/dereadi/.coinbase_config.json'))
client = RESTClient(api_key=config['api_key'].split('/')[-1], api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                      🔥 BIG THREE PRICE CHECK 🔥                           ║
║                         ETH | BTC | SOL                                    ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

# Get current prices
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

# Get account balances
accounts = client.get_accounts()['accounts']
btc_bal = float([a for a in accounts if a['currency']=='BTC'][0]['available_balance']['value'])
eth_bal = float([a for a in accounts if a['currency']=='ETH'][0]['available_balance']['value'])
sol_bal = float([a for a in accounts if a['currency']=='SOL'][0]['available_balance']['value'])

print(f"⏰ {datetime.now().strftime('%H:%M:%S')} - LIVE PRICES")
print("=" * 70)

# BTC Analysis
print(f"\n₿ BITCOIN:")
print(f"  Price: ${btc:,.0f}")
print(f"  Holdings: {btc_bal:.8f} BTC (${btc_bal * btc:,.2f})")
print(f"  Range: $111,000 - $112,000")
if btc > 112000:
    print(f"  🚀 BREAKOUT! Above $112k!")
elif btc > 111800:
    print(f"  📈 Testing resistance!")
elif btc < 111200:
    print(f"  📉 Testing support!")
else:
    print(f"  🔄 Mid-range consolidation")

# ETH Analysis
print(f"\n⟠ ETHEREUM:")
print(f"  Price: ${eth:,.2f}")
print(f"  Holdings: {eth_bal:.6f} ETH (${eth_bal * eth:,.2f})")
print(f"  Range: $4,450 - $4,490")
if eth > 4490:
    print(f"  🚀 BREAKOUT! Above $4,490!")
elif eth > 4480:
    print(f"  📈 Pushing upper band!")
elif eth < 4460:
    print(f"  📉 Near support!")
else:
    print(f"  🔄 Ranging")

# SOL Analysis
print(f"\n◎ SOLANA:")
print(f"  Price: ${sol:.2f}")
print(f"  Holdings: {sol_bal:.4f} SOL (${sol_bal * sol:,.2f})")
print(f"  Range: $212 - $216")
if sol > 216:
    print(f"  🚀 BREAKOUT! Above $216!")
elif sol > 215:
    print(f"  📈 Testing highs!")
elif sol < 213:
    print(f"  📉 Near lows!")
else:
    print(f"  🔄 Mid-range")

# Movement Analysis
print("\n📊 MOVEMENT ANALYSIS:")
print("-" * 50)

# Calculate recent movement (rough estimate from last check)
btc_prev = 111600
eth_prev = 4480
sol_prev = 216

btc_move = ((btc - btc_prev) / btc_prev) * 100
eth_move = ((eth - eth_prev) / eth_prev) * 100
sol_move = ((sol - sol_prev) / sol_prev) * 100

print(f"  BTC: {btc_move:+.2f}% {'📈' if btc_move > 0 else '📉' if btc_move < 0 else '➡️'}")
print(f"  ETH: {eth_move:+.2f}% {'📈' if eth_move > 0 else '📉' if eth_move < 0 else '➡️'}")
print(f"  SOL: {sol_move:+.2f}% {'📈' if sol_move > 0 else '📉' if sol_move < 0 else '➡️'}")

# Correlation Check
avg_move = (btc_move + eth_move + sol_move) / 3
print(f"\n  Average Move: {avg_move:+.2f}%")

if abs(btc_move - eth_move) < 0.3 and abs(eth_move - sol_move) < 0.3:
    print("  🔗 HIGHLY CORRELATED - Moving together!")
elif (btc_move > 0 and eth_move > 0 and sol_move > 0) or (btc_move < 0 and eth_move < 0 and sol_move < 0):
    print("  ↗️ SAME DIRECTION - Trend confirmed!")
else:
    print("  🔀 MIXED SIGNALS - Divergence!")

# ETH/BTC Ratio
ratio = eth / btc
print(f"\n🔗 ETH/BTC RATIO: {ratio:.5f}")
if ratio > 0.0402:
    print(f"  ETH outperforming BTC!")
elif ratio < 0.0401:
    print(f"  BTC outperforming ETH!")
else:
    print(f"  Maintaining balance")

# Action Signal
print("\n⚡ ACTION SIGNAL:")
print("-" * 50)

if btc_move > 0.5 and eth_move > 0.5:
    print("  🟢🟢🟢 STRONG BUY - Uptrend confirmed!")
    print("  Deploy all available capital NOW!")
elif btc_move < -0.5 and eth_move < -0.5:
    print("  🔴🔴🔴 SELL/MILK - Downtrend starting!")
    print("  Take profits and wait for support!")
elif abs(btc_move) < 0.1 and abs(eth_move) < 0.1:
    print("  ⏳ CONSOLIDATING - Prepare for breakout!")
    print("  Set orders at range extremes!")
else:
    print("  🔄 CHOPPY - Trade the ranges!")
    print("  Buy dips, sell rips!")

# Portfolio Impact
print("\n💰 PORTFOLIO IMPACT:")
print("-" * 50)
btc_value = btc_bal * btc
eth_value = eth_bal * eth
sol_value = sol_bal * sol
total_big_three = btc_value + eth_value + sol_value

print(f"  BTC Position: ${btc_value:,.2f}")
print(f"  ETH Position: ${eth_value:,.2f}")
print(f"  SOL Position: ${sol_value:,.2f}")
print(f"  Big Three Total: ${total_big_three:,.2f}")

# Next Targets
print("\n🎯 NEXT TARGETS:")
print("-" * 50)
print(f"  BTC: ${btc + 500:,.0f} (up) | ${btc - 500:,.0f} (down)")
print(f"  ETH: ${eth + 20:,.0f} (up) | ${eth - 20:,.0f} (down)")
print(f"  SOL: ${sol + 2:.2f} (up) | ${sol - 2:.2f} (down)")

print("\n🌀 FLYWHEEL STATUS: READY TO SPIN!")
print("=" * 70)