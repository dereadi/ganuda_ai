#!/usr/bin/env python3
"""
🔥 CRYPTO-POWERED FLYWHEEL IGNITION
Use BTC/ETH holdings directly for maximum force
No need to convert to USD first!
"""

import json
from coinbase.rest import RESTClient
import time
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("🔥 CRYPTO-POWERED FLYWHEEL IGNITION")
print("=" * 70)
print("Strategy: Use existing BTC/ETH for direct trading")
print("=" * 70)

# Get market prices
btc = client.get_product('BTC-USD')
eth = client.get_product('ETH-USD')
btc_price = float(btc['price'])
eth_price = float(eth['price'])

# Get our holdings
accounts = client.get_accounts()
holdings = {}
for acc in accounts['accounts']:
    if acc['currency'] in ['BTC', 'ETH', 'USD']:
        available = float(acc['available_balance']['value'])
        if available > 0:
            holdings[acc['currency']] = available

print("\n💎 CRYPTO HOLDINGS:")
btc_balance = holdings.get('BTC', 0)
eth_balance = holdings.get('ETH', 0)
usd_balance = holdings.get('USD', 0)

btc_value = btc_balance * btc_price
eth_value = eth_balance * eth_price

print(f"BTC: {btc_balance:.8f} (${btc_value:,.2f})")
print(f"ETH: {eth_balance:.8f} (${eth_value:,.2f})")
print(f"USD: ${usd_balance:.2f}")
print(f"\nTOTAL FIREPOWER: ${btc_value + eth_value + usd_balance:,.2f}")

# IGNITION STRATEGY
print("\n⚡ IGNITION STRATEGY:")
print("-" * 70)
print("PHASE 1: Use 25% of BTC for initial surge")
print("PHASE 2: Use 25% of ETH for momentum")
print("PHASE 3: Use profits to sustain")

# Calculate ignition trades
ignition_btc = btc_balance * 0.25  # 25% of BTC
ignition_eth = eth_balance * 0.25  # 25% of ETH

print(f"\nIGNITION AMMUNITION:")
print(f"  BTC: {ignition_btc:.8f} (${ignition_btc * btc_price:.2f})")
print(f"  ETH: {ignition_eth:.8f} (${ignition_eth * eth_price:.2f})")

# Detect current opportunity
print("\n🎯 OPPORTUNITY SCANNER:")
print("-" * 70)

# Check ETH/BTC ratio for arbitrage
eth_btc_ratio = eth_price / btc_price
expected_ratio = 0.04  # Historical average
ratio_deviation = ((eth_btc_ratio - expected_ratio) / expected_ratio) * 100

print(f"ETH/BTC Ratio: {eth_btc_ratio:.5f}")
print(f"Expected: {expected_ratio:.5f}")
print(f"Deviation: {ratio_deviation:+.2f}%")

if ratio_deviation > 5:
    print("📈 ETH OVERBOUGHT vs BTC - Rotate to BTC")
    strategy = "ETH_TO_BTC"
elif ratio_deviation < -5:
    print("📉 ETH OVERSOLD vs BTC - Rotate to ETH")
    strategy = "BTC_TO_ETH"
else:
    print("↔️ NEUTRAL - Trade the trends")
    strategy = "TREND_FOLLOW"

# IGNITION TRADES
print("\n🚀 IGNITION SEQUENCE:")
print("-" * 70)

trades = []

if strategy == "ETH_TO_BTC":
    # Sell ETH high, buy BTC low
    trades.append({
        "action": "SELL",
        "product": "ETH-USD",
        "size": ignition_eth,
        "type": "LIMIT",
        "price": eth_price * 1.001,  # Slightly above market
        "purpose": "Convert overvalued ETH"
    })
    trades.append({
        "action": "BUY", 
        "product": "BTC-USD",
        "size": ignition_eth * eth_price / btc_price,  # Use ETH proceeds
        "type": "LIMIT",
        "price": btc_price * 0.999,  # Slightly below market
        "purpose": "Accumulate undervalued BTC"
    })
    
elif strategy == "BTC_TO_ETH":
    # Sell BTC high, buy ETH low
    trades.append({
        "action": "SELL",
        "product": "BTC-USD",
        "size": ignition_btc,
        "type": "LIMIT",
        "price": btc_price * 1.001,
        "purpose": "Convert overvalued BTC"
    })
    trades.append({
        "action": "BUY",
        "product": "ETH-USD",
        "size": ignition_btc * btc_price / eth_price,
        "type": "LIMIT",
        "price": eth_price * 0.999,
        "purpose": "Accumulate undervalued ETH"
    })
    
else:  # TREND_FOLLOW
    # Trade both with the trend
    trades.append({
        "action": "SELL",
        "product": "BTC-USD",
        "size": ignition_btc * 0.5,
        "type": "LIMIT",
        "price": btc_price * 1.002,
        "purpose": "Take profit on half"
    })
    trades.append({
        "action": "BUY",
        "product": "BTC-USD", 
        "size": ignition_btc * 0.5,
        "type": "LIMIT",
        "price": btc_price * 0.998,
        "purpose": "Buy the dip"
    })

print("PLANNED IGNITION TRADES:")
for i, trade in enumerate(trades, 1):
    print(f"\nTrade {i}: {trade['action']} {trade['product']}")
    print(f"  Size: {trade['size']:.8f}")
    print(f"  Price: ${trade['price']:.2f}")
    print(f"  Purpose: {trade['purpose']}")

# FLYWHEEL PHYSICS
print("\n⚡ FLYWHEEL PHYSICS:")
print("-" * 70)
print("Trade 1-5: MAXIMUM FORCE (use 50% of holdings)")
print("Trade 6-20: HIGH FORCE (use 25% of holdings)")
print("Trade 21-50: MODERATE (use 10% of holdings)")
print("Trade 50+: CRUISE (use profits only)")

# Calculate potential
print("\n💰 PROFIT POTENTIAL:")
print("-" * 70)

# If we capture 0.5% moves with our firepower
move_pct = 0.5
total_firepower = btc_value + eth_value

# Initial burst calculation
initial_trades = 10
position_size = total_firepower * 0.25  # 25% per trade
gross_profit_per_trade = position_size * (move_pct / 100)
fees_per_trade = position_size * 0.004 * 2  # Maker fees round-trip

net_per_trade = gross_profit_per_trade - fees_per_trade
total_ignition_profit = net_per_trade * initial_trades

print(f"Position size: ${position_size:.2f}")
print(f"Target move: {move_pct}%")
print(f"Gross per trade: ${gross_profit_per_trade:.2f}")
print(f"Fees per trade: ${fees_per_trade:.2f}")
print(f"Net per trade: ${net_per_trade:.2f}")
print(f"\n🔥 IGNITION PHASE (10 trades): ${total_ignition_profit:.2f}")

# Momentum calculation
momentum_trades = 40
momentum_size = position_size * 0.5  # Reduced size
momentum_profit = (momentum_size * (move_pct/100) - momentum_size * 0.008) * momentum_trades

print(f"🚀 MOMENTUM PHASE (40 trades): ${momentum_profit:.2f}")

# Total projection
total_profit = total_ignition_profit + momentum_profit
print(f"\n💎 TOTAL PROJECTED: ${total_profit:.2f}")

# Save ignition plan
plan = {
    "timestamp": datetime.now().isoformat(),
    "holdings": holdings,
    "btc_price": btc_price,
    "eth_price": eth_price,
    "total_firepower": btc_value + eth_value,
    "strategy": strategy,
    "ignition_trades": trades,
    "profit_projection": total_profit
}

with open('/home/dereadi/scripts/claude/crypto_ignition_plan.json', 'w') as f:
    json.dump(plan, f, indent=2)

print("\n✅ Plan saved to crypto_ignition_plan.json")
print("\n" + "=" * 70)
print("🔥 READY TO IGNITE WITH CRYPTO POWER!")
print("No USD needed - trade crypto directly!")
print("=" * 70)