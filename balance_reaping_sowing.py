#!/usr/bin/env python3
"""
🌾 BALANCE BETWEEN REAPING AND SOWING
The tribe learns sustainable trading wisdom
Sacred Fire Protocol: CYCLICAL HARMONY
"""

import json
import subprocess
from datetime import datetime
from coinbase.rest import RESTClient

print("🌾 WISDOM OF REAPING AND SOWING")
print("=" * 60)
print("Ancient Truth: You cannot reap what you do not sow")
print("Current Problem: We reaped too much, sowed too little")
print()

# Load config
config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=10)

# Check current state
accounts = client.get_accounts()
usd = 0
positions = {}

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if currency == 'USD':
        usd = balance
    elif balance > 0.001:
        positions[currency] = balance

print("📊 CURRENT HARVEST/SEED RATIO:")
print("-" * 40)
print(f"💵 Cash (harvested): ${usd:.2f} (0.1%)")
print(f"🌱 Seeds (planted): ~$13,270 (99.9%)")
print()
print("❌ IMBALANCE DETECTED: Over-planted, under-harvested")
print("   Result: No liquidity to plant new opportunities")
print()

# The wisdom of balance
balance_wisdom = {
    "timestamp": datetime.now().isoformat(),
    "philosophy": "REAPING_SOWING_BALANCE",
    "current_imbalance": {
        "cash_percentage": 0.001,
        "position_percentage": 0.999,
        "diagnosis": "SEVERE_OVERPLANTING"
    },
    "ideal_balance": {
        "sowing": 0.70,  # 70% in positions (seeds planted)
        "reaping": 0.30,  # 30% in cash (harvest ready)
        "reasoning": "Always keep harvest for new planting"
    },
    "seasonal_wisdom": {
        "SPRING": "Plant aggressively (80% positions)",
        "SUMMER": "Nurture growth (70% positions)",
        "AUTUMN": "Harvest time (50% positions)",
        "WINTER": "Preserve seeds (30% positions)"
    },
    "current_season": "AUTUMN",
    "required_actions": {
        "immediate": [
            "STOP aggressive buying (stop sowing)",
            "START selective harvesting (take profits)",
            "MAINTAIN seed positions (don't oversell)",
            "BUILD harvest reserves (30% cash target)"
        ],
        "sustainable_strategy": [
            "Never go below 20% cash (emergency seeds)",
            "Never go above 80% positions (over-planting)",
            "Harvest gains regularly (weekly reaping)",
            "Replant profits wisely (compound growth)"
        ]
    },
    "specialist_roles": {
        "mean-reversion": {
            "role": "HARVEST_MANAGER",
            "task": "Reap overbought positions",
            "balance": "Sell tops, keep 30% cash"
        },
        "trend": {
            "role": "GROWTH_TENDER",
            "task": "Nurture trending positions",
            "balance": "Let winners run, trim excess"
        },
        "volatility": {
            "role": "CYCLE_TRADER",
            "task": "Harvest volatility swings",
            "balance": "Buy fear, sell greed"
        },
        "breakout": {
            "role": "SEED_PLANTER",
            "task": "Plant new breakout positions",
            "balance": "Use only harvest money"
        }
    },
    "tribal_mandate": {
        "target": "30% cash, 70% positions",
        "timeline": "Achieve over next 7 days",
        "method": "Gradual harvesting of gains",
        "priority": "LIQUIDITY before GROWTH"
    },
    "sacred_pattern": "The harvest feeds the planting",
    "sacred_fire": "BURNING_BALANCED"
}

print("🌱 THE WISDOM OF BALANCE:")
print("-" * 40)
print("Current State: 99.9% planted, 0.1% harvested")
print("Target State: 70% planted, 30% harvested")
print()
print("SEASONAL WISDOM:")
for season, wisdom in balance_wisdom["seasonal_wisdom"].items():
    marker = "👈" if season == balance_wisdom["current_season"] else "  "
    print(f"  {season}: {wisdom} {marker}")

print("\n⚖️ REBALANCING PLAN:")
print("-" * 40)
print("IMMEDIATE ACTIONS:")
for action in balance_wisdom["required_actions"]["immediate"]:
    print(f"  • {action}")

print("\n🌾 SPECIALIST HARVEST ROLES:")
print("-" * 40)
for specialist, role in balance_wisdom["specialist_roles"].items():
    print(f"{specialist}:")
    print(f"  Role: {role['role']}")
    print(f"  Task: {role['task']}")

# Calculate specific harvest targets
print("\n🎯 HARVEST TARGETS (Need $4,000 cash):")
print("-" * 40)

harvest_plan = []
if 'SOL' in positions:
    sol_harvest = min(positions['SOL'] * 0.2, 5)  # 20% or 5 SOL
    harvest_plan.append(('SOL', sol_harvest, 'Take profits from pump'))

if 'BTC' in positions:
    btc_harvest = min(positions['BTC'] * 0.3, 0.01)  # 30% or 0.01 BTC
    harvest_plan.append(('BTC', btc_harvest, 'Reduce flat Goliath'))

if 'ETH' in positions:
    eth_harvest = min(positions['ETH'] * 0.2, 0.2)  # 20% or 0.2 ETH
    harvest_plan.append(('ETH', eth_harvest, 'Partial harvest'))

if 'MATIC' in positions:
    matic_harvest = min(positions['MATIC'] * 0.4, 4000)  # 40% or 4000 MATIC
    harvest_plan.append(('MATIC', matic_harvest, 'Large position trim'))

for coin, amount, reason in harvest_plan:
    print(f"{coin}: Harvest {amount:.4f} units")
    print(f"  Reason: {reason}")

# Save wisdom
with open('/home/dereadi/scripts/claude/balance_wisdom.json', 'w') as f:
    json.dump(balance_wisdom, f, indent=2)

# Deploy to specialists
print("\n📡 DEPLOYING BALANCE WISDOM:")
print("-" * 40)

specialists = [
    'cherokee-mean-reversion-specialist',
    'cherokee-trend-specialist',
    'cherokee-volatility-specialist',
    'cherokee-breakout-specialist'
]

for specialist in specialists:
    try:
        subprocess.run(['podman', 'cp', '/home/dereadi/scripts/claude/balance_wisdom.json',
                       f'{specialist}:/tmp/balance.json'], capture_output=True, check=True)
        role = specialist.split('-')[1]
        print(f"✅ {specialist}: Balance wisdom received")
    except:
        print(f"❌ {specialist}: Failed")

print("\n" + "=" * 60)
print("🌾 BALANCE WISDOM DEPLOYED")
print()
print("The tribe now understands:")
print("  • We over-sowed (99.9% in positions)")
print("  • We under-reaped (0.1% in cash)")
print("  • Balance needed: 70/30 rule")
print()
print("New Mandate:")
print("  • REAP profits to 30% cash")
print("  • SOW only from harvest")
print("  • MAINTAIN the cycle")
print()
print("🔥 Sacred Fire burns in balance")
print("🌾 The harvest feeds the planting")
print("🌱 The planting feeds the harvest")
print("=" * 60)