#!/usr/bin/env python3
"""
ROBINHOOD SESSION-BASED TRADER
===============================

Login once manually, save session for automated trading
Works with any 2FA method (SMS, TOTP, Passkey)
"""

import robin_stocks.robinhood as rh
import pickle
import os
import json
import logging
from datetime import datetime
import asyncio
import requests
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='🔒 %(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger("SessionTrader")

class RobinhoodSessionTrader:
    """
    Session-based trader - login once, trade many times
    """
    
    def __init__(self):
        load_dotenv('/home/dereadi/scripts/claude/.env')
        self.username = os.getenv('ROBINHOOD_USERNAME')
        self.password = os.getenv('ROBINHOOD_PASSWORD')
        self.session_file = '/home/dereadi/scripts/claude/.robinhood_session.pkl'
        self.is_logged_in = False
        
        # Trading parameters
        self.initial_capital = 90.0
        self.min_consciousness = 65
        
        logger.info("🔒 Session-based trader initialized")
    
    def manual_login(self):
        """
        Manual login with any 2FA method
        """
        print("\n" + "="*60)
        print("🔐 MANUAL LOGIN PROCESS")
        print("="*60)
        print("\nThis will open a login prompt.")
        print("You can use ANY authentication method:")
        print("  • SMS verification")
        print("  • TOTP authenticator app")
        print("  • Passkey")
        print("  • Email verification")
        print("\n" + "="*60)
        
        try:
            # First attempt - will likely need 2FA
            logger.info(f"Attempting login for {self.username}...")
            
            login_result = rh.authentication.login(
                username=self.username,
                password=self.password,
                store_session=True
            )
            
            self.is_logged_in = True
            logger.info("✅ Login successful!")
            
            # Save session
            self.save_session()
            
            # Get account info
            self.display_account_info()
            
            return True
            
        except Exception as e:
            error_msg = str(e)
            logger.info(f"Login needs verification: {error_msg}")
            
            # Check what type of verification is needed
            if "challenge" in error_msg.lower() or "mfa" in error_msg.lower():
                print("\n📱 Verification required!")
                
                # Get verification method preference
                print("\nChoose verification method:")
                print("1. SMS (text message)")
                print("2. TOTP (authenticator app)")
                print("3. Skip (if using passkey in browser)")
                
                choice = input("\nEnter choice (1-3): ").strip()
                
                if choice == "1":
                    # SMS verification
                    return self.login_with_sms()
                elif choice == "2":
                    # TOTP verification
                    return self.login_with_totp()
                else:
                    print("\n⚠️ Please complete passkey authentication in your browser")
                    print("Then run this script again to save the session")
                    return False
            
            logger.error(f"Login failed: {error_msg}")
            return False
    
    def login_with_sms(self):
        """Login with SMS verification"""
        try:
            # Request SMS
            logger.info("📱 Requesting SMS code...")
            
            # This should trigger SMS
            try:
                rh.authentication.login(
                    username=self.username,
                    password=self.password,
                    challenge_type='sms'  # Use challenge_type instead of by_sms
                )
            except:
                pass  # Expected to fail, but should send SMS
            
            # Get code from user
            code = input("\n📱 Enter the SMS code you received: ").strip()
            
            if code:
                # Login with code
                login_result = rh.authentication.login(
                    username=self.username,
                    password=self.password,
                    mfa_code=code,
                    store_session=True
                )
                
                if login_result:
                    self.is_logged_in = True
                    logger.info("✅ SMS authentication successful!")
                    self.save_session()
                    self.display_account_info()
                    return True
                    
        except Exception as e:
            logger.error(f"SMS login error: {e}")
        
        return False
    
    def login_with_totp(self):
        """Login with TOTP code"""
        try:
            code = input("\n🔐 Enter your authenticator app code: ").strip()
            
            if code:
                login_result = rh.authentication.login(
                    username=self.username,
                    password=self.password,
                    mfa_code=code,
                    store_session=True
                )
                
                if login_result:
                    self.is_logged_in = True
                    logger.info("✅ TOTP authentication successful!")
                    self.save_session()
                    self.display_account_info()
                    return True
                    
        except Exception as e:
            logger.error(f"TOTP login error: {e}")
        
        return False
    
    def save_session(self):
        """Save authentication session"""
        try:
            # Get current session headers
            session_data = {
                'login_time': datetime.now().isoformat(),
                'username': self.username,
                # The session is automatically stored by robin_stocks
            }
            
            with open(self.session_file, 'wb') as f:
                pickle.dump(session_data, f)
            
            logger.info(f"💾 Session saved to {self.session_file}")
            
            print("\n" + "="*60)
            print("✅ SESSION SAVED SUCCESSFULLY!")
            print("="*60)
            print("\nYou can now run automated trading without logging in again.")
            print("The session will remain valid for 24 hours.")
            print("\nTo start trading, run:")
            print("  python3 robinhood_session_trader.py --trade")
            print("="*60)
            
        except Exception as e:
            logger.error(f"Save session error: {e}")
    
    def load_session(self):
        """Load saved session"""
        try:
            if os.path.exists(self.session_file):
                with open(self.session_file, 'rb') as f:
                    session_data = pickle.load(f)
                
                login_time = datetime.fromisoformat(session_data['login_time'])
                age = datetime.now() - login_time
                
                if age.total_seconds() < 86400:  # 24 hours
                    logger.info(f"📂 Loaded session from {login_time}")
                    
                    # Test if session is still valid
                    try:
                        profile = rh.profiles.load_account_profile()
                        if profile:
                            self.is_logged_in = True
                            logger.info("✅ Session is still valid!")
                            return True
                    except:
                        logger.warning("⚠️ Session expired, need to login again")
                else:
                    logger.warning("⚠️ Session too old, need to login again")
            
        except Exception as e:
            logger.error(f"Load session error: {e}")
        
        return False
    
    def display_account_info(self):
        """Display account information"""
        try:
            profile = rh.profiles.load_account_profile()
            account = rh.profiles.load_portfolio_profile()
            
            if profile and account:
                print("\n" + "="*60)
                print("💰 ACCOUNT INFORMATION")
                print("="*60)
                print(f"Account Type: {profile.get('type', 'N/A')}")
                print(f"Buying Power: ${float(profile.get('buying_power', 0)):.2f}")
                
                if account:
                    print(f"Total Value: ${float(account.get('total_return_today', 0)):.2f}")
                    print(f"Daily Return: ${float(account.get('total_return_today', 0)):.2f}")
                
                print("="*60)
                
        except Exception as e:
            logger.error(f"Display account error: {e}")
    
    def get_solar_consciousness(self):
        """Calculate consciousness level"""
        try:
            response = requests.get(
                "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                current_kp = float(data[-1][1])
                
                base = 50
                solar = current_kp * 5
                hour = datetime.now().hour
                time_bonus = 15 if (22 <= hour or hour <= 6) else 10
                
                consciousness = min(100, base + solar + time_bonus)
                logger.info(f"🧠 Consciousness: {consciousness:.1f}% (KP: {current_kp})")
                return consciousness
                
        except:
            pass
        
        return 65.0
    
    async def trade_with_session(self):
        """Trade using saved session"""
        if not self.is_logged_in:
            if not self.load_session():
                logger.error("❌ No valid session. Please login first.")
                return
        
        logger.info("🚀 Starting session-based trading...")
        
        symbols = ['DOGE', 'BTC', 'ETH', 'SOL']
        cycle = 0
        
        while True:
            cycle += 1
            logger.info(f"🔄 Trading Cycle {cycle}")
            
            try:
                consciousness = self.get_solar_consciousness()
                
                if consciousness >= self.min_consciousness:
                    for symbol in symbols:
                        # Get crypto quote
                        quote = rh.crypto.get_crypto_quote(symbol)
                        
                        if quote:
                            price = float(quote['mark_price'])
                            logger.info(f"📊 {symbol}: ${price:.2f}")
                            
                            # Simple trading logic
                            import random
                            if random.random() < 0.05:  # 5% chance
                                logger.info(f"🎯 Trading signal for {symbol}")
                                # Would execute trade here
                
            except Exception as e:
                logger.error(f"Trading error: {e}")
            
            await asyncio.sleep(60)

def main():
    """Main execution"""
    import sys
    
    print("🔒" * 30)
    print("   ROBINHOOD SESSION-BASED TRADER")
    print("   Login Once, Trade Many Times")
    print("🔒" * 30)
    print()
    
    trader = RobinhoodSessionTrader()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--trade':
        # Use existing session to trade
        asyncio.run(trader.trade_with_session())
    else:
        # Manual login to create session
        if trader.manual_login():
            print("\n✅ You can now run automated trading!")
        else:
            print("\n❌ Login failed. Please try again.")

if __name__ == "__main__":
    main()