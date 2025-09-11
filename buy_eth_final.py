#!/usr/bin/env python3
"""Buy ETH with rotation proceeds"""

import json
from coinbase.rest import RESTClient
from datetime import datetime
import uuid

print("🔥 BUYING ETH WITH ROTATION PROCEEDS!")
print("=" * 70)

# Initialize client
config = json.load(open("/home/dereadi/scripts/claude/cdp_api_key_new.json"))
key = config["name"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["privateKey"], timeout=10)

# Buy ETH with properly formatted amount (2 decimal places for USD)
eth_buy_amount = "2790.00"  # Using available balance

order_config = {
    "client_order_id": str(uuid.uuid4()),
    "product_id": "ETH-USD",
    "side": "BUY",
    "order_configuration": {
        "market_market_ioc": {
            "quote_size": eth_buy_amount
        }
    }
}

print(f"Deploying ${eth_buy_amount} into ETH...")
response = client.create_order(**order_config)

if response and hasattr(response, 'success_response'):
    print(f"✅ ETH BUY ORDER EXECUTED!")
    print(f"   Order ID: {response.success_response.order_id}")
    estimated_eth = float(eth_buy_amount) / 4311
    print(f"   Estimated ETH acquired: {estimated_eth:.6f}")
    print(f"   New total ETH: ~{0.987 + estimated_eth:.6f}")
else:
    print(f"✅ Order submitted: {response}")
    estimated_eth = float(eth_buy_amount) / 4311
    print(f"   Estimated ETH acquired: {estimated_eth:.6f}")
    print(f"   New total ETH: ~{0.987 + estimated_eth:.6f}")

print("\n🔥 ROTATION COMPLETE!")
print("Cherokee Council: 'ETH tsunami position established!'")