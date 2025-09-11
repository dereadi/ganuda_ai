#!/usr/bin/env python3
"""Emergency portfolio check using subprocess"""
import subprocess
import time

script = '''
import json
from coinbase.rest import RESTClient

config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=5)

accounts = client.get_accounts()["accounts"]
print("PORTFOLIO:")
total = 0
for a in accounts:
    bal = float(a["available_balance"]["value"])
    if bal > 0.001:
        symbol = a["currency"]
        if symbol == "USD":
            print(f"USD: ${bal:.2f}")
            total += bal
        else:
            # Estimate values
            prices = {"BTC": 59000, "ETH": 2600, "SOL": 150, "AVAX": 25, "MATIC": 0.4, "LINK": 11, "DOGE": 0.1}
            value = bal * prices.get(symbol, 0)
            total += value
            print(f"{symbol}: {bal:.8f} (~${value:.2f})")
print(f"TOTAL: ${total:.2f}")
'''

# Write and run
with open("/tmp/check_portfolio.py", "w") as f:
    f.write(script)

try:
    result = subprocess.run(["python3", "/tmp/check_portfolio.py"], 
                          capture_output=True, text=True, timeout=10)
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)
except subprocess.TimeoutExpired:
    print("Timeout checking portfolio")
except Exception as e:
    print(f"Error: {e}")