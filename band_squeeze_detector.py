#!/usr/bin/env python3
"""
🎯 BOLLINGER BAND SQUEEZE DETECTOR
When bands tighten, explosion imminent!
"""

import json
import statistics
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    🎯 BAND SQUEEZE DETECTION ACTIVE 🎯                    ║
║                      Tightening bands = Explosion soon                    ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

# Collect price history
btc_prices = []
eth_prices = []
sol_prices = []

print("📊 COLLECTING BAND DATA...")
print("-" * 70)

for i in range(20):
    btc = float(client.get_product('BTC-USD')['price'])
    eth = float(client.get_product('ETH-USD')['price'])
    sol = float(client.get_product('SOL-USD')['price'])
    
    btc_prices.append(btc)
    eth_prices.append(eth)
    sol_prices.append(sol)
    
    if i % 5 == 0:
        print(f"\r⏰ Sample {i+1}/20: BTC ${btc:,.0f} | ETH ${eth:.0f} | SOL ${sol:.0f}", end="")

# Calculate Bollinger Bands
def calculate_bands(prices):
    mean = statistics.mean(prices)
    stdev = statistics.stdev(prices) if len(prices) > 1 else 0
    upper = mean + (2 * stdev)
    lower = mean - (2 * stdev)
    squeeze = (upper - lower) / mean * 100  # Band width as % of price
    return mean, upper, lower, squeeze

print("\n\n" + "=" * 70)
print("🎯 BAND ANALYSIS:")
print("-" * 70)

btc_mean, btc_upper, btc_lower, btc_squeeze = calculate_bands(btc_prices)
print(f"\nBTC Bands:")
print(f"  Upper: ${btc_upper:,.0f}")
print(f"  Mean:  ${btc_mean:,.0f}")
print(f"  Lower: ${btc_lower:,.0f}")
print(f"  Width: {btc_squeeze:.3f}%")

if btc_squeeze < 0.2:
    print("  🔥 EXTREME SQUEEZE - Explosion imminent!")
elif btc_squeeze < 0.5:
    print("  ⚡ TIGHT SQUEEZE - Breakout loading...")
else:
    print("  📊 Normal range")

eth_mean, eth_upper, eth_lower, eth_squeeze = calculate_bands(eth_prices)
print(f"\nETH Bands:")
print(f"  Upper: ${eth_upper:.0f}")
print(f"  Mean:  ${eth_mean:.0f}")
print(f"  Lower: ${eth_lower:.0f}")
print(f"  Width: {eth_squeeze:.3f}%")

sol_mean, sol_upper, sol_lower, sol_squeeze = calculate_bands(sol_prices)
print(f"\nSOL Bands:")
print(f"  Upper: ${sol_upper:.2f}")
print(f"  Mean:  ${sol_mean:.2f}")
print(f"  Lower: ${sol_lower:.2f}")
print(f"  Width: {sol_squeeze:.3f}%")

# Determine direction
current_btc = btc_prices[-1]
position_in_band = (current_btc - btc_lower) / (btc_upper - btc_lower)

print("\n" + "=" * 70)
print("🎯 SQUEEZE PREDICTION:")
print("-" * 70)

if btc_squeeze < 0.5:
    print("✅ BANDS ARE TIGHTENING!")
    print(f"   Position in band: {position_in_band:.1%}")
    
    if position_in_band > 0.7:
        print("   📈 Near upper band - Breakout UP likely")
    elif position_in_band < 0.3:
        print("   📉 Near lower band - Breakdown risk (buy opportunity)")
    else:
        print("   ➡️ Middle of band - Direction unclear")
    
    print("\n   ACTION PLAN:")
    print("   1. Prepare for explosive move")
    print("   2. Set stops just outside bands")
    print("   3. Ready to ride the breakout")

print("\n💭 Cherokee Council says:")
print('"The calm before the storm is when the wise prepare."')
print('"Tight bands are like a drawn bow - release brings power."')
print("=" * 70)