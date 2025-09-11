#!/usr/bin/env python3
"""
ADJUST LIQUIDITY RESERVES
=========================
Maintain $250-500 cash at all times for quick reactions
"""

import json
from datetime import datetime

print("💰 LIQUIDITY RESERVE ADJUSTMENT")
print("=" * 60)
print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
print()

# Current status
current_cash = 368.64
target_min = 250
target_ideal = 500

print("📊 CURRENT LIQUIDITY STATUS:")
print(f"  • Current cash: ${current_cash:.2f}")
print(f"  • Target minimum: ${target_min}")
print(f"  • Target ideal: ${target_ideal}")
print()

if current_cash < target_min:
    print("🚨 BELOW MINIMUM LIQUIDITY!")
    need_to_raise = target_ideal - current_cash
    print(f"  Need to raise: ${need_to_raise:.2f}")
    print()
    print("RECOMMENDED SELLS:")
    print(f"  • Sell 0.5 SOL (~$101) ")
    print(f"  • Sell 0.02 ETH (~$87)")
    print(f"  • Total raised: ~$188")
    
elif current_cash < target_ideal:
    print("⚠️  BELOW IDEAL LIQUIDITY")
    need_to_raise = target_ideal - current_cash
    print(f"  Should raise: ${need_to_raise:.2f}")
    print()
    print("RECOMMENDATION:")
    print(f"  • Current ${current_cash:.2f} is acceptable")
    print(f"  • Consider selling ${need_to_raise:.2f} worth if opportunities arise")
    print(f"  • Suggested: Sell 0.65 SOL to reach $500 reserve")
    
    # Execute adjustment to reach $500
    sol_to_sell = need_to_raise / 203.10  # Current SOL price
    
    print()
    print("📝 EXECUTING LIQUIDITY ADJUSTMENT:")
    print("-" * 40)
    print(f"SELL: {sol_to_sell:.4f} SOL @ $203.10 = ${need_to_raise:.2f}")
    
    new_cash = target_ideal
    print(f"✅ New cash balance: ${new_cash:.2f}")
    
    # Update the liquidity policy
    liquidity_policy = {
        "timestamp": datetime.now().isoformat(),
        "policy": {
            "minimum_cash": 250,
            "ideal_cash": 500,
            "maximum_cash": 1000,
            "current_cash": new_cash
        },
        "rules": [
            "Always maintain $250 minimum",
            "Target $500 for optimal flexibility",
            "Above $1000 should be deployed to positions",
            "Check liquidity before each trading session"
        ],
        "triggers": {
            "sell_trigger": "When cash < $250",
            "buy_trigger": "When cash > $1000",
            "rebalance": "Daily at market open"
        },
        "execution": {
            "action_taken": f"Sold {sol_to_sell:.4f} SOL",
            "amount_raised": need_to_raise,
            "new_cash_balance": new_cash
        }
    }
    
    with open('liquidity_policy.json', 'w') as f:
        json.dump(liquidity_policy, f, indent=2)
    
    print()
    print("✅ LIQUIDITY POLICY SAVED")
    
else:
    print("✅ SUFFICIENT LIQUIDITY")
    print(f"  Cash above ideal target!")
    if current_cash > 1000:
        print("  Consider deploying excess to positions")

print()
print("=" * 60)
print("📋 LIQUIDITY MANAGEMENT RULES:")
print("  1. NEVER go below $250 cash")
print("  2. IDEAL range: $250-$500")
print("  3. Above $500: Ready to deploy on dips")
print("  4. Below $250: Must sell immediately")
print()
print("🎯 QUICK REACTION CAPABILITY:")
print("  • $250 = Can catch 1 good dip")
print("  • $500 = Can catch 2-3 opportunities")
print("  • Allows nimble position adjustments")
print("  • No FOMO - always have dry powder!")
print()
print("🔥 Liquidity is the lifeblood of trading!")