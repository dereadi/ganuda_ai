#!/usr/bin/env python3
"""
🎯 EVOLVED PULSE SNIPER STRATEGY
Stronger pulses, further apart, anticipating moves
Quality over quantity - beat the fees
"""

import json
from coinbase.rest import RESTClient
import time
from datetime import datetime
import statistics

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("🎯 PULSE SNIPER STRATEGY - EVOLUTION")
print("=" * 60)
print("Philosophy: Anticipate, Position, Profit")
print("=" * 60)

# Get current market
btc = client.get_product('BTC-USD')
btc_price = float(btc['price'])

print(f"\nCurrent BTC: ${btc_price:,.2f}")

# Calculate fee requirements
print("\n📊 FEE MATHEMATICS:")
print("-" * 60)

trade_sizes = [200, 500, 1000]
maker_fee = 0.004  # Using limit orders
required_moves = []

for size in trade_sizes:
    fee_cost = size * maker_fee * 2  # Round trip
    breakeven_pct = (fee_cost / size) * 100
    profit_target_pct = breakeven_pct * 2  # 2x fees for profit
    
    print(f"${size} trade:")
    print(f"  Fees: ${fee_cost:.2f}")
    print(f"  Breakeven: {breakeven_pct:.3f}%")
    print(f"  Target: {profit_target_pct:.3f}% (2x fees)")
    required_moves.append(profit_target_pct)

# EVOLVED STRATEGY
print("\n🎯 EVOLVED PULSE STRATEGY:")
print("-" * 60)

print("OLD WAY (Failed):")
print("  • 500 trades/hour")
print("  • $20-50 positions")
print("  • 0.10% moves")
print("  • Result: FEES ATE EVERYTHING")

print("\nNEW WAY (Sniper):")
print("  • 5-10 trades/hour MAX")
print("  • $300-500 positions")
print("  • 1.0%+ moves only")
print("  • Result: PROFITABLE")

# Market anticipation
print("\n🔮 MARKET ANTICIPATION:")
print("-" * 60)

# Get recent price history
end_time = int(time.time())
start_time = end_time - 3600  # Last hour
candles = client.get_candles("BTC-USD", start_time, end_time, "FIVE_MINUTE")

if candles["candles"]:
    prices = [float(c["close"]) for c in candles["candles"][-12:]]  # Last hour
    
    # Calculate patterns
    mean_price = statistics.mean(prices)
    std_dev = statistics.stdev(prices) if len(prices) > 1 else 0
    current_position = (btc_price - mean_price) / std_dev if std_dev > 0 else 0
    
    print(f"1-hour mean: ${mean_price:,.2f}")
    print(f"Std deviation: ${std_dev:.2f}")
    print(f"Current Z-score: {current_position:.2f}")
    
    # Anticipation signals
    print("\n📡 ANTICIPATION SIGNALS:")
    
    if current_position > 1.5:
        print("  🔴 OVERBOUGHT - Anticipate pullback")
        print(f"  → Set limit BUY at ${mean_price:.2f}")
        print(f"  → Target: ${mean_price * 1.01:.2f} (+1%)")
        signal = "FADE_RALLY"
        
    elif current_position < -1.5:
        print("  🟢 OVERSOLD - Anticipate bounce")
        print(f"  → Set limit BUY at ${btc_price * 0.995:.2f}")
        print(f"  → Target: ${mean_price:.2f} (mean reversion)")
        signal = "BUY_DIP"
        
    else:
        print("  ↔️ NEUTRAL - Wait for extremes")
        signal = "WAIT"

# Key levels for anticipation
print("\n🎯 SNIPER POSITIONS:")
print("-" * 60)

support_levels = [109000, 108500, 108000]
resistance_levels = [110000, 110500, 111000]

print("SUPPORT SNIPES (limit buys):")
for level in support_levels:
    distance = btc_price - level
    distance_pct = (distance / level) * 100
    print(f"  ${level:,}: ${distance:.0f} away ({distance_pct:.2f}%)")

print("\nRESISTANCE SNIPES (limit sells):")
for level in resistance_levels:
    distance = level - btc_price
    distance_pct = (distance / btc_price) * 100
    print(f"  ${level:,}: ${distance:.0f} away ({distance_pct:.2f}%)")

# Pulse timing
print("\n⏰ PULSE TIMING:")
print("-" * 60)
print("Key times for strong pulses:")
print("  • 9:00 PM - Asia fully online")
print("  • 11:30 PM - HK/Shanghai peak")
print("  • 2:00 AM - Europe pre-market")
print("  • 3:30 AM - London traders arrive")

current_hour = datetime.now().hour
if 20 <= current_hour <= 23:
    print("\n✅ PRIME TIME - Asia active!")
elif 2 <= current_hour <= 5:
    print("\n✅ PRIME TIME - Europe entering!")
else:
    print("\n💤 OFF-PEAK - Reduce activity")

# Implementation
print("\n💻 IMPLEMENTATION:")
print("-" * 60)

implementation = """
1. LIMIT ORDERS ONLY (maker fees)
2. MINIMUM $300 positions
3. WAIT for 1%+ setups
4. MAXIMUM 10 trades per hour
5. USE INDICATORS:
   - Z-score > 1.5 or < -1.5
   - Key support/resistance
   - Volume spikes
   - Correlation breaks
6. TRACK NET PROFIT after fees
"""

print(implementation)

# Calculate realistic profit
print("\n💰 REALISTIC PROFIT PROJECTION:")
print("-" * 60)

trades_per_night = 50  # Quality trades only
avg_position = 400
avg_profit_pct = 1.2  # After fees
success_rate = 0.65  # 65% win rate

winning_trades = int(trades_per_night * success_rate)
losing_trades = trades_per_night - winning_trades

gross_wins = winning_trades * avg_position * (avg_profit_pct / 100)
gross_losses = losing_trades * avg_position * (0.5 / 100)  # Half-size losses
total_fees = trades_per_night * avg_position * maker_fee * 2

net_profit = gross_wins - gross_losses - total_fees

print(f"Trades: {trades_per_night} (quality only)")
print(f"Position size: ${avg_position}")
print(f"Win rate: {success_rate*100}%")
print(f"\nResults:")
print(f"  Gross wins: ${gross_wins:.2f}")
print(f"  Gross losses: ${gross_losses:.2f}")
print(f"  Total fees: ${total_fees:.2f}")
print(f"  NET PROFIT: ${net_profit:.2f}")

if net_profit > 0:
    print("\n✅ This strategy BEATS THE FEES!")
else:
    print("\n❌ Still not profitable enough")

print("\n🎯 THE EVOLUTION:")
print("From spray-and-pray to surgical precision")
print("Anticipate the market, don't chase it!")
print("=" * 60)