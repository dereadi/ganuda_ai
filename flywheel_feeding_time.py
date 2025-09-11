#!/usr/bin/env python3
"""
⚙️ FLYWHEEL FEEDING TIME
Extract profits from winners to power the machine
"""

import json
import time
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                      ⚙️ FLYWHEEL FEEDING PROTOCOL ⚙️                      ║
║                    Milking profits to power the machine                   ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
print(f"Current USD: $6.66 (NEED MORE!)")
print("=" * 70)

# Feeding targets based on analysis
feeding_plan = [
    ("SOL", 3.0, "Taking 15% from SOL winner"),
    ("AVAX", 18.0, "Taking 15% from AVAX gainer"),
    ("MATIC", 850, "Trimming MATIC position"),
    ("DOGE", 400, "Converting meme to fuel")
]

print("\n🥛 FEEDING THE FLYWHEEL:")
print("-" * 40)

total_generated = 0
successful_feeds = []

for coin, amount, reason in feeding_plan:
    print(f"\n⚙️ Feeding from {coin}:")
    print(f"   Amount: {amount}")
    print(f"   Reason: {reason}")
    
    try:
        # Execute the feed
        order = client.market_order_sell(
            client_order_id=f"feed_{coin.lower()}_{int(time.time()*1000)}",
            product_id=f"{coin}-USD",
            base_size=str(amount)
        )
        
        # Get price for calculation
        price = float(client.get_product(f'{coin}-USD')['price'])
        usd_generated = amount * price
        total_generated += usd_generated
        successful_feeds.append((coin, amount, usd_generated))
        
        print(f"   ✅ FED! Generated ~${usd_generated:.2f}")
        time.sleep(0.5)
        
    except Exception as e:
        print(f"   ❌ Failed: {str(e)[:50]}")

print("\n" + "=" * 70)
print(f"⚙️ FLYWHEEL FEEDING COMPLETE:")
print(f"   Total USD generated: ~${total_generated:.2f}")

# Verify new balance
time.sleep(3)
accounts = client.get_accounts()['accounts']
new_usd = 0
for acc in accounts:
    if acc['currency'] == 'USD':
        new_usd = float(acc['available_balance']['value'])
        break

print(f"   New USD balance: ${new_usd:.2f}")
print(f"   Increase: ${new_usd - 6.66:.2f}")

if new_usd > 300:
    print("\n✅ FLYWHEEL FULLY POWERED!")
    print("   Ready to:")
    print("   • Catch dips aggressively")
    print("   • Ride breakout momentum")
    print("   • Deploy crawdads effectively")
    print("   • Compound gains faster")
elif new_usd > 100:
    print("\n⚙️ FLYWHEEL SPINNING UP!")
    print("   Adequate fuel for trading")
else:
    print("\n⚠️ Still need more fuel")

print("\n💭 Cherokee Wisdom:")
print('"The river that shares its water feeds many streams."')
print('"Take from abundance to create more abundance."')
print("=" * 70)