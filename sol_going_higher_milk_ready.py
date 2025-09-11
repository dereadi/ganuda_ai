#!/usr/bin/env python3
"""
☀️🚀 SOL IS GOING HIGHER! 🚀☀️
Perfect milking opportunity approaching!
Wait for the pump, then milk!
Keep the core, feed the flywheel!
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
║                    ☀️🚀 SOL GOING HIGHER! 🚀☀️                            ║
║                      Milk Buckets Ready! 🥛🥛🥛                           ║
║                    Wait for Pump, Then Extract! 💰                         ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - SOL ASCENDING")
print("=" * 70)

# Get current SOL price
sol = client.get_product('SOL-USD')
sol_price = float(sol['price'])

# Get our position
accounts = client.get_accounts()
sol_balance = 0
usd_balance = 0

for account in accounts['accounts']:
    if account['currency'] == 'SOL':
        sol_balance = float(account['available_balance']['value'])
    elif account['currency'] == 'USD':
        usd_balance = float(account['available_balance']['value'])

sol_value = sol_balance * sol_price

print("\n☀️ SOL TRAJECTORY:")
print("-" * 50)
print(f"Current: ${sol_price:.2f}")
print(f"Direction: ⬆️ GOING HIGHER!")
print(f"Our Position: {sol_balance:.4f} SOL = ${sol_value:.2f}")

# Calculate milking zones
milk_zones = [
    (215, 0.05, "First milk - 5% of position"),
    (220, 0.10, "Second milk - 10% of position"),
    (225, 0.10, "Third milk - 10% more"),
    (230, 0.15, "Big milk - 15% extraction"),
    (240, 0.20, "Mega milk - 20% harvest"),
    (250, 0.20, "Ultimate milk - 20% final")
]

print("\n🥛 MILKING PLAN AS SOL RISES:")
print("-" * 50)

total_milk_potential = 0
for target, percent, description in milk_zones:
    if sol_price < target:
        milk_amount = sol_balance * percent
        milk_value = milk_amount * target
        total_milk_potential += milk_value
        print(f"${target}: {description}")
        print(f"  → Milk {milk_amount:.4f} SOL = ${milk_value:.2f}")

print(f"\n💰 TOTAL MILK POTENTIAL: ${total_milk_potential:.2f}")

# Real-time monitoring
print("\n📊 WATCHING SOL CLIMB:")
print("-" * 50)

for i in range(3):
    sol_check = client.get_product('SOL-USD')
    current = float(sol_check['price'])
    
    if current > sol_price:
        print(f"  ✅ ${current:.2f} - CLIMBING! (+${current - sol_price:.2f})")
    elif current < sol_price:
        print(f"  📍 ${current:.2f} - Consolidating")
    else:
        print(f"  📍 ${current:.2f} - Steady")
    
    if i < 2:
        time.sleep(2)

# Milking execution readiness
print("\n🎯 MILKING EXECUTION READY:")
print("-" * 50)

if sol_price > 213:
    print("🚨 READY TO MILK NOW!")
    milk_amount = sol_balance * 0.05
    print(f"Can milk: {milk_amount:.4f} SOL = ${milk_amount * sol_price:.2f}")
    
    print("\nExecuting small milk...")
    try:
        order = client.market_order_sell(
            client_order_id=f'sol_milk_{int(time.time())}',
            product_id='SOL-USD',
            base_size=str(round(milk_amount, 4))
        )
        print(f"✅ Milked {milk_amount:.4f} SOL!")
    except Exception as e:
        print(f"Note: {str(e)[:50]}")
else:
    print(f"Waiting for SOL > $213 (currently ${sol_price:.2f})")
    print(f"Need +${213 - sol_price:.2f} more")

# Strategy reminder
print("\n☀️ SOL MILKING WISDOM:")
print("-" * 50)
print("• SOL going higher = Perfect for milking")
print("• Extract profits on pumps")
print("• Keep 10+ SOL core always")
print("• Use milk to feed flywheel")
print("• Buy back on any dips")

# Final status
print(f"\n{'☀️' * 35}")
print("SOL IS GOING HIGHER!")
print(f"Current: ${sol_price:.2f}")
print(f"Position: {sol_balance:.4f} SOL")
print("MILK BUCKETS READY!")
print("🥛" * 35)