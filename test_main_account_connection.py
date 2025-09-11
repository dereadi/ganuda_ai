#!/usr/bin/env python3
"""
Test connection to your MAIN Coinbase account
After setting up Advanced Trade API
"""

import json
import os
import sys
from datetime import datetime

print("🔥 TESTING MAIN ACCOUNT CONNECTION")
print("=" * 60)
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Check for main account config first, fall back to regular
config_paths = [
    os.path.expanduser("~/.coinbase_main_config.json"),
    os.path.expanduser("~/.coinbase_config.json")
]

config = None
config_path_used = None

for path in config_paths:
    if os.path.exists(path):
        try:
            with open(path) as f:
                config = json.load(f)
                config_path_used = path
                print(f"✅ Loaded config from: {path}")
                break
        except Exception as e:
            print(f"❌ Error loading {path}: {e}")

if not config:
    print("❌ No configuration found!")
    print("\nPlease create ~/.coinbase_main_config.json with:")
    print('{\n  "api_key": "organizations/xxx/apiKeys/yyy",')
    print('  "api_secret": "-----BEGIN EC PRIVATE KEY-----\\n...\\n-----END EC PRIVATE KEY-----"\n}')
    sys.exit(1)

print(f"API Key ends with: ...{config['api_key'][-8:]}")
print()

# Test the connection
from coinbase.rest import RESTClient

try:
    client = RESTClient(
        api_key=config['api_key'],
        api_secret=config['api_secret']
    )
    
    print("📊 FETCHING PORTFOLIO...")
    print("-" * 40)
    
    accounts = client.get_accounts()
    
    total_usd_value = 0
    crypto_count = 0
    
    # Key positions to show
    key_assets = ['USD', 'USDC', 'BTC', 'ETH', 'SOL', 'XRP', 'DOGE', 'AVAX', 'MATIC']
    positions = {}
    
    for account in accounts.accounts:
        currency = account.currency
        
        if hasattr(account.available_balance, 'value'):
            available = float(account.available_balance.value)
        else:
            available = 0
            
        if hasattr(account.hold, 'value'):
            hold = float(account.hold.value)
        else:
            hold = 0
        
        total = available + hold
        
        if total > 0.01:
            positions[currency] = {
                'available': available,
                'hold': hold,
                'total': total
            }
            
            if currency not in ['USD', 'USDC']:
                crypto_count += 1
    
    # Show balances
    print("BALANCES FOUND:")
    print()
    
    for asset in key_assets:
        if asset in positions:
            p = positions[asset]
            if asset in ['USD', 'USDC']:
                print(f"{asset:6} ${p['total']:.2f} (available: ${p['available']:.2f})")
            else:
                print(f"{asset:6} {p['total']:.4f} (available: {p['available']:.4f})")
    
    # Calculate approximate portfolio value
    print()
    print("-" * 40)
    
    if 'USD' in positions:
        total_usd_value += positions['USD']['total']
    if 'USDC' in positions:
        total_usd_value += positions['USDC']['total']
    
    # Quick price checks for rough value
    if crypto_count > 0:
        print(f"Crypto assets found: {crypto_count}")
        
        # Get some prices
        if 'BTC' in positions and positions['BTC']['total'] > 0:
            ticker = client.get_product('BTC-USD')
            price = float(ticker.price)
            value = positions['BTC']['total'] * price
            total_usd_value += value
            print(f"BTC value: ${value:,.2f}")
            
        if 'ETH' in positions and positions['ETH']['total'] > 0:
            ticker = client.get_product('ETH-USD')
            price = float(ticker.price)
            value = positions['ETH']['total'] * price
            total_usd_value += value
            print(f"ETH value: ${value:,.2f}")
            
        if 'SOL' in positions and positions['SOL']['total'] > 0:
            ticker = client.get_product('SOL-USD')
            price = float(ticker.price)
            value = positions['SOL']['total'] * price
            total_usd_value += value
            print(f"SOL value: ${value:,.2f}")
    
    print()
    print("=" * 60)
    
    if total_usd_value > 30000:
        print("🎉 SUCCESS! MAIN ACCOUNT CONNECTED!")
        print(f"Approximate Portfolio Value: ${total_usd_value:,.2f}")
        print()
        print("✅ VM Tribe can now execute trades!")
        print("✅ Cherokee Council decisions can be automated!")
        print("✅ DOGE reallocation ready to execute!")
    elif total_usd_value > 100:
        print("⚠️ Account connected but seems to be wrong one")
        print(f"Portfolio Value: ${total_usd_value:,.2f}")
        print("Expected: ~$32,947")
        print("\nMake sure you created API key for your MAIN account")
    else:
        print("❌ Connected but no significant balance found")
        print(f"Total Value: ${total_usd_value:,.2f}")
        print("\nPossible issues:")
        print("1. Wrong account")
        print("2. Assets on Coinbase One (not Advanced Trade)")
        print("3. Assets in vault or staking")
    
    print("=" * 60)
    
except Exception as e:
    print(f"❌ Connection failed: {e}")
    print()
    print("Common issues:")
    print("1. Invalid API credentials")
    print("2. Wrong API type (need Advanced Trade API)")
    print("3. Insufficient permissions (need View + Trade)")
    print()
    print("Please check your configuration and try again")

print()
print("🔥 Test complete!")