#!/usr/bin/env python3
"""
Quantum Crawdad Trading View
Interactive web dashboard with TradingView-style charts
Cherokee Constitutional AI - Visual Trading Interface
"""

from flask import Flask, render_template, jsonify, request
import yfinance as yf
import json
from datetime import datetime, timedelta
import threading
import time

app = Flask(__name__)

class CrawdadTradingView:
    def __init__(self):
        self.symbols = [
            'BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD',
            'DOGE-USD', 'SHIB-USD', 'XRP-USD', 'AVAX-USD'
        ]
        self.market_data = {}
        self.trade_history = []
        self.signals = []
        self.running = True
        
        # Start background data fetcher
        self.start_data_fetcher()
    
    def start_data_fetcher(self):
        """Continuously fetch market data in background"""
        def fetch_loop():
            while self.running:
                for symbol in self.symbols:
                    self.update_market_data(symbol)
                time.sleep(60)  # Update every minute
        
        thread = threading.Thread(target=fetch_loop, daemon=True)
        thread.start()
    
    def update_market_data(self, symbol):
        """Fetch and store market data for a symbol"""
        try:
            ticker = yf.Ticker(symbol)
            
            # Get different timeframes
            data_5m = ticker.history(period='1d', interval='5m')
            data_1h = ticker.history(period='5d', interval='1h')
            data_1d = ticker.history(period='1mo', interval='1d')
            
            if not data_5m.empty:
                current_price = data_5m['Close'].iloc[-1]
                prev_price = data_5m['Close'].iloc[-2] if len(data_5m) > 1 else current_price
                
                self.market_data[symbol] = {
                    'current_price': current_price,
                    'change': ((current_price - prev_price) / prev_price * 100),
                    'volume': data_5m['Volume'].sum(),
                    'high_24h': data_5m['High'].max(),
                    'low_24h': data_5m['Low'].min(),
                    'last_update': datetime.now().isoformat(),
                    'candles_5m': self.format_candles(data_5m),
                    'candles_1h': self.format_candles(data_1h),
                    'candles_1d': self.format_candles(data_1d)
                }
                
                # Check for signals
                self.analyze_for_signals(symbol, self.market_data[symbol])
                
        except Exception as e:
            print(f"Error updating {symbol}: {e}")
    
    def format_candles(self, data):
        """Format candlestick data for charts"""
        candles = []
        for index, row in data.iterrows():
            candles.append({
                'time': index.isoformat(),
                'open': float(row['Open']),
                'high': float(row['High']),
                'low': float(row['Low']),
                'close': float(row['Close']),
                'volume': float(row['Volume'])
            })
        return candles
    
    def analyze_for_signals(self, symbol, data):
        """Analyze for trading signals"""
        change = data['change']
        
        # Detect signals (both positive and negative)
        signal = None
        
        if change > 3:
            signal = {
                'type': 'STRONG_BUY',
                'symbol': symbol,
                'price': data['current_price'],
                'change': change,
                'reason': f'Strong momentum: +{change:.2f}%',
                'timestamp': datetime.now().isoformat(),
                'sentiment': 'bullish'
            }
        elif change > 2:
            signal = {
                'type': 'BUY',
                'symbol': symbol,
                'price': data['current_price'],
                'change': change,
                'reason': f'Momentum detected: +{change:.2f}%',
                'timestamp': datetime.now().isoformat(),
                'sentiment': 'bullish'
            }
        elif change < -3:
            signal = {
                'type': 'OVERSOLD',
                'symbol': symbol,
                'price': data['current_price'],
                'change': change,
                'reason': f'Oversold condition: {change:.2f}%',
                'timestamp': datetime.now().isoformat(),
                'sentiment': 'bearish'
            }
        elif change < -2:
            signal = {
                'type': 'WATCH',
                'symbol': symbol,
                'price': data['current_price'],
                'change': change,
                'reason': f'Decline detected: {change:.2f}%',
                'timestamp': datetime.now().isoformat(),
                'sentiment': 'bearish'
            }
        
        if signal:
            self.signals.append(signal)
            # Keep only last 50 signals
            self.signals = self.signals[-50:]
    
    def load_paper_trading_state(self):
        """Load paper trading state if available"""
        try:
            with open('paper_trading_state.json', 'r') as f:
                state = json.load(f)
                self.trade_history = state.get('trades', [])
                return state
        except:
            return None

view = CrawdadTradingView()

@app.route('/')
def index():
    """Main trading view page"""
    return render_template('trading_view.html')

@app.route('/api/market_data')
def get_market_data():
    """Get all market data"""
    return jsonify(view.market_data)

@app.route('/api/symbol/<symbol>')
def get_symbol_data(symbol):
    """Get data for specific symbol"""
    if symbol in view.market_data:
        return jsonify(view.market_data[symbol])
    return jsonify({'error': 'Symbol not found'}), 404

@app.route('/api/signals')
def get_signals():
    """Get recent trading signals"""
    return jsonify(view.signals)

@app.route('/api/trades')
def get_trades():
    """Get trade history"""
    state = view.load_paper_trading_state()
    if state:
        return jsonify({
            'trades': state.get('trades', []),
            'metrics': state.get('metrics', {}),
            'capital': state.get('capital', 90)
        })
    return jsonify({'trades': [], 'metrics': {}, 'capital': 90})

@app.route('/api/candles/<symbol>')
def get_candles(symbol):
    """Get candlestick data for charting"""
    timeframe = request.args.get('timeframe', '5m')
    
    if symbol in view.market_data:
        data = view.market_data[symbol]
        
        if timeframe == '5m':
            candles = data.get('candles_5m', [])
        elif timeframe == '1h':
            candles = data.get('candles_1h', [])
        else:
            candles = data.get('candles_1d', [])
        
        return jsonify(candles)
    
    return jsonify([])

if __name__ == '__main__':
    # Initialize with current data
    print("🦞 Initializing Crawdad Trading View...")
    for symbol in view.symbols:
        print(f"Loading {symbol}...")
        view.update_market_data(symbol)
    
    print("""
🦞 QUANTUM CRAWDAD TRADING VIEW
═══════════════════════════════════════════════════════════════════════════════════
TradingView-style interface for monitoring paper trading
Access at: http://localhost:5679
═══════════════════════════════════════════════════════════════════════════════════
    """)
    
    app.run(host='0.0.0.0', port=5679, debug=False)