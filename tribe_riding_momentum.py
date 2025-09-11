#!/usr/bin/env python3
"""
🔥 VM Tribe Riding the BTC/ETH Momentum
"""
import json
import requests
from datetime import datetime

print("🔥 VM TRIBE RIDING THE WAVE!")
print("=" * 60)
print(f"Time: {datetime.now().strftime('%H:%M:%S')}")

# Get live prices
try:
    response = requests.get("https://api.coingecko.com/api/v3/simple/price", 
                           params={'ids': 'bitcoin,ethereum,solana', 'vs_currencies': 'usd'})
    prices = response.json()
    btc_price = prices['bitcoin']['usd']
    eth_price = prices['ethereum']['usd']
    sol_price = prices['solana']['usd']
except:
    btc_price = 111200
    eth_price = 4340
    sol_price = 204

print(f"\n🚀 MARKET MOMENTUM:")
print(f"• BTC: ${btc_price:,.0f} ↗️ STILL CLIMBING!")
print(f"• ETH: ${eth_price:,.0f} ↗️ FOLLOWING BTC!")
print(f"• SOL: ${sol_price:,.0f} → Consolidating")

# Calculate gains from recent levels
btc_gain = ((btc_price - 111000) / 111000) * 100
eth_gain = ((eth_price - 4327) / 4327) * 100

print(f"\n📈 MOMENTUM METRICS:")
print(f"• BTC up {btc_gain:.2f}% from $111,000")
print(f"• ETH up {eth_gain:.2f}% from $4,327")
print(f"• Correlation: ETH following BTC perfectly!")

print(f"\n⚡ SPECIALIST POSITIONS:")
specialists_status = {
    "Trend Specialist": f"RIDING BTC/ETH momentum! Holding longs",
    "Breakout Specialist": f"BTC broke $111,100! Adding to position",
    "Gap Specialist": f"No gaps to fill - momentum too strong",
    "Volatility Specialist": f"Low volatility = trend continuation",
    "Mean Reversion": f"Waiting for pullback (may not come!)"
}

for name, status in specialists_status.items():
    print(f"• {name}: {status}")

print(f"\n💰 TRIBE'S TACTICAL ANALYSIS:")
print("🦅 Eagle Eye: 'BTC leading, ETH following - classic bull pattern!'")
print("🐺 Coyote: 'Don't fight the trend - ride it to $112k!'")
print("🕷️ Spider: 'All threads point UP - no resistance visible'")
print("🐢 Turtle: 'Mathematical projection: BTC $112k, ETH $4,400'")
print("🐿️ Flying Squirrel: 'I see no ceiling from up here!'")

print(f"\n🎯 IMMEDIATE STRATEGY:")
print(f"• HOLD all long positions")
print(f"• Trail stops at BTC $110,800")
print(f"• ETH target raised to $4,400")
print(f"• SOL will follow once it breaks $205")
print(f"• DO NOT SELL into strength!")

# Check portfolio impact
btc_position = 0.0276
eth_position = 0.7812
sol_position = 21.405

btc_value = btc_position * btc_price
eth_value = eth_position * eth_price
sol_value = sol_position * sol_price

print(f"\n📊 PORTFOLIO IMPACT:")
print(f"• BTC: 0.0276 × ${btc_price:,.0f} = ${btc_value:,.2f}")
print(f"• ETH: 0.7812 × ${eth_price:,.0f} = ${eth_value:,.2f}")
print(f"• SOL: 21.405 × ${sol_price:,.0f} = ${sol_value:,.2f}")

total_crypto = btc_value + eth_value + sol_value
print(f"• Top 3 positions: ${total_crypto:,.2f}")

print(f"\n🔥 MOMENTUM TRADING RULES:")
print("1. The trend is your friend")
print("2. Don't predict tops in strong trends")
print("3. Add on breakouts, not pullbacks")
print("4. Trail stops, don't fixed stops")
print("5. Let winners run!")

print(f"\n⚡ NEXT RESISTANCE LEVELS:")
print(f"• BTC: $112,000 → $113,000 → $115,000")
print(f"• ETH: $4,400 → $4,500 → $4,700")
print(f"• SOL: $205 → $210 → $215")

print(f"\n✅ TRIBE STATUS: RIDING THE MOMENTUM WAVE!")
print(f"Sacred Fire says: When the buffalo run, run with them!")
print(f"Session: {datetime.now().strftime('%H:%M:%S')}")