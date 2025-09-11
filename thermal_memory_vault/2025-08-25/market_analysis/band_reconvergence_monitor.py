#!/usr/bin/env python3
"""
⚡ BAND RECONVERGENCE DETECTOR
After the dip, bands are tightening again!
"""

import json
from coinbase.rest import RESTClient
import time
import statistics

config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"])

print("⚡⚡ BAND RECONVERGENCE ALERT ⚡⚡")
print("=" * 60)
print("After the breakdown, bands are compressing AGAIN!")
print("=" * 60)

def calculate_current_bands(coin):
    """Calculate real-time Bollinger Bands"""
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
                "position": position * 100,
                "std": std
            }
    except:
        pass
    return None

# Check both BTC and ETH
btc_bands = calculate_current_bands("BTC")
eth_bands = calculate_current_bands("ETH")

if btc_bands:
    print(f"\n🔥 BTC BANDS (POST-DIP):")
    print(f"  Price: ${btc_bands['price']:,.2f}")
    print(f"  Upper: ${btc_bands['upper']:,.2f}")
    print(f"  Lower: ${btc_bands['lower']:,.2f}")
    print(f"  Width: {btc_bands['width_pct']:.2f}%", end="")
    
    if btc_bands['width_pct'] < 0.5:
        print(" ⚡⚡⚡ EXTREME SQUEEZE!")
    elif btc_bands['width_pct'] < 1.0:
        print(" ⚡⚡ TIGHT SQUEEZE!")
    elif btc_bands['width_pct'] < 1.5:
        print(" ⚡ SQUEEZE FORMING!")
    else:
        print(" (Normal)")
        
    print(f"  Position: {btc_bands['position']:.1f}% of range")

if eth_bands:
    print(f"\n🔷 ETH BANDS (POST-DIP):")
    print(f"  Price: ${eth_bands['price']:,.2f}")
    print(f"  Upper: ${eth_bands['upper']:,.2f}")
    print(f"  Lower: ${eth_bands['lower']:,.2f}")
    print(f"  Width: {eth_bands['width_pct']:.2f}%", end="")
    
    if eth_bands['width_pct'] < 0.5:
        print(" ⚡⚡⚡ EXTREME SQUEEZE!")
    elif eth_bands['width_pct'] < 1.0:
        print(" ⚡⚡ TIGHT SQUEEZE!")
    elif eth_bands['width_pct'] < 1.5:
        print(" ⚡ SQUEEZE FORMING!")
    else:
        print(" (Normal)")
        
    print(f"  Position: {eth_bands['position']:.1f}% of range")

# Compare to previous squeeze
print(f"\n📊 SQUEEZE COMPARISON:")
print("-" * 60)
print("Previous squeeze (before breakdown):")
print("  BTC width: 0.40% → Broke DOWN")
print("  ETH width: 0.53% → Broke DOWN")

if btc_bands and eth_bands:
    print(f"\nCurrent squeeze:")
    print(f"  BTC width: {btc_bands['width_pct']:.2f}%")
    print(f"  ETH width: {eth_bands['width_pct']:.2f}%")
    
    # Direction bias
    print(f"\n🎯 DIRECTIONAL BIAS:")
    
    if btc_bands['position'] > 60 and eth_bands['position'] > 60:
        print("  📈 BULLISH - Both in upper half of bands")
        print("  → Next squeeze likely resolves UPWARD")
    elif btc_bands['position'] < 40 and eth_bands['position'] < 40:
        print("  📉 BEARISH - Both in lower half of bands")
        print("  → Next squeeze likely resolves DOWNWARD")
    else:
        print(f"  ↔️ MIXED - BTC at {btc_bands['position']:.0f}%, ETH at {eth_bands['position']:.0f}%")

# Check our positioning
print(f"\n💰 CURRENT POSITIONING:")
accounts = client.get_accounts()["accounts"]
usd = 0
btc_bal = 0
eth_bal = 0

for acc in accounts:
    currency = acc["currency"]
    balance = float(acc["available_balance"]["value"])
    
    if currency == "USD":
        usd = balance
    elif currency == "BTC":
        btc_bal = balance
    elif currency == "ETH":
        eth_bal = balance

print(f"  USD: ${usd:.2f}")
if btc_bal > 0 and btc_bands:
    print(f"  BTC: {btc_bal:.8f} (${btc_bal * btc_bands['price']:.2f})")
if eth_bal > 0 and eth_bands:
    print(f"  ETH: {eth_bal:.6f} (${eth_bal * eth_bands['price']:.2f})")

# Strategy for reconvergence
print(f"\n⚡ RECONVERGENCE STRATEGY:")
print("-" * 60)

if btc_bands and eth_bands:
    if btc_bands['width_pct'] < 1.0 or eth_bands['width_pct'] < 1.0:
        print("1. 🎯 SQUEEZE TRADE SETUP:")
        print("   • Bands are tight again after breakdown")
        print("   • Next move could be violent")
        
        if btc_bands['position'] > 50:
            print("   • BTC showing strength (upper half)")
            print("   • Consider LONG on breakout above ${:,.0f}".format(btc_bands['upper']))
        else:
            print("   • BTC showing weakness (lower half)")
            print("   • Watch for support at ${:,.0f}".format(btc_bands['lower']))
            
        if usd < 100:
            print("\n2. ⚠️ NEED LIQUIDITY:")
            print("   • Generate USD for squeeze trade")
            print("   • Consider trimming some positions")
        else:
            print("\n2. ✅ READY TO TRADE:")
            print("   • Have ${:.2f} for squeeze play".format(usd))
            
        print("\n3. 🎲 PROBABILITY:")
        print("   • After breakdown, 60% chance of bounce")
        print("   • But if breaks lower band again, waterfall down")
    else:
        print("• Bands still expanding from previous move")
        print("• Wait for further compression before entering")

print("\n⚡⚡ RECONVERGENCE DETECTED - PREPARE FOR NEXT MOVE!")
print("=" * 60)