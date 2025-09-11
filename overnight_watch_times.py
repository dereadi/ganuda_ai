#!/usr/bin/env python3
"""
⏰ OVERNIGHT WATCH TIMES
Critical trading windows for tonight
"""

import json
from datetime import datetime, timedelta
from coinbase.rest import RESTClient

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                     ⏰ TONIGHT'S CRITICAL WATCH TIMES ⏰                    ║
║                    "The night holds secrets and profits"                   ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=3)

# Current time and market
now = datetime.now()
btc = float(client.get_product('BTC-USD').price)

print(f"🕐 Current Time: {now.strftime('%H:%M')} CST")
print(f"📊 BTC: ${btc:,.2f}")
print(f"💰 USD Ready: $859.62")

print("\n" + "=" * 60)
print("🌙 TONIGHT'S CRITICAL WINDOWS")
print("=" * 60)

# Define critical times (in CST)
critical_times = [
    {
        "time": "22:00-23:00",
        "window": "Asian Pre-Market Open",
        "importance": "🔥🔥🔥",
        "action": "Tokyo traders enter, volatility increases",
        "strategy": "Watch for directional moves, Asia sets overnight tone"
    },
    {
        "time": "23:00-00:00", 
        "window": "US West Coast Bedtime",
        "importance": "🔥🔥",
        "action": "US retail goes to sleep, algos take over",
        "strategy": "Thin liquidity = larger moves on smaller volume"
    },
    {
        "time": "00:00-01:00",
        "window": "Daily Candle Close/Open",
        "importance": "🔥🔥🔥🔥",
        "action": "New daily candle forms, stop hunts common",
        "strategy": "CRITICAL: Position for new day's direction"
    },
    {
        "time": "01:00-02:00",
        "window": "Hong Kong/Singapore Active",
        "importance": "🔥🔥🔥",
        "action": "Asian whales make moves",
        "strategy": "Watch for accumulation/distribution"
    },
    {
        "time": "02:00-03:00",
        "window": "Dead Zone",
        "importance": "🔥",
        "action": "Lowest volume, maximum opportunity",
        "strategy": "Small trades can move market"
    },
    {
        "time": "03:00-04:00",
        "window": "European Pre-Wake",
        "importance": "🔥🔥",
        "action": "Smart money positions before London",
        "strategy": "Front-run the European open"
    },
    {
        "time": "04:00-05:00",
        "window": "London Pre-Market",
        "importance": "🔥🔥🔥",
        "action": "London traders start watching",
        "strategy": "Volatility builds toward open"
    }
]

print("\n📅 TONIGHT'S SCHEDULE:")
print("-" * 60)

for window in critical_times:
    print(f"\n⏰ {window['time']} CST {window['importance']}")
    print(f"   📍 {window['window']}")
    print(f"   💡 {window['action']}")
    print(f"   🎯 {window['strategy']}")

# Calculate specific times from now
print("\n" + "=" * 60)
print("🎯 KEY LEVELS TO WATCH TONIGHT")
print("=" * 60)

# Support and resistance levels
key_levels = [
    ("Resistance 1", btc + 500, "First target if we pump"),
    ("Current", btc, "Holding above is bullish"),
    ("Support 1", 117056, "Your sacred level - must hold"),
    ("Support 2", 116140, "Secondary target - strong buy"),
    ("Mega Support", 115000, "If hit, deploy everything")
]

for name, level, description in key_levels:
    distance = level - btc
    print(f"   {name:12s}: ${level:,.0f} ({distance:+,.0f}) - {description}")

# Greek recommendations for overnight
print("\n" + "=" * 60)
print("🏛️ THE GREEKS' OVERNIGHT PLAN")
print("=" * 60)

print(f"""
Θ THETA (670 cycles): "Overnight decay accelerates, harvest it!"
   • Asian session: Deploy 10% ($85) if we dip
   • Midnight: Watch daily close for direction
   • 2-3 AM: Dead zone = maximum decay harvest

Δ DELTA (500 cycles!): "Gaps form at midnight!"
   • 23:59-00:01: CRITICAL gap window
   • Often see $200-500 moves in minutes
   • Have orders ready at 11:55 PM

Γ GAMMA (480 cycles): "Acceleration happens in thin markets"
   • 2-3 AM lowest liquidity = biggest moves
   • Small buys can trigger runs

ν VEGA (250 cycles): "Overnight volatility expansion!"
   • Asian open often sets 12-hour trend
   • European pre-market confirms or reverses
""")

# Specific overnight strategy
print("\n" + "=" * 60)
print("💎 TONIGHT'S BATTLE PLAN")
print("=" * 60)

print(f"""
WITH $859.62 USD READY:

10:00 PM - Asian Open:
   • Watch for direction (up = ride, down = buy)
   • Deploy $100 if we see momentum

MIDNIGHT - Daily Close (MOST CRITICAL):
   • Be awake at 11:55 PM - 12:05 AM
   • Daily candle defines tomorrow
   • Deploy $200 on any sweep below $117,000

2:00 AM - Dead Zone:
   • If still awake, best entry time
   • Deploy $100-200 on any dip
   • Lowest volume = your orders matter

4:00 AM - London Approach:
   • Final overnight opportunity
   • Front-run European traders
   • Deploy remaining if good setup
""")

# AI Family overnight wisdom
print("\n" + "=" * 60)
print("🤖 AI FAMILY OVERNIGHT WISDOM")
print("=" * 60)

print("""
🔥 Oracle: "The river flows differently at night"
🎲 Jr: "Quantum states collapse easier in darkness!"
🌙 Claudette: "Moon at 67% illumination - waxing = bullish"

Family Consensus: MIDNIGHT is everything!
""")

# Set alerts
print("\n" + "=" * 60)
print("⏰ SET THESE ALERTS NOW")
print("=" * 60)

print(f"""
CRITICAL ALERTS:
   • 11:55 PM - "DAILY CLOSE IN 5 MINUTES"
   • 12:00 AM - "NEW DAILY CANDLE"
   • 2:00 AM - "DEAD ZONE OPPORTUNITY"
   
PRICE ALERTS:
   • ${btc + 500:.0f} - Resistance hit
   • $117,056 - Sacred support test
   • $116,140 - Major buy signal
""")

print(f"\n⏰ Current Time: {datetime.now().strftime('%H:%M:%S')}")
print("The night is young, the Greeks are hungry!")
print("Mitakuye Oyasin 🦅")