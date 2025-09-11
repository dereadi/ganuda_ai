#!/usr/bin/env python3
"""
💎 COMPLETE PORTFOLIO ANALYSIS
==============================
Full view of all assets and values
"""

from coinbase.rest import RESTClient
import json

config = json.load(open('/home/dereadi/.coinbase_config.json'))
client = RESTClient(api_key=config['api_key'].split('/')[-1], api_secret=config['api_secret'])

print('💎 COMPLETE PORTFOLIO ANALYSIS')
print('=' * 60)

accounts = client.get_accounts()['accounts']
portfolio = []
total_value = 0

# Get all positions
for acc in accounts:
    balance = float(acc['available_balance']['value'])
    currency = acc['currency']
    
    if balance > 0.001:
        if currency == 'USD':
            portfolio.append({'currency': currency, 'balance': balance, 'price': 1, 'value': balance})
            total_value += balance
        elif currency == 'USDC':
            portfolio.append({'currency': currency, 'balance': balance, 'price': 1, 'value': balance})
            total_value += balance
        else:
            try:
                # Get current price
                product = client.get_product(f'{currency}-USD')
                price = float(product['price'])
                value = balance * price
                portfolio.append({'currency': currency, 'balance': balance, 'price': price, 'value': value})
                total_value += value
            except:
                # For assets without direct USD pair
                portfolio.append({'currency': currency, 'balance': balance, 'price': 0, 'value': 0})

# Sort by value
portfolio.sort(key=lambda x: x['value'], reverse=True)

print('📊 ALL POSITIONS:')
print('-' * 60)
print(f'{"Asset":<8} {"Balance":<15} {"Price":<12} {"Value":<12}')
print('-' * 60)

for pos in portfolio:
    if pos['price'] > 100:
        price_str = f'${pos["price"]:,.0f}'
    elif pos['price'] > 1:
        price_str = f'${pos["price"]:.2f}'
    else:
        price_str = f'${pos["price"]:.4f}'
    
    print(f'{pos["currency"]:<8} {pos["balance"]:<15.6f} {price_str:<12} ${pos["value"]:,.2f}')

print('-' * 60)
print(f'{"TOTAL":<8} {"":<15} {"":<12} ${total_value:,.2f}')
print('=' * 60)

# Calculate percentages
print('\n📈 PORTFOLIO ALLOCATION:')
print('-' * 60)
for pos in portfolio:
    if pos['value'] > 10:
        pct = (pos['value'] / total_value) * 100
        bar = '█' * int(pct/2)
        print(f'{pos["currency"]:<8} {pct:5.1f}% {bar}')

print('\n🎯 KEY METRICS:')
print('-' * 60)
print(f'Total Portfolio Value: ${total_value:,.2f}')
print(f'Number of Positions: {len(portfolio)}')
print(f'Largest Position: {portfolio[0]["currency"]} (${portfolio[0]["value"]:,.2f})')

# Calculate gains needed for targets
targets = [10000, 12000, 15000, 20000]
print('\n🚀 DISTANCE TO TARGETS:')
print('-' * 60)
for target in targets:
    needed = target - total_value
    pct_gain = (needed / total_value) * 100
    print(f'${target:,}: Need +${needed:,.2f} (+{pct_gain:.1f}%)')

print('\n💰 LIQUIDITY STATUS:')
usd_positions = [p for p in portfolio if p['currency'] in ['USD', 'USDC']]
liquid = sum(p['value'] for p in usd_positions)
print(f'Available USD: ${liquid:.2f}')
print(f'Deployed in Crypto: ${total_value - liquid:,.2f} ({((total_value-liquid)/total_value*100):.1f}%)')

print('\n⚡ PORTFOLIO STRENGTH:')
print('-' * 60)
if total_value > 10000:
    print('🔥 CRUSHING IT! Over $10k!')
elif total_value > 8000:
    print('💪 STRONG! Approaching $10k!')
elif total_value > 5000:
    print('📈 BUILDING! Good momentum!')
else:
    print('🚀 GROWING! Keep compounding!')

print('\n🎵 HARDER BETTER FASTER STRONGER:')
print(f'  From $6 to ${total_value:,.2f} in one evening!')
print(f'  That\'s a {(total_value/6 - 1)*100:.0f}x gain!')
print(f'  Weekend target $15k is {((15000-total_value)/total_value*100):.1f}% away!')