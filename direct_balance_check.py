#!/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3
"""
Direct balance check using raw API
"""

import json
import requests
from pathlib import Path

# Load config
config_path = Path.home() / ".coinbase_config.json"
with open(config_path, 'r') as f:
    config = json.load(f)

# Try direct REST call
from coinbase.rest import RESTClient

try:
    client = RESTClient(
        api_key=config['api_key'],
        api_secret=config['api_secret']
    )
    
    print("Attempting to get accounts...")
    response = client.get_accounts()
    
    print(f"Response type: {type(response)}")
    print(f"Response: {response}")
    
    # Try different access methods
    if hasattr(response, 'accounts'):
        print("Has accounts attribute")
        accounts = response.accounts
        print(f"Accounts type: {type(accounts)}")
        
        # Try to iterate
        for i, account in enumerate(accounts):
            if i < 5:  # First 5 accounts
                print(f"\nAccount {i}:")
                print(f"  Type: {type(account)}")
                
                # Try different access patterns
                if hasattr(account, 'currency'):
                    print(f"  Currency: {account.currency}")
                    if hasattr(account, 'available_balance'):
                        print(f"  Balance obj: {account.available_balance}")
                        if hasattr(account.available_balance, 'value'):
                            print(f"  Value: {account.available_balance.value}")
                
                # Try dict access
                if isinstance(account, dict):
                    print(f"  Dict keys: {account.keys()}")
                    print(f"  Currency (dict): {account.get('currency')}")
                    print(f"  Balance (dict): {account.get('available_balance')}")
    
except Exception as e:
    print(f"Error: {e}")
    print(f"Error type: {type(e)}")
    
print("\n" + "="*60)
print("Trying alternative approach...")

# Try getting specific products
try:
    btc = client.get_product('BTC-USD')
    print(f"BTC product: {btc}")
    print(f"BTC type: {type(btc)}")
    
    if isinstance(btc, dict):
        print(f"BTC price: ${btc.get('price', 'N/A')}")
    elif hasattr(btc, 'price'):
        print(f"BTC price: ${btc.price}")
        
except Exception as e:
    print(f"Product error: {e}")