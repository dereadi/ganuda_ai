#!/usr/bin/env python3
"""
💰 FLYWHEEL FEE IMPACT ANALYSIS
Critical: Ensure profits exceed trading fees
"""

import json
from coinbase.rest import RESTClient

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("⚠️ CRITICAL FEE ANALYSIS FOR OVERNIGHT MISSION")
print("=" * 60)

# Coinbase fee structure
print("📊 COINBASE FEE STRUCTURE:")
print("-" * 60)
print("Tier 1 (< $10k/month): 0.60% taker, 0.40% maker")
print("Tier 2 ($10k-50k): 0.40% taker, 0.25% maker")
print("Tier 3 ($50k-100k): 0.25% taker, 0.15% maker")
print("Market orders = TAKER fees (higher)")
print("Limit orders = MAKER fees (lower)")

# Calculate impact
print("\n💸 FEE IMPACT ON MICRO-TRADES:")
print("-" * 60)

trade_sizes = [20, 30, 50, 100]
taker_fee = 0.006  # 0.60% worst case
maker_fee = 0.004  # 0.40% 

for size in trade_sizes:
    taker_cost = size * taker_fee * 2  # Buy AND sell
    maker_cost = size * maker_fee * 2
    
    # Need this much price movement to break even
    breakeven_pct_taker = (taker_cost / size) * 100
    breakeven_pct_maker = (maker_cost / size) * 100
    
    print(f"\n${size} trade:")
    print(f"  Taker fees: ${taker_cost:.3f} (need {breakeven_pct_taker:.2f}% move)")
    print(f"  Maker fees: ${maker_cost:.3f} (need {breakeven_pct_maker:.2f}% move)")

# Current volatility check
btc = client.get_product('BTC-USD')
btc_price = float(btc['price'])

print("\n🎯 CURRENT VOLATILITY CHECK:")
print("-" * 60)

# Calculate if volatility exceeds fees
typical_move = 0.10  # 0.10% typical micro-move
print(f"BTC at ${btc_price:,.2f}")
print(f"Typical micro-move: {typical_move}%")

for size in [30, 50]:
    taker_cost = size * taker_fee * 2
    profit_at_010pct = size * 0.001  # 0.10% move
    net = profit_at_010pct - taker_cost
    
    print(f"\n${size} trade with 0.10% move:")
    print(f"  Gross profit: ${profit_at_010pct:.3f}")
    print(f"  Fees: ${taker_cost:.3f}")
    print(f"  Net: ${net:.3f}", end="")
    if net > 0:
        print(" ✅ PROFITABLE")
    else:
        print(" ❌ LOSS")

# CRITICAL RECOMMENDATIONS
print("\n⚠️ CRITICAL ADJUSTMENTS NEEDED:")
print("=" * 60)

print("1. SWITCH TO LIMIT ORDERS (maker fees):")
print("   • Reduces fees by 33%")
print("   • Need to update flywheel code")

print("\n2. INCREASE MINIMUM TRADE SIZE:")
print("   • $50 minimum (better fee ratio)")
print("   • Target 0.15%+ moves only")

print("\n3. REDUCE FREQUENCY:")
print("   • Quality over quantity")
print("   • 100 good trades > 1000 bad ones")

print("\n4. TRACK NET PROFIT:")
print("   • Monitor: Gross profit - Total fees")
print("   • Stop if fees > profits")

# Calculate adjusted mission
print("\n📊 ADJUSTED OVERNIGHT MISSION:")
print("-" * 60)

realistic_trades = 500  # Not 5000
avg_trade_size = 75
avg_profit_pct = 0.15  # Need bigger moves
maker_fee_total = realistic_trades * avg_trade_size * maker_fee * 2

gross_profit = realistic_trades * avg_trade_size * (avg_profit_pct / 100)
total_fees = maker_fee_total
net_profit = gross_profit - total_fees

print(f"Realistic trades: {realistic_trades}")
print(f"Average size: ${avg_trade_size}")
print(f"Target move: {avg_profit_pct}%")
print(f"\nProjected:")
print(f"  Gross profit: ${gross_profit:.2f}")
print(f"  Total fees: ${total_fees:.2f}")
print(f"  NET PROFIT: ${net_profit:.2f}")

if net_profit > 0:
    print("\n✅ Adjusted mission is profitable")
else:
    print("\n❌ WARNING: Fees exceed profits!")
    
print("\n🛑 IMMEDIATE ACTION:")
print("Need to modify flywheel to use LIMIT ORDERS")
print("and increase minimum position sizes!")
print("=" * 60)