#!/usr/bin/env python3
"""
ROBINHOOD API KEY AUTHENTICATION
=================================
Uses API key instead of SMS
"""

import os
import sys
import json
import requests

print("🔑 ROBINHOOD API KEY AUTHENTICATOR")
print("="*50)
print()

# Check if you have an API key saved
api_key_file = os.path.expanduser("~/.robinhood_api_key")

if os.path.exists(api_key_file):
    with open(api_key_file, 'r') as f:
        api_key = f.read().strip()
    print(f"✅ Found saved API key: {api_key[:10]}...")
else:
    print("📝 To get your API key:")
    print("1. Log into Robinhood web: https://robinhood.com")
    print("2. Go to Account → Settings → API Access")
    print("3. Generate an API key")
    print("4. Copy it here")
    print()
    
    api_key = input("Enter your Robinhood API key: ").strip()
    
    if api_key:
        # Save for future use
        with open(api_key_file, 'w') as f:
            f.write(api_key)
        os.chmod(api_key_file, 0o600)
        print(f"✅ API key saved to {api_key_file}")

print("\n🔐 Testing API key authentication...")

# Robinhood API v2 endpoints
BASE_URL = "https://api.robinhood.com"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "User-Agent": "QuantumCrawdad/1.0"
}

# Test authentication
try:
    # Get account info
    response = requests.get(f"{BASE_URL}/accounts/", headers=headers)
    
    if response.status_code == 200:
        print("✅ API KEY AUTHENTICATED!")
        
        data = response.json()
        if data.get('results'):
            account = data['results'][0]
            print(f"\n💰 Account Number: {account.get('account_number')}")
            print(f"💵 Buying Power: ${float(account.get('buying_power', 0)):.2f}")
            print(f"💸 Cash: ${float(account.get('cash', 0)):.2f}")
        
        # Get crypto accounts
        crypto_response = requests.get(f"{BASE_URL}/crypto/accounts/", headers=headers)
        if crypto_response.status_code == 200:
            crypto_data = crypto_response.json()
            if crypto_data.get('results'):
                crypto_account = crypto_data['results'][0]
                print(f"\n🪙 Crypto Buying Power: ${float(crypto_account.get('buying_power', 0)):.2f}")
        
        # Get positions
        positions_response = requests.get(f"{BASE_URL}/crypto/holdings/", headers=headers)
        if positions_response.status_code == 200:
            positions_data = positions_response.json()
            if positions_data.get('results'):
                print("\n📊 Crypto Holdings:")
                for pos in positions_data['results']:
                    quantity = float(pos.get('quantity', 0))
                    if quantity > 0:
                        currency = pos.get('currency', {})
                        symbol = currency.get('code', 'Unknown')
                        print(f"  {symbol}: {quantity}")
        
        print("\n✅ READY TO DEPLOY $90 WITH API KEY!")
        print("🦀 No SMS needed - direct API access!")
        
        # Save config for trading
        config = {
            "api_key": api_key,
            "authenticated": True,
            "method": "api_key"
        }
        
        config_file = os.path.expanduser("~/robinhood_config.json")
        with open(config_file, 'w') as f:
            json.dump(config, f)
        print(f"\n💾 Config saved to {config_file}")
        
    elif response.status_code == 401:
        print("❌ Invalid API key")
        print("\nTo get a valid API key:")
        print("1. Log into Robinhood.com")
        print("2. Go to Settings → API Access")
        print("3. Generate a new API key")
        
        if os.path.exists(api_key_file):
            os.remove(api_key_file)
            print(f"Removed invalid key from {api_key_file}")
            
    else:
        print(f"❌ API error: {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"❌ Connection error: {e}")
    print("\nTroubleshooting:")
    print("1. Check your internet connection")
    print("2. Verify API key is correct")
    print("3. Check if Robinhood API is down")

print("\n" + "="*50)
print("API Key Benefits:")
print("✅ No SMS verification needed")
print("✅ No 2FA challenges")
print("✅ Direct programmatic access")
print("✅ Works from any IP address")
print("="*50)