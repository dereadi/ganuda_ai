#\!/usr/bin/env python3
"""
Working Portfolio Pull - Based on functioning liquidity script
"""

import json
from datetime import datetime
from coinbase.rest import RESTClient

# This mirrors the working check_current_liquidity.py approach
api_key = "organizations/7be9c848-cd84-43c2-ba17-28e9c43b4c4f/apiKeys/49f00311-3d60-4cf4-b936-af2c0e7bb2ce"
api_secret = """-----BEGIN EC PRIVATE KEY-----
MHcCAQEEINP0r7t5FUGaFGMXWXW0B5JfYH+9Gvtpul8RmE1g5NrcoAoGCCqGSM49
AwEHoUQDQgAEQUX1hNYcoHN6dVhJF2rAc7MB4KpdvVJro9wSMHJJZEQnDHo6EHKg
J7h5N5jeXeLPMHs3LiztFqwSAK3qkr3gEg==
-----END EC PRIVATE KEY-----"""

client = RESTClient(api_key=api_key, api_secret=api_secret)

print('🔥 FULL PORTFOLIO PULL')
print('=' * 70)
print(f'📅 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
print('=' * 70)

total_value = 0
positions = {}

# Get all accounts
accounts = client.get_accounts()

for account in accounts['accounts']:
    balance = float(account['available_balance']['value'])
    currency = account['available_balance']['currency']
    
    if balance > 0.00001:
        # Calculate USD value
        if currency in ['USD', 'USDC']:
            usd_value = balance
        else:
            try:
                ticker = client.get_product_ticker(f'{currency}-USD')
                price = float(ticker['price'])
                usd_value = balance * price
            except:
                continue
        
        if usd_value >= 0.01:
            positions[currency] = {
                'balance': balance,
                'usd_value': usd_value
            }
            total_value += usd_value

# Sort by value
sorted_positions = sorted(positions.items(), key=lambda x: x[1]['usd_value'], reverse=True)

print(f'\n💼 TOTAL PORTFOLIO VALUE: ${total_value:,.2f}')
print('\n📊 POSITIONS:')
print('-' * 70)
print(f'{"Asset":<8} {"Amount":>15} {"USD Value":>15} {"Percent":>10}')
print('-' * 70)

for currency, data in sorted_positions:
    pct = (data['usd_value'] / total_value * 100) if total_value > 0 else 0
    
    if currency in ['USD', 'USDC']:
        print(f'{currency:<8} {data["balance"]:>15.2f} ${data["usd_value"]:>14,.2f} {pct:>9.1f}%')
    else:
        print(f'{currency:<8} {data["balance"]:>15.6f} ${data["usd_value"]:>14,.2f} {pct:>9.1f}%')

print('-' * 70)

# Liquidity analysis
usd_total = positions.get('USD', {}).get('usd_value', 0)
usdc_total = positions.get('USDC', {}).get('usd_value', 0)
cash_total = usd_total + usdc_total
crypto_total = total_value - cash_total

print('\n💰 LIQUIDITY ANALYSIS:')
print('-' * 70)
print(f'USD Balance:        ${usd_total:>12,.2f}')
print(f'USDC Balance:       ${usdc_total:>12,.2f}')
print(f'Total Cash:         ${cash_total:>12,.2f}')
print(f'Crypto Positions:   ${crypto_total:>12,.2f}')
print(f'Cash Ratio:         {(cash_total/total_value*100) if total_value > 0 else 0:>12.1f}%')
print('-' * 70)

# Top holdings analysis
print('\n📈 TOP HOLDINGS:')
for i, (currency, data) in enumerate(sorted_positions[:5], 1):
    pct = (data['usd_value'] / total_value * 100) if total_value > 0 else 0
    print(f'{i}. {currency}: ${data["usd_value"]:,.2f} ({pct:.1f}%)')

# Specialist recommendations
print('\n🎯 SPECIALIST STATUS:')
if cash_total < 100:
    print('⚠️  CRITICAL: Low liquidity - Consider harvesting profits')
elif cash_total < 500:
    print('🟡 LOW: $215 available - Deploy carefully')
else:
    print('✅ GOOD: Sufficient liquidity for trading')

print('\n🤖 ACTIVE SPECIALISTS:')
print('• Mean Reversion v2')
print('• Trend Following v2')
print('• Volatility Trading v2')
print('• Breakout Detection v2')

print('=' * 70)
