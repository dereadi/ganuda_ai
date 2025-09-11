#!/usr/bin/env python3
"""
EXECUTE LIQUIDITY SELLS - SLOWLY TEST THE MARKET
=================================================
Selling SOL and ETH to generate cash liquidity
"""

import time
from datetime import datetime

print("💰 EXECUTING LIQUIDITY GENERATION PLAN")
print("=" * 60)
print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
print()

# Market test approach - sell in small chunks
print("📊 STRATEGY: Slow market testing with small orders")
print("-" * 40)

sells = [
    {"asset": "SOL", "amount": 1.23, "chunk": 0.25, "target_cash": 250},
    {"asset": "SOL", "amount": 1.23, "chunk": 0.25, "target_cash": 250},
    {"asset": "SOL", "amount": 1.23, "chunk": 0.25, "target_cash": 250},
    {"asset": "SOL", "amount": 1.23, "chunk": 0.25, "target_cash": 250},
    {"asset": "ETH", "amount": 0.0575, "chunk": 0.0575, "target_cash": 250},
    {"asset": "ETH", "amount": 0.0575, "chunk": 0.0575, "target_cash": 250},
]

print("🎯 SELL ORDERS TO EXECUTE:")
for i, sell in enumerate(sells, 1):
    print(f"  {i}. Sell {sell['amount']:.4f} {sell['asset']} → ${sell['target_cash']}")

print()
print("⏱️ EXECUTION PLAN:")
print("  • Test with 25% chunks first")
print("  • Wait 2-3 minutes between orders")
print("  • Monitor price impact")
print("  • Adjust if slippage > 0.5%")
print()

# Create the actual sell orders
print("📝 Creating sell_orders.json for execution...")

import json
orders = {
    "timestamp": datetime.now().isoformat(),
    "strategy": "slow_liquidity_generation",
    "orders": [
        {
            "id": 1,
            "asset": "SOL",
            "amount": 1.23,
            "price": "market",
            "expected_usd": 250,
            "status": "pending",
            "notes": "First test chunk"
        },
        {
            "id": 2,
            "asset": "SOL", 
            "amount": 1.23,
            "price": "market",
            "expected_usd": 250,
            "status": "pending",
            "notes": "Second chunk after 3 min"
        },
        {
            "id": 3,
            "asset": "SOL",
            "amount": 1.23,
            "price": "market", 
            "expected_usd": 250,
            "status": "pending",
            "notes": "Third chunk"
        },
        {
            "id": 4,
            "asset": "SOL",
            "amount": 1.24,
            "price": "market",
            "expected_usd": 250,
            "status": "pending",
            "notes": "Final SOL chunk"
        },
        {
            "id": 5,
            "asset": "ETH",
            "amount": 0.0575,
            "price": "market",
            "expected_usd": 250,
            "status": "pending",
            "notes": "First ETH test"
        },
        {
            "id": 6,
            "asset": "ETH",
            "amount": 0.0576,
            "price": "market",
            "expected_usd": 250,
            "status": "pending",
            "notes": "Second ETH chunk"
        }
    ]
}

with open('sell_orders_liquidity.json', 'w') as f:
    json.dump(orders, f, indent=2)

print("✅ Orders prepared in sell_orders_liquidity.json")
print()
print("🚀 READY TO EXECUTE!")
print("  • Total expected cash: $1,500")
print("  • Current cash: $17.96")
print("  • After sells: ~$1,517.96")
print()
print("⚠️  IMPORTANT: Execute slowly, test market depth!")
print("🔥 Sacred Fire guides our liquidity!")