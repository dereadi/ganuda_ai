#!/usr/bin/env python3
"""
Real-time Trading Data Integrator
Connects all dashboards with live paper trading data
Cherokee Constitutional AI - Unified Vision System
"""

from flask import Flask, jsonify, render_template_string
from flask_cors import CORS
import json
import threading
import time
from datetime import datetime
import yfinance as yf

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from other dashboards

class RealtimeTradingIntegrator:
    def __init__(self):
        self.update_interval = 30  # seconds
        self.last_update = None
        self.data = {
            'paper_trading': {},
            'market_prices': {},
            'solar_forecast': {},
            'signals': [],
            'performance': {},
            'system_status': {}
        }
        
        # Start background updater
        self.start_updater()
    
    def start_updater(self):
        """Start background thread to update all data"""
        def update_loop():
            while True:
                self.update_all_data()
                time.sleep(self.update_interval)
        
        thread = threading.Thread(target=update_loop, daemon=True)
        thread.start()
    
    def update_all_data(self):
        """Update all data sources"""
        self.last_update = datetime.now()
        
        # Update paper trading data
        self.update_paper_trading()
        
        # Update market prices
        self.update_market_prices()
        
        # Update solar forecast
        self.update_solar_forecast()
        
        # Update system status
        self.update_system_status()
    
    def update_paper_trading(self):
        """Load paper trading state"""
        try:
            with open('paper_trading_state.json', 'r') as f:
                state = json.load(f)
                self.data['paper_trading'] = state
                
                # Extract performance metrics
                if 'metrics' in state:
                    self.data['performance'] = state['metrics']
                
                # Extract recent trades for signals
                if 'trades' in state:
                    for trade in state['trades'][-5:]:  # Last 5 trades
                        signal = {
                            'timestamp': trade.get('timestamp'),
                            'symbol': trade.get('symbol'),
                            'action': trade.get('action'),
                            'price': trade.get('price'),
                            'type': 'TRADE'
                        }
                        if signal not in self.data['signals']:
                            self.data['signals'].append(signal)
        except:
            pass
    
    def update_market_prices(self):
        """Update live market prices"""
        symbols = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'DOGE-USD', 'SHIB-USD']
        
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period='1d', interval='5m')
                
                if not hist.empty:
                    current = hist['Close'].iloc[-1]
                    prev = hist['Close'].iloc[-2] if len(hist) > 1 else current
                    
                    self.data['market_prices'][symbol] = {
                        'price': float(current),
                        'change': float((current - prev) / prev * 100),
                        'volume': float(hist['Volume'].sum()),
                        'high': float(hist['High'].max()),
                        'low': float(hist['Low'].min()),
                        'last_update': datetime.now().isoformat()
                    }
            except:
                pass
    
    def update_solar_forecast(self):
        """Load solar forecast data"""
        try:
            with open('solar_trading_forecast.json', 'r') as f:
                forecast = json.load(f)
                self.data['solar_forecast'] = forecast
        except:
            self.data['solar_forecast'] = {
                'status': 'No forecast available',
                'next_impact': 'Unknown'
            }
    
    def update_system_status(self):
        """Update system status"""
        self.data['system_status'] = {
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'paper_trading_active': bool(self.data['paper_trading']),
            'market_data_active': bool(self.data['market_prices']),
            'solar_forecast_active': bool(self.data['solar_forecast']),
            'total_signals': len(self.data['signals']),
            'dashboards': {
                'main_portal': 'http://192.168.132.223:5678',
                'trading_view': 'http://192.168.132.223:5679',
                'realtime_api': 'http://192.168.132.223:5680'
            }
        }

integrator = RealtimeTradingIntegrator()

@app.route('/')
def index():
    """Status page"""
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Realtime Trading Integrator</title>
        <style>
            body { 
                font-family: monospace; 
                background: #0f0f1e; 
                color: #00ff88; 
                padding: 20px;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            h1 { 
                color: #ff6b35; 
                text-align: center;
                text-shadow: 0 0 10px #ff6b35;
            }
            .grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-top: 20px;
            }
            .card {
                background: rgba(26, 26, 46, 0.8);
                border: 1px solid #ff6b35;
                border-radius: 10px;
                padding: 15px;
            }
            .metric {
                display: flex;
                justify-content: space-between;
                margin: 10px 0;
                padding: 5px;
                background: rgba(0,0,0,0.3);
                border-radius: 5px;
            }
            .value { color: #ffaa00; font-weight: bold; }
            .positive { color: #00ff88; }
            .negative { color: #ff4444; }
            .endpoints {
                margin-top: 20px;
                padding: 20px;
                background: rgba(0,0,0,0.5);
                border-radius: 10px;
            }
            .endpoint {
                margin: 5px 0;
                padding: 5px 10px;
                background: rgba(255,107,53,0.1);
                border-left: 3px solid #ff6b35;
            }
            a { color: #00ff88; text-decoration: none; }
            a:hover { text-shadow: 0 0 5px #00ff88; }
        </style>
        <script>
            function updateData() {
                fetch('/api/all')
                    .then(response => response.json())
                    .then(data => {
                        // Update metrics
                        document.getElementById('lastUpdate').textContent = 
                            new Date(data.system_status.last_update).toLocaleTimeString();
                        
                        if (data.performance) {
                            document.getElementById('winRate').textContent = 
                                (data.performance.win_rate || 0).toFixed(1) + '%';
                            document.getElementById('totalTrades').textContent = 
                                data.performance.total_trades || 0;
                            document.getElementById('pnl').textContent = 
                                '$' + (data.performance.total_pnl || 0).toFixed(2);
                        }
                        
                        // Update prices
                        const pricesDiv = document.getElementById('prices');
                        pricesDiv.innerHTML = '';
                        for (const [symbol, price] of Object.entries(data.market_prices)) {
                            const changeClass = price.change > 0 ? 'positive' : 'negative';
                            pricesDiv.innerHTML += `
                                <div class="metric">
                                    <span>${symbol.replace('-USD', '')}</span>
                                    <span class="value">$${price.price.toFixed(2)} 
                                        <span class="${changeClass}">(${price.change > 0 ? '+' : ''}${price.change.toFixed(2)}%)</span>
                                    </span>
                                </div>
                            `;
                        }
                    });
            }
            
            // Update every 10 seconds
            setInterval(updateData, 10000);
            window.onload = updateData;
        </script>
    </head>
    <body>
        <div class="container">
            <h1>🦞 Quantum Crawdad Realtime Integrator</h1>
            
            <div class="grid">
                <div class="card">
                    <h3>📊 System Status</h3>
                    <div class="metric">
                        <span>Last Update:</span>
                        <span class="value" id="lastUpdate">Loading...</span>
                    </div>
                    <div class="metric">
                        <span>Paper Trading:</span>
                        <span class="value positive">ACTIVE</span>
                    </div>
                    <div class="metric">
                        <span>Solar Forecast:</span>
                        <span class="value positive">TRACKING</span>
                    </div>
                </div>
                
                <div class="card">
                    <h3>🎯 Performance</h3>
                    <div class="metric">
                        <span>Win Rate:</span>
                        <span class="value" id="winRate">0%</span>
                    </div>
                    <div class="metric">
                        <span>Total Trades:</span>
                        <span class="value" id="totalTrades">0</span>
                    </div>
                    <div class="metric">
                        <span>P&L:</span>
                        <span class="value" id="pnl">$0.00</span>
                    </div>
                </div>
                
                <div class="card">
                    <h3>💹 Live Prices</h3>
                    <div id="prices">Loading...</div>
                </div>
            </div>
            
            <div class="endpoints">
                <h3>🔌 API Endpoints (All CORS-enabled for dashboards)</h3>
                <div class="endpoint">
                    <strong>GET /api/all</strong> - All integrated data
                </div>
                <div class="endpoint">
                    <strong>GET /api/paper_trading</strong> - Paper trading state
                </div>
                <div class="endpoint">
                    <strong>GET /api/market_prices</strong> - Live market prices
                </div>
                <div class="endpoint">
                    <strong>GET /api/signals</strong> - Recent trading signals
                </div>
                <div class="endpoint">
                    <strong>GET /api/performance</strong> - Performance metrics
                </div>
                <div class="endpoint">
                    <strong>GET /api/solar</strong> - Solar forecast data
                </div>
            </div>
            
            <div class="endpoints">
                <h3>🖥️ Active Dashboards</h3>
                <div class="endpoint">
                    <a href="http://192.168.132.223:5678" target="_blank">
                        📊 Main Cherokee AI Portal (Port 5678)
                    </a>
                </div>
                <div class="endpoint">
                    <a href="http://192.168.132.223:5679" target="_blank">
                        📈 TradingView Dashboard (Port 5679)
                    </a>
                </div>
                <div class="endpoint">
                    <a href="http://192.168.132.223:5680" target="_blank">
                        🔄 Realtime API (Port 5680) - This Page
                    </a>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''
    return html

@app.route('/api/all')
def get_all_data():
    """Get all integrated data"""
    return jsonify(integrator.data)

@app.route('/api/paper_trading')
def get_paper_trading():
    """Get paper trading state"""
    return jsonify(integrator.data['paper_trading'])

@app.route('/api/market_prices')
def get_market_prices():
    """Get live market prices"""
    return jsonify(integrator.data['market_prices'])

@app.route('/api/signals')
def get_signals():
    """Get recent signals"""
    return jsonify(integrator.data['signals'])

@app.route('/api/performance')
def get_performance():
    """Get performance metrics"""
    return jsonify(integrator.data['performance'])

@app.route('/api/solar')
def get_solar():
    """Get solar forecast"""
    return jsonify(integrator.data['solar_forecast'])

if __name__ == '__main__':
    print("""
🔄 REALTIME TRADING INTEGRATOR
═══════════════════════════════════════════════════════════════════════════════════
Integrating all trading data streams into unified API
Updates every 30 seconds from all sources
═══════════════════════════════════════════════════════════════════════════════════

API Endpoints available at: http://192.168.132.223:5680/api/

Dashboards can now fetch realtime data from:
  /api/all - Complete integrated dataset
  /api/paper_trading - Paper trading state
  /api/market_prices - Live prices with changes
  /api/signals - Trading signals
  /api/performance - Win rate and P&L
  /api/solar - Solar forecast data

All endpoints are CORS-enabled for cross-dashboard access!
═══════════════════════════════════════════════════════════════════════════════════
    """)
    
    app.run(host='0.0.0.0', port=5680, debug=False)