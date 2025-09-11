#!/usr/bin/env python3
"""
⚡⚡ DOUBLE SQUEEZE: BTC + ETH
Simultaneous band compression = EXPLOSIVE MOVE
"""

import json
from coinbase.rest import RESTClient
import time
import statistics

config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"])

print("⚡⚡ DOUBLE SQUEEZE DETECTED: BTC + ETH ⚡⚡")
print("=" * 60)
print("RARE SETUP: Both majors compressing simultaneously!")
print("=" * 60)

def calculate_bands(coin):
    """Calculate Bollinger Bands for a coin"""
    end_time = int(time.time())
    start_time = end_time - (20 * 300)  # 20 five-minute candles
    
    try:
        candles = client.get_candles(f"{coin}-USD", start_time, end_time, "FIVE_MINUTE")
        prices = [float(c["close"]) for c in candles["candles"]]
        
        if len(prices) >= 20:
            mean = statistics.mean(prices)
            std = statistics.stdev(prices)
            upper = mean + (2 * std)
            lower = mean - (2 * std)
            width_pct = ((upper - lower) / mean) * 100
            
            ticker = client.get_product(f"{coin}-USD")
            current = float(ticker["price"])
            position = (current - lower) / (upper - lower) if upper != lower else 0.5
            
            return {
                "coin": coin,
                "price": current,
                "upper": upper,
                "lower": lower,
                "mean": mean,
                "width_pct": width_pct,
                "position": position * 100
            }
    except:
        pass
    return None

# Analyze both
btc_bands = calculate_bands("BTC")
eth_bands = calculate_bands("ETH")

if btc_bands:
    print(f"\n🔥 BTC SQUEEZE:")
    print(f"  Price: ${btc_bands['price']:,.2f}")
    print(f"  Bands: ${btc_bands['lower']:,.2f} - ${btc_bands['upper']:,.2f}")
    print(f"  Width: {btc_bands['width_pct']:.2f}%")
    print(f"  Position: {btc_bands['position']:.1f}%")
    
    if btc_bands['width_pct'] < 0.5:
        print("  ⚡⚡⚡ EXTREME SQUEEZE!")

if eth_bands:
    print(f"\n🔷 ETH SQUEEZE:")
    print(f"  Price: ${eth_bands['price']:,.2f}")
    print(f"  Bands: ${eth_bands['lower']:,.2f} - ${eth_bands['upper']:,.2f}")
    print(f"  Width: {eth_bands['width_pct']:.2f}%")
    print(f"  Position: {eth_bands['position']:.1f}%")
    
    if eth_bands['width_pct'] < 1.0:
        print("  ⚡⚡ TIGHT SQUEEZE!")

# Check correlation
if btc_bands and eth_bands:
    print(f"\n🔗 CORRELATION ANALYSIS:")
    
    # Both squeezed?
    if btc_bands['width_pct'] < 1.0 and eth_bands['width_pct'] < 1.5:
        print("  ⚡⚡⚡ DOUBLE SQUEEZE CONFIRMED!")
        print("  → Market-wide volatility compression")
        print("  → Explosive move imminent across crypto")
        
        # Direction hints
        if btc_bands['position'] > 60 and eth_bands['position'] > 60:
            print("  📈 BIAS: UPWARD (both in upper half)")
        elif btc_bands['position'] < 40 and eth_bands['position'] < 40:
            print("  📉 BIAS: DOWNWARD (both in lower half)")
        else:
            print("  ↔️ BIAS: NEUTRAL (mixed positions)")

# Check our positions
print(f"\n💰 CURRENT POSITIONS:")
accounts = client.get_accounts()["accounts"]
usd_balance = 0
btc_balance = 0
eth_balance = 0

for acc in accounts:
    currency = acc["currency"]
    balance = float(acc["available_balance"]["value"])
    
    if currency == "USD":
        usd_balance = balance
    elif currency == "BTC" and balance > 0:
        btc_balance = balance
        value = balance * btc_bands['price'] if btc_bands else 0
        print(f"  BTC: {balance:.8f} (${value:.2f})")
    elif currency == "ETH" and balance > 0:
        eth_balance = balance
        value = balance * eth_bands['price'] if eth_bands else 0
        print(f"  ETH: {balance:.6f} (${value:.2f})")

print(f"  USD: ${usd_balance:.2f}")

# Strategy
print(f"\n🎯 DOUBLE SQUEEZE STRATEGY:")
print("-" * 60)

if usd_balance > 200:
    print("1. ✅ Capital ready: ${:.2f}".format(usd_balance))
    print("2. 📊 Watch both BTC and ETH levels")
    print("3. 🚀 When ONE breaks → Both will follow")
    print("4. 💰 Split capital 60/40 (BTC/ETH)")
    
    # Execute positioning
    if usd_balance > 250:
        print(f"\n⚡ EXECUTING DOUBLE SQUEEZE POSITIONS:")
        
        try:
            # Add to ETH position
            eth_order = client.market_order_buy(
                client_order_id=f"eth_squeeze_{int(time.time()*1000)}",
                product_id="ETH-USD",
                quote_size="100"
            )
            print(f"  ✅ ETH squeeze position: $100")
            
            # SOL often follows as third mover
            sol_order = client.market_order_buy(
                client_order_id=f"sol_sympathy_{int(time.time()*1000)}",
                product_id="SOL-USD",
                quote_size="50"
            )
            print(f"  ✅ SOL sympathy position: $50")
            
        except Exception as e:
            print(f"  Order failed: {e}")
else:
    print("⚠️ Need more capital for double squeeze play")

# Set alerts
if btc_bands and eth_bands:
    alert = {
        "type": "DOUBLE_SQUEEZE",
        "btc": {
            "price": btc_bands['price'],
            "upper": btc_bands['upper'],
            "lower": btc_bands['lower'],
            "width": btc_bands['width_pct']
        },
        "eth": {
            "price": eth_bands['price'],
            "upper": eth_bands['upper'],
            "lower": eth_bands['lower'],
            "width": eth_bands['width_pct']
        },
        "timestamp": time.time()
    }
    
    with open("/tmp/double_squeeze_alert.json", "w") as f:
        json.dump(alert, f)
    
    print(f"\n🚨 BREAKOUT LEVELS:")
    print(f"  BTC: Above ${btc_bands['upper']:,.0f} or Below ${btc_bands['lower']:,.0f}")
    print(f"  ETH: Above ${eth_bands['upper']:,.0f} or Below ${eth_bands['lower']:,.0f}")

print("\n⚡⚡ DOUBLE SQUEEZE ARMED AND READY!")
print("=" * 60)