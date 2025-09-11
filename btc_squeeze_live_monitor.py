#!/usr/bin/env python3
"""
⚡ LIVE BTC SQUEEZE MONITOR
"""

import json
from coinbase.rest import RESTClient
import time

config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"])

print("⚡ BTC SQUEEZE LIVE MONITOR")
print("=" * 50)

# Bands from earlier calculation
upper_band = 112755
lower_band = 112231
band_width = upper_band - lower_band

print(f"Bands: ${lower_band:,.0f} - ${upper_band:,.0f} (${band_width:.0f} wide)")
print("Monitoring for breakout...")
print("-" * 50)

# Monitor for 10 updates
for i in range(10):
    ticker = client.get_product("BTC-USD")
    btc_price = float(ticker["price"])
    
    # Calculate position
    position = (btc_price - lower_band) / band_width * 100
    
    # Check for breakout
    if btc_price > upper_band:
        print(f"\n🚀🚀🚀 BREAKOUT UP DETECTED! 🚀🚀🚀")
        print(f"BTC: ${btc_price:,.2f} > ${upper_band:,.2f}")
        print("ACTION: BUY IMMEDIATELY!")
        print("Target: $115,000+ (2.5% move)")
        break
    elif btc_price < lower_band:
        print(f"\n📉📉📉 BREAKDOWN DETECTED! 📉📉📉")
        print(f"BTC: ${btc_price:,.2f} < ${lower_band:,.2f}")
        print("ACTION: SELL ALL LONGS!")
        break
    else:
        # Still in squeeze
        arrow = "↑" if position > 50 else "↓" if position < 50 else "→"
        print(f"[{i+1:2}/10] ${btc_price:,.2f} {arrow} Position: {position:.1f}%")
    
    if i < 9:
        time.sleep(5)  # Check every 5 seconds

# Final check on liquidity
print("\n💰 LIQUIDITY CHECK:")
accounts = client.get_accounts()["accounts"]
for acc in accounts:
    if acc["currency"] == "USD":
        usd = float(acc["available_balance"]["value"])
        print(f"USD Available: ${usd:.2f}")
        
        if usd > 200:
            print("✅ Ready to trade breakout!")
        elif usd > 50:
            print("⚠️ Limited capital - be selective")
        else:
            print("🚨 Need more USD for breakout trade")
        break

print("=" * 50)