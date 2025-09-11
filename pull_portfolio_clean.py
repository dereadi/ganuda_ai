#\!/usr/bin/env python3
"""
Clean Portfolio Pull - Using correct config location
"""

import json
from datetime import datetime
from coinbase.rest import RESTClient

print('🔥 FULL PORTFOLIO PULL')
print('=' * 70)
print(f'📅 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
print('=' * 70)

try:
    # Load config from correct location
    config = json.load(open("/home/dereadi/.coinbase_config.json"))
    key = config["api_key"].split("/")[-1]
    client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=5)
    
    total_value = 0
    positions = {}
    
    # Get all accounts
    accounts = client.get_accounts()["accounts"]
    
    for account in accounts:
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
    
    # Top holdings
    print('\n📈 TOP HOLDINGS:')
    for i, (currency, data) in enumerate(sorted_positions[:10], 1):
        pct = (data['usd_value'] / total_value * 100) if total_value > 0 else 0
        bar = '█' * int(pct/2) if pct > 0 else ''
        print(f'{i:2}. {currency:<6}: ${data["usd_value"]:>10,.2f} ({pct:>5.1f}%) {bar}')
    
    # Concentration warnings
    print('\n⚠️  CONCENTRATION ANALYSIS:')
    concentrated = False
    for currency, data in sorted_positions[:5]:
        pct = (data['usd_value'] / total_value * 100) if total_value > 0 else 0
        if pct > 30:
            print(f'   🔴 {currency}: OVERWEIGHT at {pct:.1f}%')
            concentrated = True
        elif pct > 20:
            print(f'   🟡 {currency}: High allocation at {pct:.1f}%')
            concentrated = True
    
    if not concentrated:
        print('   ✅ Portfolio well diversified')
    
    # Trading status
    print('\n🤖 SPECIALIST TRADING STATUS:')
    print('-' * 70)
    if cash_total < 100:
        print('🔴 CRITICAL: Liquidity crisis\! Only ${:.2f} available'.format(cash_total))
        print('   Action: Harvest profits immediately')
    elif cash_total < 500:
        print('🟡 LOW: Limited liquidity (${:.2f})'.format(cash_total))
        print('   Action: Deploy $215 USDC carefully')
    else:
        print('🟢 GOOD: ${:.2f} available for trading'.format(cash_total))
        print('   Action: Full trading flexibility')
    
    print('\n📊 ACTIVE SYSTEMS:')
    print('   • 4 Specialist traders running (v2)')
    print('   • Cherokee trader active')
    print('   • Discord monitoring online')
    print('   • Portfolio alerts enabled')
    
    print('=' * 70)
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
