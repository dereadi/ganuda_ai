#!/usr/bin/env python3
"""
📊💰 COMPLETE POSITION CHECK - EVERY SINGLE ASSET! 💰📊
Let's see EVERYTHING we own!
Every coin, every token, every dollar!
Full portfolio scan!
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=5)

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                   📊 COMPLETE PORTFOLIO AUDIT 📊                           ║
║                      Every Single Position! 💎                             ║
║                    Nothing Hidden, Everything Counted! 🔍                  ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - FULL SCAN")
print("=" * 70)

# Get ALL accounts
accounts = client.get_accounts()
all_positions = []
usd_balance = 0
total_portfolio_value = 0

# Scan every single account
for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    # Include EVERYTHING, even dust
    if balance > 0.0000001:  # Capture even the tiniest amounts
        if currency == 'USD':
            usd_balance = balance
            all_positions.append({
                'currency': currency,
                'balance': balance,
                'price': 1.0,
                'value': balance
            })
            total_portfolio_value += balance
        else:
            # Try to get USD price
            try:
                if currency in ['USDC', 'USDT', 'DAI']:
                    # Stablecoins = $1
                    price = 1.0
                else:
                    product = client.get_product(f'{currency}-USD')
                    price = float(product['price'])
                
                value = balance * price
                all_positions.append({
                    'currency': currency,
                    'balance': balance,
                    'price': price,
                    'value': value
                })
                total_portfolio_value += value
            except:
                # Asset might not have USD pair or be unsupported
                all_positions.append({
                    'currency': currency,
                    'balance': balance,
                    'price': 0,
                    'value': 0,
                    'note': 'No USD price'
                })

# Sort by value (highest first)
all_positions.sort(key=lambda x: x['value'], reverse=True)

print("\n📊 ALL POSITIONS (SORTED BY VALUE):")
print("-" * 80)
print(f"{'#':<3} {'Asset':<8} {'Balance':<18} {'Price':<12} {'Value':<12} {'%Port':<8}")
print("-" * 80)

for i, pos in enumerate(all_positions, 1):
    percent = (pos['value'] / total_portfolio_value * 100) if total_portfolio_value > 0 else 0
    
    if pos['currency'] == 'USD':
        print(f"{i:<3} {pos['currency']:<8} ${pos['balance']:<17.2f} $1.00        ${pos['value']:<11.2f} {percent:<7.1f}%")
    elif 'note' in pos:
        print(f"{i:<3} {pos['currency']:<8} {pos['balance']:<18.8f} {'N/A':<12} {'$0.00':<12} {percent:<7.1f}%")
    else:
        if pos['value'] > 1000:
            # Major positions
            print(f"{i:<3} {pos['currency']:<8} {pos['balance']:<18.8f} ${pos['price']:<11.2f} ${pos['value']:<11.2f} {percent:<7.1f}%")
        elif pos['value'] > 100:
            # Medium positions
            print(f"{i:<3} {pos['currency']:<8} {pos['balance']:<18.4f} ${pos['price']:<11.4f} ${pos['value']:<11.2f} {percent:<7.1f}%")
        elif pos['value'] > 10:
            # Small positions
            print(f"{i:<3} {pos['currency']:<8} {pos['balance']:<18.4f} ${pos['price']:<11.4f} ${pos['value']:<11.2f} {percent:<7.1f}%")
        else:
            # Dust
            print(f"{i:<3} {pos['currency']:<8} {pos['balance']:<18.8f} ${pos['price']:<11.6f} ${pos['value']:<11.2f} {percent:<7.1f}%")

print("-" * 80)
print(f"{'TOTAL PORTFOLIO VALUE:':<50} ${total_portfolio_value:<11.2f} 100.0%")
print("=" * 80)

# Categories breakdown
print("\n📈 PORTFOLIO BREAKDOWN:")
print("-" * 50)

# Major holdings (>$1000)
major_holdings = [p for p in all_positions if p['value'] > 1000]
major_value = sum(p['value'] for p in major_holdings)
print(f"Major Holdings (>${1000}):")
for p in major_holdings:
    print(f"  • {p['currency']}: ${p['value']:.2f}")
print(f"  Total: ${major_value:.2f} ({major_value/total_portfolio_value*100:.1f}%)")

# Medium holdings ($100-$1000)
medium_holdings = [p for p in all_positions if 100 < p['value'] <= 1000]
if medium_holdings:
    medium_value = sum(p['value'] for p in medium_holdings)
    print(f"\nMedium Holdings ($100-$1000):")
    for p in medium_holdings:
        print(f"  • {p['currency']}: ${p['value']:.2f}")
    print(f"  Total: ${medium_value:.2f} ({medium_value/total_portfolio_value*100:.1f}%)")

# Small holdings (<$100)
small_holdings = [p for p in all_positions if 0 < p['value'] <= 100]
if small_holdings:
    small_value = sum(p['value'] for p in small_holdings)
    print(f"\nSmall Holdings (<$100):")
    for p in small_holdings:
        print(f"  • {p['currency']}: ${p['value']:.2f}")
    print(f"  Total: ${small_value:.2f} ({small_value/total_portfolio_value*100:.1f}%)")

# Performance metrics
print("\n🚀 PERFORMANCE METRICS:")
print("-" * 50)
starting_capital = 292.50
profit = total_portfolio_value - starting_capital
roi = (profit / starting_capital) * 100
multiple = total_portfolio_value / starting_capital

print(f"Starting Capital: ${starting_capital:.2f}")
print(f"Current Value: ${total_portfolio_value:.2f}")
print(f"Total Profit: ${profit:.2f}")
print(f"ROI: {roi:,.1f}%")
print(f"Multiple: {multiple:.1f}x")

# Quick stats
print("\n📊 QUICK STATS:")
print("-" * 50)
print(f"Total Positions: {len(all_positions)}")
print(f"USD Available: ${usd_balance:.2f}")
print(f"Invested in Crypto: ${total_portfolio_value - usd_balance:.2f}")
print(f"Number of Cryptos: {len(all_positions) - 1}")

# Current prices of majors
print("\n💹 CURRENT MARKET PRICES:")
print("-" * 50)
try:
    btc = client.get_product('BTC-USD')
    eth = client.get_product('ETH-USD')
    sol = client.get_product('SOL-USD')
    print(f"BTC: ${float(btc['price']):,.2f}")
    print(f"ETH: ${float(eth['price']):,.2f}")
    print(f"SOL: ${float(sol['price']):.2f}")
except:
    pass

print(f"\n{'💎' * 35}")
print("COMPLETE POSITION CHECK!")
print(f"TOTAL VALUE: ${total_portfolio_value:,.2f}")
print(f"PROFIT: ${profit:,.2f}")
print(f"MULTIPLE: {multiple:.1f}x")
print("EVERY SATOSHI COUNTED!")
print("🚀" * 35)