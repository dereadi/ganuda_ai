#!/usr/bin/env python3
"""
Test ONE real trade to confirm everything works
"""

import json
import time
from coinbase.rest import RESTClient

print("🦀 TESTING ONE REAL TRADE")
print("=" * 50)

# Load config
config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]

# Connect
print("Connecting...")
client = RESTClient(api_key=key, api_secret=config["api_secret"])

# Get balance
accounts = client.get_accounts()
usd_account = [a for a in accounts["accounts"] if a["currency"] == "USD"][0]
balance = float(usd_account["available_balance"]["value"])

print(f"✅ Connected! Balance: ${balance:.2f}")
print()

# Make ONE small trade
print("Making ONE test trade: Buy $5 of Bitcoin")
print("Executing in 3 seconds...")
time.sleep(3)

try:
    order = client.market_order_buy(
        client_order_id=f"test_{int(time.time())}",
        product_id="BTC-USD",
        quote_size="5.00"  # Buy exactly $5 worth
    )
    
    print("\n📊 Order Result:")
    print(f"Order object: {order}")
    
    # Try to access order attributes
    if hasattr(order, 'order_id'):
        print(f"\n✅ SUCCESS! Order ID: {order['order_id']}")
        print("The crawdads can trade your money!")
    else:
        print("\n⚠️ Order response unclear")
        
except Exception as e:
    print(f"\n❌ Error: {e}")

print("\nTest complete!")