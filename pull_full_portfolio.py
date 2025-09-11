#\!/usr/bin/env python3
"""
Full Portfolio Pull Script - Works with current Coinbase API structure
Created: 2025-09-05
"""

import json
import sys
from datetime import datetime
from coinbase.rest import RESTClient

def get_portfolio():
    try:
        # Try multiple possible config locations
        config_files = [
            '/home/dereadi/scripts/claude/cdp_api_key_new.json',
            '/home/dereadi/scripts/claude/coinbase_config.json',
            '/home/dereadi/scripts/claude/api_config.json'
        ]
        
        config = None
        for config_file in config_files:
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    break
            except:
                continue
        
        if not config:
            print("❌ Could not find API config file")
            return None
            
        # Initialize client - handle different config formats
        if 'api_key' in config:
            client = RESTClient(api_key=config['api_key'], api_secret=config['api_secret'])
        elif 'key' in config:
            client = RESTClient(api_key=config['key'], api_secret=config['secret'])
        else:
            print("❌ Invalid config format")
            return None
        
        print('🔥 FULL PORTFOLIO STATUS')
        print('=' * 70)
        print(f'📅 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        print('=' * 70)
        
        total_value = 0
        positions = {}
        
        # Get accounts with proper error handling
        try:
            accounts_response = client.get_accounts()
            
            # Handle different response structures
            if hasattr(accounts_response, 'accounts'):
                accounts = accounts_response.accounts
            elif hasattr(accounts_response, 'data'):
                accounts = accounts_response.data
            elif isinstance(accounts_response, dict) and 'accounts' in accounts_response:
                accounts = accounts_response['accounts']
            else:
                accounts = accounts_response
                
        except Exception as e:
            print(f"❌ Error getting accounts: {e}")
            return None
        
        # Process each account
        for account in accounts:
            try:
                # Handle different account structures
                if isinstance(account, dict):
                    # Dictionary structure
                    if 'available_balance' in account:
                        balance = float(account['available_balance'].get('value', 0))
                        currency = account['available_balance'].get('currency', '')
                    elif 'balance' in account:
                        balance = float(account['balance'].get('amount', 0))
                        currency = account['balance'].get('currency', '')
                    else:
                        continue
                else:
                    # Object structure
                    if hasattr(account, 'available_balance'):
                        balance = float(account.available_balance.value)
                        currency = account.available_balance.currency
                    elif hasattr(account, 'balance'):
                        balance = float(account.balance.amount)
                        currency = account.balance.currency
                    else:
                        continue
                
                # Skip tiny balances
                if balance < 0.00001:
                    continue
                    
                # Calculate USD value
                if currency in ['USD', 'USDC']:
                    usd_value = balance
                else:
                    try:
                        ticker = client.get_product_ticker(f'{currency}-USD')
                        if isinstance(ticker, dict):
                            price = float(ticker.get('price', 0))
                        else:
                            price = float(ticker.price)
                        usd_value = balance * price
                    except:
                        # Skip if we can't get price
                        continue
                
                # Only track positions worth more than $0.01
                if usd_value >= 0.01:
                    positions[currency] = {
                        'balance': balance,
                        'usd_value': usd_value
                    }
                    total_value += usd_value
                    
            except Exception as e:
                continue
        
        # Sort positions by value
        sorted_positions = sorted(positions.items(), key=lambda x: x[1]['usd_value'], reverse=True)
        
        # Display results
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
        
        # Calculate liquidity
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
        
        # Trading recommendations
        print('\n🎯 SPECIALIST RECOMMENDATIONS:')
        if cash_total < 100:
            print('⚠️  CRITICAL: Low liquidity\! Consider harvesting profits')
        elif cash_total < 500:
            print('🟡 LOW: Limited trading flexibility, be selective')
        elif cash_total < 1000:
            print('🟢 MODERATE: Good liquidity for oscillation trading')
        else:
            print('✅ EXCELLENT: Full trading flexibility available')
            
        # Check for concentrated positions
        print('\n📈 POSITION ANALYSIS:')
        for currency, data in sorted_positions[:5]:  # Top 5 positions
            pct = (data['usd_value'] / total_value * 100) if total_value > 0 else 0
            if pct > 30:
                print(f'⚠️  {currency}: OVERWEIGHT at {pct:.1f}% - Consider rebalancing')
            elif pct > 20:
                print(f'🟡 {currency}: High allocation at {pct:.1f}%')
                
        return {
            'total_value': total_value,
            'positions': positions,
            'cash_available': cash_total,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    portfolio = get_portfolio()
    
    if portfolio:
        print('\n✅ Portfolio pull complete\!')
        print('=' * 70)
        
        # Save to file for other scripts
        with open('/tmp/latest_portfolio.json', 'w') as f:
            json.dump(portfolio, f, indent=2)
            print('📁 Saved to /tmp/latest_portfolio.json')
