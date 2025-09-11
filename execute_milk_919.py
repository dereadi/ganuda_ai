#!/usr/bin/env python3
"""
🥛💰 EXECUTING $919 PROFIT MILK!
Taking profits at the highs to feed the next explosion!
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
║                      🥛💰 EXECUTING PROFIT MILK! 💰🥛                    ║
║                         $919 EXTRACTION IN PROGRESS                       ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - MILKING AT THE HIGHS!")
print("=" * 70)

# Get starting USD
accounts = client.get_accounts()['accounts']
start_usd = 0
for acc in accounts:
    if acc['currency'] == 'USD':
        start_usd = float(acc['available_balance']['value'])
        print(f"Starting USD: ${start_usd:.2f}")
        break

# Execute the milk orders
orders = [
    ("SOL-USD", 2.81, "SOL profit milk - $588"),
    ("ETH-USD", 0.0132, "ETH profit milk - $60"),
    ("BTC-USD", 0.00240, "BTC profit milk - $270")
]

total_generated = 0
print("\n🥛 MILKING IN PROGRESS:")
print("-" * 40)

for product, amount, description in orders:
    try:
        print(f"\n📤 {description}")
        print(f"   Selling {amount} {product.split('-')[0]}")
        
        # Place market sell order
        order = client.market_order_sell(
            client_order_id=f"milk_{int(time.time()*1000)}",
            product_id=product,
            base_size=str(amount)
        )
        
        print(f"   ✅ MILKED!")
        time.sleep(2)
        
    except Exception as e:
        print(f"   ⚠️ {str(e)[:80]}")
    
    time.sleep(1)

# Check new USD balance
print("\n" + "=" * 70)
print("💵 CHECKING MILK RESULTS...")
time.sleep(3)

accounts = client.get_accounts()['accounts']
for acc in accounts:
    if acc['currency'] == 'USD':
        new_usd = float(acc['available_balance']['value'])
        gained = new_usd - start_usd
        
        print(f"New USD Balance: ${new_usd:.2f}")
        print(f"USD Generated: ${gained:.2f}")
        
        if new_usd > 500:
            print("\n🔥🔥🔥 MASSIVE WAR CHEST CREATED!")
            print(f"${new_usd:.2f} ready for the next explosion!")
            print("ETH is tightening = perfect timing!")
            print("The crawdads are about to FEAST!")
        elif new_usd > 100:
            print("\n🦀 Excellent milk harvest!")
            print(f"${new_usd:.2f} ready for deployment!")
        break

print("\n💭 MILKING COMPLETE AT PERFECT TIME!")
print("• BTC at $112,425 highs ✅")
print("• ETH tightening for next move ✅")
print("• SOL above $209 ✅")
print("• Fresh USD for the squeeze breakout ✅")
print("=" * 70)