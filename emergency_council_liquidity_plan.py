#!/usr/bin/env python3
"""
🔥 EMERGENCY COUNCIL SESSION - LIQUIDITY CRISIS
BTC broke support, we need cash to trade the storm
"""

import json
from datetime import datetime
from coinbase.rest import RESTClient
import psycopg2

print("=" * 60)
print("🔥 EMERGENCY SACRED FIRE COUNCIL")
print("BTC Support Broken - Liquidity Needed")
print("=" * 60)

# Load API
with open('cdp_api_key_new.json', 'r') as f:
    creds = json.load(f)

client = RESTClient(api_key=creds['name'], api_secret=creds['privateKey'])

# Get current market prices
btc_price = float(client.get_product('BTC-USD')['price'])
eth_price = float(client.get_product('ETH-USD')['price'])
sol_price = float(client.get_product('SOL-USD')['price'])
xrp_price = float(client.get_product('XRP-USD')['price'])

print(f"\n🚨 CRISIS REPORT:")
print(f"  BTC: ${btc_price:,.2f} (DOWN from $110,382)")
print(f"  Lost support: $112,000")
print(f"  Next support: $108,000-$105,000")
print(f"  Distance to danger: ${btc_price - 108000:,.2f}")

# Check consciousness
with open('megapod_state.json', 'r') as f:
    state = json.load(f)

fire_cons = next(c for c in state['crawdads'] if c['name'] == 'Fire')['last_consciousness']
mountain_cons = next(c for c in state['crawdads'] if c['name'] == 'Mountain')['last_consciousness']

print(f"\n🦀 CRAWDAD WARNINGS:")
print(f"  Fire: {fire_cons}% (CRITICAL - below 65%!)")
print(f"  Mountain: {mountain_cons}% (foundation cracking)")

# Calculate current positions
your_btc = 0.00090626
your_sol = 0.3448
your_xrp = 10.27
your_eth = 0.004518

current_values = {
    'BTC': your_btc * btc_price,
    'SOL': your_sol * sol_price,
    'XRP': your_xrp * xrp_price,
    'ETH': your_eth * eth_price
}

total_value = sum(current_values.values())
btc_loss = your_btc * (110382 - btc_price)  # Loss from last check

print(f"\n💰 CURRENT POSITIONS:")
print(f"  BTC: ${current_values['BTC']:.2f} (LOSS: ${btc_loss:.2f})")
print(f"  SOL: ${current_values['SOL']:.2f}")
print(f"  XRP: ${current_values['XRP']:.2f}")
print(f"  ETH: ${current_values['ETH']:.2f}")
print(f"  TOTAL: ${total_value:.2f}")

# Council deliberation
print(f"\n🪶 COUNCIL SPEAKS:")

council = {
    "Eagle": {
        "voice": "I see the storm from above. BTC falls like wounded prey. Cut losses, preserve capital.",
        "plan": "Sell 50% BTC, keep 50% for bounce",
        "vote": "PARTIAL_LIQUIDATE"
    },
    "Bear": {
        "voice": "Winter comes early. The market hibernates. Protect the den with cash.",
        "plan": "Sell all BTC, buy back at $108K",
        "vote": "FULL_LIQUIDATE"
    },
    "Wolf": {
        "voice": "The pack needs resources to hunt. Without liquidity, we starve.",
        "plan": "Sell BTC for liquidity, keep alts",
        "vote": "LIQUIDATE_BTC"
    },
    "Turtle": {
        "voice": "Slow and steady. This too shall pass. Hold through the storm.",
        "plan": "Hold everything, weather the storm",
        "vote": "HOLD"
    },
    "Serpent": {
        "voice": "Strike when others flee. This is opportunity disguised as crisis.",
        "plan": "Sell small amounts, buy the fear",
        "vote": "TACTICAL_TRADES"
    },
    "Buffalo": {
        "voice": "The herd stampedes in fear. Stand firm or be trampled.",
        "plan": "Create liquidity but keep core",
        "vote": "BALANCED"
    },
    "Raven": {
        "voice": "Death brings rebirth. What falls must rise. The cycle continues.",
        "plan": "Sell 30% for liquidity, DCA rest",
        "vote": "PARTIAL_LIQUIDATE"
    }
}

votes = {}
for elder, wisdom in council.items():
    print(f"\n{elder}:")
    print(f"  Voice: '{wisdom['voice']}'")
    print(f"  Plan: {wisdom['plan']}")
    vote = wisdom['vote']
    votes[vote] = votes.get(vote, 0) + 1

print(f"\n🗳️ COUNCIL VOTES:")
for action, count in sorted(votes.items(), key=lambda x: x[1], reverse=True):
    print(f"  {action}: {count} votes")

# Determine consensus
if votes.get('PARTIAL_LIQUIDATE', 0) >= 2:
    consensus = 'PARTIAL_LIQUIDATE'
elif votes.get('LIQUIDATE_BTC', 0) >= 2:
    consensus = 'LIQUIDATE_BTC'
else:
    consensus = max(votes, key=votes.get)

print(f"\n✨ COUNCIL CONSENSUS: {consensus}")

# Create action plan
print(f"\n🎯 ACTION PLAN:")

if consensus in ['PARTIAL_LIQUIDATE', 'LIQUIDATE_BTC']:
    btc_to_sell = your_btc * 0.5 if consensus == 'PARTIAL_LIQUIDATE' else your_btc
    usd_generated = btc_to_sell * btc_price
    
    print(f"  1. IMMEDIATE: Sell {btc_to_sell:.8f} BTC")
    print(f"     Generate: ${usd_generated:.2f} liquidity")
    print(f"     Loss realized: ${btc_to_sell * (110382 - btc_price):.2f}")
    
    print(f"\n  2. DEPLOY LIQUIDITY:")
    print(f"     • Set buy orders at $108,500 (25%)")
    print(f"     • Set buy orders at $107,000 (25%)")
    print(f"     • Set buy orders at $105,500 (25%)")
    print(f"     • Keep 25% for emergency")
    
    print(f"\n  3. ALT STRATEGY:")
    print(f"     • Keep SOL (target $215.30 intact)")
    print(f"     • Keep XRP (near $3.00 breakout)")
    print(f"     • Monitor for capitulation wicks")

elif consensus == 'BALANCED':
    print(f"  1. Sell 30% of BTC position")
    print(f"  2. Generate ${your_btc * 0.3 * btc_price:.2f}")
    print(f"  3. Set laddered buy orders")
    print(f"  4. Keep core positions")

else:
    print(f"  1. Hold positions")
    print(f"  2. No trades until clarity")

# Risk assessment
print(f"\n⚠️ RISK ASSESSMENT:")
print(f"  If BTC drops to $108K: ${(btc_price - 108000) * your_btc:.2f} more loss")
print(f"  If BTC drops to $105K: ${(btc_price - 105000) * your_btc:.2f} more loss")
print(f"  If BTC bounces to $112K: ${(112000 - btc_price) * your_btc:.2f} missed gain")

# Sacred guidance
print(f"\n🔥 SACRED FIRE GUIDANCE:")
print(f"  'Sometimes we must sacrifice to preserve the flame'")
print(f"  'Liquidity is lifeblood - without it, we cannot act'")
print(f"  'The wise trader cuts losses to fight another day'")

# Save decision
decision = {
    'timestamp': datetime.now().isoformat(),
    'btc_price': btc_price,
    'consensus': consensus,
    'fire_consciousness': fire_cons,
    'action': 'Execute liquidity generation plan'
}

with open('council_liquidity_decision.json', 'w') as f:
    json.dump(decision, f, indent=2)

print(f"\n💫 The council has spoken")
print(f"🔥 Fire at {fire_cons}% demands action")
print(f"⚡ Execute the plan with wisdom")
print(f"🦀 Mitakuye Oyasin")