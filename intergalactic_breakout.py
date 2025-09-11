#!/usr/bin/env python3
"""
🌌🚀 INTERGALACTIC BREAKOUT
After 4 coils, the death of fear, and 01:00...
Now we leave Earth's orbit entirely!
"""

import json
import time
import statistics
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    🌌🚀 INTERGALACTIC! 🚀🌌                              ║
║                   Beyond Moon, Beyond Mars                                ║
║                The Death of Fear = Birth of Stars                         ║
║                    4 Coils Released at Once                               ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - ESCAPE VELOCITY CHECK")
print("=" * 70)

# Check current position in space
btc = float(client.get_product('BTC-USD')['price'])
time.sleep(1)
eth = float(client.get_product('ETH-USD')['price'])
time.sleep(1)
sol = float(client.get_product('SOL-USD')['price'])

print("\n🛸 CURRENT COORDINATES:")
print(f"  BTC: ${btc:,.0f}")
print(f"  ETH: ${eth:.2f}")
print(f"  SOL: ${sol:.2f}")

# Measure velocity
print("\n🚀 MEASURING ESCAPE VELOCITY:")
print("-" * 50)

velocities = []
btc_samples = [btc]

for i in range(10):
    time.sleep(3)
    btc_now = float(client.get_product('BTC-USD')['price'])
    btc_samples.append(btc_now)
    
    velocity = btc_now - btc
    velocities.append(velocity)
    
    print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc_now:,.0f} (${velocity:+.0f})")
    
    if abs(velocity) > 100:
        print("  🚀🚀🚀 ESCAPE VELOCITY ACHIEVED!")
    elif abs(velocity) > 50:
        print("  🚀🚀 Accelerating through stratosphere...")
    elif abs(velocity) > 20:
        print("  🚀 Breaking through atmosphere...")
    else:
        print("  🌍 Still in Earth's gravity well...")
    
    btc = btc_now

# Calculate trajectory
btc_range = max(btc_samples) - min(btc_samples)
avg_velocity = sum(velocities) / len(velocities) if velocities else 0

print("\n🌌 TRAJECTORY ANALYSIS:")
print("-" * 50)
print(f"Range traveled: ${btc_range:.0f}")
print(f"Average velocity: ${avg_velocity:+.2f}/minute")

if avg_velocity > 10:
    print("Direction: TO THE STARS! 🌟")
    destination = "Alpha Centauri"
elif avg_velocity > 0:
    print("Direction: Leaving orbit ↗️")
    destination = "Mars"
elif avg_velocity < -10:
    print("Direction: Gravity pulling back ↘️")
    destination = "Re-entry"
else:
    print("Direction: Orbital drift →")
    destination = "Space Station"

print(f"Estimated destination: {destination}")

# Check intergalactic targets
print("\n🎯 INTERGALACTIC WAYPOINTS:")
print("-" * 50)

targets = [
    ("🌙 Moon Base", 115000),
    ("🔴 Mars Colony", 120000),
    ("🪐 Jupiter Station", 125000),
    ("⭐ Alpha Centauri", 150000),
    ("🌌 Andromeda Galaxy", 200000)
]

current_btc = btc_samples[-1]
for name, target in targets:
    distance = target - current_btc
    if distance < 0:
        print(f"{name}: PASSED! (${-distance:,.0f} ago)")
    elif distance < 1000:
        print(f"{name}: APPROACHING! (${distance:,.0f} away)")
    else:
        print(f"{name}: ${target:,} (${distance:,.0f} to go)")

# The philosophical moment
print("\n💫 INTERGALACTIC WISDOM:")
print("-" * 50)
print("• Four coils wound = Nuclear propulsion")
print("• Death of fear = Escape velocity")
print("• 01:00 release = Launch window")
print("• Breaking Benjamin's breath = Countdown")
print("• The Red filtered through = Rocket fuel")
print("• Now... INTERGALACTIC!")

# Portfolio rocket fuel check
try:
    accounts = client.get_accounts()
    portfolio_value = 0
    usd_balance = 0
    
    for account in accounts.get('accounts', []):
        if float(account.get('available_balance', {}).get('value', 0)) > 0:
            balance = float(account['available_balance']['value'])
            currency = account['available_balance']['currency']
            
            if currency == 'USD':
                usd_balance = balance
                portfolio_value += balance
            elif currency == 'BTC':
                portfolio_value += balance * current_btc
            elif currency == 'ETH':
                portfolio_value += balance * eth
            elif currency == 'SOL':
                portfolio_value += balance * sol
    
    print(f"\n🚀 ROCKET FUEL STATUS:")
    print(f"  Total Portfolio: ${portfolio_value:,.2f}")
    print(f"  USD Fuel: ${usd_balance:.2f}")
    
    if portfolio_value > 13000:
        print("  Status: INTERGALACTIC CAPABLE! 🌌")
    elif portfolio_value > 10000:
        print("  Status: Interplanetary ready! 🪐")
    else:
        print("  Status: Orbital missions only 🛸")
        
except Exception as e:
    print(f"\n🛸 Fuel gauge malfunction: {str(e)[:50]}")

print("\n🌌 'IT WAS THE DEATH OF FEAR, I THINK'")
print("   And the birth of the intergalactic...")
print("   No limits beyond the stratosphere...")
print("   We are ALL stardust now! ✨")
print("=" * 70)