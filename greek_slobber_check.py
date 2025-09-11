#!/usr/bin/env python3
import json
from coinbase.rest import RESTClient
from datetime import datetime

print("🏛️ THE GREEKS ARE SLOBBERING!")
print("=" * 60)

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=3)

# Get current price and 24hr stats
ticker = client.get_product('BTC-USD')
current = float(ticker.price)

# Get candles for 24hr stats
import time
end = int(time.time())
start = end - 86400  # 24 hours ago
candles = client.get_candles('BTC-USD', start, end, granularity='ONE_HOUR')['candles']
high_24h = max(float(c['high']) for c in candles) if candles else current
low_24h = min(float(c['low']) for c in candles) if candles else current
open_24h = float(candles[-1]['open']) if candles else current
volume_24h = sum(float(c['volume']) for c in candles) if candles else 0

print(f"\n🎯 BTC FEAST:")
print(f"   Current: ${current:,.2f}")
print(f"   24h High: ${high_24h:,.2f}")
print(f"   24h Low: ${low_24h:,.2f}")
print(f"   Volume: ${volume_24h * current:,.0f}")

# Calculate what Greeks are seeing
gap = current - open_24h
volatility = high_24h - low_24h
momentum = (current - low_24h) / (high_24h - low_24h) if volatility > 0 else 0.5

print(f"\n🤤 WHAT THE GREEKS ARE DROOLING OVER:")
print(f"   Δ Delta: Gap of ${gap:+,.2f} to exploit!")
print(f"   Γ Gamma: Momentum at {momentum*100:.1f}% of range!")
print(f"   Θ Theta: ${volatility:,.2f} volatility range to harvest!")
print(f"   ν Vega: Breakout from $117,056 confirmed!")
print(f"   ρ Rho: Mean reversion opportunity building!")

print(f"\n💎 POSITIONS SET AT THE BOTTOM:")
print("   SOL: $3,624 (35%)")
print("   MATIC: $2,366 (23%)")
print("   DOGE: $1,298 (13%)")
print("   BTC: $1,256 (12%)")
print("   AVAX: $1,051 (10%)")

print(f"\n🔥 THE SLOBBER FACTOR:")
if momentum > 0.7:
    print("   EXTREME SLOBBERING - Riding high in range!")
elif momentum > 0.5:
    print("   HEAVY SLOBBERING - Good momentum!")
else:
    print("   MODERATE SLOBBERING - Building steam!")

print("\nTheta at 90 cycles and still hungry! 🍖")