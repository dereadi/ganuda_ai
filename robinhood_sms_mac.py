#!/usr/bin/env python3
"""
ROBINHOOD SMS AUTHENTICATION - MAC VERSION
===========================================
Forces SMS verification instead of app approval
"""

import sys
import getpass

try:
    import robin_stocks.robinhood as rh
except ImportError:
    print("Installing robin-stocks...")
    import os
    os.system("python3 -m pip install robin-stocks")
    import robin_stocks.robinhood as rh

print("🦀 QUANTUM CRAWDAD SMS AUTHENTICATOR")
print("="*40)
print("Running from AT&T residential fiber")
print("Forcing SMS verification")
print("="*40)
print()

# Get credentials
print("Enter your Robinhood credentials:")
username = input("Email: ").strip()
password = getpass.getpass("Password: ")

print("\n📱 Requesting SMS verification...")

try:
    # First attempt with challenge_type='sms' to force SMS
    login = rh.authentication.login(
        username=username,
        password=password,
        store_session=True,
        challenge_type='sms'  # Force SMS instead of app
    )
    
    print("✅ Login attempt made, check for SMS")
    
except Exception as e:
    error_msg = str(e)
    print(f"Initial response: {error_msg}")
    
    # The error should indicate SMS was sent
    if "challenge" in error_msg.lower() or "sms" in error_msg.lower() or "code" in error_msg.lower():
        print("\n📱 SMS should be sent! Check your phone.")
        code = input("Enter the SMS code: ").strip()
        
        if code:
            try:
                # Login with SMS code
                login = rh.authentication.login(
                    username=username,
                    password=password,
                    mfa_code=code,
                    store_session=True
                )
                
                if login:
                    print("\n✅ SUCCESS! Authenticated via SMS from AT&T fiber!")
                    
                    # Get account info to prove it worked
                    profile = rh.profiles.load_account_profile()
                    if profile:
                        print(f"\n💰 Account Type: {profile.get('type', 'N/A')}")
                        print(f"💵 Buying Power: ${float(profile.get('buying_power', 0)):.2f}")
                        
                        # Check crypto holdings
                        crypto = rh.crypto.get_crypto_positions()
                        if crypto:
                            print(f"\n🪙 Crypto Holdings:")
                            for c in crypto:
                                if float(c.get('quantity', 0)) > 0:
                                    print(f"  {c['currency']['code']}: {c['quantity']}")
                        
                        print("\n🎯 Ready to deploy your $90!")
                        print("Authentication working perfectly from AT&T connection!")
                else:
                    print("❌ SMS code verification failed")
                    
            except Exception as e2:
                print(f"❌ SMS verification error: {e2}")
    else:
        print(f"\n⚠️ Unexpected response: {error_msg}")
        print("\nTry these alternatives:")
        print("1. Open Robinhood app and disable 2FA temporarily")
        print("2. Switch to TOTP authentication in settings")
        print("3. Check if SMS is blocked on your account")

# Cleanup
try:
    rh.authentication.logout()
    print("\n🔒 Logged out")
except:
    pass