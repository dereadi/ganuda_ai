#!/usr/bin/env python3
"""
📊 COMPLETE PORTFOLIO ANALYSIS FOR $200K BTC
Get EVERY holding, calculate TRUE value
Project complete portfolio to $200k BTC
Include ALL assets, not just the main ones
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                 📊 COMPLETE PORTFOLIO ANALYSIS 📊                         ║
║                     Every Asset, Every Dollar                             ║
║                    Projecting to $200K BTC                                ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - FULL INVENTORY")
print("=" * 70)

# Get ALL current prices
prices = {}
prices['BTC'] = float(client.get_product('BTC-USD')['price'])
prices['ETH'] = float(client.get_product('ETH-USD')['price'])
prices['SOL'] = float(client.get_product('SOL-USD')['price'])

# Get other prices
try:
    prices['MATIC'] = float(client.get_product('MATIC-USD')['price'])
except:
    prices['MATIC'] = 0.243

try:
    prices['AVAX'] = float(client.get_product('AVAX-USD')['price'])
except:
    prices['AVAX'] = 24.70

try:
    prices['DOGE'] = float(client.get_product('DOGE-USD')['price'])
except:
    prices['DOGE'] = 0.225

try:
    prices['XRP'] = float(client.get_product('XRP-USD')['price'])
except:
    prices['XRP'] = 3.01

try:
    prices['LINK'] = float(client.get_product('LINK-USD')['price'])
except:
    prices['LINK'] = 24.20

print(f"\n💹 CURRENT PRICES:")
print("-" * 50)
for asset, price in prices.items():
    if price > 100:
        print(f"{asset}: ${price:,.0f}")
    else:
        print(f"{asset}: ${price:.4f}")

# Get ALL account balances
accounts = client.get_accounts()
portfolio = {}
total_value = 0
usd_balance = 0

print(f"\n💼 COMPLETE HOLDINGS:")
print("-" * 50)

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if balance > 0.00001:  # Include even tiny amounts
        if currency == 'USD':
            usd_balance = balance
            print(f"\n💵 USD: ${balance:.2f}")
        elif currency in prices and prices[currency] > 0:
            value = balance * prices[currency]
            portfolio[currency] = {
                'balance': balance,
                'price': prices[currency],
                'value': value
            }
            total_value += value
            
            # Display based on value
            if balance > 1000:
                print(f"\n{currency}: {balance:,.2f} units")
            elif balance > 1:
                print(f"\n{currency}: {balance:.4f} units")
            else:
                print(f"\n{currency}: {balance:.8f} units")
            print(f"  @ ${prices[currency]:.4f} = ${value:,.2f}")
        else:
            # Try to get any other assets
            try:
                if currency == 'USDC':
                    value = balance
                    portfolio[currency] = {
                        'balance': balance,
                        'price': 1,
                        'value': value
                    }
                    total_value += value
                    print(f"\n{currency}: {balance:.2f} = ${value:.2f}")
            except:
                pass

print(f"\n{'='*50}")
print(f"TOTAL CRYPTO VALUE: ${total_value:,.2f}")
print(f"USD BALANCE: ${usd_balance:.2f}")
print(f"TOTAL PORTFOLIO: ${total_value + usd_balance:,.2f}")

# Calculate projections for $200k BTC
btc_multiplier = 200000 / prices['BTC']
print(f"\n🚀 PROJECTIONS AT $200K BTC ({btc_multiplier:.2f}x):")
print("-" * 50)

projected_value = usd_balance  # Start with USD
projection_details = []

for currency, data in portfolio.items():
    balance = data['balance']
    current_price = data['price']
    current_value = data['value']
    
    # Different multipliers for different assets
    if currency == 'BTC':
        multiplier = btc_multiplier
    elif currency == 'ETH':
        multiplier = btc_multiplier * 1.5  # ETH typically outperforms in bull
    elif currency == 'SOL':
        multiplier = btc_multiplier * 2.5  # SOL has higher beta
    elif currency in ['MATIC', 'AVAX']:
        multiplier = btc_multiplier * 2.0  # L1/L2 gains
    elif currency == 'DOGE':
        multiplier = btc_multiplier * 3.0  # Meme coin madness
    elif currency == 'XRP':
        multiplier = btc_multiplier * 1.8  # XRP moves
    elif currency == 'LINK':
        multiplier = btc_multiplier * 2.2  # Oracle play
    else:
        multiplier = btc_multiplier * 1.0  # Conservative
    
    future_price = current_price * multiplier
    future_value = balance * future_price
    gain = future_value - current_value
    
    projected_value += future_value
    projection_details.append((currency, balance, current_value, future_value, gain))
    
    print(f"\n{currency}:")
    print(f"  Current: ${current_value:,.2f}")
    print(f"  @ ${future_price:,.2f}: ${future_value:,.2f}")
    print(f"  Gain: ${gain:,.2f} ({multiplier:.1f}x)")

# Sort by future value
projection_details.sort(key=lambda x: x[3], reverse=True)

print(f"\n{'='*70}")
print(f"📊 PORTFOLIO SUMMARY AT $200K BTC:")
print("-" * 50)
print(f"Current Portfolio: ${total_value + usd_balance:,.2f}")
print(f"Projected Portfolio: ${projected_value:,.2f}")
print(f"Total Gain: ${projected_value - (total_value + usd_balance):,.2f}")
print(f"Portfolio Multiplier: {projected_value/(total_value + usd_balance):.2f}x")

print(f"\n🏆 TOP GAINERS:")
print("-" * 50)
for i, (currency, balance, current, future, gain) in enumerate(projection_details[:5], 1):
    print(f"{i}. {currency}: ${current:,.2f} → ${future:,.2f} (+${gain:,.2f})")

# Calculate if we hit certain milestones
print(f"\n🎯 MILESTONE PROJECTIONS:")
print("-" * 50)
milestones = [10000, 15000, 20000, 25000, 30000, 50000]
current_total = total_value + usd_balance

for milestone in milestones:
    if projected_value > milestone:
        btc_needed = (milestone / projected_value) * 200000
        print(f"${milestone:,}: BTC @ ${btc_needed:,.0f} ✅")

print(f"\n💡 KEY INSIGHTS:")
print("-" * 50)
print(f"• Every $1,000 BTC rises = ${(projected_value - current_total) / (200000 - prices['BTC']) * 1000:.2f} portfolio gain")
print(f"• At $150K BTC = ${current_total * (150000/prices['BTC']/btc_multiplier * projected_value/current_total):.2f}")
print(f"• Breakeven if BTC drops to: ${prices['BTC'] * 0.8:.0f}")

print(f"\n🚀 TO THE MOON!")
print("=" * 70)