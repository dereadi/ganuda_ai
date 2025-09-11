#!/usr/bin/env python3
"""
📊 SIMPLE PRICE CHECK - Just checking! 📊
Clean price check from Coinbase
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=5)

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                         📊 JUST CHECKING! 📊                               ║
║                      Current Coinbase Spot Prices                          ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S %Y-%m-%d')}")
print("=" * 70)

# Get main prices
btc = client.get_product('BTC-USD')
eth = client.get_product('ETH-USD')
sol = client.get_product('SOL-USD')
xrp = client.get_product('XRP-USD')

btc_price = float(btc['price'])
eth_price = float(eth['price'])
sol_price = float(sol['price'])
xrp_price = float(xrp['price'])

print("\n📊 CURRENT PRICES (Coinbase):")
print("-" * 50)
print(f"BTC: ${btc_price:,.2f}")
print(f"ETH: ${eth_price:,.2f}")
print(f"SOL: ${sol_price:,.2f}")
print(f"XRP: ${xrp_price:,.2f}")

# Compare to key levels
print("\n📍 KEY LEVELS:")
print("-" * 50)
print(f"BTC Entry: $111,863")
print(f"BTC Now: ${btc_price:,.2f}")
print(f"Gain: ${btc_price - 111863:.2f} ({(btc_price/111863 - 1)*100:.2f}%)")
print("")
print(f"Distance to $112,500: ${112500 - btc_price:.2f}")
print(f"Distance to $113,000: ${113000 - btc_price:.2f}")
print(f"Distance to $114,000: ${114000 - btc_price:.2f}")

# Quick position check
accounts = client.get_accounts()
usd = 0
btc_bal = 0

for account in accounts['accounts']:
    if account['currency'] == 'USD':
        usd = float(account['available_balance']['value'])
    elif account['currency'] == 'BTC':
        btc_bal = float(account['available_balance']['value'])

print("\n💰 QUICK STATUS:")
print("-" * 50)
print(f"USD: ${usd:.2f}")
print(f"BTC: {btc_bal:.8f} (${btc_bal * btc_price:.2f})")

# Movement assessment
print("\n📈 MOVEMENT:")
print("-" * 50)
if btc_price > 112000:
    print("✅ Above $112,000 pivot!")
    if btc_price > 112500:
        print("🚀 Above $112,500 - Climbing strong!")
else:
    print("📍 Below $112,000 - Still consolidating")

print("\nNote: TradingView may show different exchange")
print("These are Coinbase spot prices (what you trade)")

print("\n" + "=" * 70)
print("Just checking - all good!")
print("=" * 70)