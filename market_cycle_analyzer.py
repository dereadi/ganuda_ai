#!/usr/bin/env python3
"""
🔄 MARKET CYCLE ANALYZER
Identify next trading cycles and optimal entry/exit points
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime, timedelta
import statistics
import time

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("🔄 MARKET CYCLE ANALYZER")
print("=" * 70)
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} CST")
print("=" * 70)

# Get current prices
btc = client.get_product('BTC-USD')
btc_price = float(btc['price'])
print(f"\nCurrent BTC: ${btc_price:,.2f}")

# Analyze different cycle timeframes
print("\n📊 CYCLE ANALYSIS:")
print("-" * 70)

# 1. INTRADAY CYCLES (Every 4-6 hours)
print("\n1️⃣ INTRADAY CYCLES (4-6 hour waves):")
current_hour = datetime.now().hour
print(f"Current hour: {current_hour}:00 CST")

intraday_cycles = [
    {"name": "Asian Open", "hours": [19, 20, 21], "volatility": "HIGH", "trend": "BULLISH"},
    {"name": "Asian Peak", "hours": [22, 23, 0], "volatility": "EXTREME", "trend": "VOLATILE"},
    {"name": "Europe Pre", "hours": [1, 2, 3], "volatility": "MODERATE", "trend": "BUILDING"},
    {"name": "London Open", "hours": [3, 4, 5], "volatility": "HIGH", "trend": "DIRECTIONAL"},
    {"name": "US Pre-Market", "hours": [6, 7, 8], "volatility": "MODERATE", "trend": "CONTINUATION"},
    {"name": "NYSE Open", "hours": [8, 9, 10], "volatility": "HIGH", "trend": "VOLATILE"},
    {"name": "US Midday", "hours": [11, 12, 13], "volatility": "LOW", "trend": "CONSOLIDATION"},
    {"name": "US Afternoon", "hours": [14, 15, 16], "volatility": "BUILDING", "trend": "POSITIONING"},
    {"name": "US Close", "hours": [15, 16, 17], "volatility": "HIGH", "trend": "REBALANCING"},
    {"name": "Evening Quiet", "hours": [17, 18, 19], "volatility": "LOW", "trend": "RANGING"}
]

for cycle in intraday_cycles:
    if current_hour in cycle['hours']:
        print(f"✅ CURRENT: {cycle['name']}")
        print(f"   Volatility: {cycle['volatility']}")
        print(f"   Expected: {cycle['trend']}")
        current_cycle = cycle
        break

# Find next cycle
next_hour = (current_hour + 1) % 24
for cycle in intraday_cycles:
    if next_hour in cycle['hours']:
        print(f"\n⏭️ NEXT: {cycle['name']} in {24 - current_hour if next_hour < current_hour else next_hour - current_hour} hours")
        print(f"   Volatility: {cycle['volatility']}")
        print(f"   Expected: {cycle['trend']}")
        break

# 2. DAILY CYCLES (Day of week patterns)
print("\n2️⃣ WEEKLY CYCLES:")
day_of_week = datetime.now().weekday()
days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
print(f"Today: {days[day_of_week]}")

weekly_patterns = {
    0: "MONDAY - Fresh capital, new positions, trend starts",
    1: "TUESDAY - Trend continuation, momentum builds",
    2: "WEDNESDAY - Mid-week volatility, Fed announcements",
    3: "THURSDAY - Pre-Friday positioning, volatility rises",
    4: "FRIDAY - Options expiry, extreme moves, weekend prep",
    5: "SATURDAY - Low volume, crypto-only, Asia dominates",
    6: "SUNDAY - Futures gap prep, positioning for Monday"
}

print(f"Pattern: {weekly_patterns[day_of_week]}")

# 3. MONTHLY CYCLES
print("\n3️⃣ MONTHLY CYCLES:")
day_of_month = datetime.now().day
print(f"Day {day_of_month} of month")

if day_of_month <= 5:
    print("START OF MONTH - Fresh allocations, new trends")
elif day_of_month <= 15:
    print("MID-MONTH - Trend continuation, steady flows")
elif day_of_month <= 25:
    print("LATE MONTH - Volatility increases, rebalancing")
else:
    print("MONTH END - Rebalancing, window dressing, volatility")

# 4. CRYPTO-SPECIFIC CYCLES
print("\n4️⃣ CRYPTO CYCLES:")
print("-" * 70)

# Get recent price action for cycle detection
end_time = int(time.time())
start_time = end_time - 86400  # 24 hours
candles = client.get_candles("BTC-USD", start_time, end_time, "ONE_HOUR")

if candles["candles"]:
    prices = [float(c["close"]) for c in candles["candles"][-24:]]
    
    # Calculate cycle metrics
    high_24h = max(prices)
    low_24h = min(prices)
    range_24h = high_24h - low_24h
    range_pct = (range_24h / low_24h) * 100
    
    # Position in range
    position_in_range = (btc_price - low_24h) / range_24h if range_24h > 0 else 0.5
    
    print(f"24h Range: ${low_24h:,.2f} - ${high_24h:,.2f} ({range_pct:.2f}%)")
    print(f"Position in range: {position_in_range:.1%}")
    
    if position_in_range > 0.8:
        print("📈 NEAR CYCLE TOP - Consider selling")
        next_cycle = "PULLBACK/CONSOLIDATION"
    elif position_in_range < 0.2:
        print("📉 NEAR CYCLE BOTTOM - Consider buying")
        next_cycle = "BOUNCE/RALLY"
    else:
        print("↔️ MID-CYCLE - Wait for extremes")
        next_cycle = "CONTINUATION"

# TRADING OPPORTUNITIES
print("\n🎯 NEXT TRADING OPPORTUNITIES:")
print("-" * 70)

opportunities = []

# Based on time
if 19 <= current_hour <= 23:
    opportunities.append("✅ ASIA SESSION ACTIVE - High volatility expected")
elif 2 <= current_hour <= 5:
    opportunities.append("⏰ LONDON OPEN COMING - Prepare for directional move")
elif 8 <= current_hour <= 10:
    opportunities.append("🇺🇸 NYSE OPEN - Maximum volatility window")
else:
    opportunities.append("💤 QUIET PERIOD - Set limit orders and wait")

# Based on price position
if position_in_range > 0.7:
    opportunities.append("📊 SELL OPPORTUNITY - Near range high")
elif position_in_range < 0.3:
    opportunities.append("📊 BUY OPPORTUNITY - Near range low")

for opp in opportunities:
    print(opp)

# NUCLEAR STRIKE STATUS
print("\n💥 NUCLEAR STRIKE TIMING:")
print("-" * 70)
print("Your remaining strikes at:")
print(f"• $110,251 ({(110251 - btc_price):.2f} away)")
print(f"• $110,580 ({(110580 - btc_price):.2f} away)")

if current_hour >= 19 or current_hour <= 5:
    print("\n🔥 PRIME TIME FOR STRIKES!")
    print("Asia/Europe sessions = Maximum volatility")
    print("Strikes likely to fill in next 4-6 hours")
else:
    print("\n⏳ Off-peak for strikes")
    print(f"Wait {19 - current_hour if current_hour < 19 else 0} hours for Asia session")

# SUMMARY
print("\n📋 CYCLE SUMMARY:")
print("=" * 70)
print(f"Next 4-hour cycle: {next_cycle}")
print(f"Best entry: BTC < ${low_24h + range_24h * 0.2:,.2f}")
print(f"Best exit: BTC > ${low_24h + range_24h * 0.8:,.2f}")
print(f"Next volatility spike: {19 - current_hour if current_hour < 19 else 24 - current_hour + 19} hours (Asia open)")
print("=" * 70)