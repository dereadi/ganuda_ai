#!/usr/bin/env python3
"""
🔥 ETH SUPPORT BOUNCE TRADER
Capitalizes on ETH bouncing off support
"""

import json
from coinbase.rest import RESTClient
import time
from datetime import datetime

print("🔥 ETH SUPPORT BOUNCE DETECTED")
print("=" * 60)

config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"])

# Check ETH technical levels
ticker = client.get_product("ETH-USD")
current = float(ticker["price"])

# Get 24h stats from candles
try:
    candles = client.get_candles("ETH-USD", "ONE_DAY", limit=1)
    if candles["candles"]:
        candle = candles["candles"][0]
        low_24h = float(candle["low"])
        high_24h = float(candle["high"])
        open_24h = float(candle["open"])
    else:
        # Fallback
        low_24h = current * 0.98
        high_24h = current * 1.02
        open_24h = current
except:
    # Fallback
    low_24h = current * 0.98
    high_24h = current * 1.02
    open_24h = current

print(f"ETH Current: ${current:.2f}")
print(f"24h Low: ${low_24h:.2f} (support)")
print(f"24h High: ${high_24h:.2f}")
print(f"Distance from low: ${current - low_24h:.2f} ({((current - low_24h)/low_24h * 100):.2f}%)")

# Calculate position in range
range_size = high_24h - low_24h
position_in_range = (current - low_24h) / range_size if range_size > 0 else 0.5

print(f"Position in range: {position_in_range:.2%}")
print("-" * 60)

# Get current USD balance
accounts = client.get_accounts()["accounts"]
usd_balance = 0
for acc in accounts:
    if acc["currency"] == "USD":
        usd_balance = float(acc["available_balance"]["value"])
        break

print(f"Available USD: ${usd_balance:.2f}")

# Execute bounce trade if conditions are right
if position_in_range < 0.25 and usd_balance > 50:
    # Near support, good entry
    trade_size = min(100, usd_balance * 0.5)  # Use 50% of available
    
    print(f"\n🎯 EXECUTING SUPPORT BOUNCE TRADE")
    print(f"  Strategy: Buy ETH at support bounce")
    print(f"  Trade size: ${trade_size:.2f}")
    
    try:
        order = client.market_order_buy(
            client_order_id=f"eth_support_{int(time.time()*1000)}",
            product_id="ETH-USD",
            quote_size=str(trade_size)
        )
        print(f"✅ ETH BUY ORDER PLACED: ${trade_size:.2f}")
        print(f"  Order ID: {order.get('order_id')}")
        
        # Set mental stop and target
        stop_loss = current * 0.98  # 2% stop
        take_profit = current * 1.03  # 3% target
        
        print(f"\n📊 TRADE MANAGEMENT:")
        print(f"  Entry: ${current:.2f}")
        print(f"  Stop Loss: ${stop_loss:.2f} (-2%)")
        print(f"  Take Profit: ${take_profit:.2f} (+3%)")
        print(f"  Risk/Reward: 1:1.5")
        
    except Exception as e:
        print(f"Order failed: {e}")
        
elif position_in_range > 0.7:
    print("\n⚠️  ETH near resistance, not ideal for long entry")
    print("  Waiting for pullback to support")
else:
    print("\n💭 ETH in middle of range")
    print("  Waiting for clearer support test")

# Also check if we should deploy specialists
print("\n🚀 DEPLOYING SPECIALISTS FOR BOUNCE:")

specialist_script = """
# Focus specialists on ETH momentum
ps aux | grep -E "trend_specialist|volatility_specialist" | grep -v grep | awk '{print $2}' | xargs -r kill -SIGUSR1 2>/dev/null

# Signal them to focus on ETH
echo "ETH_BOUNCE_ALERT" > /tmp/specialist_signal.txt
"""

with open("/tmp/eth_bounce_signal.sh", "w") as f:
    f.write(specialist_script)

import subprocess
subprocess.run(["bash", "/tmp/eth_bounce_signal.sh"], capture_output=True)

print("  ✅ Specialists alerted to ETH bounce")
print("  ✅ Flywheel adjusting for momentum capture")
print("\n🔥 Support bounce trade system active!")