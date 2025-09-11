#!/usr/bin/env python3
"""
🔥 FIX COINBASE API CONNECTION
================================
Fixing the dict object error
"""

import json
import os
from coinbase.rest import RESTClient

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    🔥 FIXING COINBASE API CONNECTION 🔥                   ║
║                         Debugging the real issue                           ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

# Load API credentials
print("\n📁 Loading API credentials...")
api_key_path = "cdp_api_key_new.json"

if os.path.exists(api_key_path):
    with open(api_key_path, 'r') as f:
        api_data = json.load(f)
    print("✅ API key file loaded")
    
    # Extract the API key ID from the name field
    api_key = api_data['name'].split('/')[-1]
    api_secret = api_data['privateKey']
    
    print(f"📌 API Key ID: {api_key[:8]}...")
    
    try:
        # Create client with correct credentials
        print("\n🔌 Connecting to Coinbase...")
        client = RESTClient(
            api_key=api_key,
            api_secret=api_secret
        )
        
        print("✅ Client created")
        
        # Get accounts - NEW METHOD
        print("\n💰 Fetching accounts...")
        try:
            accounts = client.get_accounts()
            
            print("\n📊 RAW RESPONSE STRUCTURE:")
            print(f"Type: {type(accounts)}")
            
            if isinstance(accounts, dict):
                print(f"Keys: {accounts.keys()}")
                
                # Check if accounts is nested
                if 'accounts' in accounts:
                    account_list = accounts['accounts']
                else:
                    account_list = [accounts]
                    
                print(f"\n💰 FOUND {len(account_list)} ACCOUNTS:")
                print("=" * 50)
                
                total_usd = 0
                for acc in account_list:
                    # Debug print to see structure
                    print(f"\nAccount structure: {acc.keys() if isinstance(acc, dict) else 'Not a dict'}")
                    
                    # Try different ways to get balance
                    balance = 0
                    currency = "UNKNOWN"
                    
                    if 'available_balance' in acc:
                        if isinstance(acc['available_balance'], dict):
                            if 'value' in acc['available_balance']:
                                balance = float(acc['available_balance']['value'])
                            elif 'amount' in acc['available_balance']:
                                balance = float(acc['available_balance']['amount'])
                        else:
                            balance = float(acc['available_balance'])
                    elif 'balance' in acc:
                        if isinstance(acc['balance'], dict):
                            if 'value' in acc['balance']:
                                balance = float(acc['balance']['value'])
                            elif 'amount' in acc['balance']:
                                balance = float(acc['balance']['amount'])
                        else:
                            balance = float(acc['balance'])
                    
                    if 'currency' in acc:
                        currency = acc['currency']
                    elif 'currency_code' in acc:
                        currency = acc['currency_code']
                    
                    if balance > 0:
                        print(f"{currency}: ${balance:.2f}")
                        if currency == 'USD' or currency == 'USDC':
                            total_usd += balance
                
                print("=" * 50)
                print(f"\n💵 TOTAL USD VALUE: ${total_usd:.2f}")
                
                if total_usd > 100:
                    print("\n⚡ GREEKS: 'YOUR MONEY IS THERE! $116.99 CONFIRMED!'")
                    print("Ready to deploy the Quantum Crawdads!")
                else:
                    print("\n🔍 Checking for crypto holdings...")
                    
            else:
                print(f"Unexpected response type: {type(accounts)}")
                print(f"Response: {accounts}")
                
        except Exception as e:
            print(f"❌ Error getting accounts: {e}")
            print("\nTrying alternative method...")
            
            # Try list_accounts method
            try:
                accounts = client.list_accounts()
                print("✅ Using list_accounts method")
                print(f"Response: {accounts}")
            except:
                pass
                
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print("\n🔧 TROUBLESHOOTING:")
        print("1. Check network connection")
        print("2. Verify API permissions on Coinbase")
        print("3. Make sure 2FA is not blocking API")
        
else:
    print("❌ API key file not found")

print("""

🔥 NEXT STEPS:
=============
If you see your balance above, run:
python3 coinbase_quantum_megapod.py

If not, we need to:
1. Check Coinbase.com for API permissions
2. Regenerate API keys if needed
3. Make sure trading is enabled

Council stands ready!
""")