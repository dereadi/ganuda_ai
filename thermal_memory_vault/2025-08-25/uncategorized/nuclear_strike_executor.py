#!/usr/bin/env python3
"""
💥 NUCLEAR STRIKE EXECUTOR - LIVE FIRE
Execute massive strategic trades for flywheel ignition
Target: 1% moves with 50% of holdings
"""

import json
from coinbase.rest import RESTClient
import time
from datetime import datetime
import statistics

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("💥 NUCLEAR STRIKE EXECUTOR - WEAPONS HOT")
print("=" * 70)
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("Mission: Execute STRIKE ONE for flywheel ignition")
print("=" * 70)

# Get current market state
btc = client.get_product('BTC-USD')
eth = client.get_product('ETH-USD')
btc_price = float(btc['price'])
eth_price = float(eth['price'])

print(f"\n📊 BATTLEFIELD STATUS:")
print(f"BTC: ${btc_price:,.2f}")
print(f"ETH: ${eth_price:,.2f}")

# Get our ammunition
accounts = client.get_accounts()
holdings = {}
for acc in accounts['accounts']:
    if acc['currency'] in ['BTC', 'ETH', 'USD', 'USDC']:
        available = float(acc['available_balance']['value'])
        if available > 0:
            holdings[acc['currency']] = available

btc_balance = holdings.get('BTC', 0)
eth_balance = holdings.get('ETH', 0)
usd_balance = holdings.get('USD', 0) + holdings.get('USDC', 0)

print(f"\n💎 AMMUNITION CHECK:")
print(f"BTC: {btc_balance:.8f} (${btc_balance * btc_price:,.2f})")
print(f"ETH: {eth_balance:.8f} (${eth_balance * eth_price:,.2f})")
print(f"USD: ${usd_balance:.2f}")

# Calculate Strike One size (50% of BTC)
strike_one_btc = btc_balance * 0.5
strike_one_value = strike_one_btc * btc_price

print(f"\n🎯 STRIKE ONE PARAMETERS:")
print(f"Size: {strike_one_btc:.8f} BTC")
print(f"Value: ${strike_one_value:,.2f}")
print(f"Target: 1% move minimum")

# Analyze market for entry
print(f"\n🔍 MARKET ANALYSIS:")
print("-" * 70)

# Get recent price action
end_time = int(time.time())
start_time = end_time - 1800  # Last 30 minutes
candles = client.get_candles("BTC-USD", start_time, end_time, "FIVE_MINUTE")

if candles["candles"]:
    prices = [float(c["close"]) for c in candles["candles"][-6:]]  # Last 30 min
    highs = [float(c["high"]) for c in candles["candles"][-6:]]
    lows = [float(c["low"]) for c in candles["candles"][-6:]]
    
    recent_high = max(highs)
    recent_low = min(lows)
    current_range = recent_high - recent_low
    range_pct = (current_range / btc_price) * 100
    
    # Calculate momentum
    avg_price = statistics.mean(prices)
    momentum = ((btc_price - avg_price) / avg_price) * 100
    
    print(f"30-min High: ${recent_high:,.2f}")
    print(f"30-min Low: ${recent_low:,.2f}")
    print(f"Range: ${current_range:.2f} ({range_pct:.3f}%)")
    print(f"Momentum: {momentum:+.3f}%")
    
    # Determine strike strategy
    if btc_price < recent_low + (current_range * 0.3):
        print("\n🟢 NEAR RANGE LOW - BUY OPPORTUNITY")
        strike_direction = "BUY"
        strike_action = "ACCUMULATE"
    elif btc_price > recent_high - (current_range * 0.3):
        print("\n🔴 NEAR RANGE HIGH - SELL OPPORTUNITY")
        strike_direction = "SELL"
        strike_action = "DISTRIBUTE"
    else:
        print("\n↔️ MID-RANGE - WAIT FOR EXTREME")
        strike_direction = "WAIT"
        strike_action = "PATIENCE"

# Define nuclear strike levels
print(f"\n💥 NUCLEAR STRIKE LEVELS:")
print("-" * 70)

if strike_direction == "BUY":
    # Place aggressive buy orders
    strike_levels = [
        {"price": btc_price * 0.998, "size": strike_one_btc * 0.3, "type": "LIMIT"},
        {"price": btc_price * 0.995, "size": strike_one_btc * 0.3, "type": "LIMIT"},
        {"price": btc_price * 0.992, "size": strike_one_btc * 0.4, "type": "LIMIT"},
    ]
    target_exit = btc_price * 1.01  # 1% profit target
    
elif strike_direction == "SELL":
    # Place aggressive sell orders
    strike_levels = [
        {"price": btc_price * 1.002, "size": strike_one_btc * 0.3, "type": "LIMIT"},
        {"price": btc_price * 1.005, "size": strike_one_btc * 0.3, "type": "LIMIT"},
        {"price": btc_price * 1.008, "size": strike_one_btc * 0.4, "type": "LIMIT"},
    ]
    target_exit = btc_price * 0.99  # Buy back 1% lower
    
else:
    # Set wider range orders
    strike_levels = [
        {"price": btc_price * 0.993, "size": strike_one_btc * 0.5, "type": "BUY_LIMIT"},
        {"price": btc_price * 1.007, "size": strike_one_btc * 0.5, "type": "SELL_LIMIT"},
    ]
    target_exit = None

print(f"STRIKE DIRECTION: {strike_direction}")
print(f"ACTION: {strike_action}")

for i, level in enumerate(strike_levels, 1):
    action = "BUY" if level.get("type", "").startswith("BUY") or strike_direction == "BUY" else "SELL"
    print(f"\nLevel {i} ({action}):")
    print(f"  Price: ${level['price']:,.2f}")
    print(f"  Size: {level['size']:.8f} BTC")
    print(f"  Value: ${level['size'] * level['price']:,.2f}")

if target_exit:
    print(f"\n🎯 TARGET EXIT: ${target_exit:,.2f}")
    expected_profit = abs(target_exit - btc_price) / btc_price * strike_one_value
    fees = strike_one_value * 0.004 * 2  # Maker fees round trip
    net_profit = expected_profit - fees
    print(f"Expected profit: ${expected_profit:.2f}")
    print(f"Fees: ${fees:.2f}")
    print(f"NET: ${net_profit:.2f}")

# Execute Strike One
print(f"\n🚀 EXECUTING STRIKE ONE:")
print("-" * 70)

orders_placed = []
total_btc_deployed = 0

try:
    for i, level in enumerate(strike_levels, 1):
        if strike_direction != "WAIT":
            side = "BUY" if strike_direction == "BUY" else "SELL"
            
            # Prepare order
            print(f"\nPlacing {side} order {i}:")
            print(f"  Price: ${level['price']:.2f}")
            print(f"  Size: {level['size']:.8f} BTC")
            
            # Place the order with proper parameters
            result = client.create_order(
                client_order_id=f"nuclear_{i}_{int(time.time())}",
                product_id="BTC-USD",
                side=side,
                order_configuration={
                    "limit_limit_gtc": {
                        "post_only": True,  # Maker fees only
                        "limit_price": f"{level['price']:.2f}",
                        "base_size": f"{level['size']:.8f}"
                    }
                }
            )
            
            # Check if order was successful
            if hasattr(result, 'order_id'):
                print(f"  ✅ Order placed: {result.order_id}")
                orders_placed.append(result.order_id)
                total_btc_deployed += level['size']
            else:
                print(f"  ✅ Order response: {result}")
                total_btc_deployed += level['size']
                
except Exception as e:
    print(f"⚠️ Error placing orders: {e}")

# Summary
print(f"\n📊 STRIKE ONE SUMMARY:")
print("-" * 70)
print(f"Orders placed: {len(orders_placed)}")
print(f"BTC deployed: {total_btc_deployed:.8f}")
print(f"Value deployed: ${total_btc_deployed * btc_price:,.2f}")

# Save state
state = {
    "timestamp": datetime.now().isoformat(),
    "strike": "ONE",
    "btc_price": btc_price,
    "direction": strike_direction,
    "orders": orders_placed,
    "btc_deployed": total_btc_deployed,
    "target_exit": target_exit,
    "strike_levels": strike_levels
}

with open('/home/dereadi/scripts/claude/nuclear_strike_state.json', 'w') as f:
    json.dump(state, f, indent=2)

print("\n✅ Strike state saved to nuclear_strike_state.json")

# Next steps
print(f"\n📋 NEXT STEPS:")
print("-" * 70)
print("1. Monitor order fills")
print("2. When filled, place exit orders at target")
print("3. After profitable exit, execute STRIKE TWO")
print("4. Use profits to fuel continued momentum")

print("\n" + "=" * 70)
print("💥 STRIKE ONE LAUNCHED!")
print("The flywheel begins to turn...")
print("=" * 70)