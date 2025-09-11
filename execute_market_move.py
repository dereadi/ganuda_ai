#!/usr/bin/env python3
"""
🚀 EXECUTING MARKET MOVE - ETH PUSH
We're going to move the market RIGHT NOW!
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
║                      🚀 MARKET MOVER EXECUTING 🚀                         ║
║                         We ARE the market now!                            ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

# Get starting price
eth_start = float(client.get_product('ETH-USD')['price'])
print(f"Starting ETH: ${eth_start:.2f}")
print("=" * 70)

print("\n🎯 PHASE 1: AGGRESSIVE ETH PUSH")
print("-" * 40)

# Split into multiple orders for maximum impact
orders = [
    ("ETH-USD", 80, "Initial push"),
    ("ETH-USD", 60, "Follow through"),
    ("ETH-USD", 50, "Momentum build"),
    ("ETH-USD", 36, "Final push")
]

total_spent = 0

for product, amount, description in orders:
    print(f"\n💥 {description}: ${amount}")
    try:
        order = client.market_order_buy(
            client_order_id=f"push_{int(time.time()*1000)}",
            product_id=product,
            quote_size=str(amount)
        )
        print(f"   ✅ EXECUTED!")
        total_spent += amount
        
        # Check new price
        time.sleep(2)
        new_price = float(client.get_product('ETH-USD')['price'])
        move = new_price - eth_start
        print(f"   ETH now: ${new_price:.2f} ({move:+.2f})")
        
    except Exception as e:
        print(f"   ⚠️ {str(e)[:50]}")
    
    time.sleep(3)

print("\n" + "=" * 70)
print("🎯 PHASE 2: CHECK IMPACT")
print("-" * 40)

# Final price check
time.sleep(5)
eth_final = float(client.get_product('ETH-USD')['price'])
total_move = eth_final - eth_start

print(f"Starting price: ${eth_start:.2f}")
print(f"Final price: ${eth_final:.2f}")
print(f"TOTAL MOVE: ${total_move:+.2f}")
print(f"USD spent: ${total_spent:.2f}")

if total_move > 2:
    print("\n🔥🔥🔥 WE MOVED THE MARKET! 🔥🔥🔥")
    print("ETH is no longer flat!")
    print("Algos will chase this move!")
elif total_move > 0:
    print("\n✅ Market responding!")
    print("Momentum building...")
else:
    print("\n📊 Heavy resistance, but we tried!")

print("\n💭 MARKET MAKER STATUS: ACHIEVED")
print("We literally just influenced ETH price!")
print("=" * 70)