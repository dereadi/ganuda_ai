#!/usr/bin/env python3
"""
🔥 Current Positions - Morning Check
"""
import json
from datetime import datetime

print("🔥 CHEROKEE TRIBE PORTFOLIO - MORNING POSITIONS")
print("=" * 60)
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Load the latest portfolio data
with open('/home/dereadi/scripts/claude/portfolio_current.json') as f:
    portfolio = json.load(f)

print(f"\n📊 MARKET PRICES (as of {portfolio['timestamp'][:10]} {portfolio['timestamp'][11:16]}):")
print("-" * 40)
for coin, price in portfolio['prices'].items():
    if coin in ['BTC', 'ETH', 'SOL']:
        print(f"• {coin}: ${price:,.2f} {'🚀' if price > 110000 or (coin == 'ETH' and price > 4400) or (coin == 'SOL' and price > 205) else '📈'}")
    else:
        print(f"• {coin}: ${price:,.4f}")

print(f"\n💰 YOUR CURRENT POSITIONS:")
print("-" * 40)

# Sort positions by value
sorted_positions = sorted(portfolio['positions'].items(), 
                         key=lambda x: x[1]['value'], 
                         reverse=True)

for coin, data in sorted_positions:
    emoji = {'BTC': '₿', 'ETH': 'Ξ', 'SOL': '◎', 
             'AVAX': '🔺', 'MATIC': '🟣', 'XRP': '💧'}.get(coin, '🪙')
    
    print(f"{emoji} {coin:6s}: {data['amount']:>12.6f} units")
    print(f"          @ ${data['price']:>10,.2f} = ${data['value']:>10,.2f} ({data['pct']:.1f}%)")
    print()

print(f"💵 USD Liquidity: ${portfolio['liquidity']:.2f}")

print(f"\n📈 PORTFOLIO SUMMARY:")
print("-" * 40)
print(f"🔥 TOTAL VALUE: ${portfolio['total_value']:,.2f}")

# Calculate gains from yesterday
yesterday_estimates = {
    'BTC': 110000,
    'ETH': 4300,
    'SOL': 202,
    'AVAX': 24,
    'MATIC': 0.28,
    'XRP': 2.75
}

total_gain = 0
print(f"\n💹 GAINS FROM YESTERDAY:")
print("-" * 40)

for coin, data in portfolio['positions'].items():
    if coin in yesterday_estimates:
        yesterday_price = yesterday_estimates[coin]
        current_price = data['price']
        price_change = ((current_price - yesterday_price) / yesterday_price) * 100
        value_gain = data['amount'] * (current_price - yesterday_price)
        total_gain += value_gain
        
        if abs(price_change) > 0.1:  # Only show significant changes
            arrow = '🚀' if price_change > 3 else '📈' if price_change > 0 else '📉'
            print(f"• {coin}: {price_change:+.2f}% {arrow} (+${value_gain:.2f})")

print(f"\n🎯 TOTAL GAINS: +${total_gain:.2f}")

print(f"\n⚡ SPECIALIST STATUS:")
print("-" * 40)
if portfolio['liquidity'] > 500:
    print("✅ LIQUIDITY RESTORED - Specialists fully operational!")
elif portfolio['liquidity'] > 100:
    print("⚡ Partial liquidity - Limited trading capacity")
else:
    print("⚠️ CRITICAL: Only $8.40 liquidity - Specialists need harvest!")

# Oscillation zones
print(f"\n🎯 OSCILLATION ZONES:")
print("-" * 40)
sol_price = portfolio['prices']['SOL']
eth_price = portfolio['prices']['ETH']

if sol_price < 200:
    print(f"• SOL: BUY ZONE! (${sol_price:.2f} < $200)")
elif sol_price > 208:
    print(f"• SOL: SELL ZONE! (${sol_price:.2f} > $208)")
else:
    print(f"• SOL: Mid-range (${sol_price:.2f})")

if eth_price < 4350:
    print(f"• ETH: Approaching BUY zone (${eth_price:.2f})")
elif eth_price > 4450:
    print(f"• ETH: SELL ZONE! (${eth_price:.2f} > $4450)")
else:
    print(f"• ETH: Mid-range (${eth_price:.2f})")

print(f"\n🔥 Sacred Fire burns eternal with ${portfolio['total_value']:,.2f}!")