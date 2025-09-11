#!/usr/bin/env python3
"""
💰 PROFIT HARVEST - 23:13 EXTRACTION
Taking profits from the escape to feed the flywheel!
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
║                     💰 PROFIT HARVEST TIME! 💰                           ║
║                   Feeding the Flywheel After Escape!                      ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - EXTRACTING PROFITS!")
print("=" * 70)

# Get starting USD
accounts = client.get_accounts()['accounts']
start_usd = 0
for acc in accounts:
    if acc['currency'] == 'USD':
        start_usd = float(acc['available_balance']['value'])
        print(f"Starting USD: ${start_usd:.2f}")
        break

# Execute profit extraction
orders = [
    ("SOL-USD", 3.14, "SOL profit extraction"),
    ("BTC-USD", 0.00242, "BTC profit extraction"),
    ("ETH-USD", 0.0105, "ETH profit extraction")
]

total_generated = 0
print("\n🔥 EXECUTING PROFIT EXTRACTION:")
print("-" * 40)

for product, amount, description in orders:
    try:
        print(f"\n📤 {description}")
        print(f"   Selling {amount} {product.split('-')[0]}")
        
        # Place market sell order
        order = client.market_order_sell(
            client_order_id=f"harvest_{int(time.time()*1000)}",
            product_id=product,
            base_size=str(amount)
        )
        
        # Get fill price
        time.sleep(2)
        try:
            filled_value = float(order['value'])
            total_generated += filled_value
            print(f"   ✅ Generated: ${filled_value:.2f}")
        except:
            print(f"   ✅ Order placed!")
            
    except Exception as e:
        print(f"   ⚠️ {str(e)[:80]}")
    
    time.sleep(2)

# Check new USD balance
print("\n" + "=" * 70)
print("💵 CHECKING NEW USD BALANCE...")
time.sleep(3)

accounts = client.get_accounts()['accounts']
for acc in accounts:
    if acc['currency'] == 'USD':
        new_usd = float(acc['available_balance']['value'])
        gained = new_usd - start_usd
        print(f"New USD Balance: ${new_usd:.2f}")
        print(f"USD Generated: ${gained:.2f}")
        
        if new_usd > 100:
            print("\n🦀 CRAWDAD FEEDING TIME!")
            print(f"The swarm has ${new_usd:.2f} to feast on!")
            print("They're about to go WILD!")
        break

print("\n💭 PROFIT HARVEST COMPLETE!")
print("The flywheel is fed, crawdads are ready!")
print("Let the feeding frenzy begin!")
print("=" * 70)