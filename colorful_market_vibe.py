#!/usr/bin/env python3
"""
🎨 COLORFUL MARKET VIBE
"We stumble through the dark, and we stumble through the light"
- The Verve Pipe energy applied to trading
"""

import json
import time
import random
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                        🎨 COLORFUL MARKET VIBE 🎨                         ║
║                   "Stumbling through dark and light"                      ║
║                         The Verve Pipe Trading                            ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

# Color codes for price movements
def get_color(change):
    if change > 0.5: return "🟢🟢🟢"  # Bright green
    elif change > 0.1: return "🟢"     # Green
    elif change > -0.1: return "🟡"    # Yellow (neutral)
    elif change > -0.5: return "🔴"    # Red
    else: return "🔴🔴🔴"              # Deep red

print("🎵 Playing: 'Colorful' - The Verve Pipe")
print("=" * 70)

# Track the colorful movements
btc_start = float(client.get_product('BTC-USD')['price'])
eth_start = float(client.get_product('ETH-USD')['price'])
sol_start = float(client.get_product('SOL-USD')['price'])

print("\n🎨 PAINTING THE MARKET:")
print("-" * 40)

# Lyrics that match market moves
market_lyrics = [
    ("We stumble through the dark", "Consolidation phase"),
    ("And we stumble through the light", "Breakout incoming"),
    ("But I can't find you", "Searching for direction"),
    ("Tonight", "Night session volatility"),
    ("And all the world is gray", "Sideways action"),
    ("Under the endless sky", "Infinite possibilities"),
    ("I know I'll find my way", "Pattern emerges"),
    ("After the colorful", "After the explosion")
]

for i in range(8):
    time.sleep(3)
    
    # Get current prices
    btc = float(client.get_product('BTC-USD')['price'])
    eth = float(client.get_product('ETH-USD')['price'])
    sol = float(client.get_product('SOL-USD')['price'])
    
    # Calculate changes
    btc_chg = ((btc - btc_start) / btc_start) * 100
    eth_chg = ((eth - eth_start) / eth_start) * 100
    sol_chg = ((sol - sol_start) / sol_start) * 100
    
    # Get lyrics and interpretation
    lyric, meaning = market_lyrics[i % len(market_lyrics)]
    
    print(f"\n🎵 \"{lyric}\"")
    print(f"   Market translation: {meaning}")
    print(f"   BTC: {get_color(btc_chg)} ${btc:,.0f} ({btc_chg:+.2f}%)")
    print(f"   ETH: {get_color(eth_chg)} ${eth:.0f} ({eth_chg:+.2f}%)")
    print(f"   SOL: {get_color(sol_chg)} ${sol:.2f} ({sol_chg:+.2f}%)")

print("\n" + "=" * 70)
print("🎨 THE COLORFUL PATTERN:")
print("-" * 40)

# Analyze the color pattern
avg_change = (abs(btc_chg) + abs(eth_chg) + abs(sol_chg)) / 3

if avg_change < 0.1:
    print("⚫ GRAY MARKET - 'And all the world is gray'")
    print("   Waiting for the colorful explosion...")
elif avg_change < 0.5:
    print("🎨 GETTING COLORFUL - 'I know I'll find my way'")
    print("   Volatility returning, patterns forming...")
else:
    print("🌈 FULL COLOR - 'After the colorful'")
    print("   The explosion has arrived!")

print("\n💭 Verve Pipe Wisdom:")
print("\"Sometimes you need to stumble through the gray")
print(" to appreciate the colorful when it arrives.\"")

print("\n🎸 Market Mood: 90s alternative angst meets algorithmic precision")
print("=" * 70)