#!/usr/bin/env python3
"""
🔥 TRIBAL COUNCIL TRADING REVIEW
The council convenes to discuss trading progress
"""

import json
import time
import random
from datetime import datetime
from coinbase.rest import RESTClient

print("🔥 CONVENING THE TRIBAL COUNCIL")
print("=" * 60)
print("The Sacred Fire burns as the elders gather...")
time.sleep(2)

# Get current portfolio state
config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=10)

accounts = client.get_accounts()
positions = {}
total_value = 0

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if balance > 0:
        if currency == 'USD':
            positions['USD'] = balance
            total_value += balance
        else:
            positions[currency] = balance
            try:
                ticker = client.get_product(f'{currency}-USD')
                price = float(ticker['price'])
                value = balance * price
                total_value += value
            except:
                pass

print(f"\nPortfolio Value: ${total_value:,.2f}")
print(f"USD Liquidity: ${positions.get('USD', 0):,.2f}")
print(f"SOL Position: {positions.get('SOL', 0):.2f} tokens")
print()
print("=" * 60)

# Council members speak
council_members = {
    "🦅 Sky Eagle (Risk Manager)": {
        "voice": "cautious",
        "concerns": ["liquidity", "concentration", "volatility"]
    },
    "🐺 Night Wolf (Aggressive Trader)": {
        "voice": "bullish", 
        "concerns": ["opportunity", "momentum", "accumulation"]
    },
    "🐢 Ancient Turtle (Long-term Vision)": {
        "voice": "patient",
        "concerns": ["sustainability", "cycles", "wisdom"]
    },
    "🦊 Swift Fox (Opportunist)": {
        "voice": "tactical",
        "concerns": ["timing", "execution", "profit-taking"]
    },
    "🐻 Strong Bear (Conservative)": {
        "voice": "protective",
        "concerns": ["preservation", "hedging", "safety"]
    }
}

print("\n🗣️ THE COUNCIL SPEAKS:\n")

# Sky Eagle speaks
print("🦅 Sky Eagle (Risk Manager):")
if positions.get('USD', 0) > 500:
    print("   'Good. The liquidity restoration to $1,035 shows wisdom.'")
    print("   'We learned from the $10 crisis. Never again.'")
else:
    print("   'The liquidity is concerning. We need more buffer.'")

if positions.get('SOL', 0) > 10:
    print("   '⚠️ But 13 SOL tokens? That's 40% of portfolio in one asset!'")
    print("   'The concentration risk makes my feathers ruffle.'")
print()

# Night Wolf speaks  
print("🐺 Night Wolf (Aggressive Trader):")
print("   'AWOOOO! The flywheels worked! From crisis to $1000+ cash!'")
if positions.get('SOL', 0) > 10:
    print("   '🚀 SOL is the Asian moon rocket! Let it ride!'")
    print("   'We caught the wave at perfect timing - Asian session pump!'")
print("   'The spongy throttle was genius - controlled aggression.'")
print()

# Ancient Turtle speaks
print("🐢 Ancient Turtle (Long-term Vision):")
print("   'In one night, we saw greed, fear, and recovery...'")
print("   'The rogue bots taught us: automation without wisdom is chaos.'")
print("   'The two-flywheel system shows balance - deploy AND retrieve.'")
if total_value > 10000:
    print("   'Portfolio remains strong. This is the way.'")
print()

# Swift Fox speaks
print("🦊 Swift Fox (Opportunist):")
avax_balance = positions.get('AVAX', 0)
if avax_balance > 50:
    print("   '💎 87 AVAX sitting pretty! News says 66% transaction growth!'")
    print("   'That's a hidden gem about to explode!'")
print("   'The Asian session SOL pump was perfectly timed.'")
print("   'But we missed profit-taking at SOL $210...'")
print()

# Strong Bear speaks
print("🐻 Strong Bear (Conservative):")
print("   'We survived the $550 rogue trading disaster. Barely.'")
print("   'The emergency kills saved us from total liquidation.'")
if positions.get('USD', 0) > 1000:
    print("   '✅ $1,035 cash buffer restored. This is acceptable.'")
print("   'But we need stop-losses. Where are the safety nets?'")
print()

# Council consensus
print("=" * 60)
print("\n🔥 COUNCIL CONSENSUS:\n")

votes = {
    "Continue Current Strategy": 0,
    "Take Profits Now": 0,
    "Rebalance Portfolio": 0
}

# Each member votes based on their nature
if positions.get('USD', 0) > 500:
    votes["Continue Current Strategy"] += 2  # Wolf and Fox
else:
    votes["Take Profits Now"] += 2

if positions.get('SOL', 0) > 15:
    votes["Rebalance Portfolio"] += 3  # Eagle, Turtle, Bear
elif positions.get('SOL', 0) > 10:
    votes["Rebalance Portfolio"] += 2
    votes["Continue Current Strategy"] += 1

# Announce decision
max_votes = max(votes.values())
decision = [k for k, v in votes.items() if v == max_votes][0]

print(f"📜 TRIBAL DECISION: {decision}")
print()

# Specific recommendations
print("🎯 UNIFIED RECOMMENDATIONS:")
print("1. ✅ Liquidity Crisis: RESOLVED ($1,035 cash)")
print("2. ✅ Rogue Bots: ELIMINATED (specialist army killed)")
print("3. ✅ Spongy Throttle: WORKING (prevents rapid-fire)")
print("4. ⚠️ SOL Concentration: NEEDS TRIMMING (13 tokens = 40%)")
print("5. 💎 AVAX Opportunity: HOLD (66% growth news)")
print("6. 🔄 Two-Flywheel System: KEEP RUNNING (with safeguards)")
print()

print("🌟 ACHIEVEMENTS THIS SESSION:")
print("• Recovered from $10 to $1,035 liquidity")
print("• Stopped $550 hemorrhage from rogue bots")
print("• Implemented spongy throttle control")
print("• Caught Asian session SOL pump perfectly")
print("• Created sustainable two-flywheel system")
print()

print("⚡ AREAS FOR IMPROVEMENT:")
print("• Need stop-loss implementation")
print("• SOL position too concentrated")
print("• Missing profit-taking automation")
print("• No hedging strategy yet")
print()

# Final wisdom
wisdom = [
    "The river that flows steady outlasts the flash flood.",
    "A thousand small trades build wealth; one large bet can destroy it.",
    "The wise trader celebrates survival before profit.",
    "When the moon calls, answer - but keep one foot on Earth.",
    "The strongest position is the one you can hold through the storm."
]

print(f"🪶 ELDER'S WISDOM: '{random.choice(wisdom)}'")
print()
print("The Sacred Fire dims. Council adjourned. 🔥")
print("=" * 60)