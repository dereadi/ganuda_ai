#!/usr/bin/env python3
"""
Check EXACT account balances to verify $212.22 status
"""

import json
from coinbase.rest import RESTClient

# Load credentials
with open('cdp_api_key_new.json', 'r') as f:
    creds = json.load(f)

client = RESTClient(api_key=creds['name'], api_secret=creds['privateKey'])

print("=" * 60)
print("💰 CHECKING YOUR EXACT BALANCES")
print("=" * 60)

try:
    accounts = client.get_accounts()
    
    total_usd = 0
    crypto_positions = []
    
    # Check each account - handle dict structure
    account_list = accounts.accounts if hasattr(accounts, 'accounts') else accounts
    
    for account in account_list:
        # Handle dict structure from API
        if isinstance(account, dict):
            balance = account.get('available_balance', {})
            currency = balance.get('currency', 'UNKNOWN')
            value = float(balance.get('value', 0))
        else:
            if hasattr(account, 'available_balance'):
                balance = account.available_balance
                if isinstance(balance, dict):
                    currency = balance.get('currency', 'UNKNOWN')
                    value = float(balance.get('value', 0))
                else:
                    currency = getattr(balance, 'currency', 'UNKNOWN')
                    value = float(getattr(balance, 'value', 0))
            else:
                continue
            
            if value > 0.001:  # Only show non-dust balances
                print(f"\n{currency}:")
                print(f"  Amount: {value}")
                
                # Track USD/USDC
                if currency in ['USD', 'USDC']:
                    total_usd += value
                    print(f"  💵 Cash balance: ${value:.2f}")
                else:
                    crypto_positions.append(f"{currency}: {value}")
                    print(f"  📈 Crypto position")
    
    print("\n" + "=" * 60)
    print("📊 SUMMARY:")
    print(f"  Total USD/USDC: ${total_usd:.2f}")
    
    if abs(total_usd - 212.22) < 1:
        print("  ✅ Your $212.22 is STILL THERE - orders may not have filled!")
    elif total_usd < 50:
        print("  🚀 Capital deployed into positions!")
        print("  Crypto holdings:")
        for pos in crypto_positions:
            print(f"    • {pos}")
    else:
        print(f"  🤔 Balance different than expected")
    
    print("\n🔥 36 trades executed so far!")
    print("🎯 Target: $111,111")
    
except Exception as e:
    print(f"Error checking balance: {e}")
    print("\nTrying alternative method...")
    
    # Try simpler approach
    try:
        import requests
        
        # Use public API to check current prices
        response = requests.get('https://api.coinbase.com/v2/exchange-rates?currency=BTC')
        btc_price = float(response.json()['data']['rates']['USD'])
        print(f"\n📈 Current BTC: ${btc_price:,.2f}")
        print(f"Distance to $111,111: ${111111 - btc_price:,.2f}")
        
    except:
        pass

print("\nMitakuye Oyasin - All My Relations 🔥")