#!/usr/bin/env python3
"""
🔥 GENERATE LIQUIDITY FOR ETH BOUNCE
"""

import json
from coinbase.rest import RESTClient
import time

config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"])

print("🔥 GENERATING $300 USD FOR ETH BOUNCE TRADE")
print("=" * 50)

orders = []

# Sell 1 SOL for ~$196
try:
    order = client.market_order_sell(
        client_order_id=f"sol_liq_{int(time.time()*1000)}",
        product_id="SOL-USD",
        base_size="1"
    )
    print("✅ Sold 1 SOL")
    orders.append("1 SOL")
    time.sleep(1)
except Exception as e:
    print(f"SOL order failed: {e}")

# Sell 5 AVAX for ~$120
try:
    order = client.market_order_sell(
        client_order_id=f"avax_liq_{int(time.time()*1000)}",
        product_id="AVAX-USD",
        base_size="5"
    )
    print("✅ Sold 5 AVAX")
    orders.append("5 AVAX")
    time.sleep(1)
except Exception as e:
    print(f"AVAX order failed: {e}")

# Wait for settlement
print("\n⏳ Waiting for orders to settle...")
time.sleep(3)

# Check new balance
accounts = client.get_accounts()["accounts"]
for acc in accounts:
    if acc["currency"] == "USD":
        new_balance = float(acc["available_balance"]["value"])
        print(f"\n💰 NEW USD BALANCE: ${new_balance:.2f}")
        
        if new_balance > 250:
            print("✅ LIQUIDITY READY FOR ETH BOUNCE TRADE!")
            
            # Now execute ETH bounce trade
            ticker = client.get_product("ETH-USD")
            eth_price = float(ticker["price"])
            
            print(f"\n🎯 EXECUTING ETH BOUNCE TRADE")
            print(f"  ETH Price: ${eth_price:.2f}")
            print(f"  Trade Size: $200")
            
            try:
                order = client.market_order_buy(
                    client_order_id=f"eth_bounce_{int(time.time()*1000)}",
                    product_id="ETH-USD",
                    quote_size="200"
                )
                print(f"✅ ETH BUY ORDER PLACED!")
                print(f"  Entry: ${eth_price:.2f}")
                print(f"  Target: ${eth_price * 1.03:.2f} (+3%)")
                print(f"  Stop: ${eth_price * 0.98:.2f} (-2%)")
            except Exception as e:
                print(f"ETH order failed: {e}")
        break

print("\n📊 Summary:")
for o in orders:
    print(f"  • Sold {o} for liquidity")