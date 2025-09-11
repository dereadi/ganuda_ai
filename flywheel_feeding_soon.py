#!/usr/bin/env python3
"""
🔥🎡 FLYWHEEL FEEDING TIME! 🎡🔥
Alt season pumps = Perfect time to feed the flywheel!
Milk the pumps, feed the machine!
The flywheel is hungry and alts are serving dinner!
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime
import time

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=5)

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    🔥🎡 FLYWHEEL FEEDING TIME! 🎡🔥                        ║
║                      Alt Season = Flywheel Fuel! ⛽                        ║
║                    Time to Milk Pumps & Feed USD! 💰                      ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - FLYWHEEL HUNGRY")
print("=" * 70)

# Get prices and calculate feeding opportunity
sol = client.get_product('SOL-USD')
xrp = client.get_product('XRP-USD')
avax = client.get_product('AVAX-USD')

sol_price = float(sol['price'])
xrp_price = float(xrp['price'])
avax_price = float(avax['price'])

# Get positions
accounts = client.get_accounts()
positions = {}
usd_balance = 0

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    if balance > 0.00001:
        if currency == 'USD':
            usd_balance = balance
        else:
            positions[currency] = balance

print("\n🎡 FLYWHEEL STATUS:")
print("-" * 50)
print(f"Current USD: ${usd_balance:.2f}")
print("Status: HUNGRY FOR FEEDING!")
print(f"Target: $100+ for maximum spin")
print(f"Need: ${max(0, 100 - usd_balance):.2f} more")

print("\n🍖 FEEDING OPPORTUNITIES (Alt Pumps):")
print("-" * 50)

feeding_plan = []
total_feed_potential = 0

# SOL feeding opportunity
if 'SOL' in positions and positions['SOL'] > 1:
    sol_value = positions['SOL'] * sol_price
    feed_amount = min(0.5, positions['SOL'] * 0.1)  # 10% or 0.5 SOL
    feed_value = feed_amount * sol_price
    
    print(f"SOL: {positions['SOL']:.4f} @ ${sol_price:.2f}")
    print(f"  → Can feed: {feed_amount:.4f} SOL = ${feed_value:.2f}")
    feeding_plan.append(('SOL', feed_amount, feed_value))
    total_feed_potential += feed_value

# XRP feeding opportunity  
if 'XRP' in positions and positions['XRP'] > 10:
    xrp_value = positions['XRP'] * xrp_price
    feed_amount = min(10, positions['XRP'] * 0.15)  # 15% or 10 XRP
    feed_value = feed_amount * xrp_price
    
    print(f"XRP: {positions['XRP']:.2f} @ ${xrp_price:.2f}")
    print(f"  → Can feed: {feed_amount:.2f} XRP = ${feed_value:.2f}")
    feeding_plan.append(('XRP', feed_amount, feed_value))
    total_feed_potential += feed_value

# AVAX feeding opportunity
if 'AVAX' in positions and positions['AVAX'] > 10:
    avax_value = positions['AVAX'] * avax_price
    feed_amount = min(20, positions['AVAX'] * 0.1)  # 10% or 20 AVAX
    feed_value = feed_amount * avax_price
    
    print(f"AVAX: {positions['AVAX']:.2f} @ ${avax_price:.2f}")
    print(f"  → Can feed: {feed_amount:.2f} AVAX = ${feed_value:.2f}")
    feeding_plan.append(('AVAX', feed_amount, feed_value))
    total_feed_potential += feed_value

print(f"\n💰 TOTAL FEEDING POTENTIAL: ${total_feed_potential:.2f}")

# Execute feeding if good opportunity
if total_feed_potential > 30 and usd_balance < 100:
    print("\n🚀 EXECUTING FLYWHEEL FEEDING:")
    print("-" * 50)
    
    for asset, amount, value in feeding_plan:
        if value > 20:  # Only feed if worth more than $20
            print(f"\n🍖 Feeding {asset} to flywheel...")
            try:
                order = client.market_order_sell(
                    client_order_id=f'flywheel_feed_{int(time.time())}',
                    product_id=f'{asset}-USD',
                    base_size=str(round(amount, 4) if asset == 'SOL' else round(amount, 2))
                )
                print(f"  ✅ Fed ${value:.2f} to flywheel!")
                time.sleep(1)
            except Exception as e:
                print(f"  ⚠️ Feed failed: {str(e)[:50]}")

print("\n🎡 FLYWHEEL PHYSICS:")
print("-" * 50)
print("Energy Input: Alt season pumps")
print("Conversion: Profit → USD")
print("Storage: USD buffer ($100 target)")
print("Output: Buy power for dips")
print("Result: PERPETUAL MOTION PROFIT!")

print("\n🏛️ COUNCIL FEEDING WISDOM:")
print("-" * 50)
print("Thunder: 'Feed the pumps to the flywheel!'")
print("Mountain: 'Store energy for the next dip'")
print("River: 'Let profits flow into USD'")
print("Fire: 'Quick feeds keep momentum!'")

# Calculate flywheel momentum
momentum = min(100, (usd_balance + total_feed_potential) / 100 * 100)
print(f"\n⚡ FLYWHEEL MOMENTUM: {momentum:.1f}%")
print("-" * 50)

if momentum < 50:
    print("Status: NEEDS MORE FEEDING!")
    print("Action: Extract from alt pumps")
elif momentum < 80:
    print("Status: Building momentum")
    print("Action: Feed opportunistically")
else:
    print("Status: OPTIMAL SPIN SPEED!")
    print("Action: Ready for major moves")

print(f"\n{'🎡' * 35}")
print("FLYWHEEL FEEDING TIME!")
print(f"Alt pumps = Flywheel fuel!")
print(f"Current USD: ${usd_balance:.2f}")
print(f"Feed potential: ${total_feed_potential:.2f}")
print("THE MACHINE HUNGERS!")
print("🔥" * 35)