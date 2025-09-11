#!/usr/bin/env python3
"""
💰 PORTFOLIO & LIQUIDITY CHECK
"""

import json
from coinbase.rest import RESTClient

config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"])

print("💰 PORTFOLIO BREAKDOWN:")
print("-" * 40)

accounts = client.get_accounts()["accounts"]
total_value = 0
holdings = []

for acc in accounts:
    balance = float(acc["available_balance"]["value"])
    if balance > 0:
        currency = acc["currency"]
        
        if currency == "USD":
            holdings.append((currency, balance, balance))
            total_value += balance
        else:
            try:
                ticker = client.get_product(f"{currency}-USD")
                price = float(ticker["price"])
                usd_value = balance * price
                if usd_value > 1:
                    holdings.append((currency, balance, usd_value))
                    total_value += usd_value
            except:
                pass

# Sort by USD value
holdings.sort(key=lambda x: x[2], reverse=True)

for currency, balance, usd_value in holdings:
    if currency == "USD":
        print(f"{currency:6} | ${usd_value:10.2f}")
    else:
        print(f"{currency:6} | {balance:12.2f} | ${usd_value:10.2f}")

print("-" * 40)
print(f"Total: ${total_value:.2f}")

# Quick liquidity generation
usd_balance = next((h[2] for h in holdings if h[0] == "USD"), 0)
if total_value > 1000 and usd_balance < 100:
    print("\n🚨 LIQUIDITY RESTORATION NEEDED!")
    print("Options to generate USD:")
    
    for currency, balance, usd_value in holdings:
        if currency != "USD" and usd_value > 100:
            # Calculate how much to sell for $200 USD
            ticker = client.get_product(f"{currency}-USD")
            price = float(ticker["price"])
            amount_for_200 = min(200 / price, balance * 0.2)  # Max 20% of holdings
            
            print(f"  • Sell {amount_for_200:.4f} {currency} → ~${amount_for_200 * price:.2f}")
            
    print("\n🎯 Target: $200-500 USD for trading fuel")