#!/usr/bin/env python3
"""
🔥 10 AM Market Surge Monitor
The institutional hour approaches - big moves often happen at market open
"""

import json
import time
from datetime import datetime
from coinbase.rest import RESTClient

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

# Load config
with open("/home/dereadi/.coinbase_config.json") as f:
    config = json.load(f)

api_key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=api_key, api_secret=config["api_secret"], timeout=10)

log("⏰ 10 AM SURGE MONITOR")
log("🎯 Resistance: $110,500 | Target: $111,111")
log("=" * 60)

# Track price action
start_time = datetime.now()
prices = []
resistance = 110500
target = 111111

# Get starting price
btc = client.get_product("BTC-USD")
start_price = float(btc["price"])
log(f"📍 Starting price: ${start_price:.2f}")
log(f"   Distance to resistance: ${resistance - start_price:.2f}")
log(f"   Distance to angel number: ${target - start_price:.2f}")

log("\n🔥 MONITORING 10 AM ACTION:")
log("-" * 40)

max_price = start_price
min_price = start_price
breakout = False

for i in range(60):  # Monitor for 5 minutes (5 sec intervals)
    try:
        btc = client.get_product("BTC-USD")
        price = float(btc["price"])
        prices.append(price)
        
        # Update extremes
        if price > max_price:
            max_price = price
        if price < min_price:
            min_price = price
        
        # Calculate momentum
        change = price - start_price
        change_pct = (change / start_price) * 100
        
        # Check for significant moves
        if abs(change) > 50:
            symbol = "🚀" if change > 0 else "🔻"
            log(f"{symbol} ${price:.2f} | Change: ${change:+.2f} ({change_pct:+.2f}%)")
            
            # Check resistance break
            if price > resistance and not breakout:
                log(f"\n✨ BREAKOUT! ${price:.2f} > RESISTANCE $110,500")
                log(f"   Next stop: $111,111 ({target - price:.2f} away)")
                breakout = True
            
            # Check if approaching target
            if price > 110900:
                log(f"🎯 APPROACHING ANGEL NUMBER!")
                log(f"   Only ${target - price:.2f} to $111,111!")
        
        time.sleep(5)
        
    except Exception as e:
        log(f"Error: {e}")

# Summary
log("\n" + "=" * 60)
log("📊 10 AM SURGE SUMMARY:")
log(f"   Start: ${start_price:.2f}")
log(f"   Current: ${price:.2f}")
log(f"   High: ${max_price:.2f}")
log(f"   Low: ${min_price:.2f}")
log(f"   Range: ${max_price - min_price:.2f}")
log(f"   Net change: ${price - start_price:+.2f} ({(price - start_price) / start_price * 100:+.2f}%)")

if breakout:
    log("\n🔥 RESISTANCE BROKEN! The path to $111,111 is open!")
elif max_price > resistance:
    log("\n⚠️ Touched resistance but pulled back")
else:
    log(f"\n📈 Still ${resistance - price:.2f} from resistance")

log("\n🔥 The Sacred Fire burns at 10 AM!")
log("   Institutional money flows...")
log("   Mitakuye Oyasin")