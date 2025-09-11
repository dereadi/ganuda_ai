#!/usr/bin/env python3
"""
Calculate real portfolio value with all positions
"""

# Your actual positions
positions = {
    "SOL": 12.15,
    "ETH": 0.55,
    "XRP": 215,
    "DOGE": 745,
    "MATIC": 425,
    "AVAX": 13.5,
    "LINK": 18,
    "USD": 500
}

# Current prices (approximate)
prices = {
    "SOL": 206,
    "ETH": 3245,
    "XRP": 2.31,
    "DOGE": 0.335,
    "MATIC": 0.68,
    "AVAX": 28.50,
    "LINK": 14.75,
    "USD": 1
}

print("📊 PORTFOLIO CALCULATION")
print("=" * 50)

total = 0
for coin, amount in positions.items():
    price = prices[coin]
    value = amount * price
    total += value
    print(f"{coin:6} {amount:8.2f} × ${price:8.2f} = ${value:10.2f}")

print("=" * 50)
print(f"TOTAL: ${total:,.2f}")
print()

# You said portfolio is worth $12,774
actual_value = 12774
difference = actual_value - total

print(f"Expected value: ${actual_value:,.2f}")
print(f"Calculated:     ${total:,.2f}")
print(f"Difference:     ${difference:,.2f}")
print()

if difference > 100:
    print("Missing positions or price differences!")
    print("Likely missing:")
    # Could be BTC, more ETH, or other alts
    possible_btc = difference / 108542
    possible_eth = difference / 3245
    possible_sol = difference / 206
    
    print(f"  - BTC: {possible_btc:.6f} BTC")
    print(f"  - ETH: {possible_eth:.3f} ETH")
    print(f"  - SOL: {possible_sol:.2f} SOL")