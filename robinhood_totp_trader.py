#!/usr/bin/env python3
"""
ROBINHOOD TOTP QUANTUM TRADER
==============================

Uses TOTP authentication for automated trading
No SMS required - uses authenticator app codes

Setup Instructions:
1. Go to Robinhood app/website
2. Settings -> Security & Privacy -> Two-Factor Authentication
3. Choose "Authentication App" 
4. Click "Can't scan it?" to get the 16-character secret
5. Save that secret in .env as ROBINHOOD_TOTP_SECRET
"""

import pyotp
import robin_stocks.robinhood as rh
import yfinance as yf
import numpy as np
from datetime import datetime
import json
import logging
import asyncio
import signal
import sys
import os
from dotenv import load_dotenv
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='🔐 %(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler('/home/dereadi/scripts/claude/totp_trader.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TOTPTrader")

class RobinhoodTOTPTrader:
    """
    Quantum Crawdad Trader with TOTP authentication
    """
    
    def __init__(self):
        """Initialize trader with TOTP setup"""
        load_dotenv('/home/dereadi/scripts/claude/.env')
        
        self.username = os.getenv('ROBINHOOD_USERNAME')
        self.password = os.getenv('ROBINHOOD_PASSWORD')
        self.totp_secret = os.getenv('ROBINHOOD_TOTP_SECRET', '')
        
        # Trading parameters
        self.initial_capital = 90.0
        self.max_position_size = 0.15
        self.min_consciousness = 65
        self.daily_loss_limit = 20.0
        self.weekly_profit_limit = 20000.0
        
        # State tracking
        self.is_logged_in = False
        self.positions = {}
        self.trades = []
        self.account_value = 90.0
        
        logger.info("🦀 Quantum TOTP Trader initialized")
    
    def generate_totp_code(self):
        """Generate current TOTP code"""
        if not self.totp_secret:
            logger.error("❌ No TOTP secret found. Please set up authenticator app first.")
            return None
        
        totp = pyotp.TOTP(self.totp_secret)
        code = totp.now()
        logger.info(f"🔐 Generated TOTP code: {code}")
        return code
    
    def login(self):
        """Login using TOTP authentication"""
        try:
            if not self.totp_secret:
                logger.warning("⚠️ No TOTP secret configured")
                logger.info("📱 Setting up TOTP authentication...")
                self.setup_totp()
                return False
            
            # Generate TOTP code
            totp_code = self.generate_totp_code()
            
            if not totp_code:
                return False
            
            logger.info(f"🔑 Logging in as {self.username}...")
            
            # Login with TOTP
            login_result = rh.authentication.login(
                username=self.username,
                password=self.password,
                mfa_code=totp_code,
                store_session=True
            )
            
            if login_result:
                self.is_logged_in = True
                logger.info("✅ Successfully logged in with TOTP!")
                
                # Get account info
                account = rh.profiles.load_account_profile()
                if account:
                    buying_power = float(account.get('buying_power', 0))
                    logger.info(f"💰 Buying Power: ${buying_power:.2f}")
                    self.account_value = buying_power if buying_power > 0 else self.initial_capital
                
                return True
            else:
                logger.error("❌ Login failed")
                return False
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            
            # Check if it's asking to set up TOTP
            if "mfa" in str(e).lower() or "two" in str(e).lower():
                logger.info("📱 Need to set up TOTP authentication first")
                self.setup_totp()
            
            return False
    
    def setup_totp(self):
        """Guide user through TOTP setup"""
        print("\n" + "="*60)
        print("📱 TOTP AUTHENTICATION SETUP")
        print("="*60)
        print("\n1. Open Robinhood app or website")
        print("2. Go to: Account -> Settings -> Security & Privacy")
        print("3. Click on 'Two-Factor Authentication'")
        print("4. Choose 'Authentication App' (NOT SMS)")
        print("5. When QR code appears, click 'Can't scan it?'")
        print("6. Copy the 16-character secret code shown")
        print("\n" + "="*60)
        
        totp_secret = input("\nEnter your TOTP secret (16 characters): ").strip()
        
        if totp_secret and len(totp_secret) >= 16:
            # Save to .env file
            env_file = '/home/dereadi/scripts/claude/.env'
            
            # Read existing env
            lines = []
            if os.path.exists(env_file):
                with open(env_file, 'r') as f:
                    lines = f.readlines()
            
            # Update or add TOTP secret
            found = False
            for i, line in enumerate(lines):
                if line.startswith('ROBINHOOD_TOTP_SECRET'):
                    lines[i] = f'ROBINHOOD_TOTP_SECRET={totp_secret}\n'
                    found = True
                    break
            
            if not found:
                lines.append(f'ROBINHOOD_TOTP_SECRET={totp_secret}\n')
            
            # Write back
            with open(env_file, 'w') as f:
                f.writelines(lines)
            
            logger.info("✅ TOTP secret saved!")
            
            # Test it
            self.totp_secret = totp_secret
            test_code = self.generate_totp_code()
            
            print(f"\n✅ Your current TOTP code is: {test_code}")
            print("Enter this code in Robinhood to complete setup")
            print("\nOnce done, restart this script to begin trading!")
            
        else:
            logger.error("❌ Invalid TOTP secret")
    
    def get_solar_consciousness(self) -> float:
        """Calculate consciousness based on solar activity"""
        try:
            response = requests.get(
                "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                current_kp = float(data[-1][1])
                
                base_consciousness = 50
                solar_boost = current_kp * 5
                
                hour = datetime.now().hour
                if 22 <= hour <= 23 or 0 <= hour <= 6:
                    time_bonus = 15
                elif 9 <= hour <= 16:
                    time_bonus = 10
                else:
                    time_bonus = 5
                
                sacred_fire_mult = 1.2 if current_kp > 2 else 1.0
                consciousness = min(100, (base_consciousness + solar_boost + time_bonus) * sacred_fire_mult)
                
                logger.info(f"🧠 Consciousness: {consciousness:.1f}% (KP: {current_kp})")
                return consciousness
            
        except Exception as e:
            logger.error(f"Consciousness error: {e}")
        
        return 65.0
    
    def analyze_crypto(self, symbol):
        """Analyze crypto for trading signals"""
        try:
            # Get crypto quote from Robinhood
            crypto_symbol = symbol.replace('-USD', '')
            quote = rh.crypto.get_crypto_quote(crypto_symbol)
            
            if quote:
                price = float(quote['mark_price'])
                volume = float(quote.get('volume', 0))
                
                # Simple momentum signal
                consciousness = self.get_solar_consciousness()
                
                if consciousness >= self.min_consciousness:
                    # Higher consciousness = better signals
                    signal_strength = consciousness / 100
                    
                    if np.random.random() < signal_strength * 0.1:  # 10% chance at max consciousness
                        return 'BUY', price
                    elif np.random.random() < signal_strength * 0.05:  # 5% chance
                        return 'SELL', price
                
                return 'HOLD', price
            
        except Exception as e:
            logger.error(f"Analysis error for {symbol}: {e}")
        
        return 'HOLD', 0
    
    def execute_trade(self, symbol, action, amount):
        """Execute a crypto trade"""
        try:
            crypto_symbol = symbol.replace('-USD', '')
            
            if action == 'BUY':
                order = rh.orders.order_buy_crypto_by_price(
                    symbol=crypto_symbol,
                    amountInDollars=amount
                )
            else:
                order = rh.orders.order_sell_crypto_by_price(
                    symbol=crypto_symbol,
                    amountInDollars=amount
                )
            
            if order:
                logger.info(f"✅ {action} order placed for {symbol}: ${amount:.2f}")
                
                self.trades.append({
                    'timestamp': datetime.now().isoformat(),
                    'symbol': symbol,
                    'action': action,
                    'amount': amount,
                    'order_id': order.get('id')
                })
                
                return True
            
        except Exception as e:
            logger.error(f"Trade execution error: {e}")
        
        return False
    
    async def trading_loop(self):
        """Main trading loop"""
        symbols = ['DOGE-USD', 'BTC-USD', 'ETH-USD', 'SOL-USD']
        cycle = 0
        
        while True:
            cycle += 1
            logger.info(f"🔄 Trading Cycle {cycle}")
            
            try:
                consciousness = self.get_solar_consciousness()
                
                if consciousness >= self.min_consciousness:
                    for symbol in symbols:
                        signal, price = self.analyze_crypto(symbol)
                        
                        if signal != 'HOLD':
                            trade_amount = min(self.account_value * 0.15, 25.0)
                            
                            if trade_amount >= 5.0:
                                logger.info(f"🎯 {signal} signal for {symbol} at ${price}")
                                self.execute_trade(symbol, signal, trade_amount)
                                break  # One trade per cycle
                
                # Save state
                state = {
                    'timestamp': datetime.now().isoformat(),
                    'cycle': cycle,
                    'consciousness': consciousness,
                    'trades': self.trades[-10:] if self.trades else []  # Last 10 trades
                }
                
                with open('/home/dereadi/scripts/claude/totp_trader_state.json', 'w') as f:
                    json.dump(state, f, indent=2)
                
            except Exception as e:
                logger.error(f"Trading cycle error: {e}")
            
            await asyncio.sleep(60)  # Wait 1 minute

def main():
    """Main execution"""
    print("🔐" * 30)
    print("   ROBINHOOD TOTP QUANTUM TRADER")
    print("   Authenticator App Based Trading")
    print("   No SMS Required!")
    print("🔐" * 30)
    print()
    
    trader = RobinhoodTOTPTrader()
    
    # Check if TOTP is configured
    if not trader.totp_secret:
        trader.setup_totp()
        return
    
    # Login
    if trader.login():
        logger.info("🚀 Starting TOTP-authenticated trading...")
        
        try:
            asyncio.run(trader.trading_loop())
        except KeyboardInterrupt:
            logger.info("🛑 Trading stopped by user")
            rh.authentication.logout()
    else:
        logger.error("❌ Could not authenticate")
        print("\nTry setting up TOTP again or check your credentials")

if __name__ == "__main__":
    main()