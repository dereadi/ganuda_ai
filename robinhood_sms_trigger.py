#!/usr/bin/env python3
"""
ROBINHOOD SMS TRIGGER - DIRECT API
===================================

Triggers SMS verification directly through Robinhood API
"""

import robin_stocks.robinhood as rh
import os
from dotenv import load_dotenv
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='📱 %(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger("SMSTrigger")

def trigger_sms():
    """Trigger SMS verification through Robinhood API"""
    try:
        # Load credentials
        load_dotenv('/home/dereadi/scripts/claude/.env')
        username = os.getenv('ROBINHOOD_USERNAME')
        password = os.getenv('ROBINHOOD_PASSWORD')
        
        if not username or not password:
            logger.error("Missing credentials")
            return False
        
        logger.info(f"Attempting login for {username}...")
        
        # Try to login which should trigger 2FA options
        try:
            # First attempt - this should fail and request 2FA
            login_result = rh.authentication.login(
                username=username,
                password=password,
                expiresIn=86400,
                store_session=False,
                mfa_code=None
            )
        except Exception as e:
            error_msg = str(e)
            logger.info(f"Initial login response: {error_msg}")
            
            # Check if it's asking for 2FA
            if "mfa" in error_msg.lower() or "two" in error_msg.lower() or "challenge" in error_msg.lower():
                logger.info("✅ 2FA required - SMS should be triggered")
                
                # Try to explicitly request SMS
                try:
                    # Request SMS by attempting login with by_sms flag
                    rh.authentication.login(
                        username=username,
                        password=password,
                        expiresIn=86400,
                        store_session=False,
                        by_sms=True  # This should trigger SMS
                    )
                except Exception as sms_error:
                    logger.info(f"SMS trigger response: {sms_error}")
                    if "sent" in str(sms_error).lower() or "code" in str(sms_error).lower():
                        logger.info("✅ SMS verification code sent!")
                        return True
                    
                return True
            else:
                logger.warning(f"Unexpected response: {error_msg}")
                return False
                
    except Exception as e:
        logger.error(f"SMS trigger error: {e}")
        return False

if __name__ == "__main__":
    success = trigger_sms()
    if success:
        print("\n📱 SMS verification code should be sent to your phone!")
        print("Check your messages and enter the code when prompted.")
        
        # Wait for user to enter code
        code = input("\nEnter the SMS code you received: ")
        
        if code:
            # Try to complete login with the code
            try:
                load_dotenv('/home/dereadi/scripts/claude/.env')
                username = os.getenv('ROBINHOOD_USERNAME')
                password = os.getenv('ROBINHOOD_PASSWORD')
                
                login_result = rh.authentication.login(
                    username=username,
                    password=password,
                    expiresIn=86400,
                    store_session=True,
                    mfa_code=code
                )
                
                if login_result:
                    print("✅ Successfully authenticated!")
                    print("You can now use the trading system.")
                else:
                    print("❌ Authentication failed")
                    
            except Exception as e:
                print(f"❌ Login error: {e}")
    else:
        print("❌ Failed to trigger SMS verification")