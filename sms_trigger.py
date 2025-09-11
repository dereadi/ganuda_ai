#!/usr/bin/env python3
"""
DIRECT SMS TRIGGER FOR ROBINHOOD
"""

import os
import sys

print("🔥 ROBINHOOD SMS TRIGGER")
print("="*40)
print()

# Install if needed
try:
    import robin_stocks.robinhood as rh
except:
    os.system("python3 -m pip install robin-stocks")
    import robin_stocks.robinhood as rh

# Credentials
username = "dereadi@gmail.com"
password = "D0naldD!ck2028"

print(f"📧 Account: {username}")
print("📱 Forcing SMS verification...")
print()

# Clear any existing session
try:
    rh.logout()
except:
    pass

# Force SMS by setting challenge response header
rh.globals.SESSION.headers['X-Challenge-Type'] = 'sms'

try:
    # This will fail but trigger SMS
    result = rh.login(
        username=username,
        password=password,
        by_sms=True,
        challenge_type='sms'
    )
except Exception as e:
    print(f"SMS trigger response: {e}")
    print()
    print("📱 CHECK YOUR PHONE FOR SMS CODE!")
    print()
    
    code = input("Enter 6-digit code: ").strip()
    
    if code:
        try:
            # Login with code
            result = rh.login(
                username=username,
                password=password,
                mfa_code=code
            )
            
            if result:
                print("\n✅ SUCCESS!")
                
                # Get account info
                profile = rh.profiles.load_account_profile()
                cash = float(profile.get('cash', 0))
                print(f"💰 Cash: ${cash:.2f}")
                
                # Ready to trade
                print("\n🦀 READY TO DEPLOY $90!")
                
        except Exception as e2:
            print(f"Code error: {e2}")