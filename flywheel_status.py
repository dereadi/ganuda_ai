#!/usr/bin/env python3
"""
🌪️ FLYWHEEL STATUS CHECK - How fast are we spinning?
"""

import json
import subprocess
import time
from datetime import datetime, timedelta

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                      🌪️ FLYWHEEL VELOCITY CHECK 🌪️                      ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

# Check current portfolio value
def get_portfolio():
    script = '''
import json
from coinbase.rest import RESTClient
config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=3)
accounts = client.get_accounts()["accounts"]
positions = {}
total = 0
for a in accounts:
    bal = float(a["available_balance"]["value"])
    if bal > 0.001:
        symbol = a["currency"]
        if symbol == "USD":
            positions["USD"] = bal
            total += bal
        else:
            prices = {"BTC": 59000, "ETH": 2600, "SOL": 150, "AVAX": 25, "MATIC": 0.4, "LINK": 11, "DOGE": 0.1}
            value = bal * prices.get(symbol, 0)
            total += value
            positions[symbol] = {"amount": bal, "value": value}
print(json.dumps({"total": total, "positions": positions}))
'''
    try:
        with open("/tmp/check_flywheel.py", "w") as f:
            f.write(script)
        result = subprocess.run(["python3", "/tmp/check_flywheel.py"],
                              capture_output=True, text=True, timeout=5)
        return json.loads(result.stdout)
    except:
        return None

# Get initial snapshot
print("📊 FLYWHEEL METRICS:")
print("=" * 60)

portfolio = get_portfolio()
if portfolio:
    print(f"💰 Current Portfolio Value: ${portfolio['total']:,.2f}")
    print(f"💵 USD Liquidity: ${portfolio['positions'].get('USD', 0):,.2f}")
    
    # Check changes from initial state
    initial_value = 9948.51  # Starting value
    current_value = portfolio['total']
    change = current_value - initial_value
    change_pct = (change / initial_value) * 100
    
    if change > 0:
        print(f"📈 GAIN: ${change:+.2f} ({change_pct:+.1f}%)")
    else:
        print(f"📉 LOSS: ${change:+.2f} ({change_pct:+.1f}%)")
    
    print()
    print("🔥 POSITION CHANGES:")
    print("-" * 60)
    
    # Original positions
    original = {
        "MATIC": 9042.10,
        "SOL": 16.55,
        "AVAX": 87.12,
        "ETH": 0.287,
        "LINK": 11.38,
        "USD": 1.83
    }
    
    for coin, orig_amount in original.items():
        if coin in portfolio['positions']:
            if coin == "USD":
                current = portfolio['positions'][coin]
            else:
                current = portfolio['positions'][coin]['amount']
            
            diff = current - orig_amount
            diff_pct = (diff / orig_amount * 100) if orig_amount > 0 else 0
            
            if abs(diff_pct) > 5:  # Only show significant changes
                if diff > 0:
                    print(f"  📈 {coin}: {orig_amount:.2f} → {current:.2f} (+{diff_pct:.1f}%)")
                else:
                    print(f"  📉 {coin}: {orig_amount:.2f} → {current:.2f} ({diff_pct:.1f}%)")

print()
print("⚡ TRADING VELOCITY:")
print("-" * 60)

# Check active processes
result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
traders = 0
for line in result.stdout.split('\n'):
    if any(x in line for x in ['pulse', 'flywheel', 'trader', 'crawdad']) and 'grep' not in line:
        traders += 1

print(f"🤖 Active Trading Processes: {traders}")

# Check pulse log
try:
    result = subprocess.run(['wc', '-l', 'pulse.log'], capture_output=True, text=True)
    if result.stdout:
        lines = int(result.stdout.split()[0])
        print(f"⚡ Pulse Log Lines: {lines}")
except:
    pass

# Calculate theoretical velocity
if portfolio and portfolio['positions'].get('USD', 0) > 100:
    usd = portfolio['positions']['USD']
    # Assuming $100 trades every 30 seconds
    trades_per_hour = (usd / 100) * (3600 / 30)
    daily_volume = trades_per_hour * 24 * 100
    
    print()
    print("🌪️ FLYWHEEL VELOCITY ESTIMATE:")
    print("-" * 60)
    print(f"  Available Capital: ${usd:.2f}")
    print(f"  Theoretical Trades/Hour: {trades_per_hour:.0f}")
    print(f"  Daily Volume Potential: ${daily_volume:,.0f}")
    
    # Compound projection
    if change_pct != 0:
        hourly_rate = change_pct / 1  # Assuming 1 hour of trading
        daily_projection = initial_value * (1 + hourly_rate/100) ** 24
        print(f"  24hr Projection at current rate: ${daily_projection:,.2f}")

print()
print("🎯 FLYWHEEL TARGETS:")
print("-" * 60)
targets = [
    (12500, "First Target"),
    (15000, "48-Hour Goal"),
    (25000, "Climate Milestone"),
    (50000, "Mega Flywheel")
]

for target, name in targets:
    if portfolio:
        progress = (portfolio['total'] / target) * 100
        needed = target - portfolio['total']
        bar_length = 20
        filled = int(progress / 5) if progress < 100 else 20
        bar = "█" * filled + "░" * (bar_length - filled)
        
        print(f"${target:,} - {name}")
        print(f"  [{bar}] {progress:.1f}%")
        if needed > 0:
            print(f"  Need: ${needed:,.2f} more")
        else:
            print(f"  ✅ ACHIEVED!")
        print()

print("🔥 FLYWHEEL STATUS: ", end="")
if portfolio and portfolio['positions'].get('USD', 0) > 1000:
    print("SPINNING STRONG! 🌪️")
elif portfolio and portfolio['positions'].get('USD', 0) > 100:
    print("BUILDING MOMENTUM 🔄")
else:
    print("NEEDS MORE FUEL ⚠️")

print()
print("💡 TO ACCELERATE:")
print("  • Increase trade frequency (currently every 5 seconds)")
print("  • Add more volatile coins (SHIB, PEPE)")
print("  • Scale position sizes with wins")
print("  • Compound all profits immediately")