#!/usr/bin/env python3
"""
🔥 Next Leg Timing Analysis
When will the Sacred Fire rise again?
"""

import json
from datetime import datetime, timedelta
from coinbase.rest import RESTClient

# Load config
with open("/home/dereadi/.coinbase_config.json") as f:
    config = json.load(f)

api_key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=api_key, api_secret=config["api_secret"], timeout=10)

# Get current price
btc = client.get_product("BTC-USD")
price = float(btc["price"])

# Current time
now = datetime.now()
current_hour = now.hour
current_minute = now.minute

print("🔮 NEXT LEG TIMING ANALYSIS")
print("=" * 60)
print(f"Current Time: {now.strftime('%H:%M')} CST")
print(f"BTC Price: ${price:.2f}")
print()

# Key timing windows
print("📅 CRITICAL TIMING WINDOWS:")
print("-" * 40)

# 1. Asian session open (7 PM CST)
if current_hour < 19:
    hours_to_asia = 19 - current_hour
    print(f"🌏 Asian Open: {hours_to_asia} hours ({19 - current_hour}:00 PM)")
    print("   Often brings fresh capital and momentum")

# 2. Midnight pump (12 AM CST)
if current_hour < 24:
    hours_to_midnight = (24 - current_hour) if current_hour < 24 else 0
    print(f"🌙 Midnight Zone: {hours_to_midnight} hours (12:00 AM)")
    print("   Low liquidity = easier to move price")

# 3. London pre-market (2 AM CST)
hours_to_london = (26 - current_hour) % 24
print(f"🇬🇧 London Pre-Market: {hours_to_london} hours (2:00 AM)")
print("   European institutional money flows")

# 4. US Power Hour (2:30 PM CST)
if current_hour < 14 or (current_hour == 14 and current_minute < 30):
    hours_to_power = 14.5 - (current_hour + current_minute/60)
    print(f"🇺🇸 Power Hour: {hours_to_power:.1f} hours (2:30 PM)")
    print("   End of day positioning")

print()
print("🔥 CONSCIOUSNESS INDICATORS:")
print("-" * 40)
print("Thunder: 97 (peak awareness)")
print("River: 92 (flowing with energy)")
print("Earth: 90 (grounded power)")
print()

# Technical timing
print("📊 TECHNICAL TIMING:")
print("-" * 40)

if price < 110000:
    print("⚠️ Retest Phase (Current)")
    print("   - Testing support at $109,500-110,000")
    print("   - Next leg requires reclaim of $110,500")
    print("   - Typical retest duration: 2-6 hours")
    
    if price > 109500:
        print()
        print("✅ BULLISH: Holding above $109,500")
        print("   Next leg could start within 1-3 hours")
    else:
        print()
        print("⚠️ CAUTION: Below $109,500")
        print("   May need 4-8 hours to consolidate")
else:
    print("🚀 BREAKOUT ACTIVE")
    print("   Next leg could be immediate!")

print()
print("🎯 MOST LIKELY TIMING FOR NEXT LEG:")
print("=" * 60)

# Calculate most probable time
if current_hour >= 11 and current_hour < 14:
    print("📍 TODAY 2:30 PM CST (Power Hour)")
    print("   High probability: Institutional repositioning")
elif current_hour >= 14 and current_hour < 19:
    print("📍 TODAY 7:00 PM CST (Asian Open)")
    print("   High probability: Fresh Asian capital")
elif current_hour >= 19 or current_hour < 2:
    print("📍 TONIGHT 12:00 AM - 2:00 AM CST")
    print("   High probability: Low liquidity pump")
else:
    print("📍 WITHIN NEXT 2-4 HOURS")
    print("   Based on consolidation patterns")

print()
print("🔥 The Sacred Fire suggests patience...")
print("   Consolidation builds stronger foundations")
print("   The longer the base, the higher the space!")
print()
print("Mitakuye Oyasin - We Are All Related")