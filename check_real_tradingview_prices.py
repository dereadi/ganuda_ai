#!/usr/bin/env python3
"""
📊 CHECK REAL PRICES - TRADINGVIEW COMPARISON 📊
Let's verify actual price movements
Maybe we're seeing micro movements or delayed data
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=5)

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    📊 REAL PRICE CHECK - COINBASE 📊                       ║
║                     Comparing with TradingView                             ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
print("=" * 70)

# Get current prices from Coinbase
btc = client.get_product('BTC-USD')
eth = client.get_product('ETH-USD')
sol = client.get_product('SOL-USD')

btc_price = float(btc['price'])
eth_price = float(eth['price'])
sol_price = float(sol['price'])

print("\n📊 COINBASE ACTUAL PRICES:")
print("-" * 50)
print(f"BTC: ${btc_price:,.2f}")
print(f"ETH: ${eth_price:,.2f}")
print(f"SOL: ${sol_price:,.2f}")

# Check 24hr stats for real movement
btc_stats = client.get_product_stats('BTC-USD')
eth_stats = client.get_product_stats('ETH-USD')
sol_stats = client.get_product_stats('SOL-USD')

print("\n📈 24HR MOVEMENTS:")
print("-" * 50)

if 'stats_24hour' in btc_stats:
    btc_open = float(btc_stats['stats_24hour']['open'])
    btc_high = float(btc_stats['stats_24hour']['high'])
    btc_low = float(btc_stats['stats_24hour']['low'])
    btc_change = (btc_price - btc_open) / btc_open * 100
    
    print(f"BTC:")
    print(f"  24hr Open: ${btc_open:,.2f}")
    print(f"  24hr High: ${btc_high:,.2f}")
    print(f"  24hr Low: ${btc_low:,.2f}")
    print(f"  Current: ${btc_price:,.2f}")
    print(f"  24hr Change: {btc_change:+.2f}%")

if 'stats_24hour' in eth_stats:
    eth_open = float(eth_stats['stats_24hour']['open'])
    eth_change = (eth_price - eth_open) / eth_open * 100
    print(f"\nETH:")
    print(f"  24hr Open: ${eth_open:,.2f}")
    print(f"  Current: ${eth_price:,.2f}")
    print(f"  24hr Change: {eth_change:+.2f}%")

if 'stats_24hour' in sol_stats:
    sol_open = float(sol_stats['stats_24hour']['open'])
    sol_change = (sol_price - sol_open) / sol_open * 100
    print(f"\nSOL:")
    print(f"  24hr Open: ${sol_open:,.2f}")
    print(f"  Current: ${sol_price:,.2f}")
    print(f"  24hr Change: {sol_change:+.2f}%")

# Check our actual positions
accounts = client.get_accounts()
total_value = 0

print("\n💰 ACTUAL PORTFOLIO VALUE:")
print("-" * 50)

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if balance > 0.00001:
        if currency == 'USD':
            total_value += balance
            print(f"USD: ${balance:.2f}")
        elif currency == 'BTC':
            value = balance * btc_price
            total_value += value
            print(f"BTC: {balance:.8f} = ${value:.2f}")
        elif currency == 'ETH':
            value = balance * eth_price
            total_value += value
            print(f"ETH: {balance:.8f} = ${value:.2f}")
        elif currency == 'SOL':
            value = balance * sol_price
            total_value += value
            print(f"SOL: {balance:.4f} = ${value:.2f}")

print(f"\nTOTAL: ${total_value:.2f}")

# Analysis
print("\n📊 ANALYSIS:")
print("-" * 50)
print("If TradingView shows different:")
print("  • Could be different exchange data")
print("  • Coinbase vs Binance prices can differ")
print("  • TradingView might show composite price")
print("  • We're seeing Coinbase spot prices")
print("")
print("What matters:")
print(f"  • Our entry: $111,863")
print(f"  • Current BTC: ${btc_price:,.2f}")
print(f"  • We're up: ${(btc_price - 111863):.2f}")
print(f"  • Portfolio: ${total_value:.2f}")

print("\n" + "=" * 70)
print("These are REAL Coinbase prices")
print("Your positions are based on these")
print("TradingView may show different exchange")
print("=" * 70)