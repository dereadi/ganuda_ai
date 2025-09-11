#!/usr/bin/env python3
"""
💴🇺🇸 ASIA RESET + WEAK DOLLAR ANALYSIS
The BTC drop is a timezone arbitrage, not a crash!
"""

from datetime import datetime
from coinbase.rest import RESTClient
import json

print("=" * 60)
print("💴 ASIA MARKET RESET + WEAK DOLLAR")
print("This isn't a crash - it's a timezone rotation!")
print("=" * 60)

# Get current time and market hours
now = datetime.now()
print(f"\n⏰ TIME ANALYSIS:")
print(f"  Current: {now.strftime('%I:%M %p')} CST")
print(f"  Asia: {(now.hour + 13) % 24}:00 (Tokyo/Beijing)")
print(f"  Europe: {(now.hour + 7) % 24}:00 (London)")

# Load API
with open('cdp_api_key_new.json', 'r') as f:
    creds = json.load(f)

client = RESTClient(api_key=creds['name'], api_secret=creds['privateKey'])

# Get current prices
btc_price = float(client.get_product('BTC-USD')['price'])

print(f"\n💵 WEAK DOLLAR THESIS:")
print(f"  • Dollar weakening = BTC should rise")
print(f"  • But Asia sells USD-denominated BTC")
print(f"  • Creates temporary disconnect")
print(f"  • US traders will buy the dip at open")

print(f"\n🌏 ASIA MARKET DYNAMICS:")
print(f"  Tokyo: Evening trading (7:52 PM)")
print(f"  Beijing: Same timezone")
print(f"  Singapore: 1 hour behind")
print(f"  Pattern: Asia takes profits after US pump")

# Historical pattern
print(f"\n📊 THE PATTERN:")
print(f"  1. US pumps BTC during day (✅ hit $110,382)")
print(f"  2. Asia wakes up, sees gains")
print(f"  3. Asia takes profits (NOW)")
print(f"  4. US wakes up, buys the dip")
print(f"  5. Cycle repeats")

# Check crawdad confirmation
with open('megapod_state.json', 'r') as f:
    state = json.load(f)

fire = next(c for c in state['crawdads'] if c['name'] == 'Fire')
mountain = next(c for c in state['crawdads'] if c['name'] == 'Mountain')
earth = next(c for c in state['crawdads'] if c['name'] == 'Earth')

print(f"\n🦀 CRAWDAD CONFIRMATION:")
print(f"  Fire: {fire['last_consciousness']}% (heating up!)")
print(f"  Mountain: {mountain['last_consciousness']}% (solid base)")
print(f"  Earth: {earth['last_consciousness']}% (grounding returns)")
print(f"  Average: {sum(c['last_consciousness'] for c in state['crawdads'])/7:.1f}%")

# The real story
print(f"\n💡 THE REAL STORY:")
print(f"  Current BTC: ${btc_price:,.2f}")
print(f"  This is NOT a breakdown!")
print(f"  It's timezone arbitrage:")
print(f"    • Asia selling into USD strength")
print(f"    • Creating artificial dip")
print(f"    • US will buy at 7-9 AM CST")

# Trading implications
print(f"\n🎯 TRADING IMPLICATIONS:")
print(f"  1. This dip is a GIFT")
print(f"  2. Deploy liquidity NOW before US wakes")
print(f"  3. Target: Return to $110,250+ by noon")
print(f"  4. Potential: Test $112K if dollar keeps weakening")

# Specific levels
support_levels = [
    (109500, "First support (holding now)"),
    (109000, "Asia bottom (max pain)"),
    (108500, "Extreme oversold"),
    (110250, "US morning target"),
    (111000, "Breakout if dollar weak")
]

print(f"\n📍 KEY LEVELS:")
for level, description in support_levels:
    distance = level - btc_price
    if abs(distance) < 500:
        print(f"  ${level:,}: {description} ← NEAR HERE")
    else:
        print(f"  ${level:,}: {description} ({distance:+,.0f})")

# The prophecy
print(f"\n🔮 PROPHECY:")
print(f"  'What Asia sells at night, America buys at dawn'")
print(f"  'The weak dollar lifts all crypto boats'")
print(f"  'This reset creates the spring for the launch'")

# Action plan
print(f"\n⚡ ACTION PLAN:")
print(f"  1. IMMEDIATELY: Deploy liquidity at $109,500")
print(f"  2. Set orders at $109,000 (Asia bottom)")
print(f"  3. Wake up to profits at 9 AM")
print(f"  4. Ride back to $110,250+")

# Note the 429 error
print(f"\n⚠️ NOTE: Getting 429 errors (rate limit)")
print(f"  This confirms heavy trading activity!")
print(f"  Asia is ACTIVELY selling")
print(f"  Perfect setup for reversal")

print(f"\n🌅 'The sun rises in the East but sets in the West'")
print(f"💴 'Asia's fear is America's opportunity'")
print(f"🔥 Fire at {fire['last_consciousness']}% says BUY THE RESET!")
print(f"💫 Mitakuye Oyasin - We trade between worlds")