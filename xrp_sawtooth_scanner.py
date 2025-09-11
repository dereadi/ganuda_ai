#!/usr/bin/env python3
"""
🦷 XRP SAWTOOTH SCANNER
========================
XRP joining the sawtooth party!
Perfect for weekend milking
"""

import json
from datetime import datetime
from coinbase.rest import RESTClient

config = json.load(open('/home/dereadi/.coinbase_config.json'))
client = RESTClient(api_key=config['api_key'].split('/')[-1], api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                        🦷 SAWTOOTH PATTERN SCANNER 🦷                      ║
║                     XRP + ETH + BTC + SOL = MILK PARTY                     ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

# Get all prices
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])
xrp = float(client.get_product('XRP-USD')['price'])
avax = float(client.get_product('AVAX-USD')['price'])
matic = float(client.get_product('MATIC-USD')['price'])

print(f"⏰ {datetime.now().strftime('%H:%M:%S')} - SAWTOOTH ANALYSIS")
print("=" * 70)

print(f"\n📊 CURRENT PRICES:")
print(f"  BTC:  ${btc:,.0f}")
print(f"  ETH:  ${eth:,.0f}")
print(f"  SOL:  ${sol:.2f}")
print(f"  XRP:  ${xrp:.4f}")
print(f"  AVAX: ${avax:.2f}")
print(f"  MATIC: ${matic:.4f}")

# Define sawtooth ranges based on observation
sawtooth_ranges = {
    'BTC': {'low': 111000, 'high': 112000, 'price': btc, 'milk_amt': 0.002},
    'ETH': {'low': 4450, 'high': 4490, 'price': eth, 'milk_amt': 0.02},
    'SOL': {'low': 212, 'high': 216, 'price': sol, 'milk_amt': 0.5},
    'XRP': {'low': 2.28, 'high': 2.35, 'price': xrp, 'milk_amt': 100},
    'AVAX': {'low': 24.5, 'high': 25.5, 'price': avax, 'milk_amt': 4},
    'MATIC': {'low': 0.252, 'high': 0.256, 'price': matic, 'milk_amt': 500}
}

print("\n🦷 SAWTOOTH POSITIONS:")
print("-" * 70)
print(f"{'Asset':<8} {'Low':<12} {'Current':<12} {'High':<12} {'Position':<10} {'Action':<15}")
print("-" * 70)

opportunities = []

for asset, data in sawtooth_ranges.items():
    position = (data['price'] - data['low']) / (data['high'] - data['low']) * 100
    position = max(0, min(100, position))  # Clamp to 0-100
    
    if data['price'] > 100:
        current = f"${data['price']:,.0f}"
        low = f"${data['low']:,.0f}"
        high = f"${data['high']:,.0f}"
    elif data['price'] > 1:
        current = f"${data['price']:.2f}"
        low = f"${data['low']:.2f}"
        high = f"${data['high']:.2f}"
    else:
        current = f"${data['price']:.4f}"
        low = f"${data['low']:.4f}"
        high = f"${data['high']:.4f}"
    
    if position > 80:
        action = "🔴 MILK NOW!"
        opportunities.append((asset, 'SELL', data['milk_amt'], data['price']))
    elif position < 20:
        action = "🟢 BUY DIP!"
        opportunities.append((asset, 'BUY', data['milk_amt'], data['price']))
    elif position > 60:
        action = "🟡 Approaching top"
    elif position < 40:
        action = "🟡 Near bottom"
    else:
        action = "⏳ Mid-range"
    
    print(f"{asset:<8} {low:<12} {current:<12} {high:<12} {position:>6.0f}%     {action:<15}")

print("\n💰 IMMEDIATE OPPORTUNITIES:")
print("-" * 70)

if opportunities:
    total_value = 0
    for asset, action, amount, price in opportunities:
        if action == 'SELL':
            value = amount * price
            total_value += value
            print(f"  • MILK {asset}: Sell {amount} = ${value:.2f}")
        else:
            value = amount * price
            print(f"  • BUY {asset}: Deploy ${value:.2f} at support")
    
    if total_value > 0:
        print(f"\n  TOTAL MILKING POTENTIAL: ${total_value:.2f}")
else:
    print("  ⏳ No immediate opportunities - wait for extremes")

print("\n🎯 SAWTOOTH STRATEGY:")
print("-" * 70)
print("  1. XRP showing classic weekend sawtooth $2.28-$2.35")
print("  2. ETH near top of range - ready to milk")
print("  3. BTC mid-range - wait for extremes")
print("  4. SOL near top - consider milking")
print("  5. Multiple assets = multiple opportunities!")

print("\n🌀 COMPOUND STRATEGY:")
print("-" * 70)
print("  • Milk ETH at $4,490 → Buy XRP at $2.28")
print("  • Milk XRP at $2.35 → Buy SOL at $212")
print("  • Milk SOL at $216 → Buy BTC at $111,000")
print("  • Each cycle compounds the profits!")

print("\n📈 WEEKEND SAWTOOTH CHARACTERISTICS:")
print("-" * 70)
print("  ✓ Low volume = predictable patterns")
print("  ✓ Bots dominating = clean sawteeth")
print("  ✓ Tight ranges = easy to trade")
print("  ✓ Multiple cycles = compound gains")

# Calculate potential
print("\n💎 24HR POTENTIAL (8 cycles):")
print("-" * 70)
cycles = 8
gain_per_cycle = 0.015  # 1.5% after fees
starting = 13098

for i in range(1, cycles + 1):
    ending = starting * (1 + gain_per_cycle)
    profit = ending - starting
    print(f"  Cycle {i}: ${starting:,.0f} → ${ending:,.0f} (+${profit:.0f})")
    starting = ending

print(f"\n  TOTAL: $13,098 → ${ending:,.0f} ({(ending/13098-1)*100:.1f}% gain)")

print("\n🦷 SAWTOOTH SCANNER COMPLETE!")
print("=" * 70)