#!/usr/bin/env python3
"""
🔥 VM TRIBE EXECUTES WITH NEW CDP API KEY
Testing the new API from sasass
"""

import json
import time
import os
import sys
from datetime import datetime
from coinbase.rest import RESTClient

print("🔥 VM TRIBE TESTING NEW API CONNECTION")
print("=" * 60)
print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
print("API Source: sasass Downloads/cdp_api_key_CVM.json")
print()

# Load the new main account config
config_path = os.path.expanduser("~/.coinbase_main_config.json")
with open(config_path) as f:
    config = json.load(f)

print(f"✅ Loaded new API key ending in: ...{config['api_key'][-8:]}")
print()

try:
    # Initialize client with new credentials
    client = RESTClient(
        api_key=config['api_key'],
        api_secret=config['api_secret']
    )
    
    print("📊 CHECKING ACCOUNTS...")
    print("-" * 40)
    
    # Get all accounts
    accounts = client.get_accounts()
    
    found_accounts = 0
    total_value = 0
    
    # Check account structure
    print(f"Response type: {type(accounts)}")
    
    if hasattr(accounts, 'accounts'):
        print(f"Number of accounts: {len(accounts.accounts)}")
        print()
        
        for account in accounts.accounts:
            currency = account.currency
            
            # Get balances
            available = 0
            hold = 0
            
            if hasattr(account, 'available_balance') and hasattr(account.available_balance, 'value'):
                available = float(account.available_balance.value)
            
            if hasattr(account, 'hold') and hasattr(account.hold, 'value'):
                hold = float(account.hold.value)
            
            total = available + hold
            
            # Show any non-zero balance
            if total > 0.00001:
                found_accounts += 1
                
                if currency in ['USD', 'USDC']:
                    print(f"{currency}: ${total:.2f} (available: ${available:.2f})")
                    total_value += total
                else:
                    print(f"{currency}: {total:.8f} (available: {available:.8f})")
                    
                    # Try to get USD value
                    if currency in ['BTC', 'ETH', 'SOL', 'XRP', 'DOGE']:
                        try:
                            ticker = client.get_product(f'{currency}-USD')
                            price = float(ticker.price)
                            value = total * price
                            print(f"  → Value: ${value:.2f} @ ${price:.2f}")
                            total_value += value
                        except:
                            pass
    
    print()
    print("-" * 40)
    
    if found_accounts > 0:
        print(f"✅ Found {found_accounts} accounts with balances")
        print(f"Estimated total value: ${total_value:.2f}")
        
        if total_value > 30000:
            print()
            print("🎉 SUCCESS! MAIN PORTFOLIO CONNECTED!")
            print("VM Tribe can now execute DOGE reallocation!")
            
            # Try to execute if we have the assets
            print()
            print("🔥 CHECKING FOR DOGE REALLOCATION ASSETS...")
            
            # Re-check for specific assets
            sol_balance = 0
            xrp_balance = 0
            doge_balance = 0
            
            for account in accounts.accounts:
                if account.currency == 'SOL' and hasattr(account.available_balance, 'value'):
                    sol_balance = float(account.available_balance.value)
                elif account.currency == 'XRP' and hasattr(account.available_balance, 'value'):
                    xrp_balance = float(account.available_balance.value)
                elif account.currency == 'DOGE' and hasattr(account.available_balance, 'value'):
                    doge_balance = float(account.available_balance.value)
            
            print(f"SOL: {sol_balance:.4f}")
            print(f"XRP: {xrp_balance:.2f}")
            print(f"DOGE: {doge_balance:.2f}")
            
            if sol_balance >= 3.75 and xrp_balance >= 68:
                print()
                print("✅ READY TO EXECUTE DOGE REALLOCATION!")
                print("Run: python3 tribe_final_doge_execution.py")
        else:
            print()
            print(f"⚠️ Connected but portfolio value (${total_value:.2f}) doesn't match expected $32,947")
            print()
            print("Possible issues:")
            print("1. Assets might be in regular Coinbase (not Advanced Trade)")
            print("2. Need to transfer from Coinbase to Advanced Trade")
            print("3. Different account than expected")
    else:
        print("❌ No accounts with balances found")
        print()
        print("This usually means:")
        print("1. Assets are in regular Coinbase (not Advanced Trade)")
        print("2. You need to transfer assets to Advanced Trade")
        print()
        print("To fix:")
        print("1. Log into Coinbase.com")
        print("2. Go to Advanced Trade")
        print("3. Transfer assets from Simple Trade to Advanced Trade")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
print("🔥 VM Tribe connection test complete!")