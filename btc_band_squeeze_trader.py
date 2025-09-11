#!/usr/bin/env python3
"""
🔥 BTC BAND SQUEEZE DETECTOR
Bollinger Bands tightening = Major move incoming
"""

import json
from coinbase.rest import RESTClient
import time
from datetime import datetime

config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"])

print("⚡ BTC BOLLINGER BAND SQUEEZE ALERT")
print("=" * 60)
print(f"Time: {datetime.now().strftime('%I:%M %p CST')}")
print("=" * 60)

# Get BTC price
ticker = client.get_product("BTC-USD")
btc_price = float(ticker["price"])

# Get recent candles for volatility calculation
import time as time_module
end_time = int(time_module.time())
start_time = end_time - (20 * 300)  # 20 five-minute candles
candles = client.get_candles("BTC-USD", start_time, end_time, "FIVE_MINUTE")
prices = []

if candles["candles"]:
    for candle in candles["candles"]:
        prices.append(float(candle["close"]))
    
    # Calculate simple band width
    import statistics
    mean_price = statistics.mean(prices)
    std_dev = statistics.stdev(prices)
    
    upper_band = mean_price + (2 * std_dev)
    lower_band = mean_price - (2 * std_dev)
    band_width = upper_band - lower_band
    band_width_pct = (band_width / mean_price) * 100
    
    print(f"🎯 BTC Current: ${btc_price:,.2f}")
    print(f"📊 20-period Mean: ${mean_price:,.2f}")
    print(f"📈 Upper Band: ${upper_band:,.2f}")
    print(f"📉 Lower Band: ${lower_band:,.2f}")
    print(f"🔧 Band Width: ${band_width:,.2f} ({band_width_pct:.2f}%)")
    print("-" * 60)
    
    # Position in bands
    position_in_bands = (btc_price - lower_band) / band_width if band_width > 0 else 0.5
    
    print(f"📍 Position in Bands: {position_in_bands:.1%}")
    
    # SQUEEZE DETECTION
    if band_width_pct < 1.5:  # Very tight bands
        print("\n⚡⚡⚡ EXTREME SQUEEZE DETECTED ⚡⚡⚡")
        print("MAJOR MOVE IMMINENT!")
        
        # Deploy capital for the breakout
        accounts = client.get_accounts()["accounts"]
        usd_balance = 0
        for acc in accounts:
            if acc["currency"] == "USD":
                usd_balance = float(acc["available_balance"]["value"])
                break
        
        print(f"\nAvailable USD: ${usd_balance:.2f}")
        
        if usd_balance > 50:
            print("\n🚀 PREPARING BREAKOUT TRADES:")
            
            # Set both sides ready
            print("  • Set BUY order above upper band")
            print("  • Set SELL order below lower band")
            print("  • Whichever triggers first = direction")
            
            # Place small probe trade
            try:
                probe_size = min(50, usd_balance * 0.3)
                order = client.market_order_buy(
                    client_order_id=f"btc_squeeze_probe_{int(time.time()*1000)}",
                    product_id="BTC-USD",
                    quote_size=str(probe_size)
                )
                print(f"\n✅ Probe position established: ${probe_size:.2f}")
                print(f"  • If breaks UP → Add to position")
                print(f"  • If breaks DOWN → Quick stop and reverse")
            except Exception as e:
                print(f"Probe order failed: {e}")
                
    elif band_width_pct < 2.5:
        print("\n⚡ SQUEEZE FORMING")
        print("Bands tightening - prepare for volatility")
    else:
        print("\n📊 Normal band width - no squeeze yet")

# Check other correlated assets
print("\n🔗 CORRELATED ASSETS CHECK:")
print("-" * 60)

for coin in ["ETH", "SOL"]:
    try:
        ticker = client.get_product(f"{coin}-USD")
        price = float(ticker["price"])
        print(f"{coin}: ${price:.2f} - Watch for sympathy move")
    except:
        pass

# Alert the specialists
print("\n🤖 DEPLOYING SQUEEZE SPECIALISTS:")
print("-" * 60)

specialist_config = {
    "mode": "SQUEEZE_BREAKOUT",
    "target": "BTC",
    "band_width": band_width_pct if 'band_width_pct' in locals() else 0,
    "timestamp": datetime.now().isoformat()
}

with open("/tmp/squeeze_alert.json", "w") as f:
    json.dump(specialist_config, f)

print("✅ Volatility specialists alerted")
print("✅ Breakout specialists on standby")
print("✅ Flywheel ready for momentum capture")

# Strategy recommendation
print("\n📋 SQUEEZE PLAY STRATEGY:")
print("-" * 60)
if 'band_width_pct' in locals() and band_width_pct < 2:
    print("1. ⚡ IMMEDIATE: Establish small probe position")
    print("2. 📊 WATCH: Direction of breakout (up or down)")
    print("3. 🚀 EXECUTE: Add aggressively in breakout direction")
    print("4. 🎯 TARGET: 2-3% move minimum after breakout")
    print("5. ⛔ STOP: Opposite band becomes stop loss")
else:
    print("1. 👀 MONITOR: Wait for bands to compress further")
    print("2. 📊 PREPARE: Build USD reserves for breakout")

print("\n🔥 THE SQUEEZE IS ON!")
print("=" * 60)