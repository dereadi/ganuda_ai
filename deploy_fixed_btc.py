#!/usr/bin/env python3
"""Fixed BTC deployment"""

import subprocess
import time

# Use subprocess to work around API issues
script = '''
import json
from coinbase.rest import RESTClient
import time

config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=10)

# Check balances
accounts = client.get_accounts()["accounts"]
usd = 0
for a in accounts:
    if a["currency"] == "USD":
        usd = float(a["available_balance"]["value"])
        break

print(f"USD Available: ${usd:.2f}")

if usd > 10:
    deploy = round(usd - 10, 2)
    print(f"Deploying: ${deploy}")
    
    # Create order
    try:
        order = client.create_order(
            client_order_id=f"btc_{int(time.time())}",
            product_id="BTC-USD",
            side="BUY",
            order_configuration={
                "market_market_ioc": {
                    "quote_size": str(deploy)
                }
            }
        )
        print(f"Order ID: {order.order_id if hasattr(order, 'order_id') else 'Failed'}")
    except Exception as e:
        print(f"Error: {e}")
'''

with open("/tmp/deploy_btc.py", "w") as f:
    f.write(script)

result = subprocess.run(["python3", "/tmp/deploy_btc.py"], capture_output=True, text=True, timeout=10)
print(result.stdout)
if result.stderr:
    print(result.stderr)