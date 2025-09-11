#!/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3
"""
Debug Coinbase API structure
"""

import json
from pathlib import Path
from coinbase.rest import RESTClient

def debug_api():
    """Debug the API response structure"""
    
    print("🔥 DEBUGGING COINBASE API STRUCTURE")
    print("=" * 60)
    
    try:
        # Load config
        config_path = Path.home() / ".coinbase_config.json"
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        client = RESTClient(
            api_key=config['api_key'],
            api_secret=config['api_secret']
        )
        
        # Get accounts
        print("Getting accounts...")
        accounts = client.get_accounts()
        
        # Debug first account
        if accounts.accounts and len(accounts.accounts) > 0:
            first_account = accounts.accounts[0]
            print(f"\nFirst account type: {type(first_account)}")
            
            if isinstance(first_account, dict):
                print("Account is a dictionary")
                print(f"Keys: {first_account.keys()}")
                print(f"\nFull structure: {json.dumps(first_account, indent=2)}")
            else:
                print("Account is an object")
                print(f"Attributes: {dir(first_account)}")
                print(f"Currency: {first_account.currency}")
                print(f"Available balance type: {type(first_account.available_balance)}")
                if hasattr(first_account, 'available_balance'):
                    ab = first_account.available_balance
                    if isinstance(ab, dict):
                        print(f"Available balance dict: {ab}")
                    else:
                        print(f"Available balance attributes: {dir(ab)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_api()