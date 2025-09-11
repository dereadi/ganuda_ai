#!/usr/bin/env python3
"""
⚡ FLYWHEEL IGNITION SURGE SYSTEM
Maximum force at startup → Momentum carries forward
One strong wheel beats three weak wheels
"""

import json
from coinbase.rest import RESTClient
import time
from datetime import datetime
import statistics

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("⚡ FLYWHEEL IGNITION SURGE - MAXIMUM FORCE DEPLOYMENT")
print("=" * 70)
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("Strategy: HIT HARD → BUILD MOMENTUM → CRUISE")
print("=" * 70)

# Get market state
btc = client.get_product('BTC-USD')
eth = client.get_product('ETH-USD')
btc_price = float(btc['price'])
eth_price = float(eth['price'])

print(f"\n📊 MARKET STATE:")
print(f"BTC: ${btc_price:,.2f}")
print(f"ETH: ${eth_price:,.2f}")

# Get account balances
accounts = client.get_accounts()
balances = {}
for acc in accounts['accounts']:
    if acc['currency'] in ['USD', 'USDC', 'BTC', 'ETH']:
        available = float(acc['available_balance']['value'])
        if available > 0:
            balances[acc['currency']] = available

print(f"\n💰 AVAILABLE CAPITAL:")
for currency, balance in balances.items():
    if currency == 'USD':
        print(f"  {currency}: ${balance:.2f}")
    else:
        print(f"  {currency}: {balance:.8f}")

available_usd = balances.get('USD', 0) + balances.get('USDC', 0)
print(f"\nTotal USD equivalent: ${available_usd:.2f}")

# IGNITION PHASE CONFIGURATION
print("\n⚡ IGNITION CONFIGURATION:")
print("-" * 70)

phase_config = {
    "current_phase": "IGNITION",
    "trade_count": 0,
    "momentum_score": 0,
    "phases": {
        "IGNITION": {
            "trades": [1, 10],
            "position_size": min(1000, available_usd * 0.5),  # 50% or $1000
            "min_move_pct": 0.4,  # 0.4% minimum
            "accept_taker_fees": True,
            "energy_level": "MAXIMUM"
        },
        "ACCELERATION": {
            "trades": [11, 30],
            "position_size": min(500, available_usd * 0.25),
            "min_move_pct": 0.3,
            "accept_taker_fees": False,  # Limit orders only
            "energy_level": "HIGH"
        },
        "MOMENTUM": {
            "trades": [31, 100],
            "position_size": min(200, available_usd * 0.10),
            "min_move_pct": 0.2,
            "accept_taker_fees": False,
            "energy_level": "MODERATE"
        },
        "CRUISE": {
            "trades": [101, 9999],
            "position_size": min(100, available_usd * 0.05),
            "min_move_pct": 0.15,
            "accept_taker_fees": False,
            "energy_level": "MAINTENANCE"
        }
    }
}

current_phase_name = phase_config["current_phase"]
current_phase = phase_config["phases"][current_phase_name]

print(f"Phase: {current_phase_name}")
print(f"Position Size: ${current_phase['position_size']:.2f}")
print(f"Minimum Move: {current_phase['min_move_pct']}%")
print(f"Energy Level: {current_phase['energy_level']}")

# TREND DETECTION (Primary Flywheel)
print("\n📈 TREND FLYWHEEL ANALYSIS:")
print("-" * 70)

# Get recent candles for trend
end_time = int(time.time())
start_time = end_time - 3600  # Last hour
btc_candles = client.get_candles("BTC-USD", start_time, end_time, "FIVE_MINUTE")

if btc_candles["candles"]:
    prices = [float(c["close"]) for c in btc_candles["candles"][-20:]]
    
    # Calculate trend strength
    sma_5 = statistics.mean(prices[-5:])
    sma_20 = statistics.mean(prices)
    
    trend_strength = ((sma_5 - sma_20) / sma_20) * 100
    
    print(f"5-period SMA: ${sma_5:.2f}")
    print(f"20-period SMA: ${sma_20:.2f}")
    print(f"Trend Strength: {trend_strength:+.3f}%")
    
    if trend_strength > 0.1:
        print("📈 UPTREND DETECTED - Momentum long")
        trend_signal = "UP"
    elif trend_strength < -0.1:
        print("📉 DOWNTREND DETECTED - Momentum short")
        trend_signal = "DOWN"
    else:
        print("➡️ SIDEWAYS - Wait for breakout")
        trend_signal = "NEUTRAL"

# IGNITION TARGETS
print("\n🎯 IGNITION TARGETS:")
print("-" * 70)

if trend_signal == "UP":
    # Place limit buys below market for pullbacks
    targets = [
        {"price": btc_price * 0.997, "size": current_phase['position_size']},
        {"price": btc_price * 0.995, "size": current_phase['position_size']},
        {"price": btc_price * 0.993, "size": current_phase['position_size'] * 1.5},
    ]
    print("UPTREND STRATEGY: Buy pullbacks")
elif trend_signal == "DOWN":
    # Place limit sells above market for bounces
    targets = [
        {"price": btc_price * 1.003, "size": current_phase['position_size']},
        {"price": btc_price * 1.005, "size": current_phase['position_size']},
        {"price": btc_price * 1.007, "size": current_phase['position_size'] * 1.5},
    ]
    print("DOWNTREND STRATEGY: Sell bounces")
else:
    # Range trading at extremes
    targets = [
        {"price": btc_price * 0.995, "size": current_phase['position_size']},
        {"price": btc_price * 1.005, "size": current_phase['position_size']},
    ]
    print("NEUTRAL STRATEGY: Trade range extremes")

for i, target in enumerate(targets, 1):
    price = target['price']
    size_usd = target['size']
    size_btc = size_usd / price
    print(f"\nTarget {i}:")
    print(f"  Price: ${price:,.2f}")
    print(f"  Size: ${size_usd:.2f} ({size_btc:.6f} BTC)")
    
# MOMENTUM TRACKING
print("\n🔥 MOMENTUM METRICS:")
print("-" * 70)

momentum_metrics = {
    "trades_completed": 0,
    "profitable_trades": 0,
    "total_profit": 0,
    "momentum_score": 0,
    "phase_transition_ready": False
}

# Calculate when to transition phases
if momentum_metrics['trades_completed'] >= 10 and momentum_metrics['profitable_trades'] >= 7:
    momentum_metrics['phase_transition_ready'] = True
    print("✅ READY FOR ACCELERATION PHASE!")
else:
    trades_needed = 10 - momentum_metrics['trades_completed']
    print(f"Need {trades_needed} more ignition trades")

# TIME WINDOW OPTIMIZATION
print("\n⏰ TIME WINDOW ANALYSIS:")
print("-" * 70)
current_hour = datetime.now().hour

time_windows = {
    "MAXIMUM": [20, 21, 22, 23],  # Asia open
    "HIGH": [2, 3, 4, 5],  # Europe pre
    "MODERATE": [9, 10, 11],  # US morning
    "LOW": list(range(12, 20))  # Afternoon
}

for level, hours in time_windows.items():
    if current_hour in hours:
        print(f"🔥 {level} ENERGY WINDOW ACTIVE!")
        if level == "MAXIMUM":
            print("   → DEPLOY MAXIMUM FORCE NOW!")
            position_multiplier = 1.5
        elif level == "HIGH":
            print("   → Good secondary window")
            position_multiplier = 1.2
        else:
            position_multiplier = 1.0
        break

# EXECUTION PLAN
print("\n💫 EXECUTION PLAN:")
print("-" * 70)

execution_steps = [
    "1. STOP any existing weak flywheels",
    "2. DEPLOY first ignition trade NOW",
    "3. Use LIMIT orders at key levels",
    "4. Accept higher fees for first 10 trades",
    "5. Track momentum score after each trade",
    "6. Transition to ACCELERATION after momentum builds",
    "7. Reduce size as wheel gains speed",
    "8. Target self-sustaining by trade 100"
]

for step in execution_steps:
    print(step)

# SAVE STATE
state = {
    "timestamp": datetime.now().isoformat(),
    "phase": current_phase_name,
    "btc_price": btc_price,
    "eth_price": eth_price,
    "available_usd": available_usd,
    "trend_signal": trend_signal,
    "position_size": current_phase['position_size'],
    "targets": targets,
    "momentum_metrics": momentum_metrics
}

with open('/home/dereadi/scripts/claude/flywheel_ignition_state.json', 'w') as f:
    json.dump(state, f, indent=2)

print("\n✅ State saved to flywheel_ignition_state.json")

print("\n" + "=" * 70)
print("🔥 IGNITION SEQUENCE READY!")
print("Remember: HIT HARD at the start, momentum carries forward")
print("One strong flywheel > Three weak flywheels")
print("=" * 70)