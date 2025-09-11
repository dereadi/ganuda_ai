#!/usr/bin/env python3
"""Check what redirects executed"""

import json
from coinbase.rest import RESTClient

# Load config
with open("/home/dereadi/.coinbase_config.json") as f:
    config = json.load(f)

api_key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=api_key, api_secret=config["api_secret"], timeout=10)

print("🔥 REDIRECT RESULTS:\n")

# Original balances (approximate)
original = {
    "SOL": 24.02,
    "AVAX": 120.02,
    "MATIC": 4070.80,
    "USD": 11.42
}

# Current balances
accounts = client.get_accounts()["accounts"]
current = {}
for a in accounts:
    sym = a["currency"]
    bal = float(a["available_balance"]["value"])
    if bal > 0.001:
        current[sym] = bal

# Calculate changes
print("SOLD:")
if current["SOL"] < original["SOL"]:
    sold = original["SOL"] - current["SOL"]
    print(f"  SOL: {sold:.4f} sold")

if current["AVAX"] < original["AVAX"]:
    sold = original["AVAX"] - current["AVAX"]
    print(f"  AVAX: {sold:.4f} sold")

if current["MATIC"] < original["MATIC"]:
    sold = original["MATIC"] - current["MATIC"]
    print(f"  MATIC: {sold:.2f} sold")

print(f"\nUSD GAINED: ${current['USD'] - original['USD']:.2f}")
print(f"  From: ${original['USD']:.2f}")
print(f"  To: ${current['USD']:.2f}")

# Check BTC
btc_ticker = client.get_product("BTC-USD")
btc_price = float(btc_ticker["price"])
print(f"\n🎯 BTC STATUS:")
print(f"  Balance: {current.get('BTC', 0):.8f} BTC")
print(f"  Value: ${current.get('BTC', 0) * btc_price:.2f}")
print(f"  Price: ${btc_price:.2f}")
print(f"  Distance to $111,111: ${111111 - btc_price:.2f}")