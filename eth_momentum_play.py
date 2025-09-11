#!/usr/bin/env python3
"""
🎯 ETH MOMENTUM PLAY
Sell a bit to create movement, then buy back harder!
Market maker tactics on thin overnight books!
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
║                       🎯 ETH MOMENTUM PLAY 🎯                            ║
║                    Creating Movement Through Action                       ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - EXECUTING MOMENTUM STRATEGY!")
print("=" * 70)

# Get starting price
eth_start = float(client.get_product('ETH-USD')['price'])
print(f"Starting ETH Price: ${eth_start:.2f}")

# Phase 1: Create liquidity
print("\n📤 PHASE 1: SELLING 0.02 ETH")
print("-" * 40)

try:
    sell_order = client.market_order_sell(
        client_order_id=f"momentum_sell_{int(time.time()*1000)}",
        product_id="ETH-USD",
        base_size="0.02"
    )
    print(f"✅ Sold 0.02 ETH!")
    print(f"   Generated ~$91 USD")
    time.sleep(3)
except Exception as e:
    print(f"⚠️ {str(e)[:80]}")

# Check USD balance
accounts = client.get_accounts()['accounts']
usd_balance = 0
for acc in accounts:
    if acc['currency'] == 'USD':
        usd_balance = float(acc['available_balance']['value'])
        print(f"\n💵 USD Available: ${usd_balance:.2f}")
        break

# Phase 2: Buy back aggressively
print("\n📥 PHASE 2: AGGRESSIVE BUY BACK")
print("-" * 40)

if usd_balance > 90:
    # Split into multiple buys for impact
    buy_amounts = [30, 25, 20, 15]  # $90 total
    
    for amount in buy_amounts:
        if amount <= usd_balance:
            try:
                print(f"💥 Buying ${amount} of ETH...")
                buy_order = client.market_order_buy(
                    client_order_id=f"momentum_buy_{int(time.time()*1000)}",
                    product_id="ETH-USD",
                    quote_size=str(amount)
                )
                print(f"   ✅ Executed!")
                time.sleep(2)
                
                # Check new price
                eth_new = float(client.get_product('ETH-USD')['price'])
                print(f"   ETH now: ${eth_new:.2f} ({eth_new - eth_start:+.2f})")
                
            except Exception as e:
                print(f"   ⚠️ {str(e)[:50]}")

# Final check
print("\n" + "=" * 70)
print("🎯 MOMENTUM PLAY COMPLETE!")

time.sleep(3)
eth_final = float(client.get_product('ETH-USD')['price'])
total_move = eth_final - eth_start

print(f"Starting price: ${eth_start:.2f}")
print(f"Final price: ${eth_final:.2f}")
print(f"Total movement: ${total_move:+.2f}")

if total_move > 0:
    print("\n🔥 SUCCESS! ETH MOVING UP!")
    print("The momentum play worked!")
else:
    print("\n📊 Market absorbed the play")
    print("But we tried to move it!")

print("\n💭 Market Maker Wisdom:")
print("Sometimes you have to create the movement you want to see!")
print("=" * 70)