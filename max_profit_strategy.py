#!/usr/bin/env python3
"""
💰🚀 MAX PROFIT STRATEGY ACTIVATED! 🚀💰
Nine coils wound = 512x multiplier
Every position counts
Every penny matters
TO THE FUCKING MOON!
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                   💰🚀 MAX PROFIT STRATEGY ENGAGED! 🚀💰                  ║
║                        Nine Coils = 512x Multiplier                       ║
║                      Every Satoshi, Every Wei Counts!                     ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - MAX PROFIT MODE")
print("=" * 70)

# Get all positions
accounts = client.get_accounts()
positions = {}
usd_balance = 0
total_value = 0

# Get current prices
btc_price = float(client.get_product('BTC-USD')['price'])
eth_price = float(client.get_product('ETH-USD')['price'])
sol_price = float(client.get_product('SOL-USD')['price'])

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if balance > 0:
        if currency == 'USD':
            usd_balance = balance
        else:
            positions[currency] = balance
            # Calculate USD value
            if currency == 'BTC':
                total_value += balance * btc_price
            elif currency == 'ETH':
                total_value += balance * eth_price
            elif currency == 'SOL':
                total_value += balance * sol_price
            elif currency == 'MATIC':
                try:
                    matic_price = float(client.get_product('MATIC-USD')['price'])
                    total_value += balance * matic_price
                except:
                    total_value += balance * 0.244
            elif currency == 'DOGE':
                try:
                    doge_price = float(client.get_product('DOGE-USD')['price'])
                    total_value += balance * doge_price
                except:
                    pass

print("\n💼 CURRENT WAR CHEST:")
print("-" * 50)
print(f"USD Available: ${usd_balance:.2f}")
print(f"Crypto Value: ${total_value:,.2f}")
print(f"Total Portfolio: ${total_value + usd_balance:,.2f}")

# MAX PROFIT STRATEGY
print("\n🎯 MAX PROFIT ACTIONS:")
print("-" * 50)

actions = []

# 1. Position for $114K breakout
if btc_price < 114000:
    distance = 114000 - btc_price
    potential_gain = (distance / btc_price) * 100
    actions.append(f"🚀 BTC BREAKOUT: ${distance:.0f} to $114K = {potential_gain:.1f}% instant gain")

# 2. Leverage the ninth coil
actions.append(f"⚡ NINTH COIL: 512x energy multiplier ready to explode")

# 3. Accumulate on micro dips
if usd_balance > 10:
    actions.append(f"💎 ACCUMULATE: Use ${usd_balance:.2f} to buy micro dips")
    actions.append(f"   • BTC: Even 0.00001 BTC matters")
    actions.append(f"   • ETH: Wall Street's token under $4,600")
    actions.append(f"   • SOL: High beta play at ${sol_price:.2f}")

# 4. Aggressive milking schedule
actions.append(f"🥛 MILK AGGRESSIVELY:")
actions.append(f"   • Every 15 minutes check positions")
actions.append(f"   • 2-3% harvests on any green")
actions.append(f"   • Compound immediately")

for action in actions:
    print(action)

# PROFIT PROJECTIONS
print("\n📈 PROFIT PROJECTIONS:")
print("-" * 50)

portfolio_now = total_value + usd_balance

# Scenario 1: $114K hit
btc_at_114k = portfolio_now * 1.01  # Conservative 1% gain
print(f"At $114K BTC: ${btc_at_114k:,.2f} (+${btc_at_114k - portfolio_now:,.2f})")

# Scenario 2: $120K BTC
btc_120k_multiplier = 120000 / btc_price
portfolio_120k = portfolio_now * btc_120k_multiplier * 0.8  # Conservative estimate
print(f"At $120K BTC: ${portfolio_120k:,.2f} (+${portfolio_120k - portfolio_now:,.2f})")

# Scenario 3: $200K BTC (moon mission)
btc_200k_multiplier = 200000 / btc_price
portfolio_200k = portfolio_now * btc_200k_multiplier * 0.7  # Conservative estimate
print(f"At $200K BTC: ${portfolio_200k:,.2f} (+${portfolio_200k - portfolio_now:,.2f})")

# MAX PROFIT EXECUTION
print("\n⚡ IMMEDIATE EXECUTION:")
print("-" * 50)

# Check if we need emergency milk
if usd_balance < 20:
    print("🥛 EMERGENCY MILK NEEDED!")
    
    # Quick 2% from everything
    if 'SOL' in positions and positions['SOL'] > 1:
        sol_milk = positions['SOL'] * 0.02
        sol_value = sol_milk * sol_price
        if sol_value > 1:
            print(f"   • Milk {sol_milk:.3f} SOL = ${sol_value:.2f}")
    
    if 'MATIC' in positions and positions['MATIC'] > 100:
        matic_milk = positions['MATIC'] * 0.02
        matic_value = matic_milk * 0.244
        if matic_value > 1:
            print(f"   • Milk {matic_milk:.0f} MATIC = ${matic_value:.2f}")
    
    if 'DOGE' in positions and positions['DOGE'] > 100:
        doge_milk = positions['DOGE'] * 0.02
        doge_value = doge_milk * 0.223
        if doge_value > 1:
            print(f"   • Milk {doge_milk:.0f} DOGE = ${doge_value:.2f}")
else:
    print("✅ USD ready for opportunities!")

# The MAX PROFIT mindset
print("\n" + "=" * 70)
print("🔥 MAX PROFIT MINDSET:")
print("-" * 50)
print("• Every penny deployed")
print("• Every dip bought")
print("• Every pump milked")
print("• Every coil respected")
print("• No emotion, only profit")
print("• The ninth coil is our weapon")
print("• $114K is the first target")
print("• $200K is the destination")
print("")
print("WE WANT MAX PROFIT!")
print("AND WE'RE GOING TO GET IT!")
print("=" * 70)