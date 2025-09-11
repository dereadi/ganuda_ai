#!/usr/bin/env python3
"""
📊 MARKET COMPARISON & OPPORTUNITY ANALYSIS
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"])

print("📊 CRYPTO MARKET ANALYSIS - AFTERNOON SESSION")
print("=" * 70)
print(f"Time: {datetime.now().strftime('%I:%M %p CST')}")
print("=" * 70)

# Major coins to analyze
coins = ["BTC", "ETH", "SOL", "AVAX", "MATIC", "DOGE", "LINK", "DOT", "ATOM", "NEAR"]

market_data = []

for coin in coins:
    try:
        ticker = client.get_product(f"{coin}-USD")
        price = float(ticker["price"])
        
        # Get 24h candle for stats
        candles = client.get_candles(f"{coin}-USD", "ONE_DAY", limit=2)
        if candles["candles"] and len(candles["candles"]) >= 2:
            current_candle = candles["candles"][0]
            prev_candle = candles["candles"][1]
            
            high_24h = float(current_candle["high"])
            low_24h = float(current_candle["low"])
            open_24h = float(prev_candle["close"])  # Previous close is today's open
            
            change_24h = ((price - open_24h) / open_24h) * 100
            range_size = high_24h - low_24h
            position_in_range = (price - low_24h) / range_size if range_size > 0 else 0.5
            volatility = (range_size / price) * 100
            
            market_data.append({
                "coin": coin,
                "price": price,
                "change_24h": change_24h,
                "position": position_in_range,
                "volatility": volatility,
                "high": high_24h,
                "low": low_24h
            })
    except:
        pass

# Sort by 24h change
market_data.sort(key=lambda x: x["change_24h"], reverse=True)

print("\n🏆 TOP GAINERS:")
print("-" * 70)
print(f"{'Coin':<6} {'Price':>12} {'24h %':>8} {'Position':>10} {'Volatility':>10}")
print("-" * 70)

for data in market_data[:5]:
    pos_emoji = "🔥" if data["position"] > 0.7 else "❄️" if data["position"] < 0.3 else "➡️"
    trend = "📈" if data["change_24h"] > 0 else "📉"
    
    print(f"{data['coin']:<6} ${data['price']:>11.2f} {data['change_24h']:>7.2f}% "
          f"{pos_emoji} {data['position']:>6.1%} {data['volatility']:>9.2f}%")

print("\n📉 BIGGEST LOSERS (Potential Bounces):")
print("-" * 70)

for data in market_data[-3:]:
    pos_emoji = "🔥" if data["position"] > 0.7 else "❄️" if data["position"] < 0.3 else "➡️"
    
    print(f"{data['coin']:<6} ${data['price']:>11.2f} {data['change_24h']:>7.2f}% "
          f"{pos_emoji} {data['position']:>6.1%} {data['volatility']:>9.2f}%")

# Our positions
print("\n💼 OUR POSITIONS:")
print("-" * 70)

accounts = client.get_accounts()["accounts"]
our_positions = {}

for acc in accounts:
    balance = float(acc["available_balance"]["value"])
    if balance > 0:
        currency = acc["currency"]
        if currency in coins:
            our_positions[currency] = balance
        elif currency == "USD":
            our_positions["USD"] = balance

for coin in our_positions:
    if coin != "USD":
        # Find market data
        coin_data = next((d for d in market_data if d["coin"] == coin), None)
        if coin_data:
            value = our_positions[coin] * coin_data["price"]
            print(f"{coin:<6} {our_positions[coin]:>12.4f} units | ${value:>10.2f} | "
                  f"{coin_data['change_24h']:>+6.2f}% | Pos: {coin_data['position']:.1%}")

if "USD" in our_positions:
    print(f"USD    ${our_positions['USD']:>10.2f}")

# Trading signals
print("\n🎯 TRADING SIGNALS:")
print("-" * 70)

signals = []

for data in market_data:
    # Oversold bounce candidates
    if data["position"] < 0.25 and data["volatility"] > 3:
        signals.append(f"🟢 {data['coin']}: OVERSOLD BOUNCE (at {data['position']:.1%} of range)")
    
    # Overbought fade candidates
    elif data["position"] > 0.85 and data["change_24h"] > 5:
        signals.append(f"🔴 {data['coin']}: OVERBOUGHT FADE (at {data['position']:.1%} of range)")
    
    # Breakout candidates
    elif data["position"] > 0.9 and data["volatility"] > 5:
        signals.append(f"🚀 {data['coin']}: BREAKOUT ALERT (testing highs)")

for signal in signals[:5]:
    print(f"  {signal}")

print("\n📈 MARKET SUMMARY:")
print("-" * 70)

avg_change = sum(d["change_24h"] for d in market_data) / len(market_data)
avg_volatility = sum(d["volatility"] for d in market_data) / len(market_data)

if avg_change > 2:
    print("  🔥 BULLISH MARKET - Risk-on environment")
elif avg_change < -2:
    print("  ❄️ BEARISH MARKET - Look for oversold bounces")
else:
    print("  ➡️ NEUTRAL MARKET - Range trading opportunities")

print(f"  Average 24h change: {avg_change:+.2f}%")
print(f"  Average volatility: {avg_volatility:.2f}%")

# ETH specific update
eth_data = next((d for d in market_data if d["coin"] == "ETH"), None)
if eth_data:
    print(f"\n🔷 ETH UPDATE:")
    print(f"  Current: ${eth_data['price']:.2f}")
    print(f"  Position in range: {eth_data['position']:.1%}")
    print(f"  Our entry: $4575.70")
    pnl = ((eth_data['price'] - 4575.70) / 4575.70) * 100
    print(f"  P&L: {pnl:+.2f}%")
    
    if eth_data['position'] < 0.35:
        print("  ✅ Near support - good bounce zone!")
    elif eth_data['position'] > 0.65:
        print("  ⚠️ Moving away from support")

print("=" * 70)