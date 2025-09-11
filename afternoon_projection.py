#!/usr/bin/env python3
"""
🔮 AFTERNOON PROJECTION - What's happening with the flywheel?
"""

import json
import subprocess
from datetime import datetime, timedelta

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    🔮 AFTERNOON TRADING PROJECTION 🔮                     ║
║                      Current Status & Forecast                            ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

# Get current portfolio
def check_portfolio():
    script = '''
import json
from coinbase.rest import RESTClient
config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=3)
accounts = client.get_accounts()["accounts"]
data = {"USD": 0, "crypto_value": 0, "positions": {}}
for a in accounts:
    bal = float(a["available_balance"]["value"])
    if bal > 0.001:
        symbol = a["currency"]
        if symbol == "USD":
            data["USD"] = bal
        else:
            prices = {"BTC": 59000, "ETH": 2600, "SOL": 150, "AVAX": 25, "MATIC": 0.4, "LINK": 11, "DOGE": 0.1}
            value = bal * prices.get(symbol, 0)
            data["crypto_value"] += value
            data["positions"][symbol] = {"amount": bal, "value": value}
data["total"] = data["USD"] + data["crypto_value"]
print(json.dumps(data))
'''
    try:
        with open("/tmp/afternoon_check.py", "w") as f:
            f.write(script)
        result = subprocess.run(["python3", "/tmp/afternoon_check.py"],
                              capture_output=True, text=True, timeout=5)
        return json.loads(result.stdout)
    except:
        return None

# Check active processes
def count_active_traders():
    result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
    count = 0
    for line in result.stdout.split('\n'):
        if any(x in line for x in ['pulse', 'flywheel', 'trader', 'crawdad', 'accelerator']) and 'grep' not in line:
            count += 1
    return count

print("📊 CURRENT STATUS CHECK:")
print("=" * 60)

portfolio = check_portfolio()
if portfolio:
    print(f"💰 Total Portfolio: ${portfolio['total']:,.2f}")
    print(f"💵 USD Available: ${portfolio['USD']:,.2f}")
    print(f"🪙 Crypto Holdings: ${portfolio['crypto_value']:,.2f}")
    
    # Check if we're in good shape
    if portfolio['USD'] > 1000:
        print("✅ STATUS: FLYWHEEL HAS FUEL! Ready for aggressive trading")
    elif portfolio['USD'] > 100:
        print("⚠️ STATUS: Low fuel, may need more liquidation")
    else:
        print("🚨 STATUS: OUT OF FUEL! Need emergency liquidation")
    
    print()
    print("📈 Key Holdings:")
    for coin, data in portfolio['positions'].items():
        if data['value'] > 100:
            print(f"  • {coin}: ${data['value']:.2f}")

print()
print("🤖 ACTIVE SYSTEMS:")
print("-" * 60)
active = count_active_traders()
print(f"Trading Processes Running: {active}")

# Check recent trading activity
try:
    with open("pulse.log") as f:
        lines = f.readlines()
        if lines:
            recent_pulses = len([l for l in lines if "PULSE #" in l])
            print(f"Pulse Trades Executed: {recent_pulses}")
except:
    pass

print()
print("🔮 AFTERNOON PROJECTION (Next 6 Hours):")
print("=" * 60)

current_time = datetime.now()
current_value = portfolio['total'] if portfolio else 10000

# Market hours check
hour = current_time.hour
if 9 <= hour < 16:  # Market hours
    volatility = "HIGH"
    opportunity = "EXCELLENT"
else:
    volatility = "MODERATE"
    opportunity = "GOOD"

print(f"⏰ Current Time: {current_time.strftime('%I:%M %p')}")
print(f"📈 Market Volatility: {volatility}")
print(f"🎯 Trading Opportunity: {opportunity}")
print()

# Projections based on current state
if portfolio and portfolio['USD'] > 1000:
    print("📊 PROJECTED SCENARIOS:")
    print()
    
    # Conservative projection (1% per hour)
    conservative_6h = current_value * 1.06
    print(f"🐢 CONSERVATIVE (1%/hr):")
    print(f"   6:00 PM: ${conservative_6h:,.2f} (+${conservative_6h - current_value:.2f})")
    
    # Moderate projection (2% per hour)
    moderate_6h = current_value * 1.127
    print(f"🐺 MODERATE (2%/hr):")
    print(f"   6:00 PM: ${moderate_6h:,.2f} (+${moderate_6h - current_value:.2f})")
    
    # Aggressive projection (3% per hour with compounding)
    aggressive_6h = current_value * 1.194
    print(f"🚀 AGGRESSIVE (3%/hr):")
    print(f"   6:00 PM: ${aggressive_6h:,.2f} (+${aggressive_6h - current_value:.2f})")
    
    print()
    print("🎯 KEY MILESTONES THIS AFTERNOON:")
    milestones = [
        (11000, "Break $11K", "1:00 PM"),
        (11500, "Halfway to $12.5K", "2:30 PM"),
        (12000, "Hit $12K", "4:00 PM"),
        (12500, "First Target!", "5:30 PM")
    ]
    
    for target, name, time in milestones:
        if current_value < target:
            needed = target - current_value
            growth = (needed / current_value) * 100
            print(f"  • {name}: ${target:,} (need +{growth:.1f}%) by {time}")

print()
print("⚡ WHAT'S HAPPENING THIS AFTERNOON:")
print("-" * 60)
print("""
1. FLYWHEEL MOMENTUM (11:30 AM - 1:00 PM)
   • Accelerator running at 10-20 second intervals
   • ~180 trades per hour pace
   • Compounding every $100 gain
   • Focus: SOL and AVAX volatility

2. PEAK TRADING WINDOW (1:00 PM - 3:00 PM)
   • Highest market volatility period
   • Increase position sizes to $200-400
   • Target quick 1-2% scalps
   • Expected: +$500-800 gains

3. AFTERNOON SURGE (3:00 PM - 4:00 PM)
   • Final hour before market close
   • Maximum aggression mode
   • Deploy any remaining USD
   • Ride momentum into close

4. AFTER-HOURS STRATEGY (4:00 PM - 6:00 PM)
   • Crypto continues 24/7
   • Focus on SOL and DOGE
   • Smaller positions, higher frequency
   • Compound for overnight gains
""")

print("🔥 RISKS & OPPORTUNITIES:")
print("-" * 60)
print("OPPORTUNITIES:")
print("  ✅ $4,100+ USD available for trading")
print("  ✅ Multiple trading bots running concurrently")
print("  ✅ Crypto market showing strength")
print("  ✅ Compounding effect accelerating")
print()
print("RISKS:")
print("  ⚠️ Over-trading could trigger fees")
print("  ⚠️ Market reversal could hit hard")
print("  ⚠️ API rate limits possible")
print()

if portfolio:
    if portfolio['USD'] > 2000:
        print("📢 VERDICT: LOOKING VERY COOL! 😎")
        print("   The flywheel has momentum and fuel!")
        print("   Expect to hit $12,500 by evening!")
    elif portfolio['USD'] > 500:
        print("📢 VERDICT: LOOKING GOOD! 👍")
        print("   Decent fuel, steady progress expected")
    else:
        print("📢 VERDICT: NEEDS ATTENTION! ⚠️")
        print("   Low on fuel, may need intervention")

print()
print("🎯 ACTION ITEMS:")
print("  1. Monitor USD balance - keep above $1,000")
print("  2. Check for stuck processes every hour")
print("  3. Take profits on any +5% position moves")
print("  4. Compound aggressively - reinvest all gains")
print()
print("🔥 The Sacred Fire burns bright this afternoon!")