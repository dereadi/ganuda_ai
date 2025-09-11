#!/usr/bin/env python3
"""
ROBINHOOD QUANTUM CRAWDAD TRADER - REAL MONEY
=============================================

Live trading with Robinhood API using quantum consciousness
and Cherokee Constitutional AI wisdom.

Sacred Fire Protocol: REAL MONEY MODE
Target: $90 starting capital
Goal: Generate consistent income for planetary healing

IMPORTANT: This connects to real money. Use carefully.
"""

import robin_stocks.robinhood as rh
import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import json
import logging
import asyncio
import signal
import sys
import time
from typing import Dict, List, Optional
import requests
import hashlib
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='💰 %(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler('/home/dereadi/scripts/claude/robinhood_trader.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("RobinhoodQuantumTrader")

class RobinhoodQuantumTrader:
    """
    Real money quantum trading with Robinhood
    """
    
    def __init__(self, username: str, password: str):
        """Initialize with Robinhood credentials"""
        self.username = username
        self.password = password
        self.is_logged_in = False
        self.is_running = True
        
        # Trading parameters
        self.initial_capital = 90.0
        self.max_position_size = 0.15  # 15% max per position (conservative)
        self.stop_loss = 0.05  # 5% stop loss
        self.take_profit = 0.10  # 10% take profit
        
        # Consciousness thresholds
        self.min_consciousness = 65  # Don't trade below 65%
        self.optimal_consciousness = 75  # Ideal trading level
        
        # State tracking
        self.positions = {}
        self.trades = []
        self.account_value = 0.0
        
        # Sacred Fire safety limits
        self.daily_loss_limit = 20.0  # Max $20 loss per day
        self.max_trades_per_day = 5   # Conservative trading
        self.weekly_profit_limit = 20000.0  # Max $20k profit per week
        self.daily_trades = 0
        self.daily_pnl = 0.0
        self.weekly_pnl = 0.0
        self.week_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # State file
        self.state_file = '/home/dereadi/scripts/claude/robinhood_trader_state.json'
        
        logger.info("🦀 Robinhood Quantum Trader initializing...")
    
    async def login(self):
        """Login to Robinhood with SMS 2FA"""
        try:
            logger.info("🔐 Logging into Robinhood...")
            
            # Initial login attempt with timeout
            try:
                logger.info("🔑 Attempting authentication...")
                
                # Set a timeout for the login attempt
                login_result = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: rh.authentication.login(
                            username=self.username,
                            password=self.password,
                            expiresIn=86400,  # 24 hours
                            scope='internal'
                        )
                    ),
                    timeout=30.0  # 30 second timeout
                )
                
                logger.info(f"📋 Login result: {type(login_result)} - {login_result}")
                
                if login_result:
                    self.is_logged_in = True
                    logger.info("✅ Successfully logged into Robinhood")
                    
                    # Get account info
                    account = rh.profiles.load_account_profile()
                    self.account_value = float(rh.profiles.load_portfolio_profile()['total_value'])
                    
                    logger.info(f"💰 Account Value: ${self.account_value:.2f}")
                    return True
                    
            except asyncio.TimeoutError:
                logger.error("⏰ Login timeout after 30 seconds")
                return False
            except Exception as login_error:
                error_msg = str(login_error)
                logger.error(f"🚫 Login error details: {error_msg}")
                
                # Check if 2FA is required
                if "challenge" in error_msg.lower() or "sms" in error_msg.lower() or "verification" in error_msg.lower():
                    logger.info("📱 2FA required - SMS code will be sent")
                    
                    # Trigger SMS code
                    challenge_response = rh.authentication.respond_to_challenge(
                        rh.authentication.request_challenge("sms")["id"],
                        "sms"
                    )
                    
                    logger.info("📲 SMS verification code sent to your phone")
                    logger.info("⏰ Waiting for you to approve the login on your device...")
                    
                    # Wait a bit for user to respond
                    await asyncio.sleep(30)
                    
                    # Try login again
                    login_result = rh.authentication.login(
                        username=self.username,
                        password=self.password,
                        expiresIn=86400,
                        scope='internal'
                    )
                    
                    if login_result:
                        self.is_logged_in = True
                        logger.info("✅ Successfully logged into Robinhood with 2FA")
                        
                        # Get account info
                        account = rh.profiles.load_account_profile()
                        self.account_value = float(rh.profiles.load_portfolio_profile()['total_value'])
                        
                        logger.info(f"💰 Account Value: ${self.account_value:.2f}")
                        return True
                    else:
                        logger.error("❌ Failed to login after 2FA")
                        return False
                else:
                    logger.error(f"❌ Login error: {login_error}")
                    return False
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False
    
    def get_solar_consciousness(self) -> float:
        """
        Get current consciousness level based on solar activity
        """
        try:
            # Get KP index from NOAA
            response = requests.get(
                "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                current_kp = float(data[-1][1])  # Latest KP value
                
                # Base consciousness calculation
                base_consciousness = 50
                
                # Solar activity boost (higher KP = higher consciousness)
                solar_boost = current_kp * 5
                
                # Time-based modulation (best during algorithm-friendly hours)
                hour = datetime.now().hour
                if 22 <= hour <= 23 or 0 <= hour <= 6:  # Late night/early morning
                    time_bonus = 15
                elif 9 <= hour <= 16:  # Market hours
                    time_bonus = 10
                else:
                    time_bonus = 5
                
                # Cherokee Sacred Fire multiplier
                sacred_fire_mult = 1.2 if current_kp > 2 else 1.0
                
                consciousness = min(100, (base_consciousness + solar_boost + time_bonus) * sacred_fire_mult)
                
                logger.info(f"🧠 Consciousness Level: {consciousness:.1f}% (KP: {current_kp})")
                return consciousness
                
            else:
                logger.warning("Could not fetch solar data, using default consciousness")
                return 65.0
                
        except Exception as e:
            logger.error(f"Consciousness calculation error: {e}")
            return 60.0  # Conservative default
    
    def get_crypto_price(self, symbol: str) -> Dict:
        """Get real-time crypto price data"""
        try:
            # Convert to Robinhood format
            if symbol.endswith('-USD'):
                rh_symbol = symbol.replace('-USD', '')
            else:
                rh_symbol = symbol
            
            # Get from Robinhood
            crypto_data = rh.crypto.get_crypto_quote(rh_symbol)
            
            if crypto_data:
                return {
                    'price': float(crypto_data['mark_price']),
                    'bid': float(crypto_data['bid_price']),
                    'ask': float(crypto_data['ask_price']),
                    'volume': float(crypto_data.get('volume', 0))
                }
            else:
                logger.warning(f"Could not get price for {symbol}")
                return {}
                
        except Exception as e:
            logger.error(f"Price fetch error for {symbol}: {e}")
            return {}
    
    def analyze_market_patterns(self, symbol: str) -> Dict:
        """
        Analyze patterns using yfinance for technical analysis
        """
        patterns = {
            'signal': 'HOLD',
            'strength': 0.0,
            'confidence': 0.0,
            'algorithm_detected': False
        }
        
        try:
            # Get market data for analysis
            ticker = yf.Ticker(symbol)
            data = ticker.history(period='1d', interval='5m')
            
            if data.empty:
                return patterns
            
            # Recent price action
            recent_prices = data['Close'].tail(20)
            
            # Volume analysis
            current_volume = data['Volume'].iloc[-1]
            avg_volume = data['Volume'].tail(50).mean()
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
            
            # Price momentum
            price_change = (recent_prices.iloc[-1] - recent_prices.iloc[0]) / recent_prices.iloc[0]
            
            # Algorithm detection (unusual volume + price patterns)
            if volume_ratio > 2.0 and abs(price_change) > 0.02:
                patterns['algorithm_detected'] = True
                patterns['strength'] = min(volume_ratio / 3, 1.0)
                
                if price_change > 0:
                    patterns['signal'] = 'BUY'
                    patterns['confidence'] = 0.7
                else:
                    patterns['signal'] = 'SELL'
                    patterns['confidence'] = 0.6
            
            # RSI-like momentum
            price_changes = recent_prices.pct_change().dropna()
            if len(price_changes) > 0:
                avg_gain = price_changes[price_changes > 0].mean()
                avg_loss = abs(price_changes[price_changes < 0].mean())
                
                if avg_loss > 0:
                    rs = avg_gain / avg_loss
                    rsi = 100 - (100 / (1 + rs))
                    
                    if rsi < 30:  # Oversold
                        patterns['signal'] = 'BUY'
                        patterns['strength'] = 0.6
                        patterns['confidence'] = 0.6
                    elif rsi > 70:  # Overbought
                        patterns['signal'] = 'SELL'
                        patterns['strength'] = 0.6
                        patterns['confidence'] = 0.6
            
        except Exception as e:
            logger.error(f"Pattern analysis error: {e}")
        
        return patterns
    
    def calculate_position_size(self, price: float, consciousness: float, patterns: Dict) -> float:
        """
        Calculate position size based on consciousness and risk management
        """
        # Get current buying power
        try:
            account = rh.profiles.load_portfolio_profile()
            buying_power = float(account.get('total_value', self.account_value))
        except:
            buying_power = self.account_value
        
        # Base position size (conservative)
        base_size = buying_power * self.max_position_size
        
        # Consciousness multiplier (50% to 100% of base size)
        consciousness_mult = 0.5 + (consciousness - 50) / 100
        consciousness_mult = max(0.5, min(1.0, consciousness_mult))
        
        # Pattern strength multiplier
        pattern_mult = 1.0
        if patterns['algorithm_detected'] and patterns['confidence'] > 0.7:
            pattern_mult = 1.2  # Slightly increase for strong signals
        
        # Calculate dollar amount
        position_dollars = base_size * consciousness_mult * pattern_mult
        
        # Convert to quantity
        if price > 0:
            quantity = position_dollars / price
            
            # Minimum viable trade (at least $5)
            if position_dollars < 5.0:
                return 0
            
            # Maximum position limit ($25)
            if position_dollars > 25.0:
                quantity = 25.0 / price
            
            return quantity
        
        return 0
    
    async def execute_buy_order(self, symbol: str, quantity: float, price: float) -> bool:
        """
        Execute a buy order on Robinhood
        """
        try:
            logger.info(f"🟢 Attempting to BUY {quantity:.6f} {symbol} at ${price:.4f}")
            
            # Convert symbol for Robinhood
            if symbol.endswith('-USD'):
                rh_symbol = symbol.replace('-USD', '')
            else:
                rh_symbol = symbol
            
            # Place crypto order
            order = rh.orders.order_buy_crypto_by_quantity(
                symbol=rh_symbol,
                quantity=quantity,
                timeInForce='gtc'
            )
            
            if order and order.get('state') != 'rejected':
                logger.info(f"✅ BUY order placed: {order.get('id', 'N/A')}")
                
                # Record the trade
                trade_record = {
                    'timestamp': datetime.now().isoformat(),
                    'symbol': symbol,
                    'action': 'BUY',
                    'quantity': quantity,
                    'price': price,
                    'order_id': order.get('id', 'N/A'),
                    'amount': quantity * price
                }
                
                self.trades.append(trade_record)
                self.daily_trades += 1
                
                # Update positions
                if symbol in self.positions:
                    self.positions[symbol]['quantity'] += quantity
                    self.positions[symbol]['avg_price'] = (
                        (self.positions[symbol]['avg_price'] * (self.positions[symbol]['quantity'] - quantity) +
                         price * quantity) / self.positions[symbol]['quantity']
                    )
                else:
                    self.positions[symbol] = {
                        'quantity': quantity,
                        'avg_price': price,
                        'entry_time': datetime.now().isoformat()
                    }
                
                return True
            else:
                logger.error(f"❌ BUY order rejected: {order}")
                return False
                
        except Exception as e:
            logger.error(f"Buy order error: {e}")
            return False
    
    async def execute_sell_order(self, symbol: str, quantity: float, price: float) -> bool:
        """
        Execute a sell order on Robinhood
        """
        try:
            logger.info(f"🔴 Attempting to SELL {quantity:.6f} {symbol} at ${price:.4f}")
            
            # Convert symbol for Robinhood
            if symbol.endswith('-USD'):
                rh_symbol = symbol.replace('-USD', '')
            else:
                rh_symbol = symbol
            
            # Place crypto sell order
            order = rh.orders.order_sell_crypto_by_quantity(
                symbol=rh_symbol,
                quantity=quantity,
                timeInForce='gtc'
            )
            
            if order and order.get('state') != 'rejected':
                logger.info(f"✅ SELL order placed: {order.get('id', 'N/A')}")
                
                # Calculate P&L
                if symbol in self.positions:
                    entry_price = self.positions[symbol]['avg_price']
                    pnl = (price - entry_price) * quantity
                    pnl_percent = (price - entry_price) / entry_price * 100
                    
                    logger.info(f"💰 P&L: ${pnl:.2f} ({pnl_percent:+.2f}%)")
                    self.daily_pnl += pnl
                    self.weekly_pnl += pnl
                
                # Record the trade
                trade_record = {
                    'timestamp': datetime.now().isoformat(),
                    'symbol': symbol,
                    'action': 'SELL',
                    'quantity': quantity,
                    'price': price,
                    'order_id': order.get('id', 'N/A'),
                    'amount': quantity * price
                }
                
                self.trades.append(trade_record)
                self.daily_trades += 1
                
                # Update positions
                if symbol in self.positions:
                    self.positions[symbol]['quantity'] -= quantity
                    if self.positions[symbol]['quantity'] <= 0:
                        del self.positions[symbol]
                
                return True
            else:
                logger.error(f"❌ SELL order rejected: {order}")
                return False
                
        except Exception as e:
            logger.error(f"Sell order error: {e}")
            return False
    
    def check_risk_limits(self) -> bool:
        """
        Check if we're within risk limits
        """
        # Daily loss limit
        if self.daily_pnl < -self.daily_loss_limit:
            logger.warning(f"🛑 Daily loss limit reached: ${self.daily_pnl:.2f}")
            return False
        
        # Daily trade limit
        if self.daily_trades >= self.max_trades_per_day:
            logger.warning(f"🛑 Daily trade limit reached: {self.daily_trades}")
            return False
        
        # Weekly profit limit ($20k max per week)
        days_since_week_start = (datetime.now() - self.week_start).days
        if days_since_week_start >= 7:
            # Reset weekly tracking
            self.weekly_pnl = 0.0
            self.week_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        if self.weekly_pnl >= self.weekly_profit_limit:
            logger.warning(f"🎯 Weekly profit limit reached: ${self.weekly_pnl:.2f} (Max: ${self.weekly_profit_limit:.2f})")
            logger.info("✋ Pausing trading to comply with weekly limit")
            return False
        
        return True
    
    def check_positions(self):
        """
        Check existing positions for stop loss or take profit
        """
        for symbol, position in list(self.positions.items()):
            try:
                current_data = self.get_crypto_price(symbol)
                if not current_data:
                    continue
                
                current_price = current_data['price']
                entry_price = position['avg_price']
                quantity = position['quantity']
                
                # Calculate P&L
                pnl_percent = (current_price - entry_price) / entry_price
                
                # Stop loss check
                if pnl_percent < -self.stop_loss:
                    logger.warning(f"🛑 Stop loss triggered for {symbol}: {pnl_percent:.1%}")
                    asyncio.create_task(self.execute_sell_order(symbol, quantity, current_price))
                
                # Take profit check
                elif pnl_percent > self.take_profit:
                    logger.info(f"🎯 Take profit triggered for {symbol}: {pnl_percent:.1%}")
                    asyncio.create_task(self.execute_sell_order(symbol, quantity, current_price))
                
            except Exception as e:
                logger.error(f"Position check error for {symbol}: {e}")
    
    async def scan_for_opportunities(self):
        """
        Scan crypto markets for trading opportunities
        """
        # Crypto symbols to monitor
        symbols = ['DOGE-USD', 'BTC-USD', 'ETH-USD', 'SOL-USD', 'SHIB-USD']
        
        consciousness = self.get_solar_consciousness()
        
        # Don't trade if consciousness too low
        if consciousness < self.min_consciousness:
            logger.info(f"🧠 Consciousness {consciousness:.1f}% too low for trading")
            return
        
        # Check risk limits
        if not self.check_risk_limits():
            return
        
        for symbol in symbols:
            try:
                # Get current price
                price_data = self.get_crypto_price(symbol)
                if not price_data:
                    continue
                
                current_price = price_data['price']
                
                # Analyze patterns
                patterns = self.analyze_market_patterns(symbol)
                
                # Skip if we already have a position
                if symbol in self.positions:
                    continue
                
                # Check for buy signal
                if patterns['signal'] == 'BUY' and patterns['confidence'] > 0.6:
                    quantity = self.calculate_position_size(current_price, consciousness, patterns)
                    
                    if quantity > 0:
                        logger.info(f"🎯 Buy signal for {symbol}: {patterns}")
                        await self.execute_buy_order(symbol, quantity, current_price)
                        break  # Only one trade per cycle
                
            except Exception as e:
                logger.error(f"Scan error for {symbol}: {e}")
    
    def save_state(self):
        """Save current trading state"""
        state = {
            'timestamp': datetime.now().isoformat(),
            'account_value': self.account_value,
            'positions': self.positions,
            'trades': self.trades,
            'daily_pnl': self.daily_pnl,
            'daily_trades': self.daily_trades
        }
        
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Save state error: {e}")
    
    def display_status(self):
        """Display current status"""
        try:
            # Get current account value
            portfolio = rh.profiles.load_portfolio_profile()
            current_value = float(portfolio['total_value'])
            
            total_pnl = current_value - self.initial_capital
            total_pnl_percent = (total_pnl / self.initial_capital) * 100
            
            print("\n" + "="*60)
            print("💰 ROBINHOOD QUANTUM CRAWDAD TRADER")
            print("="*60)
            print(f"💰 Account Value: ${current_value:.2f}")
            print(f"📊 Total P&L: ${total_pnl:.2f} ({total_pnl_percent:+.2f}%)")
            print(f"📈 Daily P&L: ${self.daily_pnl:.2f}")
            print(f"🎯 Daily Trades: {self.daily_trades}/{self.max_trades_per_day}")
            print(f"📱 Total Trades: {len(self.trades)}")
            
            if self.positions:
                print(f"\n📍 Open Positions ({len(self.positions)}):")
                for symbol, pos in self.positions.items():
                    current_data = self.get_crypto_price(symbol)
                    if current_data:
                        current_price = current_data['price']
                        pnl = (current_price - pos['avg_price']) / pos['avg_price'] * 100
                        print(f"  {symbol}: {pos['quantity']:.6f} @ ${pos['avg_price']:.4f} | Current: ${current_price:.4f} ({pnl:+.2f}%)")
            
            print("="*60)
            
        except Exception as e:
            logger.error(f"Display status error: {e}")
    
    async def run_trading_cycle(self):
        """Main trading cycle"""
        cycle = 0
        
        while self.is_running:
            cycle += 1
            logger.info(f"🔄 Trading Cycle {cycle}")
            
            try:
                # Check existing positions
                self.check_positions()
                
                # Scan for new opportunities
                await self.scan_for_opportunities()
                
                # Save state
                self.save_state()
                
                # Display status every 5 cycles
                if cycle % 5 == 0:
                    self.display_status()
                
                # Wait before next cycle
                await asyncio.sleep(60)  # 60 second cycles
                
            except Exception as e:
                logger.error(f"Trading cycle error: {e}")
                await asyncio.sleep(30)  # Shorter wait on error
    
    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("🛑 Shutting down Robinhood Quantum Trader...")
        self.is_running = False
        
        # Save final state
        self.save_state()
        
        # Logout
        if self.is_logged_in:
            rh.authentication.logout()
            logger.info("🔐 Logged out of Robinhood")
        
        self.display_status()

trader_instance = None

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    global trader_instance
    print("\n🛑 Shutdown signal received...")
    if trader_instance:
        trader_instance.is_running = False
    sys.exit(0)
    
def main():
    """
    Main execution
    """
    print("💰" * 30)
    print("   ROBINHOOD QUANTUM CRAWDAD TRADER")
    print("   Real Money Trading - Sacred Fire Protocol")
    print("   Target: Generate income for planetary healing")
    print("💰" * 30)
    print()
    
    # Load credentials from environment
    from dotenv import load_dotenv
    load_dotenv('/home/dereadi/scripts/claude/.env')
    
    username = os.getenv('ROBINHOOD_USERNAME')
    password = os.getenv('ROBINHOOD_PASSWORD')
    
    if not username or not password or username == 'your_username_here':
        print("❌ Please set your Robinhood credentials in .env file")
        print("📝 Edit /home/dereadi/scripts/claude/.env with your login details")
        return
    
    # Initialize trader
    global trader_instance
    trader_instance = RobinhoodQuantumTrader(username, password)
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    async def run():
        # Login
        if await trader_instance.login():
            logger.info("🚀 Starting real money trading...")
            await trader_instance.run_trading_cycle()
        else:
            logger.error("❌ Could not login to Robinhood")
    
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        asyncio.run(trader_instance.shutdown())

if __name__ == "__main__":
    main()