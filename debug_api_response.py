#!/usr/bin/env python3
"""
Debug API response to understand account structure
"""

from coinbase.rest import RESTClient
import json
import os

# Test with main account
config_path = os.path.expanduser('~/.coinbase_main_config.json')
with open(config_path) as f:
    config = json.load(f)

client = RESTClient(api_key=config['api_key'], api_secret=config['api_secret'])

print('🔍 DEBUGGING API RESPONSE')
print('=' * 50)

# Get raw response
accounts = client.get_accounts()
print(f'Account count: {len(accounts.accounts)}')
print()

# Show ALL accounts to see what we have
print('ALL ACCOUNTS:')
print('-' * 40)
for i, account in enumerate(accounts.accounts):
    print(f'{i+1}. {account.currency}:')
    
    # Check for available balance
    if hasattr(account, 'available_balance') and hasattr(account.available_balance, 'value'):
        avail = account.available_balance.value
        print(f'   Available: {avail}')
    
    # Check for hold
    if hasattr(account, 'hold') and hasattr(account.hold, 'value'):
        hold = account.hold.value
        print(f'   Hold: {hold}')
    
    # Check for any balance attribute
    if hasattr(account, 'balance'):
        print(f'   Balance attr: {account.balance}')

print()
print('Testing API functionality...')
print('-' * 40)

# Test price fetching
try:
    btc = client.get_product('BTC-USD')
    eth = client.get_product('ETH-USD')
    doge = client.get_product('DOGE-USD')
    
    print(f'BTC: ${btc.price}')
    print(f'ETH: ${eth.price}')
    print(f'DOGE: ${doge.price}')
    print()
    print('✅ API is working for price data!')
    
except Exception as e:
    print(f'❌ API error: {e}')

print()
print('DIAGNOSIS:')
print('-' * 40)
print('If you see 14 accounts all with 0 balance, it means:')
print('1. API key is valid and working')
print('2. Advanced Trade accounts exist but are empty')
print('3. Your assets are in Simple Trade (regular Coinbase)')
print()
print('TO FIX:')
print('1. Log into Coinbase.com')
print('2. Go to Advanced Trade section')
print('3. You should see "Transfer assets to Advanced Trade"')
print('4. Transfer SOL, XRP, DOGE, etc.')
print('5. Transfers are instant and free!')