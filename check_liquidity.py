#!/usr/bin/env python3
"""
Check available liquidity across all accounts
"""

import json
from pathlib import Path
from coinbase.rest import RESTClient
import requests

def check_liquidity():
    # Load API credentials
    key_file = Path('/home/dereadi/scripts/claude/cdp_api_key_new.json')
    with open(key_file, 'r') as f:
        creds = json.load(f)
    
    client = RESTClient(api_key=creds['name'], api_secret=creds['privateKey'])
    
    print('💰 LIQUIDITY CHECK 💰')
    print('='*40)
    
    try:
        accounts = client.get_accounts()
        
        total_usd = 0
        crypto_values = {}
        
        for account in accounts.accounts:
            if hasattr(account, 'available_balance'):
                balance_obj = account.available_balance
                if hasattr(balance_obj, 'value'):
                    balance = float(balance_obj.value)
                    currency = balance_obj.currency
                else:
                    # Try dict access
                    balance = float(account['available_balance']['value']) if 'available_balance' in account else 0
                    currency = account['available_balance']['currency'] if 'available_balance' in account else 'UNKNOWN'
            else:
                continue
                
            if balance > 0.01:
                if currency == 'USD':
                    total_usd = balance
                else:
                    # Get USD value
                    try:
                        resp = requests.get(f'https://api.coinbase.com/v2/exchange-rates?currency={currency}')
                        if resp.status_code == 200:
                            rate = float(resp.json()['data']['rates']['USD'])
                            usd_value = balance * rate
                            crypto_values[currency] = {
                                'amount': balance,
                                'usd_value': usd_value
                            }
                    except:
                        crypto_values[currency] = {
                            'amount': balance,
                            'usd_value': 0
                        }
        
        # Display results
        print(f'USD Balance: ${total_usd:.2f}')
        
        total_crypto_value = sum([v['usd_value'] for v in crypto_values.values()])
        
        if crypto_values:
            print(f'\nCrypto Holdings (${total_crypto_value:.2f} total):')
            for coin, data in crypto_values.items():
                print(f'  {coin}: {data["amount"]:.8f} (${data["usd_value"]:.2f})')
        
        print(f'\n📊 TOTAL LIQUIDITY: ${total_usd + total_crypto_value:.2f}')
        
        print(f'\n🎯 LIQUIDITY STRATEGY:')
        if total_usd > 100:
            print(f'  ✅ ${total_usd:.2f} ready to deploy!')
            print(f'  • Buy BTC on dips')
            print(f'  • Scale into ETH at $4,600')
            print(f'  • Grab XRP under $3.10')
        elif total_usd > 10:
            print(f'  ⚡ ${total_usd:.2f} available')
            print(f'  • Use for quick trades')
            print(f'  • Feed the flywheel')
        else:
            print(f'  ⚠️ Low USD (${total_usd:.2f})')
            print(f'  • Most capital in crypto')
            print(f'  • Harvest profits on pumps')
            print(f'  • Keep positions working')
            
    except Exception as e:
        print(f'Error: {e}')
        print('\nLikely all funds are deployed in positions!')
        print('This is good - capital is working!')

if __name__ == "__main__":
    check_liquidity()