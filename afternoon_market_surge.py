#!/usr/bin/env python3
"""
📰 AFTERNOON MARKET SURGE ANALYSIS
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"])

print("📰 CRYPTO MARKET UPDATE - AFTERNOON SURGE")
print("=" * 60)
print(f"Time: {datetime.now().strftime('%I:%M %p CST')}")
print("=" * 60)

# Get major coins
markets = {}
for coin in ["BTC", "ETH", "SOL", "AVAX", "MATIC", "LINK", "ATOM", "NEAR", "DOGE"]:
    try:
        ticker = client.get_product(f"{coin}-USD")
        price = float(ticker["price"])
        markets[coin] = price
    except:
        pass

# Display market prices
print("\n🔥 MARKET PRICES:")
print("-" * 60)
for coin, price in markets.items():
    if coin in ["BTC", "ETH"]:
        print(f"{coin:5} ${price:>12,.2f}")
    else:
        print(f"{coin:5} ${price:>12.4f}")

# Check our positions
print("\n💼 OUR POSITIONS:")
print("-" * 60)

accounts = client.get_accounts()["accounts"]
total_value = 0
positions = {}

for acc in accounts:
    balance = float(acc["available_balance"]["value"])
    if balance > 0:
        currency = acc["currency"]
        if currency == "USD":
            positions["USD"] = balance
            total_value += balance
        elif currency in markets:
            value = balance * markets[currency]
            if value > 10:
                positions[currency] = {"balance": balance, "value": value}
                total_value += value

for coin in positions:
    if coin != "USD":
        data = positions[coin]
        print(f"{coin:5} {data['balance']:>10.4f} = ${data['value']:>8.2f}")

if "USD" in positions:
    print(f"USD   ${positions['USD']:>10.2f}")

print(f"\nTotal Portfolio: ${total_value:,.2f}")

# Trading signals based on levels
print("\n🎯 AFTERNOON TRADING SIGNALS:")
print("-" * 60)

# ETH analysis
eth_price = markets.get("ETH", 0)
if eth_price > 0:
    if eth_price > 4600:
        print(f"• ETH at ${eth_price:.2f} - Breaking resistance! 🚀")
    elif eth_price < 4550:
        print(f"• ETH at ${eth_price:.2f} - Testing support zone 📊")
    else:
        print(f"• ETH at ${eth_price:.2f} - Consolidating")
    
    # Our ETH position
    if "ETH" in positions:
        eth_pnl = ((eth_price - 4575.70) / 4575.70) * 100
        print(f"  → Our ETH: {eth_pnl:+.2f}% P&L")

# SOL analysis  
sol_price = markets.get("SOL", 0)
if sol_price > 200:
    print(f"• SOL at ${sol_price:.2f} - Above $200 psychological level 💪")
elif sol_price > 0:
    print(f"• SOL at ${sol_price:.2f}")

# BTC analysis
btc_price = markets.get("BTC", 0)
if btc_price > 112000:
    print(f"• BTC at ${btc_price:,.0f} - New highs territory! 🔥")
elif btc_price > 110000:
    print(f"• BTC at ${btc_price:,.0f} - Strong above $110k")

# AVAX check
if "AVAX" in markets and markets["AVAX"] < 24:
    print(f"• AVAX at ${markets['AVAX']:.2f} - Potential bounce zone")

print("\n📊 SYSTEM STATUS:")
print("-" * 60)

# Check active processes
import subprocess
result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
specialists = result.stdout.count("specialist.py")
flywheels = result.stdout.count("flywheel")
crawdads = result.stdout.count("crawdad")

print(f"• Specialists: {specialists} active")
print(f"• Flywheels: {flywheels} spinning")
print(f"• Crawdads: {crawdads} hunting")

# Check recent logs
try:
    with open("flywheel_accelerator.log", "r") as f:
        lines = f.readlines()
        if lines:
            last_line = lines[-1] if lines[-1].strip() else lines[-2]
            if "PULSE" in last_line:
                print(f"• Last flywheel: {last_line.strip()}")
except:
    pass

print("\n🔥 AFTERNOON SURGE READY!")
print("=" * 60)