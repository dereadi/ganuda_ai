#!/usr/bin/env python3
"""
ROBINHOOD FORCE SMS AUTHENTICATOR
==================================
Explicitly triggers SMS verification
"""

import sys
import os
import json
import getpass

try:
    import robin_stocks.robinhood as rh
except ImportError:
    print("Installing robin-stocks...")
    os.system("python3 -m pip install robin-stocks")
    import robin_stocks.robinhood as rh

print("🔥 SACRED FIRE SMS AUTHENTICATOR")
print("=" * 50)
print("Forcing SMS verification from AT&T residential fiber")
print("=" * 50)
print()

# Get credentials
print("Enter your Robinhood credentials:")
username = input("Email [dereadi@gmail.com]: ").strip() or "dereadi@gmail.com"
password = getpass.getpass("Password: ")

print("\n📱 FORCING SMS VERIFICATION...")
print("This will explicitly request SMS instead of app approval")
print()

# Clear any existing session
try:
    rh.authentication.logout()
except:
    pass

# Method 1: Direct SMS challenge request
print("Method 1: Direct SMS challenge...")
try:
    # This should trigger SMS directly
    response = rh.authentication.request_challenge(
        username=username,
        device_token=rh.authentication.generate_device_token()
    )
    print(f"Challenge response: {response}")
    
    if response and response.get('challenge'):
        print("\n✅ SMS challenge triggered!")
        print("Check your phone for the code")
        
except Exception as e:
    print(f"Direct challenge error: {e}")

# Method 2: Login with SMS preference
print("\nMethod 2: Login with SMS preference...")
try:
    # Set headers to prefer SMS
    rh.authentication.SESSION.headers.update({
        'X-Robinhood-Challenge-Response-ID': 'sms'
    })
    
    # Attempt login which should trigger SMS
    login = rh.authentication.login(
        username=username,
        password=password,
        by_sms=True,  # Prefer SMS
        store_session=False  # Don't store until we have SMS code
    )
    
except Exception as e:
    error_msg = str(e)
    print(f"Response: {error_msg}")
    
    # Check if SMS was triggered
    if "challenge" in error_msg.lower() or "code" in error_msg.lower():
        print("\n✅ SMS verification triggered!")
        print("📱 CHECK YOUR PHONE NOW!")
        print()
        
        # Wait for code
        code = input("Enter the 6-digit SMS code: ").strip()
        
        if code and len(code) == 6:
            print(f"\nSubmitting SMS code: {code}")
            
            try:
                # Complete login with SMS code
                login = rh.authentication.login(
                    username=username,
                    password=password,
                    mfa_code=code,
                    store_session=True
                )
                
                if login:
                    print("\n🎉 SUCCESS! Authenticated via SMS!")
                    
                    # Verify account access
                    profile = rh.profiles.load_account_profile()
                    if profile:
                        buying_power = float(profile.get('cash', 0))
                        print(f"\n💰 Cash Available: ${buying_power:.2f}")
                        
                        # Check crypto buying power
                        crypto_info = rh.profiles.load_crypto_profile()
                        if crypto_info:
                            crypto_bp = float(crypto_info.get('buying_power', 0))
                            print(f"🪙 Crypto Buying Power: ${crypto_bp:.2f}")
                        
                        # Show crypto positions
                        positions = rh.crypto.get_crypto_positions()
                        if positions:
                            print("\n📊 Current Crypto Holdings:")
                            for pos in positions:
                                qty = float(pos.get('quantity', 0))
                                if qty > 0:
                                    symbol = pos['currency']['code']
                                    print(f"  {symbol}: {qty}")
                        
                        print("\n✅ READY TO DEPLOY YOUR $90!")
                        print("🦀 Quantum Crawdad trading system ready!")
                        
                        # Save session for trading
                        session_file = os.path.expanduser("~/robinhood_session.json")
                        with open(session_file, 'w') as f:
                            json.dump({
                                'authenticated': True,
                                'username': username,
                                'buying_power': buying_power
                            }, f)
                        print(f"\n💾 Session saved to: {session_file}")
                        
                else:
                    print("❌ SMS verification failed")
                    
            except Exception as e2:
                print(f"❌ SMS submission error: {e2}")
        else:
            print("❌ Invalid code format")
    
    elif "device" in error_msg.lower():
        print("\n⚠️ Device approval requested instead of SMS")
        print("Trying to override...")
        
        # Force SMS by rejecting device approval
        try:
            # Explicitly request SMS challenge
            challenge_type = 'sms'
            login = rh.authentication.respond_to_challenge(
                challenge_id=None,  # Will get from error
                challenge_type=challenge_type
            )
            print("Forced SMS request sent")
            
        except Exception as e3:
            print(f"Override failed: {e3}")
            print("\nManual steps:")
            print("1. Open Robinhood app")
            print("2. Go to Settings → Security")
            print("3. Change 2FA to 'Text Message'")
            print("4. Run this script again")
    
    else:
        print(f"\n⚠️ Unexpected response: {error_msg}")

# Method 3: Raw API call to force SMS
if not locals().get('login'):
    print("\nMethod 3: Raw API SMS trigger...")
    try:
        import requests
        
        # Direct API call to trigger SMS
        api_url = "https://api.robinhood.com/challenge/"
        
        payload = {
            'username': username,
            'password': password,
            'challenge_type': 'sms',
            'device_token': rh.authentication.generate_device_token()
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
            'Accept': 'application/json',
            'X-Robinhood-Challenge-Type': 'sms'
        }
        
        response = requests.post(api_url, json=payload, headers=headers)
        print(f"API Response: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SMS should be sent!")
            code = input("Enter SMS code: ").strip()
            
            if code:
                # Submit code
                payload['mfa_code'] = code
                response = requests.post(api_url, json=payload, headers=headers)
                
                if response.status_code == 200:
                    print("✅ Authenticated!")
                    
    except Exception as e:
        print(f"Raw API error: {e}")

print("\n" + "="*50)
print("If SMS still not working:")
print("1. Temporarily disable 2FA in Robinhood app")
print("2. Switch to TOTP authentication")
print("3. Use app approval then switch to SMS")
print("="*50)

# Cleanup
try:
    if locals().get('login'):
        print("\nKeeping session active for trading...")
    else:
        rh.authentication.logout()
        print("\n🔒 Logged out")
except:
    pass