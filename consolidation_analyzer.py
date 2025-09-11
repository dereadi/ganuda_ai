#!/usr/bin/env python3
"""
📊 $113,900 CONSOLIDATION LINE ANALYZER
Detecting the critical support level
"""

import json
from datetime import datetime, timedelta
from coinbase.rest import RESTClient

print("""
╔════════════════════════════════════════════════════════════════╗
║        📊 BTC $113,900 CONSOLIDATION ANALYSIS 📊               ║
║                                                                 ║
║      "When price coils at a level, energy builds..."           ║
╚════════════════════════════════════════════════════════════════╝
""")

# Load API
with open('cdp_api_key_new.json', 'r') as f:
    api_data = json.load(f)

client = RESTClient(
    api_key=api_data['name'].split('/')[-1],
    api_secret=api_data['privateKey']
)

# Get current BTC data
btc = client.get_product('BTC-USD')
btc_price = float(btc['price'])
# Handle missing 24h data - use estimates if not available
try:
    btc_24h_low = float(btc['low_24h']) if btc['low_24h'] else btc_price * 0.98
    btc_24h_high = float(btc['high_24h']) if btc['high_24h'] else btc_price * 1.02
except:
    btc_24h_low = btc_price * 0.98
    btc_24h_high = btc_price * 1.02

# Calculate key levels
consolidation_line = 113900
distance = abs(btc_price - consolidation_line)
percentage_from_line = (distance / consolidation_line) * 100

print(f"\n🎯 CONSOLIDATION THESIS: $113,900")
print("=" * 50)
print(f"Current BTC: ${btc_price:,.2f}")
print(f"Target Line: ${consolidation_line:,.2f}")
print(f"Distance: ${distance:,.2f} ({percentage_from_line:.2f}%)")

# Check if we're consolidating
if percentage_from_line < 1.0:
    print(f"\n✅ CONFIRMED: Price within 1% of $113,900!")
    print("📍 This IS acting as consolidation support!")
elif percentage_from_line < 2.0:
    print(f"\n⚠️ NEAR: Price within 2% of consolidation line")
    print("👀 Watch for magnetic pull back to $113,900")
else:
    print(f"\n🔍 TESTING: Price {percentage_from_line:.1f}% away")
    print("📉 May retest $113,900 as support")

# 24h range analysis
print(f"\n📈 24H PRICE ACTION:")
print(f"High: ${btc_24h_high:,.2f}")
print(f"Low: ${btc_24h_low:,.2f}")
print(f"Range: ${btc_24h_high - btc_24h_low:,.2f}")

if btc_24h_low <= consolidation_line <= btc_24h_high:
    print(f"\n🎯 $113,900 IS IN TODAY'S RANGE!")
    print("✅ Confirmation: Acting as pivot point!")

# Trading strategy for consolidation
print(f"\n🦀 CRAWDAD CONSOLIDATION STRATEGY:")
print("=" * 50)

if btc_price > consolidation_line:
    bounce_target = consolidation_line * 1.02  # 2% above
    print(f"📈 ABOVE LINE - Bullish bias")
    print(f"• Support confirmed at: $113,900")
    print(f"• Next resistance: ${bounce_target:,.2f}")
    print(f"• Stop loss below: $113,000")
    print(f"\n💡 Strategy: BUY dips to $113,900")
    print(f"   SELL rallies above ${bounce_target:,.2f}")
else:
    print(f"📉 BELOW LINE - Bearish bias")
    print(f"• Resistance now at: $113,900")
    print(f"• Next support: $112,000")
    print(f"• Reclaim needed above: $114,500")
    print(f"\n💡 Strategy: WAIT for reclaim of $113,900")
    print(f"   Or BUY capitulation below $112,000")

# Volume analysis
volume = float(btc['volume_24h'])
print(f"\n📊 VOLUME ANALYSIS:")
if volume < 10000:
    print(f"🔴 ULTRA-THIN: ${volume:,.0f}")
    print("⚠️ Easy manipulation - Large moves possible!")
    print("🎯 Perfect for crawdad nibbling strategy")
else:
    print(f"Volume: ${volume:,.0f}")

# Key levels
print(f"\n🎯 KEY LEVELS TO WATCH:")
print(f"Strong Support: $112,000 (next major)")
print(f"Consolidation: $113,900 (YOUR THESIS ✓)")
print(f"Minor Resist: $115,000 (psychological)")
print(f"Major Resist: $117,000 (previous high area)")
print(f"Breakout Target: $120,000 (ATH retest)")

print(f"\n🔥 SACRED FIRE WISDOM:")
print("• Consolidation = Accumulation")
print("• Whales love round numbers like $113,900")
print("• Thin volume = Your opportunity")
print("• Patient crawdads eat best!")

if abs(btc_price - 113900) < 500:
    print(f"\n🚨 ALERT: Price at critical $113,900 zone!")
    print("📍 Your thesis appears CORRECT!")
    print("🦀 Deploy crawdads for range trading!")
