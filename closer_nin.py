#!/usr/bin/env python3
"""
🖤 CLOSER - NINE INCH NAILS
"You get me closer to god"
The market is pulling us in... closer and closer to the explosion
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
║                        🖤 CLOSER - NIN 🖤                                 ║
║                    "You Get Me Closer to God"                             ║
║                  The Coils Are Pulling Us In...                           ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - GETTING CLOSER")
print("=" * 70)

# Track how close we're getting
print("\n🖤 MEASURING THE PULL:")
print("-" * 50)

btc_samples = []
ranges = []
closest_range = 1000

for i in range(20):
    btc = float(client.get_product('BTC-USD')['price'])
    btc_samples.append(btc)
    
    if len(btc_samples) >= 3:
        recent_range = max(btc_samples[-3:]) - min(btc_samples[-3:])
        ranges.append(recent_range)
        
        if recent_range < closest_range:
            closest_range = recent_range
        
        if i % 4 == 0:
            print(f"\n{datetime.now().strftime('%H:%M:%S')}:")
            print(f"  BTC: ${btc:,.0f}")
            print(f"  3-tick range: ${recent_range:.0f}")
            
            if recent_range < 5:
                print("  🖤🖤🖤 'I want to fuck you like an animal'")
                print("         IMPOSSIBLY CLOSE!")
            elif recent_range < 10:
                print("  🖤🖤 'You get me closer to god'")
                print("       Getting tighter...")
            elif recent_range < 20:
                print("  🖤 'Help me get away from myself'")
                print("     Pulling closer...")
            else:
                print("  ⚫ Still distant...")
    
    time.sleep(2)

# Analysis
final_btc = btc_samples[-1]
avg_range = sum(ranges) / len(ranges) if ranges else 0

print("\n" + "=" * 70)
print("🖤 CLOSER ANALYSIS:")
print("-" * 50)
print(f"Current BTC: ${final_btc:,.0f}")
print(f"Tightest range: ${closest_range:.0f}")
print(f"Average range: ${avg_range:.2f}")

if closest_range < 5:
    print("\n🖤🖤🖤 WE'RE AT THE EVENT HORIZON!")
    print("'My whole existence is flawed'")
    print("'You get me closer to god'")
    print("\nThe sixth coil might be forming...")
elif closest_range < 10:
    print("\n🖤🖤 EXTREMELY CLOSE!")
    print("'I want to feel you from the inside'")
    print("The pressure is unbearable...")
elif closest_range < 20:
    print("\n🖤 GETTING CLOSER...")
    print("'You can have my isolation'")
    print("The spiral tightens...")
else:
    print("\n⚫ Not close enough yet...")
    print("The pull will intensify...")

# Check portfolio distance to target
print("\n💰 DISTANCE TO TRANSCENDENCE:")
print("-" * 50)

try:
    accounts = client.get_accounts()
    portfolio_value = 0
    
    for account in accounts['accounts']:
        balance = float(account['available_balance']['value'])
        currency = account['currency']
        
        if currency == 'USD' and balance > 0:
            portfolio_value += balance
        elif currency == 'BTC' and balance > 0:
            portfolio_value += balance * final_btc
        elif currency == 'ETH' and balance > 0:
            eth_price = float(client.get_product('ETH-USD')['price'])
            portfolio_value += balance * eth_price
        elif currency == 'SOL' and balance > 0:
            sol_price = float(client.get_product('SOL-USD')['price'])
            portfolio_value += balance * sol_price
    
    print(f"Current portfolio: ${portfolio_value:,.2f}")
    
    # Distance to key levels
    distances = [
        (10000, "Closer"),
        (12500, "Much Closer"),
        (15000, "Extremely Close"),
        (20000, "Transcendence")
    ]
    
    for target, label in distances:
        distance = target - portfolio_value
        if distance > 0:
            print(f"  ${target:,} ({label}): ${distance:,.0f} away")
        else:
            print(f"  ${target:,} ({label}): ACHIEVED ✓")
    
except Exception as e:
    print(f"Error: {str(e)[:50]}")

print("\n🌀 THE SIXTH COIL?")
print("-" * 50)

# Quick coil check
current_samples = []
for i in range(10):
    btc = float(client.get_product('BTC-USD')['price'])
    current_samples.append(btc)
    time.sleep(1)

coil_range = max(current_samples) - min(current_samples)
stdev = statistics.stdev(current_samples) if len(current_samples) > 1 else 0
compression = (stdev / statistics.mean(current_samples)) * 100

print(f"10-second range: ${coil_range:.0f}")
print(f"Compression: {compression:.5f}%")

if compression < 0.005:
    print("\n🖤🖤🖤 SIXTH COIL FORMING!")
    print("This shouldn't be possible...")
    print("'You get me closer to god'")
    print("Reality is breaking down...")
elif compression < 0.01:
    print("\n🖤🖤 Coiling continues...")
    print("Getting closer to the singularity...")
else:
    print("\n🖤 Normal volatility")
    print("But the pull remains...")

print("\n🎵 NIN - CLOSER:")
print("-" * 50)
print("'You let me violate you'")
print("'You let me desecrate you'")
print("'You let me penetrate you'")
print("'You let me complicate you'")
print("")
print("'Help me'")
print("'I broke apart my insides'")
print("'Help me'")
print("'I've got no soul to sell'")
print("")
print("'You get me closer to god'")

print("\n🖤 THE CLOSER WE GET:")
print("• The tighter the coils")
print("• The bigger the explosion")
print("• The more violent the break")
print("• The closer to transcendence")

print("\n'YOU GET ME CLOSER TO GOD'")
print("=" * 70)