#!/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3
"""
Debug portfolio - see ALL accounts including those with holds
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open("/home/dereadi/scripts/claude/cdp_api_key_new.json"))
key = config["name"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["privateKey"], timeout=10)

print("🔍 DEBUG: Checking ALL accounts")
print("=" * 70)

# Get accounts
response = client.get_accounts()

# Debug the response structure
print(f"Response type: {type(response)}")

if hasattr(response, 'accounts'):
    accounts = response.accounts
    print(f"Found {len(accounts)} accounts via .accounts")
elif isinstance(response, dict) and 'accounts' in response:
    accounts = response['accounts']
    print(f"Found {len(accounts)} accounts via ['accounts']")
else:
    accounts = response
    print(f"Response is accounts list directly")

print("\n📊 ALL ACCOUNTS (including zero/hold balances):")
print("-" * 70)

total_available = 0
total_hold = 0
all_positions = {}

for i, account in enumerate(accounts):
    try:
        # Get all attributes
        if hasattr(account, '__dict__'):
            print(f"\nAccount {i} attributes: {account.__dict__.keys()}")
        
        # Get currency
        currency = account.currency if hasattr(account, 'currency') else account.get('currency', '?')
        
        # Get available balance
        if hasattr(account, 'available_balance'):
            if hasattr(account.available_balance, 'value'):
                available = float(account.available_balance.value)
            else:
                available = float(account.available_balance['value'])
        else:
            available = float(account.get('available_balance', {}).get('value', 0))
        
        # Check for hold/locked balance
        hold = 0
        if hasattr(account, 'hold'):
            if hasattr(account.hold, 'value'):
                hold = float(account.hold.value)
            elif account.hold and 'value' in account.hold:
                hold = float(account.hold['value'])
        
        # Get total balance (might be a separate field)
        total_balance = available + hold
        
        # Print everything, even zeros
        print(f"\n{currency}:")
        print(f"  Available: {available:.8f}")
        if hold > 0:
            print(f"  🔒 ON HOLD: {hold:.8f}")
        print(f"  Total: {total_balance:.8f}")
        
        # Get USD value for non-zero balances
        if total_balance > 0.00001:
            if currency in ['USD', 'USDC']:
                usd_value = total_balance
            else:
                try:
                    ticker_response = client.get_product(f"{currency}-USD")
                    # Debug the ticker response
                    print(f"  Ticker response type: {type(ticker_response)}")
                    
                    # Try multiple ways to get the price
                    price = None
                    if hasattr(ticker_response, 'price'):
                        price = float(ticker_response.price)
                    elif hasattr(ticker_response, 'last'):
                        price = float(ticker_response.last)
                    elif isinstance(ticker_response, dict):
                        price = float(ticker_response.get('price', ticker_response.get('last', 0)))
                    
                    if price:
                        usd_value = total_balance * price
                        print(f"  Price: ${price:.2f}")
                        print(f"  💰 USD Value: ${usd_value:.2f}")
                    
                    all_positions[currency] = {
                        'available': available,
                        'hold': hold,
                        'total': total_balance,
                        'price': price,
                        'usd_value': usd_value
                    }
                    
                    total_available += (available * price)
                    total_hold += (hold * price)
                except Exception as e:
                    print(f"  ⚠️ Could not get price: {e}")
            
            if currency in ['USD', 'USDC']:
                all_positions[currency] = {
                    'available': available,
                    'hold': hold,
                    'total': total_balance,
                    'price': 1.0,
                    'usd_value': total_balance
                }
                total_available += available
                total_hold += hold
                
    except Exception as e:
        print(f"Error processing account {i}: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 70)
print("📊 SUMMARY:")
print(f"  Available Value: ${total_available:.2f}")
print(f"  🔒 On Hold Value: ${total_hold:.2f}")
print(f"  💎 TOTAL VALUE: ${total_available + total_hold:.2f}")

# Save debug data
with open('/home/dereadi/scripts/claude/debug_portfolio.json', 'w') as f:
    json.dump({
        'timestamp': datetime.now().isoformat(),
        'total_available': total_available,
        'total_hold': total_hold,
        'total_value': total_available + total_hold,
        'positions': all_positions
    }, f, indent=2)

print(f"\n✅ Debug data saved to debug_portfolio.json")