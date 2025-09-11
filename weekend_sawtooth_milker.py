#!/usr/bin/env python3
"""
🪚🦀 WEEKEND SAWTOOTH MILKER - Low Volume Opportunity
=====================================================
Exploits predictable weekend sawtooth patterns in low volume
Perfect for crawdads to nibble profits while whales sleep
"""

import json
import time
from datetime import datetime
from coinbase.rest import RESTClient

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                  🪚 WEEKEND SAWTOOTH MILKER ACTIVATED 🪚                   ║
║                    Low Volume = Predictable Patterns                       ║
║                      Crawdads Feast on Lazy Whales                        ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

# Get current prices
btc = client.get_product('BTC-USD')
eth = client.get_product('ETH-USD')
sol = client.get_product('SOL-USD')

btc_price = float(btc['price'])
eth_price = float(eth['price'])
sol_price = float(sol['price'])

print(f"\n⏰ Time: {datetime.now().strftime('%A %H:%M:%S')}")
print("=" * 70)

print("\n📊 CURRENT PRICES:")
print(f"  BTC: ${btc_price:,.2f}")
print(f"  ETH: ${eth_price:,.2f}")
print(f"  SOL: ${sol_price:,.2f}")

# Weekend Sawtooth Characteristics
print("\n🪚 WEEKEND SAWTOOTH PATTERN:")
print("-" * 50)
print("• Low Volume = Easier to move price")
print("• Bots dominate = Predictable ranges")
print("• Retail sleeps = Less competition")
print("• Asia wakes Sunday 6pm ET = Volume returns")

# Calculate sawtooth ranges based on typical weekend patterns
btc_range = btc_price * 0.008  # 0.8% typical weekend range
eth_range = eth_price * 0.012  # 1.2% ETH more volatile
sol_range = sol_price * 0.025  # 2.5% SOL swings harder

print("\n🎯 EXPECTED WEEKEND RANGES:")
print("-" * 50)
print(f"BTC Sawtooth: ${btc_price - btc_range/2:,.0f} ↔ ${btc_price + btc_range/2:,.0f}")
print(f"  • Tooth size: ${btc_range:,.0f} ({btc_range/btc_price*100:.1f}%)")
print(f"  • Buy zone: < ${btc_price - btc_range/3:,.0f}")
print(f"  • Sell zone: > ${btc_price + btc_range/3:,.0f}")

print(f"\nETH Sawtooth: ${eth_price - eth_range/2:,.0f} ↔ ${eth_price + eth_range/2:,.0f}")
print(f"  • Tooth size: ${eth_range:,.0f} ({eth_range/eth_price*100:.1f}%)")
print(f"  • Buy zone: < ${eth_price - eth_range/3:,.0f}")
print(f"  • Sell zone: > ${eth_price + eth_range/3:,.0f}")

print(f"\nSOL Sawtooth: ${sol_price - sol_range/2:,.2f} ↔ ${sol_price + sol_range/2:,.2f}")
print(f"  • Tooth size: ${sol_range:,.2f} ({sol_range/sol_price*100:.1f}%)")
print(f"  • Buy zone: < ${sol_price - sol_range/3:,.2f}")
print(f"  • Sell zone: > ${sol_price + sol_range/3:,.2f}")

# Milking Strategy
print("\n🦀 CRAWDAD MILKING STRATEGY:")
print("-" * 50)
print("1. SET LIMIT ORDERS at tooth bottoms")
print("2. SELL at tooth tops (don't be greedy)")
print("3. REPEAT every 2-4 hours (weekend cycles)")
print("4. SMALL POSITIONS (1-2% per trade)")
print("5. COMPOUND profits into Monday surge")

# Specific weekend timings
print("\n⏱️ OPTIMAL WEEKEND TIMING:")
print("-" * 50)
print("• Friday 8pm-12am: Post-work dump")
print("• Saturday 2am-6am: Asia morning pump")
print("• Saturday 2pm-6pm: US afternoon drift")
print("• Saturday 10pm-2am: Late night volatility")
print("• Sunday 6am-10am: Europe wake pump")
print("• Sunday 6pm ET: ASIA OPENS - Volume returns!")

# Risk Management
print("\n⚠️ WEEKEND RISKS:")
print("-" * 50)
print("• Flash wicks from low liquidity")
print("• Stop hunts more effective")
print("• News can move market 5% instantly")
print("• Options expiry aftershocks")

# Current Position in Sawtooth
if btc_price > (btc_price - btc_range/3) and btc_price < (btc_price + btc_range/3):
    position = "MIDDLE ZONE - Wait for extremes"
elif btc_price <= (btc_price - btc_range/3):
    position = "BUY ZONE - Accumulate!"
else:
    position = "SELL ZONE - Take profits!"

print("\n🎯 CURRENT SAWTOOTH POSITION:")
print("-" * 50)
print(f"  {position}")

# Council Wisdom
print("\n🏔️ MOUNTAIN FATHER'S WEEKEND WISDOM:")
print("-" * 50)
print('  "Weekend warriors sleep. Smart crawdads feast."')
print('  "Small consistent profits beat one big gamble."')
print('  "The sawtooth is your friend in low volume."')
print('  "Monday always brings new energy - be ready."')

print("\n✅ WEEKEND SAWTOOTH MILKER READY")
print("=" * 70)
print("Set your orders and let the patterns work for you! 🦀")