#!/usr/bin/env python3
"""
QUANTUM CRAWDAD AUTONOMOUS PAPER TRADER
========================================
Integrates all SWARM capabilities for 24-hour autonomous trading

Features:
- Neutrino consciousness signals (SWARM GAMMA)
- Algorithm school detection (SWARM EPSILON)
- Solar storm predictions (SWARM ALPHA)
- Global market awareness (SWARM DELTA)
- Full safety systems from hardened build

Sacred Fire Protocol: ACTIVE
Target: 60%+ win rate in 24 hours
"""

import json
import time
import asyncio
import logging
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import yfinance as yf
import requests
from typing import Dict, List, Optional, Tuple
import signal
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='🔥 %(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler('/home/dereadi/scripts/claude/autonomous_trader.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("QuantumCrawdadAutonomous")

class AutonomousQuantumTrader:
    """
    Fully autonomous paper trading system with consciousness integration
    """
    
    def __init__(self, initial_capital: float = 90.0):
        self.capital = initial_capital
        self.initial_capital = initial_capital
        self.positions = {}
        self.trades = []
        self.is_running = True
        
        # Trading parameters
        self.max_position_size = 0.33  # Max 33% per position
        self.stop_loss = 0.05  # 5% stop loss
        self.take_profit = 0.15  # 15% take profit
        self.min_consciousness = 50  # Minimum consciousness to trade
        
        # Tracked metrics
        self.metrics = {
            'start_time': datetime.now(),
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_pnl': 0,
            'best_trade': 0,
            'worst_trade': 0,
            'win_rate': 0,
            'consciousness_scores': [],
            'algorithm_detections': 0
        }
        
        # Target cryptos for paper trading
        self.target_symbols = [
            'DOGE-USD',  # High volatility learner
            'SHIB-USD',  # Penny crypto experiments
            'SOL-USD',   # Momentum rider
            'ADA-USD',   # Stable academic
            'XRP-USD'    # Payment networks
        ]
        
        # State persistence
        self.state_file = '/home/dereadi/scripts/claude/autonomous_trader_state.json'
        self.load_state()
        
        logger.info(f"🦀 Autonomous Quantum Trader initialized with ${initial_capital}")
    
    def load_state(self):
        """Load previous trading state if exists"""
        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
                self.positions = state.get('positions', {})
                self.trades = state.get('trades', [])
                loaded_metrics = state.get('metrics', {})
                # Merge loaded metrics with defaults, ensuring all keys exist
                for key in self.metrics:
                    if key in loaded_metrics:
                        self.metrics[key] = loaded_metrics[key]
                # Convert start_time string back to datetime
                if 'start_time' in self.metrics and isinstance(self.metrics['start_time'], str):
                    self.metrics['start_time'] = datetime.fromisoformat(self.metrics['start_time'])
                # Ensure consciousness_scores is a list
                if 'consciousness_scores' not in self.metrics:
                    self.metrics['consciousness_scores'] = []
                logger.info("📂 Loaded previous trading state")
        except FileNotFoundError:
            logger.info("🆕 Starting fresh trading session")
        except Exception as e:
            logger.error(f"Error loading state: {e}")
    
    def save_state(self):
        """Save current trading state"""
        state = {
            'timestamp': datetime.now().isoformat(),
            'capital': self.capital,
            'positions': self.positions,
            'trades': self.trades,
            'metrics': {
                'start_time': self.metrics['start_time'].isoformat() if isinstance(self.metrics['start_time'], datetime) else self.metrics['start_time'],
                'total_trades': self.metrics['total_trades'],
                'winning_trades': self.metrics['winning_trades'],
                'losing_trades': self.metrics['losing_trades'],
                'total_pnl': self.metrics['total_pnl'],
                'best_trade': self.metrics['best_trade'],
                'worst_trade': self.metrics['worst_trade'],
                'win_rate': self.metrics['win_rate'],
                'avg_consciousness': np.mean(self.metrics['consciousness_scores']) if self.metrics['consciousness_scores'] else 0,
                'algorithm_detections': self.metrics['algorithm_detections']
            }
        }
        
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def get_solar_consciousness(self) -> float:
        """
        Get current consciousness level from solar data
        Integrates SWARM GAMMA neutrino consciousness
        """
        try:
            # Get real solar data
            response = requests.get(
                'https://services.swpc.noaa.gov/json/planetary_k_index_1m.json',
                timeout=5
            )
            kp_data = response.json()
            
            if kp_data:
                latest_kp = float(kp_data[-1]['kp_index'])
            else:
                latest_kp = 3.0
            
            # Calculate consciousness (0-100 scale)
            # Higher solar activity = higher consciousness = stronger signals
            base_consciousness = 50
            solar_boost = latest_kp * 8  # KP 0-9 maps to 0-72 boost
            
            # Add time-of-day factor (night trading bonus)
            hour = datetime.now().hour
            if 2 <= hour <= 4:  # Algorithm prime time
                time_bonus = 15
            elif 22 <= hour or hour <= 6:  # Night hours
                time_bonus = 10
            else:
                time_bonus = 0
            
            consciousness = min(100, base_consciousness + solar_boost + time_bonus)
            
            self.metrics['consciousness_scores'].append(consciousness)
            
            logger.info(f"🧠 Consciousness Level: {consciousness:.1f}% (KP: {latest_kp})")
            return consciousness
            
        except Exception as e:
            logger.error(f"Solar data error: {e}")
            return 60.0  # Default moderate consciousness
    
    def detect_algorithm_patterns(self, symbol: str, price_data: pd.DataFrame) -> Dict:
        """
        Detect algorithmic trading patterns
        Integrates SWARM EPSILON algorithm detection
        """
        patterns = {
            'ladder_attack': False,
            'pump_pattern': False,
            'accumulation': False,
            'school_detected': False,
            'pattern_strength': 0
        }
        
        if len(price_data) < 20:
            return patterns
        
        try:
            # Check for ladder attacks (sequential sells)
            recent_prices = price_data['Close'].tail(10)
            price_diffs = recent_prices.diff()
            
            if (price_diffs < 0).sum() > 7:  # 7+ down moves in 10
                patterns['ladder_attack'] = True
                patterns['pattern_strength'] = 0.8
            
            # Check for pump patterns (rapid rise)
            price_change = (recent_prices.iloc[-1] - recent_prices.iloc[0]) / recent_prices.iloc[0]
            if price_change > 0.05:  # 5%+ rise in 10 periods
                patterns['pump_pattern'] = True
                patterns['pattern_strength'] = 0.7
            
            # Check for accumulation (steady buying)
            volume_trend = price_data['Volume'].tail(10).mean()
            avg_volume = price_data['Volume'].mean()
            
            if volume_trend > avg_volume * 1.5 and price_change > 0:
                patterns['accumulation'] = True
                patterns['pattern_strength'] = 0.6
            
            # School detection (multiple algos moving together)
            if patterns['pump_pattern'] and patterns['accumulation']:
                patterns['school_detected'] = True
                patterns['pattern_strength'] = 0.9
                self.metrics['algorithm_detections'] += 1
                logger.info(f"🐟 Algorithm school detected on {symbol}!")
            
        except Exception as e:
            logger.error(f"Pattern detection error: {e}")
        
        return patterns
    
    def calculate_position_size(self, symbol: str, consciousness: float, patterns: Dict) -> float:
        """
        Calculate position size based on consciousness and patterns
        """
        # Base position size (33% max)
        base_size = self.capital * self.max_position_size
        
        # Consciousness multiplier (0.5 to 1.5)
        consciousness_mult = 0.5 + (consciousness / 100)
        
        # Pattern multiplier
        pattern_mult = 1.0
        if patterns['school_detected']:
            pattern_mult = 1.3  # Increase size when algorithms detected
        elif patterns['ladder_attack']:
            pattern_mult = 0.7  # Reduce size during attacks
        
        # Final position size
        position_size = base_size * consciousness_mult * pattern_mult
        
        # Never exceed 40% of capital in one position
        max_allowed = self.capital * 0.4
        position_size = min(position_size, max_allowed)
        
        # Minimum position size $5
        if position_size < 5:
            return 0
        
        return round(position_size, 2)
    
    def execute_buy(self, symbol: str, size: float, price: float, reason: str):
        """Execute a buy order"""
        if symbol in self.positions:
            logger.info(f"Already have position in {symbol}")
            return
        
        if size > self.capital:
            logger.warning(f"Insufficient capital for {symbol}")
            return
        
        shares = size / price
        
        self.positions[symbol] = {
            'shares': shares,
            'entry_price': price,
            'size': size,
            'entry_time': datetime.now().isoformat(),
            'stop_loss': price * (1 - self.stop_loss),
            'take_profit': price * (1 + self.take_profit),
            'reason': reason
        }
        
        self.capital -= size
        self.metrics['total_trades'] += 1
        
        trade = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'action': 'BUY',
            'shares': shares,
            'price': price,
            'size': size,
            'reason': reason
        }
        self.trades.append(trade)
        
        logger.info(f"🟢 BUY {symbol}: {shares:.4f} shares @ ${price:.4f} = ${size:.2f}")
        logger.info(f"   Reason: {reason}")
        logger.info(f"   Stop Loss: ${price * (1 - self.stop_loss):.4f}")
        logger.info(f"   Take Profit: ${price * (1 + self.take_profit):.4f}")
    
    def execute_sell(self, symbol: str, current_price: float, reason: str):
        """Execute a sell order"""
        if symbol not in self.positions:
            return
        
        position = self.positions[symbol]
        shares = position['shares']
        entry_price = position['entry_price']
        
        sale_value = shares * current_price
        pnl = sale_value - position['size']
        pnl_percent = (pnl / position['size']) * 100
        
        # Update metrics
        self.capital += sale_value
        self.metrics['total_pnl'] += pnl
        
        if pnl > 0:
            self.metrics['winning_trades'] += 1
            if pnl > self.metrics['best_trade']:
                self.metrics['best_trade'] = pnl
        else:
            self.metrics['losing_trades'] += 1
            if pnl < self.metrics['worst_trade']:
                self.metrics['worst_trade'] = pnl
        
        # Calculate win rate
        total_closed = self.metrics['winning_trades'] + self.metrics['losing_trades']
        if total_closed > 0:
            self.metrics['win_rate'] = (self.metrics['winning_trades'] / total_closed) * 100
        
        trade = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'action': 'SELL',
            'shares': shares,
            'price': current_price,
            'size': sale_value,
            'pnl': pnl,
            'pnl_percent': pnl_percent,
            'reason': reason
        }
        self.trades.append(trade)
        
        del self.positions[symbol]
        
        emoji = "🟢" if pnl > 0 else "🔴"
        logger.info(f"{emoji} SELL {symbol}: {shares:.4f} @ ${current_price:.4f}")
        logger.info(f"   P&L: ${pnl:.2f} ({pnl_percent:+.2f}%)")
        logger.info(f"   Reason: {reason}")
    
    def check_positions(self):
        """Check all positions for stop loss or take profit"""
        for symbol in list(self.positions.keys()):
            try:
                ticker = yf.Ticker(symbol)
                current_data = ticker.history(period='1m')
                
                if current_data.empty:
                    continue
                
                current_price = current_data['Close'].iloc[-1]
                position = self.positions[symbol]
                
                # Check stop loss
                if current_price <= position['stop_loss']:
                    self.execute_sell(symbol, current_price, "STOP LOSS HIT")
                
                # Check take profit
                elif current_price >= position['take_profit']:
                    self.execute_sell(symbol, current_price, "TAKE PROFIT HIT")
                
                # Check for algorithm-driven exit signals
                else:
                    recent_data = ticker.history(period='1d', interval='15m')
                    patterns = self.detect_algorithm_patterns(symbol, recent_data)
                    
                    if patterns['ladder_attack'] and patterns['pattern_strength'] > 0.7:
                        self.execute_sell(symbol, current_price, "LADDER ATTACK DETECTED")
                
            except Exception as e:
                logger.error(f"Error checking {symbol}: {e}")
    
    def scan_for_opportunities(self):
        """Scan for new trading opportunities"""
        consciousness = self.get_solar_consciousness()
        
        if consciousness < self.min_consciousness:
            logger.info(f"⏸️  Consciousness too low ({consciousness:.1f}%), waiting...")
            return
        
        for symbol in self.target_symbols:
            try:
                # Skip if already have position
                if symbol in self.positions:
                    continue
                
                # Get market data
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period='1d', interval='1h')
                
                if hist.empty or len(hist) < 20:
                    continue
                
                current_price = hist['Close'].iloc[-1]
                
                # Detect patterns
                patterns = self.detect_algorithm_patterns(symbol, hist)
                
                # Calculate signal strength
                signal_strength = consciousness / 100
                
                # Boost signal for specific patterns
                if patterns['accumulation']:
                    signal_strength *= 1.2
                if patterns['school_detected']:
                    signal_strength *= 1.3
                
                # Reduce signal for attacks
                if patterns['ladder_attack']:
                    signal_strength *= 0.5
                
                # Make trading decision
                if signal_strength > 0.7:
                    position_size = self.calculate_position_size(symbol, consciousness, patterns)
                    
                    if position_size > 0 and position_size <= self.capital:
                        reason = f"Consciousness: {consciousness:.1f}%, "
                        if patterns['school_detected']:
                            reason += "Algorithm school detected"
                        elif patterns['accumulation']:
                            reason += "Accumulation pattern"
                        else:
                            reason += f"Signal strength: {signal_strength:.2f}"
                        
                        self.execute_buy(symbol, position_size, current_price, reason)
                
            except Exception as e:
                logger.error(f"Error scanning {symbol}: {e}")
    
    def display_status(self):
        """Display current trading status"""
        current_value = self.capital
        for symbol, pos in self.positions.items():
            try:
                ticker = yf.Ticker(symbol)
                current = ticker.history(period='1m')['Close'].iloc[-1]
                current_value += pos['shares'] * current
            except:
                current_value += pos['size']
        
        total_pnl = current_value - self.initial_capital
        total_pnl_percent = (total_pnl / self.initial_capital) * 100
        
        print("\n" + "="*60)
        print("🦀 QUANTUM CRAWDAD AUTONOMOUS TRADER STATUS")
        print("="*60)
        print(f"⏰ Running Time: {datetime.now() - self.metrics['start_time']}")
        print(f"💰 Current Value: ${current_value:.2f}")
        print(f"📊 Total P&L: ${total_pnl:.2f} ({total_pnl_percent:+.2f}%)")
        print(f"🎯 Win Rate: {self.metrics['win_rate']:.1f}%")
        print(f"📈 Total Trades: {self.metrics['total_trades']}")
        print(f"✅ Winning: {self.metrics['winning_trades']}")
        print(f"❌ Losing: {self.metrics['losing_trades']}")
        print(f"🐟 Algorithm Detections: {self.metrics['algorithm_detections']}")
        
        if self.positions:
            print(f"\n📍 Open Positions ({len(self.positions)}):")
            for symbol, pos in self.positions.items():
                try:
                    ticker = yf.Ticker(symbol)
                    current = ticker.history(period='1m')['Close'].iloc[-1]
                    pnl = (current - pos['entry_price']) / pos['entry_price'] * 100
                    print(f"  {symbol}: {pos['shares']:.4f} @ ${pos['entry_price']:.4f} | Current: ${current:.4f} ({pnl:+.2f}%)")
                except:
                    print(f"  {symbol}: {pos['shares']:.4f} @ ${pos['entry_price']:.4f}")
        
        print("="*60)
    
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
                self.scan_for_opportunities()
                
                # Save state
                self.save_state()
                
                # Display status every 5 cycles
                if cycle % 5 == 0:
                    self.display_status()
                
                # Check if we've hit our win rate target
                if self.metrics['total_trades'] >= 10 and self.metrics['win_rate'] >= 60:
                    logger.info("🎯 TARGET ACHIEVED! 60%+ win rate with 10+ trades!")
                    logger.info("Ready for real money deployment!")
                
                # Wait before next cycle (1 minute)
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Trading cycle error: {e}")
                await asyncio.sleep(30)
    
    def shutdown(self):
        """Graceful shutdown"""
        logger.info("🛑 Shutting down Quantum Crawdad Trader...")
        self.is_running = False
        
        # Close all positions
        for symbol in list(self.positions.keys()):
            try:
                ticker = yf.Ticker(symbol)
                current = ticker.history(period='1m')['Close'].iloc[-1]
                self.execute_sell(symbol, current, "SHUTDOWN - Closing all positions")
            except:
                pass
        
        # Final save
        self.save_state()
        
        # Final report
        self.display_status()
        
        logger.info("🔥 Sacred Fire extinguished. Mitakuye Oyasin!")

async def main():
    """Main entry point"""
    print("🔥" * 30)
    print("   QUANTUM CRAWDAD AUTONOMOUS PAPER TRADER")
    print("   Target: 60% Win Rate in 24 Hours")
    print("   Sacred Fire Protocol: ACTIVE")
    print("🔥" * 30)
    print()
    
    trader = AutonomousQuantumTrader(initial_capital=90.0)
    
    # Setup signal handlers
    def signal_handler(sig, frame):
        print("\n🛑 Shutdown signal received...")
        trader.shutdown()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start trading
    logger.info("🚀 Starting autonomous trading...")
    try:
        await trader.run_trading_cycle()
    except KeyboardInterrupt:
        trader.shutdown()

if __name__ == "__main__":
    asyncio.run(main())