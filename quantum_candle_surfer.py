#!/usr/bin/env python3
"""
🕯️🦀 QUANTUM CANDLE SURFER
===========================
Day trading on the second-by-second waves
"""

import json
import time
import threading
from datetime import datetime, timedelta
from collections import deque
from coinbase.rest import RESTClient

class CandleSurferCrawdad:
    def __init__(self, name, symbol, capital):
        self.name = name
        self.symbol = symbol
        self.capital = capital
        self.position = 0
        self.trades = []
        self.price_history = deque(maxlen=60)  # 60 seconds
        self.candles = deque(maxlen=20)  # Last 20 candles
        
    def analyze_micro_trend(self):
        """Detect micro trends in seconds"""
        if len(self.price_history) < 5:
            return "NEUTRAL"
        
        # Calculate micro momentum
        recent = list(self.price_history)[-5:]
        older = list(self.price_history)[-10:-5] if len(self.price_history) >= 10 else recent
        
        recent_avg = sum(recent) / len(recent)
        older_avg = sum(older) / len(older)
        
        momentum = ((recent_avg - older_avg) / older_avg) * 100
        
        if momentum > 0.05:  # 0.05% up = micro bull
            return "MICRO_BULL"
        elif momentum < -0.05:  # 0.05% down = micro bear
            return "MICRO_BEAR"
        else:
            return "RANGING"
    
    def detect_candle_pattern(self):
        """Detect micro candle patterns"""
        if len(self.candles) < 3:
            return None
        
        last_3 = list(self.candles)[-3:]
        
        # Micro hammer (reversal up)
        if last_3[-1]['low'] < last_3[-2]['low'] and last_3[-1]['close'] > last_3[-1]['open']:
            return "MICRO_HAMMER"
        
        # Micro shooting star (reversal down)
        if last_3[-1]['high'] > last_3[-2]['high'] and last_3[-1]['close'] < last_3[-1]['open']:
            return "SHOOTING_STAR"
        
        # Three white soldiers (strong up)
        if all(c['close'] > c['open'] for c in last_3):
            return "BULL_RUN"
        
        # Three black crows (strong down)
        if all(c['close'] < c['open'] for c in last_3):
            return "BEAR_RAID"
        
        return None

class QuantumCandleSurfing:
    def __init__(self):
        # Load config
        config_path = "/home/dereadi/.coinbase_config.json"
        with open(config_path) as f:
            self.config = json.load(f)
        
        self.client = RESTClient(
            api_key=self.config["api_key"],
            api_secret=self.config["api_secret"]
        )
        
        # Create specialized surfer crawdads
        self.surfers = [
            CandleSurferCrawdad("Lightning", "SOL", 50),  # Fast scalper
            CandleSurferCrawdad("Wave", "ETH", 50),      # Trend rider
            CandleSurferCrawdad("Pulse", "BTC", 50),     # Steady trader
        ]
        
        self.running = False
        self.total_trades = 0
        self.profitable_trades = 0
        
    def get_ticker(self, symbol):
        """Get real-time price"""
        try:
            ticker = self.client.get_product(f"{symbol}-USD")
            if ticker:
                return {
                    'price': float(ticker.get('price', 0)),
                    'bid': float(ticker.get('bid', 0)),
                    'ask': float(ticker.get('ask', 0)),
                    'volume': float(ticker.get('volume_24h', 0))
                }
        except:
            pass
        return None
    
    def create_micro_candle(self, prices, timeframe=5):
        """Create a micro candle from price data"""
        if not prices:
            return None
        
        return {
            'open': prices[0],
            'high': max(prices),
            'low': min(prices),
            'close': prices[-1],
            'volume': len(prices),
            'time': datetime.now().isoformat()
        }
    
    def execute_micro_trade(self, surfer, action, size_pct=0.1):
        """Execute a micro trade (10% of allocated capital)"""
        trade_size = surfer.capital * size_pct
        
        if trade_size < 10:  # Minimum $10
            return None
        
        ticker = self.get_ticker(surfer.symbol)
        if not ticker:
            return None
        
        print(f"  🏄 {surfer.name} {action} ${trade_size:.2f} {surfer.symbol} @ ${ticker['price']:,.2f}")
        
        try:
            if action == "BUY":
                order = self.client.market_order_buy(
                    client_order_id=f"surf_{surfer.name}_{int(time.time()*1000)}",
                    product_id=f"{surfer.symbol}-USD",
                    quote_size=str(round(trade_size, 2))
                )
            else:  # SELL
                # Calculate base size
                base_size = trade_size / ticker['price']
                order = self.client.market_order_sell(
                    client_order_id=f"surf_{surfer.name}_{int(time.time()*1000)}",
                    product_id=f"{surfer.symbol}-USD",
                    base_size=str(round(base_size, 8))
                )
            
            if order:
                self.total_trades += 1
                surfer.trades.append({
                    'action': action,
                    'price': ticker['price'],
                    'size': trade_size,
                    'time': datetime.now().isoformat()
                })
                return order
                
        except Exception as e:
            print(f"    ❌ Trade failed: {e}")
        
        return None
    
    def surf_the_candles(self):
        """Main surfing loop - ride the micro waves"""
        
        print("\n🏄 CANDLE SURFING ACTIVE")
        print("="*60)
        
        cycle = 0
        last_prices = {}
        
        while self.running:
            cycle += 1
            
            # Collect price data every second
            for surfer in self.surfers:
                ticker = self.get_ticker(surfer.symbol)
                if ticker:
                    price = ticker['price']
                    surfer.price_history.append(price)
                    
                    # Create 5-second candles
                    if cycle % 5 == 0 and len(surfer.price_history) >= 5:
                        candle = self.create_micro_candle(list(surfer.price_history)[-5:])
                        if candle:
                            surfer.candles.append(candle)
            
            # Make trading decisions every 5 seconds
            if cycle % 5 == 0:
                print(f"\n🕯️ Cycle {cycle//5} - {datetime.now().strftime('%H:%M:%S')}")
                
                for surfer in self.surfers:
                    if len(surfer.price_history) < 10:
                        continue
                    
                    # Get current price
                    current_price = surfer.price_history[-1]
                    
                    # Analyze micro conditions
                    trend = surfer.analyze_micro_trend()
                    pattern = surfer.detect_candle_pattern()
                    
                    # Trading logic
                    action = None
                    
                    if pattern == "MICRO_HAMMER" and trend != "MICRO_BEAR":
                        action = "BUY"  # Reversal up
                    elif pattern == "SHOOTING_STAR" and trend != "MICRO_BULL":
                        action = "SELL"  # Reversal down
                    elif pattern == "BULL_RUN" and trend == "MICRO_BULL":
                        action = "BUY"  # Momentum up
                    elif pattern == "BEAR_RAID" and trend == "MICRO_BEAR":
                        action = "SELL"  # Momentum down
                    elif trend == "RANGING" and surfer.position != 0:
                        # Close positions in ranging market
                        action = "SELL" if surfer.position > 0 else "BUY"
                    
                    # Execute if action determined
                    if action:
                        self.execute_micro_trade(surfer, action, 0.05)  # 5% trades for safety
                        
                        # Update position
                        if action == "BUY":
                            surfer.position += 1
                        else:
                            surfer.position -= 1
                    
                    # Display status
                    if pattern or trend != "NEUTRAL":
                        print(f"  📊 {surfer.name}: {trend} | Pattern: {pattern}")
            
            # Performance update every minute
            if cycle % 60 == 0:
                print(f"\n📈 PERFORMANCE UPDATE:")
                print(f"  Total trades: {self.total_trades}")
                win_rate = (self.profitable_trades / self.total_trades * 100) if self.total_trades > 0 else 0
                print(f"  Win rate: {win_rate:.1f}%")
            
            time.sleep(1)  # Check every second
    
    def start(self):
        """Start the candle surfing system"""
        self.running = True
        
        print("\n🕯️🦀 QUANTUM CANDLE SURFER")
        print("="*60)
        print("Strategy: Surf micro price waves")
        print("Timeframe: 1-5 second candles")
        print("Risk: 5% per trade")
        print("="*60)
        
        # Start surfing in thread
        surf_thread = threading.Thread(target=self.surf_the_candles)
        surf_thread.daemon = True
        surf_thread.start()
        
        print("\n🏄 Surfer Crawdads Deployed:")
        for surfer in self.surfers:
            print(f"  • {surfer.name}: ${surfer.capital} on {surfer.symbol}")
        
        print("\n⚡ Watching for:")
        print("  • Micro hammers (reversal up)")
        print("  • Shooting stars (reversal down)")
        print("  • Three white soldiers (bull run)")
        print("  • Three black crows (bear raid)")
        
        print("\nPress Ctrl+C to stop surfing...")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.running = False
            print("\n\n🛑 Surfing stopped")
            print(f"Total micro trades: {self.total_trades}")

if __name__ == "__main__":
    surfer = QuantumCandleSurfing()
    surfer.start()