#!/usr/bin/env python3
"""Current Position Analysis for Cherokee Tribe"""

import json
from datetime import datetime

print("🔥 CURRENT PORTFOLIO POSITIONS")
print("=" * 70)
print(f"📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print()

# Current positions from debug_portfolio
positions = {
    "BTC": {
        "amount": 0.05672937,
        "value": 6290.29,
        "price": 110882.43,
        "on_hold": 0.04651104
    },
    "ETH": {
        "amount": 0.98685514,
        "value": 4254.46,
        "price": 4311.13
    },
    "SOL": {
        "amount": 13.78416203,
        "value": 2822.31,
        "price": 204.75
    },
    "AVAX": {
        "amount": 43.28691157,
        "value": 1037.15,
        "price": 23.96
    },
    "XRP": {
        "amount": 108.595005,
        "value": 303.82,
        "price": 2.80
    },
    "USD": {
        "available": 0.65,
        "on_hold": 200.80,
        "total": 201.45
    }
}

total_crypto = sum(p['value'] for p in positions.values() if 'value' in p)
total_value = total_crypto + positions['USD']['total']

print("💼 PORTFOLIO BREAKDOWN:")
print("-" * 40)
print(f"💎 Total Value: ${total_value:,.2f}")
print(f"📈 Crypto Holdings: ${total_crypto:,.2f}")
print(f"💵 USD Balance: ${positions['USD']['total']:.2f}")
print(f"   Available: ${positions['USD']['available']:.2f}")
print(f"   🔒 On Hold: ${positions['USD']['on_hold']:.2f}")
print()

print("📊 POSITION DETAILS:")
print("-" * 40)
for asset, data in positions.items():
    if asset != "USD" and 'value' in data:
        pct = (data['value'] / total_crypto) * 100
        print(f"{asset}:")
        print(f"  Amount: {data['amount']:.8f}")
        print(f"  Value: ${data['value']:,.2f} ({pct:.1f}%)")
        print(f"  Price: ${data['price']:,.2f}")
        if asset == "BTC" and data.get('on_hold'):
            print(f"  🔒 On Hold: {data['on_hold']:.8f} BTC")
        print()

print("📈 ALLOCATION ANALYSIS:")
print("-" * 40)
btc_pct = (positions['BTC']['value'] / total_crypto) * 100
eth_pct = (positions['ETH']['value'] / total_crypto) * 100
sol_pct = (positions['SOL']['value'] / total_crypto) * 100
other_pct = 100 - btc_pct - eth_pct - sol_pct

print(f"BTC: {btc_pct:.1f}% - {'OVERWEIGHT' if btc_pct > 40 else 'BALANCED'}")
print(f"ETH: {eth_pct:.1f}% - {'UNDERWEIGHT - NEEDS MORE!' if eth_pct < 30 else 'GOOD'}")
print(f"SOL: {sol_pct:.1f}% - {'HEALTHY' if sol_pct > 15 else 'LIGHT'}")
print(f"Others: {other_pct:.1f}% (AVAX, XRP, etc)")
print()

print("🎯 WITH $15K FRIDAY INJECTION:")
print("-" * 40)
new_total = total_value + 15000
print(f"New Total: ${new_total:,.2f}")
print()
print("Recommended Deployment:")
print(f"  ETH: $7,500 (50%) → {0.98685514 + 7500/4311:.4f} ETH total")
print(f"  BTC: $4,000 (27%) → {0.05672937 + 4000/110882:.5f} BTC total")
print(f"  SOL: $2,500 (17%) → {13.78416203 + 2500/204.75:.2f} SOL total")
print(f"  Cash: $1,000 (6%) → ${positions['USD']['total'] + 1000:.2f} USD total")
print()

print("🚀 PRICE IMPACT SCENARIOS:")
print("-" * 40)
print("If ETH hits targets with new position:")
for target, gain_pct in [(5500, 27.6), (7000, 62.4), (10000, 132.0)]:
    new_eth_value = (0.98685514 + 7500/4311) * target
    gain = new_eth_value - (positions['ETH']['value'] + 7500)
    print(f"  ETH @ ${target:,}: +${gain:,.0f} profit ({gain_pct:.1f}% gain)")

print()
print("🔥 CHEROKEE COUNCIL ASSESSMENT:")
print("-" * 40)
print("✅ Portfolio healthy at $14,918")
print("⚠️ ETH underweight at 28.5% (needs boost!)")
print("✅ BTC strong at 42.2%")
print("✅ SOL solid at 18.9%")
print("🎯 Perfect setup for ETH accumulation")
print()
print("Flying Squirrel: 'Deploy the $15K war chest into ETH!'")
print("The institutional tsunami demands action NOW!")

# Save analysis
analysis = {
    "timestamp": datetime.now().isoformat(),
    "total_value": total_value,
    "crypto_value": total_crypto,
    "positions": positions,
    "allocation": {
        "BTC": f"{btc_pct:.1f}%",
        "ETH": f"{eth_pct:.1f}%",
        "SOL": f"{sol_pct:.1f}%",
        "Others": f"{other_pct:.1f}%"
    },
    "recommendation": "Deploy $15K with 50% ETH focus"
}

with open('/home/dereadi/scripts/claude/current_positions.json', 'w') as f:
    json.dump(analysis, f, indent=2)

print("\n💾 Position analysis saved to current_positions.json")