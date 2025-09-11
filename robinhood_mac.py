#!/usr/bin/env python3
"""
ROBINHOOD MAC TRADER - AT&T FIBER EDITION
==========================================
Run this from your Mac with AT&T fiber connection
No datacenter blocking!
"""

import os
import sys
import getpass

print("🦀 QUANTUM CRAWDAD MAC TRADER")
print("="*40)
print("Running from AT&T residential fiber")
print("="*40)
print()

# Check for required packages
try:
    import robin_stocks.robinhood as rh
except ImportError:
    print("Installing robin-stocks...")
    os.system("pip3 install robin-stocks")
    import robin_stocks.robinhood as rh

try:
    import pyotp
except ImportError:
    print("Installing pyotp...")
    os.system("pip3 install pyotp")
    import pyotp

# Get credentials
print("Enter your Robinhood credentials:")
username = input("Email: ").strip()
password = getpass.getpass("Password: ")

print("\n🔐 Attempting login from AT&T residential IP...")

try:
    # First login attempt
    login = rh.authentication.login(
        username=username,
        password=password,
        store_session=True
    )
    
    if login:
        print("✅ SUCCESS! Logged in from AT&T fiber!")
        
        # Get account info
        profile = rh.profiles.load_account_profile()
        if profile:
            print(f"\n💰 Account Type: {profile.get('type', 'N/A')}")
            print(f"💵 Buying Power: ${float(profile.get('buying_power', 0)):.2f}")
            
        # Get positions
        positions = rh.positions.get_open_stock_positions()
        crypto = rh.crypto.get_crypto_positions()
        
        print(f"\n📊 Open Positions:")
        if positions:
            for pos in positions[:5]:  # Show first 5
                symbol = rh.stocks.get_symbol_by_url(pos['instrument'])
                quantity = float(pos['quantity'])
                if quantity > 0:
                    print(f"  {symbol}: {quantity} shares")
        
        if crypto:
            print(f"\n🪙 Crypto Holdings:")
            for c in crypto:
                if float(c['quantity']) > 0:
                    print(f"  {c['currency']['code']}: {c['quantity']}")
        
        print("\n✅ Authentication working from AT&T connection!")
        print("You can now run automated trading from this Mac!")
        
except Exception as e:
    error_msg = str(e)
    print(f"\n❌ Login error: {error_msg}")
    
    if "challenge" in error_msg.lower() or "mfa" in error_msg.lower():
        print("\n📱 2FA Required. Choose method:")
        print("1. SMS verification")
        print("2. TOTP (authenticator app)")
        
        choice = input("\nEnter choice (1 or 2): ").strip()
        
        if choice == "1":
            print("\n📱 Requesting SMS...")
            # The initial login attempt should have triggered SMS
            code = input("Enter SMS code: ").strip()
            
        elif choice == "2":
            code = input("Enter authenticator app code: ").strip()
        else:
            print("Invalid choice")
            sys.exit(1)
        
        # Try login with code
        try:
            login = rh.authentication.login(
                username=username,
                password=password,
                mfa_code=code,
                store_session=True
            )
            
            if login:
                print("\n✅ SUCCESS! Authenticated from AT&T fiber!")
                
                profile = rh.profiles.load_account_profile()
                if profile:
                    print(f"💰 Buying Power: ${float(profile.get('buying_power', 0)):.2f}")
                    
                print("\n🎯 Ready to trade with your $90!")
                
        except Exception as e2:
            print(f"❌ Authentication failed: {e2}")
    else:
        print("\nTroubleshooting:")
        print("1. Make sure you're running from your Mac with AT&T internet")
        print("2. Check your credentials")
        print("3. Try disabling 2FA temporarily in Robinhood settings")

# Logout
rh.authentication.logout()
print("\n🔒 Logged out")