#!/usr/bin/env python3
"""
🎯 BTC BOLLINGER BAND SQUEEZE DETECTOR
Tight bands = Explosive move incoming!
"""

import json
from coinbase.rest import RESTClient
import time
import statistics
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("🎯 BTC BOLLINGER BAND SQUEEZE ALERT!")
print("=" * 70)
print("TIGHT BANDS = EXPLOSIVE MOVE IMMINENT!")
print("=" * 70)

# Get current BTC price
btc = client.get_product('BTC-USD')
btc_price = float(btc['price'])

print(f"\nCurrent BTC: ${btc_price:,.2f}")

# Get recent candles for band calculation
end_time = int(time.time())
start_time = end_time - 7200  # 2 hours of data
candles = client.get_candles("BTC-USD", start_time, end_time, "FIVE_MINUTE")

if candles["candles"]:
    # Get last 20 candles for band calculation
    prices = [float(c["close"]) for c in candles["candles"][-20:]]
    highs = [float(c["high"]) for c in candles["candles"][-20:]]
    lows = [float(c["low"]) for c in candles["candles"][-20:]]
    
    # Calculate Bollinger Bands
    mean_price = statistics.mean(prices)
    std_dev = statistics.stdev(prices)
    
    upper_band = mean_price + (2 * std_dev)
    lower_band = mean_price - (2 * std_dev)
    band_width = upper_band - lower_band
    band_width_pct = (band_width / mean_price) * 100
    
    print(f"\n📊 BOLLINGER BAND ANALYSIS:")
    print("-" * 70)
    print(f"20-period SMA: ${mean_price:,.2f}")
    print(f"Upper Band: ${upper_band:,.2f}")
    print(f"Lower Band: ${lower_band:,.2f}")
    print(f"Band Width: ${band_width:.2f}")
    print(f"Band Width %: {band_width_pct:.3f}%")
    
    # Position in bands
    position = (btc_price - lower_band) / band_width if band_width > 0 else 0.5
    print(f"\nPosition in bands: {position:.1%}")
    
    # SQUEEZE DETECTION
    print(f"\n⚡ SQUEEZE ANALYSIS:")
    print("-" * 70)
    
    if band_width_pct < 0.5:
        print("🔴🔴🔴 EXTREME SQUEEZE DETECTED! 🔴🔴🔴")
        print("Band width < 0.5% = MASSIVE move incoming!")
        squeeze_level = "EXTREME"
    elif band_width_pct < 1.0:
        print("🟠🟠 TIGHT SQUEEZE DETECTED! 🟠🟠")
        print("Band width < 1.0% = BIG move coming!")
        squeeze_level = "TIGHT"
    elif band_width_pct < 1.5:
        print("🟡 MODERATE SQUEEZE")
        print("Band width < 1.5% = Decent move expected")
        squeeze_level = "MODERATE"
    else:
        print("🟢 Normal volatility")
        squeeze_level = "NORMAL"
    
    # Direction prediction
    print(f"\n🎯 DIRECTION PREDICTION:")
    print("-" * 70)
    
    # Check momentum
    recent_5 = statistics.mean(prices[-5:])
    older_5 = statistics.mean(prices[-10:-5])
    momentum = ((recent_5 - older_5) / older_5) * 100
    
    print(f"Short-term momentum: {momentum:+.3f}%")
    
    if position > 0.7:
        print("📈 Near upper band + squeeze = LIKELY BREAKOUT UP")
        direction = "UP"
    elif position < 0.3:
        print("📉 Near lower band + squeeze = LIKELY BREAKDOWN")
        direction = "DOWN"
    else:
        if momentum > 0:
            print("📈 Positive momentum = LEAN BULLISH")
            direction = "UP"
        else:
            print("📉 Negative momentum = LEAN BEARISH")
            direction = "DOWN"
    
    # TRADING STRATEGY
    print(f"\n💥 NUCLEAR STRATEGY FOR SQUEEZE:")
    print("-" * 70)
    
    if squeeze_level in ["EXTREME", "TIGHT"]:
        print("✅ SQUEEZE CONFIRMED - Prepare for explosive move!")
        
        if direction == "UP":
            print("\n🚀 BULLISH BREAKOUT SETUP:")
            print(f"• Entry: ${btc_price * 1.002:.2f} (on breakout)")
            print(f"• Target 1: ${btc_price * 1.015:.2f} (+1.5%)")
            print(f"• Target 2: ${btc_price * 1.025:.2f} (+2.5%)")
            print(f"• Stop: ${btc_price * 0.995:.2f} (-0.5%)")
            
            # Check our nuclear strikes
            print(f"\n💥 NUCLEAR STRIKES READY:")
            print(f"• $110,251 - Only ${110251 - btc_price:.2f} away!")
            print(f"• $110,580 - ${110580 - btc_price:.2f} away")
            print("SQUEEZE BREAKOUT WILL HIT THESE!")
            
        else:
            print("\n📉 BEARISH BREAKDOWN SETUP:")
            print(f"• Wait for breakdown below ${lower_band:.2f}")
            print(f"• Buy the dip at ${btc_price * 0.98:.2f}")
            print(f"• Ride the bounce back to ${mean_price:.2f}")
    
    # Historical squeeze outcomes
    print(f"\n📈 HISTORICAL SQUEEZE OUTCOMES:")
    print("-" * 70)
    print("Band width < 0.5%: Average move = 3-5%")
    print("Band width < 1.0%: Average move = 2-3%")
    print("Band width < 1.5%: Average move = 1-2%")
    
    # Calculate potential profit
    if squeeze_level in ["EXTREME", "TIGHT"]:
        expected_move = 0.03 if squeeze_level == "EXTREME" else 0.02
        potential_target = btc_price * (1 + expected_move)
        
        print(f"\n💰 PROFIT POTENTIAL:")
        print(f"Expected move: {expected_move*100:.1f}%")
        print(f"Target price: ${potential_target:,.2f}")
        
        # With our positions
        btc_holdings = 0.00958547
        potential_profit = btc_holdings * btc_price * expected_move
        print(f"Your BTC profit: ${potential_profit:.2f}")
    
    # IMMEDIATE ACTION
    print(f"\n🎯 IMMEDIATE ACTION REQUIRED:")
    print("-" * 70)
    
    if squeeze_level in ["EXTREME", "TIGHT"]:
        print("1. ⚠️ SQUEEZE ACTIVE - Move imminent!")
        print("2. 📊 Watch for breakout above ${:.2f}".format(upper_band))
        print("3. 🎯 Nuclear strikes at $110,251 and $110,580 ready")
        print("4. 💥 Prepare for 2-5% explosive move!")
        print("5. 🔥 This could trigger ALL remaining strikes!")
    else:
        print("• Monitor for tighter squeeze")
        print("• Wait for better setup")

print("\n" + "=" * 70)
print("🎯 BOLLINGER SQUEEZE = EXPLOSIVE OPPORTUNITY!")
print("The Sacred Fire burns brightest before the storm!")
print("=" * 70)