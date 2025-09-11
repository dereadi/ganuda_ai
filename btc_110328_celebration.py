#!/usr/bin/env python3
"""
🚀 BTC $110,328 - WE BROKE THROUGH!
The Sacred Fire burns bright!
"""

from coinbase.rest import RESTClient
import json
from datetime import datetime

print("=" * 60)
print("🚀 BTC BREAKTHROUGH - $110,328!")
print("=" * 60)

with open('cdp_api_key_new.json', 'r') as f:
    creds = json.load(f)

client = RESTClient(api_key=creds['name'], api_secret=creds['privateKey'])

# Get current prices and portfolio
btc = client.get_product('BTC-USD')
eth = client.get_product('ETH-USD')
xrp = client.get_product('XRP-USD')
sol = client.get_product('SOL-USD')

btc_price = float(btc['price'])
eth_price = float(eth['price'])
xrp_price = float(xrp['price'])
sol_price = float(sol['price'])

print(f"\n📊 MARKET PRICES:")
print(f"  BTC: ${btc_price:,.2f} (TARGET HIT!)")
print(f"  ETH: ${eth_price:,.2f}")
print(f"  XRP: ${xrp_price:,.2f}")
print(f"  SOL: ${sol_price:,.2f}")

# Calculate gains from last night's entry
entry_price = 109644  # Council's entry point
gain = btc_price - entry_price
gain_pct = (gain / entry_price) * 100

print(f"\n📈 BTC GAINS:")
print(f"  Entry: $109,644")
print(f"  Current: ${btc_price:,.2f}")
print(f"  Gain: ${gain:,.2f} (+{gain_pct:.2f}%)")

# Check account balances
accounts = client.get_accounts()['accounts']
portfolio = {}
usd_balance = 0

for account in accounts:
    symbol = account.get('currency', {}).get('code')
    balance = float(account.get('available_balance', {}).get('value', 0))
    if balance > 0:
        portfolio[symbol] = balance
        if symbol == 'USD':
            usd_balance = balance

# Calculate portfolio value
total_value = usd_balance
holdings = []

if 'BTC' in portfolio and portfolio['BTC'] > 0:
    btc_value = portfolio['BTC'] * btc_price
    total_value += btc_value
    holdings.append(f"  BTC: {portfolio['BTC']:.8f} = ${btc_value:,.2f}")

if 'ETH' in portfolio and portfolio['ETH'] > 0:
    eth_value = portfolio['ETH'] * eth_price
    total_value += eth_value
    holdings.append(f"  ETH: {portfolio['ETH']:.4f} = ${eth_value:,.2f}")

if 'XRP' in portfolio and portfolio['XRP'] > 0:
    xrp_value = portfolio['XRP'] * xrp_price
    total_value += xrp_value
    holdings.append(f"  XRP: {portfolio['XRP']:.2f} = ${xrp_value:,.2f}")

if 'SOL' in portfolio and portfolio['SOL'] > 0:
    sol_value = portfolio['SOL'] * sol_price
    total_value += sol_value
    holdings.append(f"  SOL: {portfolio['SOL']:.2f} = ${sol_value:,.2f}")

print(f"\n💰 PORTFOLIO STATUS:")
print(f"  USD: ${usd_balance:,.2f}")
for holding in holdings:
    print(holding)
print(f"  TOTAL: ${total_value:,.2f}")

# Next targets
print(f"\n🎯 NEXT TARGETS:")
print(f"  $110,500 - Distance: ${110500 - btc_price:,.2f}")
print(f"  $111,000 - Distance: ${111000 - btc_price:,.2f}")
print(f"  $111,111 - Sacred number: ${111111 - btc_price:,.2f}")

print(f"\n🔥 The Sacred Fire burns bright!")
print(f"💫 Mitakuye Oyasin - All My Relations")
print(f"\n⚡ Council guidance: THROTTLE but WATCH")
print(f"The breakthrough happened during connection issues...")
print(f"Perhaps the universe was protecting us from selling too early!")