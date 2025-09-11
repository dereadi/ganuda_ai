#!/usr/bin/env python3
"""
Quantum Crawdad Paper Trading System
24-hour live paper trading with real market data
Cherokee Constitutional AI - Testing the Sacred Waters
"""

import yfinance as yf
import json
import time
import random
from datetime import datetime, timedelta
import threading
import os

class QuantumCrawdadPaperTrader:
    """
    Live paper trading system with real-time decision making
    """
    
    def __init__(self):
        self.mode = 'PAPER'
        self.initial_capital = 90
        self.capital = 90
        self.positions = {}
        self.trades = []
        self.active_threads = []
        self.running = True
        
        # Performance tracking
        self.metrics = {
            'start_time': datetime.now(),
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_pnl': 0,
            'best_trade': 0,
            'worst_trade': 0,
            'current_positions': 0,
            'win_rate': 0
        }
        
        # Trading parameters
        self.max_position_size = 9  # 10% of capital
        self.stop_loss_percent = 5
        self.take_profit_percent = 10
        self.confidence_threshold = 0.6
        
        # Tracked symbols
        self.symbols = [
            'BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD',
            'DOGE-USD', 'SHIB-USD', 'XRP-USD', 'AVAX-USD'
        ]
        
    def fetch_market_data(self, symbol):
        """Fetch real-time market data"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period='1d', interval='5m')
            
            if not hist.empty and len(hist) > 10:
                current_price = hist['Close'].iloc[-1]
                prev_price = hist['Close'].iloc[-10]
                high = hist['High'].max()
                low = hist['Low'].min()
                volume = hist['Volume'].sum()
                
                # Calculate indicators
                change_pct = ((current_price - prev_price) / prev_price * 100)
                volatility = ((high - low) / low * 100) if low > 0 else 0
                
                return {
                    'symbol': symbol,
                    'price': current_price,
                    'change': change_pct,
                    'volatility': volatility,
                    'volume': volume,
                    'high': high,
                    'low': low,
                    'timestamp': datetime.now()
                }
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
            return None
    
    def analyze_opportunity(self, data):
        """Analyze market data for trading opportunities"""
        if not data:
            return None
            
        signals = []
        
        # Momentum strategy
        if data['change'] > 2:
            signals.append({
                'strategy': 'momentum',
                'action': 'BUY',
                'confidence': min(0.9, 0.5 + data['change'] * 0.1),
                'reason': f"Strong momentum: {data['change']:.2f}% gain"
            })
        
        # Reversal strategy
        if data['change'] < -3:
            signals.append({
                'strategy': 'reversal',
                'action': 'BUY',
                'confidence': min(0.85, 0.5 + abs(data['change']) * 0.08),
                'reason': f"Oversold bounce: {data['change']:.2f}% drop"
            })
        
        # Volatility breakout
        if data['volatility'] > 5 and data['price'] > data['high'] * 0.95:
            signals.append({
                'strategy': 'breakout',
                'action': 'BUY',
                'confidence': 0.75,
                'reason': f"Volatility breakout: {data['volatility']:.2f}%"
            })
        
        # Check existing positions for exit signals
        if data['symbol'] in self.positions:
            position = self.positions[data['symbol']]
            pnl_pct = ((data['price'] - position['entry_price']) / position['entry_price'] * 100)
            
            if pnl_pct <= -self.stop_loss_percent:
                signals.append({
                    'strategy': 'stop_loss',
                    'action': 'SELL',
                    'confidence': 1.0,
                    'reason': f"Stop loss triggered: {pnl_pct:.2f}%"
                })
            elif pnl_pct >= self.take_profit_percent:
                signals.append({
                    'strategy': 'take_profit',
                    'action': 'SELL',
                    'confidence': 1.0,
                    'reason': f"Take profit triggered: {pnl_pct:.2f}%"
                })
        
        # Return highest confidence signal
        if signals:
            return max(signals, key=lambda x: x['confidence'])
        return None
    
    def execute_paper_trade(self, symbol, signal, market_data):
        """Execute a paper trade"""
        timestamp = datetime.now()
        
        if signal['action'] == 'BUY':
            # Check if we already have a position
            if symbol in self.positions:
                print(f"⚠️ Already have position in {symbol}")
                return
            
            # Calculate position size
            position_size = min(self.max_position_size, self.capital * 0.1)
            
            if position_size > self.capital:
                print(f"⚠️ Insufficient capital for {symbol}")
                return
            
            # Execute buy
            self.positions[symbol] = {
                'entry_price': market_data['price'],
                'size': position_size,
                'entry_time': timestamp,
                'strategy': signal['strategy']
            }
            
            self.capital -= position_size
            
            trade = {
                'timestamp': timestamp.isoformat(),
                'symbol': symbol,
                'action': 'BUY',
                'price': market_data['price'],
                'size': position_size,
                'reason': signal['reason'],
                'strategy': signal['strategy']
            }
            
            self.trades.append(trade)
            self.metrics['total_trades'] += 1
            self.metrics['current_positions'] += 1
            
            print(f"""
🦞 PAPER BUY: {symbol}
   Price: ${market_data['price']:.2f}
   Size: ${position_size:.2f}
   Strategy: {signal['strategy']}
   Reason: {signal['reason']}
            """)
            
        elif signal['action'] == 'SELL' and symbol in self.positions:
            position = self.positions[symbol]
            exit_price = market_data['price']
            
            # Calculate P&L
            pnl = (exit_price - position['entry_price']) / position['entry_price'] * position['size']
            pnl_pct = ((exit_price - position['entry_price']) / position['entry_price'] * 100)
            
            # Update metrics
            self.capital += position['size'] + pnl
            self.metrics['total_pnl'] += pnl
            
            if pnl > 0:
                self.metrics['winning_trades'] += 1
                self.metrics['best_trade'] = max(self.metrics['best_trade'], pnl)
            else:
                self.metrics['losing_trades'] += 1
                self.metrics['worst_trade'] = min(self.metrics['worst_trade'], pnl)
            
            # Remove position
            del self.positions[symbol]
            self.metrics['current_positions'] -= 1
            
            trade = {
                'timestamp': timestamp.isoformat(),
                'symbol': symbol,
                'action': 'SELL',
                'price': exit_price,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'reason': signal['reason'],
                'strategy': signal['strategy']
            }
            
            self.trades.append(trade)
            
            print(f"""
💰 PAPER SELL: {symbol}
   Exit Price: ${exit_price:.2f}
   P&L: ${pnl:.2f} ({pnl_pct:.2f}%)
   Reason: {signal['reason']}
            """)
    
    def trading_loop(self):
        """Main trading loop"""
        print("""
🦞 QUANTUM CRAWDAD PAPER TRADING STARTED
═══════════════════════════════════════════════════════════════════════════════════
Mode: PAPER TRADING (No Real Money)
Capital: $90
Target: 60% Win Rate
Duration: 24 Hours
═══════════════════════════════════════════════════════════════════════════════════
        """)
        
        scan_count = 0
        
        while self.running:
            scan_count += 1
            
            print(f"\n📊 Market Scan #{scan_count} - {datetime.now().strftime('%H:%M:%S')}")
            print(f"Capital: ${self.capital:.2f} | Positions: {len(self.positions)}")
            
            # Scan all symbols
            for symbol in self.symbols:
                # Fetch market data
                market_data = self.fetch_market_data(symbol)
                
                if market_data:
                    # Analyze for opportunities
                    signal = self.analyze_opportunity(market_data)
                    
                    if signal and signal['confidence'] >= self.confidence_threshold:
                        # Execute trade
                        self.execute_paper_trade(symbol, signal, market_data)
            
            # Update metrics
            self.update_metrics()
            
            # Display performance every 10 scans
            if scan_count % 10 == 0:
                self.display_performance()
            
            # Save state
            if scan_count % 5 == 0:
                self.save_state()
            
            # Wait before next scan (5 minutes)
            time.sleep(300)
    
    def update_metrics(self):
        """Update performance metrics"""
        total = self.metrics['winning_trades'] + self.metrics['losing_trades']
        if total > 0:
            self.metrics['win_rate'] = (self.metrics['winning_trades'] / total) * 100
    
    def display_performance(self):
        """Display current performance"""
        runtime = (datetime.now() - self.metrics['start_time']).total_seconds() / 3600
        
        print(f"""

📈 PERFORMANCE UPDATE
═══════════════════════════════════════════════════════════════════════════════════
Runtime: {runtime:.1f} hours
Total Trades: {self.metrics['total_trades']}
Win Rate: {self.metrics['win_rate']:.1f}%
P&L: ${self.metrics['total_pnl']:.2f}
Current Capital: ${self.capital:.2f} ({((self.capital/self.initial_capital-1)*100):.1f}%)
Active Positions: {self.metrics['current_positions']}
Best Trade: ${self.metrics['best_trade']:.2f}
Worst Trade: ${self.metrics['worst_trade']:.2f}
═══════════════════════════════════════════════════════════════════════════════════
        """)
        
        if self.metrics['win_rate'] >= 60:
            print("🎯 TARGET ACHIEVED! 60% win rate reached!")
    
    def save_state(self):
        """Save current trading state"""
        state = {
            'timestamp': datetime.now().isoformat(),
            'mode': self.mode,
            'capital': self.capital,
            'positions': self.positions,
            'metrics': self.metrics,
            'trades': self.trades[-100:]  # Last 100 trades
        }
        
        with open('paper_trading_state.json', 'w') as f:
            json.dump(state, f, indent=2, default=str)
    
    def stop_trading(self):
        """Stop trading and generate final report"""
        self.running = False
        
        print("""

🏁 PAPER TRADING COMPLETE
═══════════════════════════════════════════════════════════════════════════════════
        """)
        
        self.display_performance()
        
        # Close all positions at market
        for symbol in list(self.positions.keys()):
            market_data = self.fetch_market_data(symbol)
            if market_data:
                self.execute_paper_trade(symbol, {
                    'action': 'SELL',
                    'strategy': 'close_all',
                    'confidence': 1.0,
                    'reason': 'End of paper trading'
                }, market_data)
        
        # Final report
        print(f"""

📊 FINAL REPORT
═══════════════════════════════════════════════════════════════════════════════════
Initial Capital: ${self.initial_capital:.2f}
Final Capital: ${self.capital:.2f}
Total Return: {((self.capital/self.initial_capital-1)*100):.2f}%
Win Rate: {self.metrics['win_rate']:.1f}%
Total Trades: {self.metrics['total_trades']}

RECOMMENDATION: {"✅ READY FOR LIVE TRADING" if self.metrics['win_rate'] >= 60 else "⚠️ MORE TESTING NEEDED"}
═══════════════════════════════════════════════════════════════════════════════════
        """)
        
        self.save_state()

def start_paper_trading():
    """Start the paper trading system"""
    trader = QuantumCrawdadPaperTrader()
    
    # Start trading in background thread
    trading_thread = threading.Thread(target=trader.trading_loop, daemon=True)
    trading_thread.start()
    
    print("""
Commands:
  'status' - Show current performance
  'positions' - Show open positions
  'stop' - Stop trading and exit
    """)
    
    # Command loop
    while trader.running:
        try:
            cmd = input("\n> ").strip().lower()
            
            if cmd == 'status':
                trader.display_performance()
            elif cmd == 'positions':
                if trader.positions:
                    print("\n📊 OPEN POSITIONS:")
                    for symbol, pos in trader.positions.items():
                        print(f"  {symbol}: ${pos['size']:.2f} @ ${pos['entry_price']:.2f}")
                else:
                    print("No open positions")
            elif cmd == 'stop':
                trader.stop_trading()
                break
        except KeyboardInterrupt:
            trader.stop_trading()
            break
    
    return trader

if __name__ == "__main__":
    print("""
🦞 QUANTUM CRAWDAD PAPER TRADING SYSTEM
═══════════════════════════════════════════════════════════════════════════════════
Starting 24-hour paper trading test as ordered by Cherokee Council
All safety features active - No real money at risk
═══════════════════════════════════════════════════════════════════════════════════
    """)
    
    trader = start_paper_trading()