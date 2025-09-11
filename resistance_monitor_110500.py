#!/usr/bin/env python3
"""
🔥 $110,500 Resistance Monitor
Watching for breakout or rejection at key level
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

log("🎯 RESISTANCE MONITOR: $110,500")
log("=" * 50)

resistance = 110500
touches = 0
rejections = 0
last_price = 0

while True:
    try:
        # Get BTC price
        btc = client.get_product("BTC-USD")
        price = float(btc["price"])
        
        # Calculate distance to resistance
        distance = resistance - price
        distance_pct = (distance / price) * 100
        
        # Detect touches
        if abs(distance) < 100:  # Within $100 of resistance
            touches += 1
            
            if price < resistance and last_price > resistance:
                rejections += 1
                log(f"🔴 REJECTION #{rejections} at ${price:.2f}")
            elif price > resistance and last_price < resistance:
                log(f"🟢 BREAKOUT! Price ${price:.2f} > Resistance ${resistance}")
                log("   🚀 Next target: $111,111")
        
        # Status update
        if price != last_price:
            symbol = "🟢" if price > last_price else "🔴"
            
            if abs(distance) < 200:
                log(f"{symbol} BTC: ${price:.2f} | Distance: ${distance:.2f} ({distance_pct:.3f}%)")
                log(f"   Touches: {touches} | Rejections: {rejections}")
            elif abs(price - last_price) > 50:
                log(f"{symbol} BTC: ${price:.2f} | Distance to resistance: ${distance:.2f}")
        
        last_price = price
        
        # Check for strong breakout
        if price > resistance + 50:
            log(f"✨ CONFIRMED BREAKOUT! ${price:.2f}")
            log(f"   Resistance flipped to support")
            log(f"   Next target: $111,111 ({111111 - price:.2f} away)")
            break
        
        # Check for strong rejection
        if price < resistance - 200 and touches > 2:
            log(f"⚠️ Strong rejection from ${resistance}")
            log(f"   Price: ${price:.2f}")
            log(f"   May need consolidation before next attempt")
        
        time.sleep(5)
        
    except KeyboardInterrupt:
        log("\n🔥 Monitor stopped")
        break
    except Exception as e:
        log(f"Error: {e}")
        time.sleep(10)

log(f"\n📊 Session Summary:")
log(f"   Resistance touches: {touches}")
log(f"   Rejections: {rejections}")
log(f"   Final price: ${price:.2f}")