#!/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3
"""
Find ALL positions including those with any balance
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime
import requests

config = json.load(open("/home/dereadi/scripts/claude/cdp_api_key_new.json"))
key = config["name"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["privateKey"], timeout=10)

print("🔍 FINDING ALL POSITIONS")
print("=" * 70)

# Get accounts
response = client.get_accounts()

# Handle response structure
if hasattr(response, 'accounts'):
    accounts = response.accounts
else:
    accounts = response.get('accounts', response)

print(f"\n📊 Total accounts found: {len(accounts)}")
print("-" * 70)

# Track all currencies we find
all_currencies = set()
positions_with_balance = {}

for account in accounts:
    try:
        # Get currency
        if hasattr(account, 'currency'):
            currency = account.currency
        else:
            currency = account.get('currency', 'UNKNOWN')
        
        all_currencies.add(currency)
        
        # Get available balance
        available = 0
        if hasattr(account, 'available_balance'):
            if hasattr(account.available_balance, 'value'):
                available = float(account.available_balance.value)
            else:
                available = float(account.available_balance.get('value', 0))
        
        # Get hold balance
        hold = 0
        if hasattr(account, 'hold'):
            if hasattr(account.hold, 'value'):
                hold = float(account.hold.value)
            elif isinstance(account.hold, dict):
                hold = float(account.hold.get('value', 0))
        
        # Total balance
        total = available + hold
        
        # Store if non-zero
        if total > 0.00000001:
            positions_with_balance[currency] = {
                'available': available,
                'hold': hold,
                'total': total
            }
            
    except Exception as e:
        print(f"Error processing account: {e}")

print(f"\n🪙 All currencies found: {sorted(all_currencies)}")
print(f"\n💰 Positions with balance:")
print("-" * 70)

total_portfolio_value = 0

for currency, balances in positions_with_balance.items():
    print(f"\n{currency}:")
    print(f"  Available: {balances['available']:.8f}")
    if balances['hold'] > 0:
        print(f"  🔒 On Hold: {balances['hold']:.8f}")
    print(f"  Total: {balances['total']:.8f}")
    
    # Try to get USD value
    if currency in ['USD', 'USDC']:
        usd_value = balances['total']
    else:
        # Try Coinbase public API
        try:
            url = f"https://api.coinbase.com/v2/exchange-rates?currency={currency}"
            response = requests.get(url, timeout=5)
            data = response.json()
            if 'data' in data and 'rates' in data['data'] and 'USD' in data['data']['rates']:
                price = float(data['data']['rates']['USD'])
                usd_value = balances['total'] * price
                print(f"  Price: ${price:,.2f}")
            else:
                usd_value = 0
                print(f"  ⚠️ Could not get price")
        except Exception as e:
            print(f"  ⚠️ Price error: {e}")
            usd_value = 0
    
    if usd_value > 0:
        print(f"  💵 USD Value: ${usd_value:,.2f}")
        total_portfolio_value += usd_value

print("\n" + "=" * 70)
print(f"💎 TOTAL PORTFOLIO VALUE: ${total_portfolio_value:,.2f}")

# Check if we're missing the $13.7k
if total_portfolio_value < 10000:
    print(f"\n⚠️ WARNING: Portfolio shows ${total_portfolio_value:,.2f} but user states $13,700")
    print("Possible issues:")
    print("  1. Some positions may be in open orders (check 'hold' balances)")
    print("  2. API may not be returning all accounts")
    print("  3. Some assets may be staked or locked")
    print("  4. Check if there are sub-accounts or portfolios")