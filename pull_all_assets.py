#\!/usr/bin/env python3
"""
Pull ALL assets including crypto positions
"""

import json
from datetime import datetime
from coinbase.rest import RESTClient

print('🔥 COMPLETE PORTFOLIO PULL - ALL ASSETS')
print('=' * 70)
print(f'📅 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
print('=' * 70)

try:
    # Load config
    config = json.load(open("/home/dereadi/.coinbase_config.json"))
    key = config["api_key"].split("/")[-1]
    client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=10)
    
    total_value = 0
    positions = {}
    
    # Get ALL accounts - not just available_balance
    accounts_response = client.get_accounts()
    
    # Try to get both regular accounts and trading accounts
    if isinstance(accounts_response, dict):
        accounts = accounts_response.get('accounts', [])
    else:
        accounts = accounts_response
    
    print(f"Found {len(accounts)} accounts\n")
    
    for account in accounts:
        # Try multiple balance fields
        balance = 0
        currency = ""
        
        # Check different balance structures
        if 'balance' in account:
            balance = float(account['balance'].get('amount', 0))
            currency = account['balance'].get('currency', '')
        elif 'available_balance' in account:
            balance = float(account['available_balance'].get('value', 0))
            currency = account['available_balance'].get('currency', '')
        
        # Also check for hold balance
        if 'hold_balance' in account:
            hold = float(account['hold_balance'].get('value', 0))
            balance += hold
        
        if balance > 0.00001 and currency:
            # Get USD value
            if currency in ['USD', 'USDC']:
                usd_value = balance
            else:
                try:
                    # Try to get current price
                    product = f'{currency}-USD'
                    ticker = client.get_product_ticker(product)
                    price = float(ticker.get('price', 0))
                    usd_value = balance * price
                    
                    # Debug print for crypto
                    if usd_value > 100:
                        print(f"Found {currency}: {balance:.6f} @ ${price:.2f} = ${usd_value:.2f}")
                        
                except Exception as e:
                    # Try USDC pair if USD fails
                    try:
                        product = f'{currency}-USDC'
                        ticker = client.get_product_ticker(product)
                        price = float(ticker.get('price', 0))
                        usd_value = balance * price
                    except:
                        continue
            
            if usd_value >= 0.01:
                if currency in positions:
                    positions[currency]['balance'] += balance
                    positions[currency]['usd_value'] += usd_value
                else:
                    positions[currency] = {
                        'balance': balance,
                        'usd_value': usd_value
                    }
                total_value += usd_value
    
    # Also try to get portfolio explicitly
    try:
        portfolio = client.get_portfolio()
        print(f"Portfolio call returned: {type(portfolio)}")
    except Exception as e:
        print(f"Portfolio call failed: {e}")
    
    # Sort positions
    sorted_positions = sorted(positions.items(), key=lambda x: x[1]['usd_value'], reverse=True)
    
    print('\n' + '=' * 70)
    print(f'💼 TOTAL VALUE: ${total_value:,.2f}')
    
    # Show expected vs found
    expected = 30609.76
    difference = expected - total_value
    if abs(difference) > 100:
        print(f'⚠️  MISSING: ${difference:,.2f} (Expected ${expected:,.2f})')
        print('   Some positions may not be visible via API')
    
    print('\n📊 ALL POSITIONS FOUND:')
    print('-' * 70)
    
    for currency, data in sorted_positions:
        pct = (data['usd_value'] / total_value * 100) if total_value > 0 else 0
        print(f'{currency:<6}: ${data["usd_value"]:>10,.2f} ({pct:>5.1f}%) - {data["balance"]:.6f} {currency}')
    
    print('-' * 70)
    
    # Check if we're missing crypto
    cash_total = positions.get('USD', {}).get('usd_value', 0) + positions.get('USDC', {}).get('usd_value', 0)
    if cash_total > 400 and total_value < 500:
        print('\n❌ ISSUE: Only seeing cash accounts\!')
        print('   Crypto positions not visible through this API endpoint')
        print('   You have ~$30,193 in crypto not showing here')
    
    print('=' * 70)
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
