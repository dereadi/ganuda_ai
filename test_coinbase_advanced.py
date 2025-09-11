#!/usr/bin/env python3
"""
Test Coinbase Advanced Trade API with proper CDP authentication
"""

import json
import os
from coinbase.rest import RESTClient

print("🔥 Testing Coinbase Advanced Trade API")
print("=" * 50)

# Load config
config_file = os.path.expanduser("~/.coinbase_config.json")
with open(config_file) as f:
    config = json.load(f)

api_key = config.get("api_key")
api_secret = config.get("api_secret")

# Extract just the key name (last part)
key_name = api_key.split('/')[-1] if '/' in api_key else api_key

print(f"API Key Name: {key_name}")
print(f"Key type: CDP (Advanced Trade)")
print()

try:
    # Initialize the client with CDP credentials
    client = RESTClient(
        api_key=key_name,  # Just the UUID part
        api_secret=api_secret,
        verbose=True
    )
    
    print("📡 Attempting to get accounts...")
    
    # Try to get accounts
    accounts = client.get_accounts()
    
    print("✅ SUCCESS! Connected to Coinbase!")
    print(f"\n💰 Your Accounts:")
    
    if accounts and 'accounts' in accounts:
        for account in accounts['accounts']:
            currency = account.get('currency', 'N/A')
            balance = account.get('available_balance', {}).get('value', '0')
            print(f"  • {currency}: {balance}")
    else:
        print("  No accounts found or unexpected response format")
        print(f"  Response: {accounts}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nTroubleshooting:")
    print("1. Ensure your account is fully verified (Level 2)")
    print("2. The API key must have the correct permissions")
    print("3. Try creating a new API key specifically for 'Advanced Trade'")
    print("4. Make sure you're using the Coinbase Advanced Trade product, not Coinbase Pro")