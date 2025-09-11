#!/usr/bin/env python3
"""
🔄 TACTICAL PIVOT - Market is dipping, should we flip strategy?
"""

import json
from coinbase.rest import RESTClient
import statistics
import time

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("🔄 TACTICAL PIVOT ANALYSIS")
print("=" * 70)

# Get current price and recent action
btc = client.get_product('BTC-USD')
btc_price = float(btc['price'])

# Get 15-min candles
end_time = int(time.time())
start_time = end_time - 900  # 15 minutes
candles = client.get_candles("BTC-USD", start_time, end_time, "ONE_MINUTE")

if candles["candles"]:
    prices = [float(c["close"]) for c in candles["candles"][-15:]]
    high_15min = max([float(c["high"]) for c in candles["candles"][-15:]])
    low_15min = min([float(c["low"]) for c in candles["candles"][-15:]])
    
    # Calculate momentum
    first_5_avg = statistics.mean(prices[:5])
    last_5_avg = statistics.mean(prices[-5:])
    momentum = ((last_5_avg - first_5_avg) / first_5_avg) * 100
    
    print(f"Current BTC: ${btc_price:,.2f}")
    print(f"15-min High: ${high_15min:,.2f}")
    print(f"15-min Low: ${low_15min:,.2f}")
    print(f"Momentum: {momentum:+.3f}%")
    
    # Decision matrix
    print("\n📊 DECISION MATRIX:")
    print("-" * 70)
    
    # Check distance from high
    from_high = ((high_15min - btc_price) / btc_price) * 100
    print(f"Down from high: {from_high:.2f}%")
    
    if momentum < -0.2:
        print("📉 STRONG DOWNWARD MOMENTUM")
        action = "PIVOT"
    elif from_high > 0.5:
        print("📉 SIGNIFICANT PULLBACK")  
        action = "PIVOT"
    else:
        print("↔️ NORMAL FLUCTUATION")
        action = "HOLD"
    
    print(f"\n🎯 RECOMMENDATION: {action}")
    
    if action == "PIVOT":
        print("\n🔄 PIVOT STRATEGY:")
        print("-" * 70)
        print("1. CANCEL high sell orders")
        print("2. BUY the dip with 25% of BTC")
        print("3. Place NEW sells 1% higher")
        print("4. Ride the bounce")
        
        # Calculate new targets
        buy_target = btc_price * 0.998
        sell_target = btc_price * 1.01
        
        print(f"\nNew buy target: ${buy_target:.2f}")
        print(f"New sell target: ${sell_target:.2f}")
        print(f"Expected profit: ${(sell_target - buy_target) * 0.005:.2f}")
        
    else:
        print("\n✋ HOLD STRATEGY:")
        print("-" * 70)
        print("1. KEEP sell orders in place")
        print("2. Market will return to highs")
        print("3. Patience wins")
        
        # Distance to sells
        print(f"\nDistance to first sell: ${109921.90 - btc_price:.2f}")
        print(f"Just {((109921.90 - btc_price)/btc_price)*100:.2f}% away")

print("\n" + "=" * 70)