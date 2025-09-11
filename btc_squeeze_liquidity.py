#!/usr/bin/env python3
"""
🔥 EMERGENCY LIQUIDITY FOR BTC SQUEEZE
"""

import json
from coinbase.rest import RESTClient
import time

config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"])

print("🔥 EMERGENCY LIQUIDITY FOR BTC SQUEEZE")
print("=" * 50)

# Sell 2000 MATIC for immediate liquidity
try:
    order = client.market_order_sell(
        client_order_id=f"squeeze_liq_{int(time.time()*1000)}",
        product_id="MATIC-USD",
        base_size="2000"
    )
    print("✅ Sold 2000 MATIC")
    time.sleep(2)
except Exception as e:
    print(f"MATIC order failed: {e}")

# Check new balance
accounts = client.get_accounts()["accounts"]
for acc in accounts:
    if acc["currency"] == "USD":
        usd = float(acc["available_balance"]["value"])
        print(f"New USD: ${usd:.2f}")
        
        if usd > 400:
            # Execute BTC squeeze trade
            ticker = client.get_product("BTC-USD")
            btc_price = float(ticker["price"])
            
            print(f"\n🚀 POSITIONING FOR SQUEEZE")
            print(f"BTC: ${btc_price:,.2f}")
            
            try:
                order = client.market_order_buy(
                    client_order_id=f"btc_squeeze_{int(time.time()*1000)}",
                    product_id="BTC-USD",
                    quote_size="200"
                )
                print(f"✅ BTC squeeze position: $200")
            except Exception as e:
                print(f"BTC order failed: {e}")
        break

print("=" * 50)