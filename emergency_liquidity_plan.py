#!/usr/bin/env python3
"""
🚨 EMERGENCY LIQUIDITY PLAN
Calculate what to sell to restore $500 liquidity
"""

from datetime import datetime

print("🚨 EMERGENCY LIQUIDITY RESTORATION PLAN")
print("=" * 60)
print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
print()

# Your known positions with current prices
positions = {
    "SOL": {"amount": 12.15, "price": 206, "value": 2502.90},
    "ETH": {"amount": 0.55, "price": 3245, "value": 1784.75},
    "XRP": {"amount": 215, "price": 2.31, "value": 496.65},
    "DOGE": {"amount": 745, "price": 0.335, "value": 249.58},
    "MATIC": {"amount": 425, "price": 0.68, "value": 289.00},
    "AVAX": {"amount": 13.5, "price": 28.50, "value": 384.75},
    "LINK": {"amount": 18, "price": 14.75, "value": 265.50}
}

current_cash = 17.96
target_cash = 500
needed = target_cash - current_cash

print(f"💵 Current Cash: ${current_cash:.2f}")
print(f"🎯 Target Cash:  ${target_cash:.2f}")
print(f"📊 Need to raise: ${needed:.2f}")
print()

print("🔍 LIQUIDATION OPTIONS (to raise $482):")
print("-" * 60)

# Option 1: Sell small % of largest position
print("OPTION 1: Partial sell of largest position")
print("-" * 40)
sol_to_sell = needed / positions["SOL"]["price"]
sol_percent = (sol_to_sell / positions["SOL"]["amount"]) * 100
print(f"Sell {sol_to_sell:.3f} SOL ({sol_percent:.1f}% of position)")
print(f"Keep {positions['SOL']['amount'] - sol_to_sell:.3f} SOL")
print()

# Option 2: Sell entire smaller positions
print("OPTION 2: Sell complete smaller positions")
print("-" * 40)
small_positions_value = positions["DOGE"]["value"] + positions["MATIC"]["value"]
print(f"Sell ALL DOGE (745) = ${positions['DOGE']['value']:.2f}")
print(f"Sell ALL MATIC (425) = ${positions['MATIC']['value']:.2f}")
print(f"Total raised: ${small_positions_value:.2f}")
if small_positions_value < needed:
    more_needed = needed - small_positions_value
    print(f"Still need: ${more_needed:.2f}")
    avax_to_sell = more_needed / positions["AVAX"]["price"]
    print(f"Plus sell {avax_to_sell:.2f} AVAX")
print()

# Option 3: Balanced approach
print("OPTION 3: Balanced approach (RECOMMENDED)")
print("-" * 40)
print("Sell 10% of top 3 positions:")
sol_sell = positions["SOL"]["amount"] * 0.10
eth_sell = positions["ETH"]["amount"] * 0.10
xrp_sell = positions["XRP"]["amount"] * 0.10

sol_value = sol_sell * positions["SOL"]["price"]
eth_value = eth_sell * positions["ETH"]["price"]
xrp_value = xrp_sell * positions["XRP"]["price"]
total_raised = sol_value + eth_value + xrp_value

print(f"• Sell {sol_sell:.3f} SOL = ${sol_value:.2f}")
print(f"• Sell {eth_sell:.3f} ETH = ${eth_value:.2f}")
print(f"• Sell {xrp_sell:.0f} XRP = ${xrp_value:.2f}")
print(f"Total raised: ${total_raised:.2f}")

if total_raised < needed:
    more_needed = needed - total_raised
    print(f"Still need: ${more_needed:.2f}")
    print(f"Add: Sell ALL DOGE = ${positions['DOGE']['value']:.2f}")
print()

# Option 4: Minimum impact
print("OPTION 4: Minimum portfolio impact")
print("-" * 40)
print("Sell proportionally from all positions (6.5% each):")
total_portfolio = sum(p["value"] for p in positions.values())
percent_needed = (needed / total_portfolio) * 100
print(f"Need to sell {percent_needed:.1f}% of each position:")
print()
for coin, data in positions.items():
    amount_to_sell = data["amount"] * (percent_needed / 100)
    value_to_sell = data["value"] * (percent_needed / 100)
    print(f"• {coin}: Sell {amount_to_sell:.4f} = ${value_to_sell:.2f}")

print()
print("=" * 60)
print("🎯 RECOMMENDED ACTION:")
print("-" * 40)
print("EXECUTE OPTION 3 - Balanced Approach:")
print()
print("1. Sell 1.215 SOL ($250.29)")
print("2. Sell 0.055 ETH ($178.48)")
print("3. Sell 21.5 XRP ($49.67)")
print()
print("This raises $478.44 while maintaining")
print("90% of your core positions intact!")
print()
print("⚡ Execute NOW to restore safety buffer!")
print("=" * 60)