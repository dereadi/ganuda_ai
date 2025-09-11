#!/usr/bin/env python3
"""
ROBINHOOD TOTP AUTHENTICATOR LOGIN
===================================
Uses Authenticator App instead of SMS
"""

import os
import sys
import pyotp
import getpass

# Install updated robin-stocks from GitHub (not PyPI)
print("🔧 Installing updated robin-stocks from GitHub...")
os.system("pip3 install --upgrade git+https://github.com/jmfernandes/robin_stocks.git --quiet")

import robin_stocks.robinhood as rh

print("🔐 ROBINHOOD AUTHENTICATOR APP LOGIN")
print("="*50)
print()

print("📱 SETUP AUTHENTICATOR APP:")
print("1. Open Robinhood app on your iPhone")
print("2. Go to Profile → Settings → Security")
print("3. Select 'Two-Factor Authentication'")
print("4. Choose 'Authenticator App'")
print("5. Select 'Other' when asked which app")
print("6. Copy the SETUP KEY shown")
print()

# Get credentials
username = input("Email [dereadi@gmail.com]: ").strip() or "dereadi@gmail.com"
password = getpass.getpass("Password: ")
setup_key = input("Authenticator Setup Key (from Robinhood): ").strip()

if setup_key:
    # Generate TOTP code
    totp = pyotp.TOTP(setup_key)
    code = totp.now()
    
    print(f"\n🔢 Generated code: {code}")
    print("Logging in...")
    
    try:
        # Login with TOTP
        login = rh.authentication.login(
            username=username,
            password=password,
            mfa_code=code,
            store_session=True
        )
        
        if login:
            print("\n✅ SUCCESS! Logged in with Authenticator App!")
            
            # Get account info
            profile = rh.profiles.load_account_profile()
            if profile:
                cash = float(profile.get('cash', 0))
                buying_power = float(profile.get('buying_power', 0))
                
                print(f"\n💰 Cash: ${cash:.2f}")
                print(f"💵 Buying Power: ${buying_power:.2f}")
                
                # Check crypto
                crypto_profile = rh.profiles.load_crypto_profile()
                if crypto_profile:
                    crypto_bp = float(crypto_profile.get('buying_power', 0))
                    print(f"🪙 Crypto Buying Power: ${crypto_bp:.2f}")
                
                # Save setup key for future use
                config_file = os.path.expanduser("~/.robinhood_totp.txt")
                with open(config_file, 'w') as f:
                    f.write(setup_key)
                os.chmod(config_file, 0o600)
                
                print(f"\n💾 Setup key saved to {config_file}")
                print("🦀 Ready to deploy $500 Megapod!")
                
    except Exception as e:
        print(f"❌ Login error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure authenticator app is set up in Robinhood")
        print("2. Check that the setup key is correct")
        print("3. Ensure your system time is synchronized")

else:
    print("\n❌ No setup key provided")
    print("Please set up authenticator app in Robinhood first")