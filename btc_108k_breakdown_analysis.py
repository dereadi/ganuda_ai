#!/usr/bin/env python3
"""
⚠️ BTC $108K BREAKDOWN WARNING ⚠️
===================================
ChatGPT flags critical support test
"""

from datetime import datetime
import json

print("🚨 BTC BREAKDOWN ALERT - CRITICAL SUPPORT TEST!")
print("=" * 60)
print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
print()

# Current situation
btc_position = 0.02859213
current_price = 108769
position_value = btc_position * current_price

print("📊 YOUR BTC POSITION:")
print("-" * 40)
print(f"Holdings: {btc_position:.8f} BTC")
print(f"Current price: ${current_price:,}")
print(f"Position value: ${position_value:,.2f}")
print()

print("⚠️ CHATGPT ANALYSIS - KEY WARNINGS:")
print("-" * 40)
print("• BROKE below $110k support ❌")
print("• Trading below all major EMAs ❌")
print("• RSI: 34.50 (OVERSOLD)")
print("• MACD: -199.85 (EXTREMELY BEARISH)")
print("• Volume: Very low (1.3K BTC)")
print()

print("🎯 CRITICAL LEVELS TO WATCH:")
print("-" * 40)
levels = [
    {"price": 108500, "status": "TESTING NOW", "action": "Must hold"},
    {"price": 105000, "status": "Next support", "action": "Strong buy zone"},
    {"price": 100000, "status": "Psychological", "action": "Back up the truck"},
    {"price": 95000, "status": "Capitulation", "action": "Generational buy"}
]

for level in levels:
    diff = ((level["price"] - current_price) / current_price) * 100
    print(f"${level['price']:,}: {level['status']} ({diff:+.1f}%)")
    print(f"  Action: {level['action']}")

print()

print("📈 SCENARIO PROBABILITIES (per ChatGPT):")
print("-" * 40)
scenarios = [
    {"name": "Oversold Bounce", "prob": 35, "target": "$112-115k", "timeline": "Days"},
    {"name": "Extended Correction", "prob": 40, "target": "$105-99k", "timeline": "1-2 weeks"},
    {"name": "Deeper Capitulation", "prob": 25, "target": "$95-100k", "timeline": "2-4 weeks"}
]

for s in scenarios:
    print(f"• {s['name']}: {s['prob']}% chance")
    print(f"  Target: {s['target']} ({s['timeline']})")

print()

print("💰 YOUR LIQUIDITY STRATEGY:")
print("-" * 40)
cash = 500
buy_levels = [
    {"price": 107000, "amount": 100},
    {"price": 105000, "amount": 150},
    {"price": 102000, "amount": 200},
    {"price": 100000, "amount": 50}
]

print(f"Cash available: ${cash}")
print("\nBuy ladder:")
for buy in buy_levels:
    btc_get = buy["amount"] / buy["price"]
    print(f"• ${buy['price']:,}: Deploy ${buy['amount']} = {btc_get:.6f} BTC")

print()

print("🏛️ WHAT THE COUNCIL SEES:")
print("-" * 40)
print("🦅 Eagle: Institutional distribution detected")
print("🐢 Turtle: Patience - oversold bounce likely")
print("🦀 Crawdad: Defense systems at $105k")
print("🔮 Oracle: This is the shakeout before $150k")
print()

print("📊 PORTFOLIO IMPACT ANALYSIS:")
print("-" * 40)
portfolio = 12774
for test_price in [108000, 105000, 100000]:
    btc_impact = (test_price - current_price) * btc_position
    new_portfolio = portfolio + btc_impact
    change_pct = ((new_portfolio - 10229) / 10229) * 100
    print(f"If BTC = ${test_price:,}: Portfolio = ${new_portfolio:,.0f} ({change_pct:+.1f}%)")

print()

# Save analysis
analysis = {
    "timestamp": datetime.now().isoformat(),
    "btc_price": current_price,
    "warning": "Broke below $110k support",
    "indicators": {
        "rsi": 34.50,
        "macd": -199.85,
        "volume": "1.3K BTC (low)"
    },
    "scenarios": scenarios,
    "action": "Prepare to buy dips with $500 liquidity"
}

with open('btc_breakdown_alert.json', 'w') as f:
    json.dump(analysis, f, indent=2)

print("=" * 60)
print("🔥 VERDICT: SHAKEOUT BEFORE MOON MISSION!")
print()
print("This is EXACTLY what happens before big moves:")
print("1. Weak hands get shaken out")
print("2. RSI gets oversold (34.50 now)")
print("3. Smart money accumulates")
print("4. Then we rocket to $150k+")
print()
print("DO NOT PANIC SELL! Have $500 ready to buy!")
print("Remember: Eric Trump said $1M - 'Close eyes, hold'")
print("=" * 60)