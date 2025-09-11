#!/usr/bin/env python3
"""
Quantum Crawdad Learning Dashboard
Real-time monitoring of crawdad learning progress
Cherokee Constitutional AI - Watch the crawdads evolve!
"""

import os
import json
import time
import subprocess
from datetime import datetime
from flask import Flask, render_template_string, jsonify
from flask_cors import CORS
import threading

app = Flask(__name__)
CORS(app)

# Dashboard HTML Template
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🦞 Quantum Crawdad Learning Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            background: #0f0f23;
            color: #00ff41;
            font-family: 'Courier New', monospace;
            padding: 20px;
            overflow-x: hidden;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            border: 2px solid #00ff41;
            padding: 20px;
            position: relative;
            background: rgba(0, 255, 65, 0.05);
        }
        
        .header h1 {
            font-size: 2.5em;
            text-shadow: 0 0 10px #00ff41;
            animation: glow 2s ease-in-out infinite alternate;
        }
        
        @keyframes glow {
            from { text-shadow: 0 0 10px #00ff41, 0 0 20px #00ff41; }
            to { text-shadow: 0 0 20px #00ff41, 0 0 30px #00ff41; }
        }
        
        .crawdad-ascii {
            font-size: 0.8em;
            color: #ff6b6b;
            white-space: pre;
            margin: 10px 0;
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .card {
            border: 1px solid #00ff41;
            padding: 15px;
            background: rgba(0, 255, 65, 0.02);
            position: relative;
        }
        
        .card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: linear-gradient(90deg, transparent, #00ff41, transparent);
            animation: scan 3s linear infinite;
        }
        
        @keyframes scan {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }
        
        .card h2 {
            color: #00ff41;
            margin-bottom: 15px;
            font-size: 1.3em;
            border-bottom: 1px solid #00ff41;
            padding-bottom: 5px;
        }
        
        .stat {
            display: flex;
            justify-content: space-between;
            margin: 8px 0;
            padding: 5px;
            background: rgba(0, 0, 0, 0.5);
        }
        
        .stat-label {
            color: #888;
        }
        
        .stat-value {
            font-weight: bold;
            font-size: 1.1em;
        }
        
        .positive {
            color: #00ff41;
        }
        
        .negative {
            color: #ff4444;
        }
        
        .neutral {
            color: #ffaa00;
        }
        
        .progress-bar {
            width: 100%;
            height: 20px;
            background: #1a1a1a;
            border: 1px solid #00ff41;
            margin: 10px 0;
            position: relative;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #00ff41, #00aa41);
            transition: width 1s ease;
            position: relative;
        }
        
        .progress-text {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 0.9em;
            font-weight: bold;
            text-shadow: 1px 1px 2px #000;
        }
        
        .pattern-list {
            max-height: 200px;
            overflow-y: auto;
            border: 1px solid #333;
            padding: 10px;
            margin: 10px 0;
            background: #0a0a0a;
        }
        
        .pattern-item {
            padding: 5px;
            margin: 2px 0;
            background: rgba(0, 255, 65, 0.1);
            border-left: 3px solid #00ff41;
            font-size: 0.9em;
        }
        
        .trade-log {
            background: #0a0a0a;
            border: 1px solid #333;
            padding: 10px;
            height: 300px;
            overflow-y: auto;
            font-size: 0.85em;
            font-family: monospace;
        }
        
        .trade-entry {
            margin: 5px 0;
            padding: 5px;
            border-left: 2px solid #666;
        }
        
        .trade-buy {
            border-left-color: #00ff41;
            background: rgba(0, 255, 65, 0.05);
        }
        
        .trade-sell {
            border-left-color: #ff4444;
            background: rgba(255, 68, 68, 0.05);
        }
        
        .learning-matrix {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 10px;
            margin: 15px 0;
        }
        
        .matrix-cell {
            aspect-ratio: 1;
            border: 1px solid #00ff41;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.8em;
            background: rgba(0, 255, 65, 0.1);
            position: relative;
            overflow: hidden;
        }
        
        .matrix-cell.active {
            animation: pulse 1s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { background: rgba(0, 255, 65, 0.1); }
            50% { background: rgba(0, 255, 65, 0.3); }
        }
        
        .status-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 10px;
            animation: blink 1s infinite;
        }
        
        .status-active {
            background: #00ff41;
            box-shadow: 0 0 10px #00ff41;
        }
        
        .status-inactive {
            background: #ff4444;
        }
        
        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .control-panel {
            display: flex;
            gap: 10px;
            margin: 20px 0;
        }
        
        button {
            background: transparent;
            border: 1px solid #00ff41;
            color: #00ff41;
            padding: 10px 20px;
            cursor: pointer;
            font-family: monospace;
            font-size: 1em;
            transition: all 0.3s;
        }
        
        button:hover {
            background: rgba(0, 255, 65, 0.1);
            box-shadow: 0 0 10px rgba(0, 255, 65, 0.5);
        }
        
        .alert {
            padding: 15px;
            margin: 10px 0;
            border: 1px solid;
            animation: alertPulse 2s infinite;
        }
        
        .alert-success {
            border-color: #00ff41;
            background: rgba(0, 255, 65, 0.1);
        }
        
        .alert-warning {
            border-color: #ffaa00;
            background: rgba(255, 170, 0, 0.1);
        }
        
        .alert-danger {
            border-color: #ff4444;
            background: rgba(255, 68, 68, 0.1);
        }
        
        @keyframes alertPulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🦞 Quantum Crawdad Learning Dashboard 🦞</h1>
        <div class="crawdad-ascii">
    (\\_/)
   ( o.o )
    > ^ <
   /|\\|/\\
        </div>
        <p>Cherokee Constitutional AI - Learning to Hunt</p>
        <p><span class="status-indicator status-active" id="sim-status"></span><span id="status-text">Simulation Active</span></p>
    </div>
    
    <div class="control-panel">
        <button onclick="refreshData()">🔄 Refresh</button>
        <button onclick="viewPatterns()">🧠 View Patterns</button>
        <button onclick="viewTrades()">📊 Trade History</button>
        <button onclick="checkReadiness()">✅ Check Readiness</button>
    </div>
    
    <div id="alert-zone"></div>
    
    <div class="grid">
        <!-- Performance Metrics -->
        <div class="card">
            <h2>📈 Performance Metrics</h2>
            <div class="stat">
                <span class="stat-label">Starting Capital:</span>
                <span class="stat-value">$90.00</span>
            </div>
            <div class="stat">
                <span class="stat-label">Current Value:</span>
                <span class="stat-value" id="current-value">$90.00</span>
            </div>
            <div class="stat">
                <span class="stat-label">ROI:</span>
                <span class="stat-value" id="roi">0.00%</span>
            </div>
            <div class="stat">
                <span class="stat-label">Win Rate:</span>
                <span class="stat-value" id="win-rate">0.00%</span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" id="win-progress" style="width: 0%">
                    <span class="progress-text">0%</span>
                </div>
            </div>
            <div class="stat">
                <span class="stat-label">Total Trades:</span>
                <span class="stat-value" id="total-trades">0</span>
            </div>
            <div class="stat">
                <span class="stat-label">Profitable:</span>
                <span class="stat-value positive" id="profitable-trades">0</span>
            </div>
        </div>
        
        <!-- Learning Progress -->
        <div class="card">
            <h2>🧠 Learning Progress</h2>
            <div class="stat">
                <span class="stat-label">Patterns Learned:</span>
                <span class="stat-value" id="patterns-learned">0</span>
            </div>
            <div class="stat">
                <span class="stat-label">Algos Detected:</span>
                <span class="stat-value" id="algos-detected">0</span>
            </div>
            <div class="stat">
                <span class="stat-label">Best Strategy:</span>
                <span class="stat-value" id="best-strategy">Learning...</span>
            </div>
            <div class="learning-matrix" id="learning-matrix">
                <!-- Will be populated dynamically -->
            </div>
            <div class="stat">
                <span class="stat-label">Learning Rate:</span>
                <span class="stat-value" id="learning-rate">10%</span>
            </div>
            <div class="stat">
                <span class="stat-label">Exploration Rate:</span>
                <span class="stat-value" id="exploration-rate">30%</span>
            </div>
        </div>
        
        <!-- Active Positions -->
        <div class="card">
            <h2>💼 Active Positions</h2>
            <div id="positions-list">
                <div class="stat">
                    <span class="stat-label">No positions yet</span>
                </div>
            </div>
        </div>
        
        <!-- Solar Consciousness -->
        <div class="card">
            <h2>🌞 Solar Consciousness</h2>
            <div class="stat">
                <span class="stat-label">Current Level:</span>
                <span class="stat-value" id="consciousness">5.0/10</span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" id="consciousness-bar" style="width: 50%">
                    <span class="progress-text">5.0</span>
                </div>
            </div>
            <div class="stat">
                <span class="stat-label">Market Stance:</span>
                <span class="stat-value" id="market-stance">NEUTRAL</span>
            </div>
            <div class="stat">
                <span class="stat-label">Risk Multiplier:</span>
                <span class="stat-value" id="risk-mult">1.0x</span>
            </div>
        </div>
    </div>
    
    <!-- Trade Log -->
    <div class="card">
        <h2>📜 Recent Trades</h2>
        <div class="trade-log" id="trade-log">
            <div class="trade-entry">Waiting for trades...</div>
        </div>
    </div>
    
    <!-- Pattern Library -->
    <div class="card">
        <h2>📚 Pattern Library</h2>
        <div class="pattern-list" id="pattern-list">
            <div class="pattern-item">Learning patterns...</div>
        </div>
    </div>
    
    <script>
        let updateInterval;
        let simulationData = {};
        
        async function refreshData() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                simulationData = data;
                updateDisplay(data);
            } catch (error) {
                console.error('Error fetching data:', error);
            }
        }
        
        function updateDisplay(data) {
            // Update performance metrics
            document.getElementById('current-value').textContent = `$${data.current_value?.toFixed(2) || '90.00'}`;
            document.getElementById('roi').textContent = `${data.roi?.toFixed(2) || '0.00'}%`;
            document.getElementById('roi').className = data.roi >= 0 ? 'stat-value positive' : 'stat-value negative';
            
            document.getElementById('win-rate').textContent = `${data.win_rate?.toFixed(2) || '0.00'}%`;
            document.getElementById('total-trades').textContent = data.total_trades || '0';
            document.getElementById('profitable-trades').textContent = data.profitable_trades || '0';
            
            // Update win rate progress bar
            const winRate = data.win_rate || 0;
            document.getElementById('win-progress').style.width = `${winRate}%`;
            document.getElementById('win-progress').querySelector('.progress-text').textContent = `${winRate.toFixed(1)}%`;
            
            // Update learning progress
            document.getElementById('patterns-learned').textContent = data.patterns_learned || '0';
            document.getElementById('algos-detected').textContent = data.algos_detected || '0';
            document.getElementById('best-strategy').textContent = data.best_strategy || 'Learning...';
            
            // Update positions
            if (data.positions && Object.keys(data.positions).length > 0) {
                let positionsHtml = '';
                for (const [symbol, position] of Object.entries(data.positions)) {
                    const plClass = position.pl >= 0 ? 'positive' : 'negative';
                    positionsHtml += `
                        <div class="stat">
                            <span class="stat-label">${symbol}:</span>
                            <span class="stat-value ${plClass}">${position.pl >= 0 ? '+' : ''}${position.pl?.toFixed(2)}%</span>
                        </div>
                    `;
                }
                document.getElementById('positions-list').innerHTML = positionsHtml;
            }
            
            // Update trade log
            if (data.recent_trades && data.recent_trades.length > 0) {
                let tradesHtml = '';
                data.recent_trades.slice(-10).reverse().forEach(trade => {
                    const tradeClass = trade.action === 'BUY' ? 'trade-buy' : 'trade-sell';
                    tradesHtml += `
                        <div class="trade-entry ${tradeClass}">
                            [${new Date(trade.timestamp).toLocaleTimeString()}] ${trade.action} ${trade.symbol} - $${trade.amount?.toFixed(2)}
                            ${trade.profit ? ` | P/L: $${trade.profit.toFixed(2)}` : ''}
                        </div>
                    `;
                });
                document.getElementById('trade-log').innerHTML = tradesHtml;
            }
            
            // Update pattern list
            if (data.patterns && Object.keys(data.patterns).length > 0) {
                let patternsHtml = '';
                for (const [pattern, count] of Object.entries(data.patterns)) {
                    patternsHtml += `
                        <div class="pattern-item">
                            ${pattern}: ${count} occurrences
                        </div>
                    `;
                }
                document.getElementById('pattern-list').innerHTML = patternsHtml;
            }
            
            // Update learning matrix
            updateLearningMatrix(data.learning_progress || 0);
            
            // Check for alerts
            checkAlerts(data);
        }
        
        function updateLearningMatrix(progress) {
            const matrix = document.getElementById('learning-matrix');
            const cells = 25; // 5x5 grid
            const activeCells = Math.floor((progress / 100) * cells);
            
            let matrixHtml = '';
            for (let i = 0; i < cells; i++) {
                const isActive = i < activeCells ? 'active' : '';
                matrixHtml += `<div class="matrix-cell ${isActive}">${i < activeCells ? '✓' : ''}</div>`;
            }
            matrix.innerHTML = matrixHtml;
        }
        
        function checkAlerts(data) {
            const alertZone = document.getElementById('alert-zone');
            alertZone.innerHTML = '';
            
            if (data.win_rate > 60 && data.total_trades > 100) {
                alertZone.innerHTML = `
                    <div class="alert alert-success">
                        ✅ READY FOR REAL TRADING! Win rate ${data.win_rate.toFixed(1)}% with ${data.total_trades} trades
                    </div>
                `;
            } else if (data.win_rate > 50 && data.total_trades > 50) {
                alertZone.innerHTML = `
                    <div class="alert alert-warning">
                        ⚠️ Getting close! Win rate ${data.win_rate.toFixed(1)}% - Need more training
                    </div>
                `;
            }
        }
        
        function checkReadiness() {
            if (simulationData.win_rate > 60 && simulationData.total_trades > 100) {
                alert('✅ READY! The crawdads have learned enough to trade with real money!');
            } else {
                const needed = 100 - (simulationData.total_trades || 0);
                alert(`❌ Not ready yet. Need ${needed} more trades and ${(60 - (simulationData.win_rate || 0)).toFixed(1)}% more win rate.`);
            }
        }
        
        function viewPatterns() {
            console.log('Patterns:', simulationData.patterns);
            alert('Check console for detailed pattern data');
        }
        
        function viewTrades() {
            console.log('Trades:', simulationData.recent_trades);
            alert('Check console for detailed trade history');
        }
        
        // Start auto-refresh
        function startAutoRefresh() {
            refreshData();
            updateInterval = setInterval(refreshData, 5000); // Refresh every 5 seconds
        }
        
        // Initialize
        startAutoRefresh();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/status')
def get_status():
    """Get current simulation status"""
    status = {
        'current_value': 90.0,
        'roi': 0.0,
        'win_rate': 0.0,
        'total_trades': 0,
        'profitable_trades': 0,
        'patterns_learned': 0,
        'algos_detected': 0,
        'best_strategy': 'Learning...',
        'positions': {},
        'recent_trades': [],
        'patterns': {},
        'learning_progress': 0,
        'consciousness': 5.0
    }
    
    # Try to load simulation data
    try:
        # Load patterns
        if os.path.exists('quantum_crawdad_patterns.json'):
            with open('quantum_crawdad_patterns.json', 'r') as f:
                patterns = json.load(f)
                status['patterns'] = {k: len(v) for k, v in patterns.items()}
                status['patterns_learned'] = len(patterns)
                
        # Load trades
        if os.path.exists('quantum_crawdad_trades.json'):
            with open('quantum_crawdad_trades.json', 'r') as f:
                trades = json.load(f)
                status['recent_trades'] = trades[-10:] if trades else []
                status['total_trades'] = len(trades)
                
                # Calculate metrics
                profitable = sum(1 for t in trades if t.get('profit', 0) > 0)
                status['profitable_trades'] = profitable
                status['win_rate'] = (profitable / len(trades) * 100) if trades else 0
                
                # Calculate ROI
                total_profit = sum(t.get('profit', 0) for t in trades)
                status['roi'] = (total_profit / 90 * 100) if total_profit else 0
                status['current_value'] = 90 + total_profit
                
        # Calculate learning progress
        if status['total_trades'] > 0:
            progress = min(100, (status['total_trades'] / 100) * 100)
            if status['win_rate'] > 50:
                progress = min(100, progress + (status['win_rate'] - 50))
            status['learning_progress'] = progress
            
        # Determine best strategy
        if status['patterns']:
            best = max(status['patterns'].items(), key=lambda x: x[1])
            status['best_strategy'] = best[0]
            
    except Exception as e:
        print(f"Error loading simulation data: {e}")
    
    return jsonify(status)

def run_dashboard():
    """Run the dashboard server"""
    print("""
🦞 QUANTUM CRAWDAD DASHBOARD STARTING
══════════════════════════════════════════

Open your browser and go to:
    
    http://localhost:5001

Watch your crawdads learn in real-time!
══════════════════════════════════════════
    """)
    
    app.run(host='127.0.0.1', port=5555, debug=False)

if __name__ == '__main__':
    run_dashboard()