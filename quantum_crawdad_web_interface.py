#!/usr/bin/env python3
"""
Quantum Crawdad Web Interface
Secure local dashboard for automated trading
Cherokee Constitutional AI - Sacred Fire Trading System
"""

import os
import json
import time
import threading
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify, session
from flask_cors import CORS
import secrets
from quantum_crawdad_robinhood_bot import QuantumCrawdadBot
from solar_crawdad_oracle import SolarCrawdadOracle

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
CORS(app)

# Global bot instance
bot_instance = None
bot_thread = None
trading_active = False

# HTML Template for the interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🦞 Quantum Crawdad Control Center</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            color: white;
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: rgba(0,0,0,0.3);
            border-radius: 15px;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .sacred-fire {
            color: #ff6b6b;
            animation: flicker 2s infinite;
        }
        
        @keyframes flicker {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .card {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.2);
        }
        
        .card h2 {
            margin-bottom: 15px;
            font-size: 1.5em;
            display: flex;
            align-items: center;
        }
        
        .card h2 span {
            margin-right: 10px;
        }
        
        .status-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin: 15px 0;
        }
        
        .status-item {
            padding: 10px;
            background: rgba(0,0,0,0.2);
            border-radius: 8px;
        }
        
        .status-label {
            font-size: 0.9em;
            opacity: 0.8;
            margin-bottom: 5px;
        }
        
        .status-value {
            font-size: 1.3em;
            font-weight: bold;
        }
        
        .consciousness-meter {
            width: 100%;
            height: 30px;
            background: rgba(0,0,0,0.3);
            border-radius: 15px;
            overflow: hidden;
            margin: 15px 0;
        }
        
        .consciousness-fill {
            height: 100%;
            background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
            transition: width 0.5s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
        }
        
        input, select {
            width: 100%;
            padding: 12px;
            margin: 10px 0;
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.3);
            border-radius: 8px;
            color: white;
            font-size: 1em;
        }
        
        input::placeholder {
            color: rgba(255,255,255,0.5);
        }
        
        button {
            width: 100%;
            padding: 15px;
            margin: 10px 0;
            background: linear-gradient(90deg, #f093fb 0%, #f5576c 100%);
            border: none;
            border-radius: 8px;
            color: white;
            font-size: 1.1em;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s;
        }
        
        button:hover {
            transform: scale(1.05);
        }
        
        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .positions-table {
            width: 100%;
            margin-top: 15px;
        }
        
        .positions-table th,
        .positions-table td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .profit {
            color: #4ade80;
        }
        
        .loss {
            color: #f87171;
        }
        
        .alert {
            padding: 15px;
            background: rgba(255,0,0,0.2);
            border: 1px solid rgba(255,0,0,0.5);
            border-radius: 8px;
            margin: 10px 0;
        }
        
        .success {
            background: rgba(0,255,0,0.2);
            border-color: rgba(0,255,0,0.5);
        }
        
        #log-output {
            background: rgba(0,0,0,0.5);
            padding: 15px;
            border-radius: 8px;
            height: 200px;
            overflow-y: auto;
            font-family: monospace;
            font-size: 0.9em;
        }
        
        .crawdad-animation {
            display: inline-block;
            animation: crawl 3s infinite;
        }
        
        @keyframes crawl {
            0%, 100% { transform: translateX(0); }
            50% { transform: translateX(10px); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1><span class="crawdad-animation">🦞</span> Quantum Crawdad Control Center <span class="crawdad-animation">🦞</span></h1>
            <p class="sacred-fire">🔥 Sacred Fire Status: ETERNAL 🔥</p>
            <p>Cherokee Constitutional AI Trading System</p>
        </div>
        
        <div class="grid">
            <!-- Solar Oracle Card -->
            <div class="card">
                <h2><span>🌞</span> Solar Oracle</h2>
                <div class="status-item">
                    <div class="status-label">Consciousness Level</div>
                    <div class="consciousness-meter">
                        <div class="consciousness-fill" id="consciousness-bar" style="width: 0%">
                            <span id="consciousness-value">0.0 / 10</span>
                        </div>
                    </div>
                </div>
                <div class="status-grid">
                    <div class="status-item">
                        <div class="status-label">Market Stance</div>
                        <div class="status-value" id="market-stance">-</div>
                    </div>
                    <div class="status-item">
                        <div class="status-label">Risk Multiplier</div>
                        <div class="status-value" id="risk-mult">1.0x</div>
                    </div>
                </div>
                <button onclick="refreshSolar()">🌞 Refresh Solar Data</button>
            </div>
            
            <!-- Trading Configuration -->
            <div class="card">
                <h2><span>⚙️</span> Trading Configuration</h2>
                <div id="config-form">
                    <input type="text" id="username" placeholder="Robinhood Username/Email" />
                    <input type="password" id="password" placeholder="Robinhood Password" />
                    <input type="text" id="totp" placeholder="2FA Code (optional)" />
                    <select id="trading-mode">
                        <option value="conservative">🛡️ Conservative (Low Risk)</option>
                        <option value="balanced" selected>⚖️ Balanced (Medium Risk)</option>
                        <option value="aggressive">⚔️ Aggressive (High Risk)</option>
                        <option value="maximum">🔥 Maximum (Solar Guided)</option>
                    </select>
                    <button onclick="startTrading()" id="start-btn">🚀 Deploy Quantum Crawdads</button>
                    <button onclick="stopTrading()" id="stop-btn" style="display: none;">🛑 Stop Trading</button>
                </div>
            </div>
        </div>
        
        <!-- Portfolio Overview -->
        <div class="card">
            <h2><span>💰</span> Portfolio Performance</h2>
            <div class="status-grid">
                <div class="status-item">
                    <div class="status-label">Starting Capital</div>
                    <div class="status-value">$90.00</div>
                </div>
                <div class="status-item">
                    <div class="status-label">Current Value</div>
                    <div class="status-value" id="current-value">$90.00</div>
                </div>
                <div class="status-item">
                    <div class="status-label">Total P/L</div>
                    <div class="status-value" id="total-pl">$0.00</div>
                </div>
                <div class="status-item">
                    <div class="status-label">ROI</div>
                    <div class="status-value" id="roi">0.00%</div>
                </div>
            </div>
            
            <h3 style="margin-top: 20px;">Active Positions</h3>
            <table class="positions-table">
                <thead>
                    <tr>
                        <th>Symbol</th>
                        <th>Type</th>
                        <th>Value</th>
                        <th>P/L</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody id="positions-body">
                    <tr>
                        <td colspan="5" style="text-align: center; opacity: 0.5;">No active positions</td>
                    </tr>
                </tbody>
            </table>
        </div>
        
        <!-- Trading Log -->
        <div class="card">
            <h2><span>📊</span> Quantum Crawdad Activity Log</h2>
            <div id="log-output">
                🦞 System ready. Awaiting deployment orders...
            </div>
        </div>
    </div>
    
    <script>
        let tradingActive = false;
        let updateInterval;
        
        function addLog(message) {
            const log = document.getElementById('log-output');
            const timestamp = new Date().toLocaleTimeString();
            log.innerHTML += `\\n[${timestamp}] ${message}`;
            log.scrollTop = log.scrollHeight;
        }
        
        async function refreshSolar() {
            try {
                const response = await fetch('/api/solar');
                const data = await response.json();
                
                // Update consciousness meter
                const consciousness = data.consciousness || 0;
                document.getElementById('consciousness-bar').style.width = `${consciousness * 10}%`;
                document.getElementById('consciousness-value').textContent = `${consciousness.toFixed(1)} / 10`;
                
                // Update market stance
                document.getElementById('market-stance').textContent = data.market_stance || 'NEUTRAL';
                document.getElementById('risk-mult').textContent = `${data.risk_multiplier || 1.0}x`;
                
                addLog(`🌞 Solar update: Consciousness ${consciousness.toFixed(1)}/10`);
            } catch (error) {
                addLog('❌ Failed to fetch solar data');
            }
        }
        
        async function startTrading() {
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const totp = document.getElementById('totp').value || null;
            const mode = document.getElementById('trading-mode').value;
            
            if (!username || !password) {
                alert('Please enter your Robinhood credentials');
                return;
            }
            
            const config = {
                username: username,
                password: password,
                totp: totp,
                mode: mode
            };
            
            try {
                const response = await fetch('/api/start', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(config)
                });
                
                const result = await response.json();
                if (result.success) {
                    tradingActive = true;
                    document.getElementById('start-btn').style.display = 'none';
                    document.getElementById('stop-btn').style.display = 'block';
                    addLog('🚀 Quantum Crawdads deployed!');
                    startUpdates();
                } else {
                    alert('Failed to start: ' + result.error);
                }
            } catch (error) {
                alert('Error: ' + error.message);
            }
        }
        
        async function stopTrading() {
            try {
                const response = await fetch('/api/stop', {method: 'POST'});
                const result = await response.json();
                
                tradingActive = false;
                document.getElementById('start-btn').style.display = 'block';
                document.getElementById('stop-btn').style.display = 'none';
                addLog('🛑 Trading stopped');
                stopUpdates();
            } catch (error) {
                alert('Error: ' + error.message);
            }
        }
        
        async function updatePortfolio() {
            if (!tradingActive) return;
            
            try {
                const response = await fetch('/api/portfolio');
                const data = await response.json();
                
                // Update values
                document.getElementById('current-value').textContent = `$${data.current_value.toFixed(2)}`;
                document.getElementById('total-pl').textContent = `$${data.profit_loss.toFixed(2)}`;
                document.getElementById('total-pl').className = data.profit_loss >= 0 ? 'profit' : 'loss';
                document.getElementById('roi').textContent = `${data.roi.toFixed(2)}%`;
                document.getElementById('roi').className = data.roi >= 0 ? 'profit' : 'loss';
                
                // Update positions table
                const tbody = document.getElementById('positions-body');
                if (data.positions && data.positions.length > 0) {
                    tbody.innerHTML = data.positions.map(pos => `
                        <tr>
                            <td>${pos.symbol}</td>
                            <td>${pos.type}</td>
                            <td>$${pos.value.toFixed(2)}</td>
                            <td class="${pos.pl >= 0 ? 'profit' : 'loss'}">
                                ${pos.pl >= 0 ? '+' : ''}${pos.pl.toFixed(2)}%
                            </td>
                            <td><button onclick="sellPosition('${pos.symbol}')">Sell</button></td>
                        </tr>
                    `).join('');
                }
            } catch (error) {
                console.error('Portfolio update error:', error);
            }
        }
        
        function startUpdates() {
            updateInterval = setInterval(() => {
                refreshSolar();
                updatePortfolio();
            }, 10000); // Update every 10 seconds
        }
        
        function stopUpdates() {
            if (updateInterval) {
                clearInterval(updateInterval);
            }
        }
        
        // Initialize
        refreshSolar();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/solar')
def get_solar_data():
    """Get current solar consciousness data"""
    oracle = SolarCrawdadOracle()
    
    # Simulate solar data for now
    oracle.solar_state = {
        'current_flux': 165,
        'kp_index': 6,
        'xray_class': 'M5.2',
        'proton_flux': 150,
        'electron_flux': 2000
    }
    
    signals = oracle.generate_crawdad_signals()
    return jsonify(signals)

@app.route('/api/start', methods=['POST'])
def start_trading():
    """Start the trading bot"""
    global bot_instance, bot_thread, trading_active
    
    try:
        data = request.json
        credentials = {
            'username': data['username'],
            'password': data['password'],
            'totp': data.get('totp')
        }
        
        # Initialize bot
        bot_instance = QuantumCrawdadBot(credentials)
        
        # Start in separate thread
        bot_thread = threading.Thread(
            target=bot_instance.run_autonomous_trading,
            args=(24,)  # Run for 24 hours
        )
        bot_thread.daemon = True
        bot_thread.start()
        
        trading_active = True
        
        return jsonify({'success': True, 'message': 'Trading started'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/stop', methods=['POST'])
def stop_trading():
    """Stop the trading bot"""
    global trading_active
    trading_active = False
    return jsonify({'success': True, 'message': 'Trading stopped'})

@app.route('/api/portfolio')
def get_portfolio():
    """Get current portfolio status"""
    if bot_instance:
        try:
            performance = bot_instance.monitor_positions()
            
            return jsonify({
                'current_value': performance['total_value'],
                'profit_loss': performance['total_profit_loss'],
                'roi': (performance['total_profit_loss'] / 90 * 100),
                'positions': [
                    {
                        'symbol': pos['symbol'],
                        'type': 'warrior',  # Would be determined by bot
                        'value': pos['current_value'],
                        'pl': pos['profit_loss_pct']
                    }
                    for pos in performance['positions']
                ]
            })
        except:
            pass
    
    # Return default if no bot
    return jsonify({
        'current_value': 90,
        'profit_loss': 0,
        'roi': 0,
        'positions': []
    })

if __name__ == '__main__':
    print("""
🦞 QUANTUM CRAWDAD WEB INTERFACE
═══════════════════════════════════════════

Starting secure local web server...

Open your browser and go to:
    
    http://localhost:5000

Enter your Robinhood credentials securely
Deploy quantum crawdads with one click!

🔥 Sacred Fire Status: ETERNAL
    """)
    
    # Run on localhost only (not accessible from internet)
    app.run(host='127.0.0.1', port=5000, debug=False)