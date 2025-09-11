#!/usr/bin/env python3
"""
🔥 CHECK ALL BALANCES - VM AND MAIN ACCOUNT
"""

import json
import os
from datetime import datetime
from coinbase.rest import RESTClient

print("🔥 CHECKING ALL BALANCES")
print("=" * 60)
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

def check_account(name, config_path):
    """Check balances for a specific account"""
    print(f"📊 {name}:")
    print("-" * 40)
    
    if not os.path.exists(config_path):
        print(f"Config not found: {config_path}")
        return
    
    try:
        with open(config_path) as f:
            config = json.load(f)
        
        client = RESTClient(
            api_key=config['api_key'],
            api_secret=config['api_secret']
        )
        
        # Get accounts
        accounts = client.get_accounts()
        
        total_value = 0
        found_assets = False
        balances = {}
        
        # Process accounts
        for account in accounts.accounts:
            currency = account.currency
            
            # Get balance
            available = 0
            hold = 0
            
            if hasattr(account, 'available_balance') and hasattr(account.available_balance, 'value'):
                available = float(account.available_balance.value)
            
            if hasattr(account, 'hold') and hasattr(account.hold, 'value'):
                hold = float(account.hold.value)
            
            total = available + hold
            
            if total > 0.01:
                found_assets = True
                balances[currency] = {
                    'available': available,
                    'hold': hold,
                    'total': total
                }
        
        # Display key assets
        key_assets = ['USD', 'USDC', 'BTC', 'ETH', 'SOL', 'XRP', 'DOGE', 'AVAX', 'MATIC']
        
        for asset in key_assets:
            if asset in balances:
                bal = balances[asset]
                if asset in ['USD', 'USDC']:
                    print(f"{asset:6} ${bal['available']:.2f} available, ${bal['hold']:.2f} hold")
                    total_value += bal['total']
                else:
                    print(f"{asset:6} {bal['available']:.4f} available, {bal['hold']:.4f} hold")
                    
                    # Get USD value
                    try:
                        ticker = client.get_product(f'{asset}-USD')
                        price = float(ticker.price)
                        value = bal['total'] * price
                        print(f"       → ${value:,.2f} @ ${price:.2f}")
                        total_value += value
                    except:
                        pass
        
        if found_assets:
            print(f"\n💰 Total estimated value: ${total_value:,.2f}")
        else:
            print("No balances found")
            
    except Exception as e:
        print(f"Error: {str(e)[:100]}")
    
    print()
    return total_value

# Check VM account
vm_value = check_account("VM ACCOUNT (Advanced Trade)", 
                         os.path.expanduser("~/.coinbase_config.json"))

# Check main account  
main_value = check_account("MAIN ACCOUNT (New API Key from sasass)",
                          os.path.expanduser("~/.coinbase_main_config.json"))

print("=" * 60)
print("📊 SUMMARY:")
print("-" * 40)

if main_value > 30000:
    print("🎉 SUCCESS! Main account connected with full portfolio!")
    print("✅ Ready to execute DOGE reallocation!")
    print("✅ VM Tribe can now trade your portfolio!")
elif main_value > 1000:
    print("⚠️ Main account has some funds but not full portfolio")
    print("Check if assets need to be transferred to Advanced Trade")
elif vm_value > 0 and main_value == 0:
    print("❌ Main account shows no balance")
    print("📱 Need to transfer from Simple Trade to Advanced Trade:")
    print("1. Go to Coinbase.com")
    print("2. Click 'Advanced Trade'")
    print("3. Transfer assets from Simple to Advanced")
    print("4. Then VM Tribe can execute!")
else:
    print("⚠️ Both accounts show minimal balances")
    print("Check if portfolio is on different platform")

print()
print("🔥 Current DOGE price check...")
try:
    # Use whichever client worked
    if main_value > 0 or vm_value > 0:
        config_path = "~/.coinbase_main_config.json" if main_value > 0 else "~/.coinbase_config.json"
        with open(os.path.expanduser(config_path)) as f:
            config = json.load(f)
        client = RESTClient(api_key=config['api_key'], api_secret=config['api_secret'])
        
        doge_ticker = client.get_product('DOGE-USD')
        doge_price = float(doge_ticker.price)
        print(f"DOGE: ${doge_price:.4f} - {'GOOD ENTRY!' if doge_price < 0.24 else 'Still decent'}")
except:
    pass

print()
print("=" * 60)
print("🔥 Balance check complete!")