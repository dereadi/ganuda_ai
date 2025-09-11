#!/usr/bin/env python3
"""
Fixed Trading View Dashboard
Quantum Crawdad version with CORS support and proxy endpoints
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import requests
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# API base URL
API_BASE = "http://192.168.132.223:5680/api"

# Serve the HTML directly
@app.route('/')
def index():
    html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quantum Crawdad Trading View</title>
    <script src="https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f0f1e 0%, #1a1a2e 50%, #0f0f1e 100%);
            color: #e0e0e0;
            min-height: 100vh;
        }
        .header {
            background: rgba(26, 26, 46, 0.95);
            padding: 15px 20px;
            border-bottom: 2px solid #ff6b35;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .logo {
            font-size: 24px;
            font-weight: bold;
            background: linear-gradient(45deg, #ff6b35, #f7931e);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .container {
            display: grid;
            grid-template-columns: 250px 1fr 300px;
            gap: 20px;
            padding: 20px;
            height: calc(100vh - 80px);
        }
        .sidebar {
            background: rgba(26, 26, 46, 0.6);
            border-radius: 10px;
            padding: 15px;
            overflow-y: auto;
        }
        .crypto-list { list-style: none; }
        .crypto-item {
            padding: 12px;
            margin: 5px 0;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
        }
        .crypto-item:hover {
            background: rgba(255, 107, 53, 0.2);
        }
        .main-chart {
            background: rgba(26, 26, 46, 0.6);
            border-radius: 10px;
            padding: 15px;
            display: flex;
            flex-direction: column;
        }
        #chart {
            flex: 1;
            border-radius: 8px;
            overflow: hidden;
        }
        .right-panel {
            background: rgba(26, 26, 46, 0.6);
            border-radius: 10px;
            padding: 15px;
            overflow-y: auto;
        }
        .positive { color: #00ff88; }
        .negative { color: #ff4444; }
        .signal-item {
            padding: 10px;
            margin: 8px 0;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            border-left: 3px solid #ff6b35;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">🦞 Quantum Crawdad Trading View</div>
        <div id="status">Loading...</div>
    </div>
    
    <div class="container">
        <div class="sidebar">
            <h3>Cryptocurrencies</h3>
            <ul class="crypto-list" id="cryptoList"></ul>
        </div>
        
        <div class="main-chart">
            <h3 id="chartTitle">Select a cryptocurrency</h3>
            <div id="chart"></div>
        </div>
        
        <div class="right-panel">
            <h3>Trading Data</h3>
            <div id="tradingData">
                <p>Loading trading data...</p>
            </div>
        </div>
    </div>
    
    <script>
        let chart = null;
        let candlestickSeries = null;
        
        // Initialize chart
        function initChart() {
            const chartContainer = document.getElementById('chart');
            chart = LightweightCharts.createChart(chartContainer, {
                width: chartContainer.offsetWidth,
                height: 400,
                layout: {
                    background: { type: 'solid', color: 'transparent' },
                    textColor: '#d1d4dc',
                },
                grid: {
                    vertLines: { color: 'rgba(42, 46, 57, 0.5)' },
                    horzLines: { color: 'rgba(42, 46, 57, 0.5)' },
                }
            });
            
            candlestickSeries = chart.addCandlestickSeries({
                upColor: '#00ff88',
                downColor: '#ff4444'
            });
        }
        
        // Fetch and display market data
        async function updateMarketData() {
            try {
                console.log('Fetching market data...');
                // Fetch from our proxy endpoint (same domain)
                const response = await fetch('/api/market_prices');
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                const prices = await response.json();
                
                if (prices.error) {
                    throw new Error(prices.error);
                }
                
                const list = document.getElementById('cryptoList');
                list.innerHTML = '';
                
                for (const [symbol, data] of Object.entries(prices)) {
                    const li = document.createElement('li');
                    li.className = 'crypto-item';
                    const changeClass = data.change > 0 ? 'positive' : 'negative';
                    li.innerHTML = `
                        <div>${symbol.replace('-USD', '')}</div>
                        <div>$${data.price.toFixed(2)}</div>
                        <div class="${changeClass}">${data.change > 0 ? '+' : ''}${data.change.toFixed(2)}%</div>
                    `;
                    li.onclick = () => loadChart(symbol, data);
                    list.appendChild(li);
                }
                
                document.getElementById('status').textContent = 'Connected';
                console.log('Market data loaded successfully');
            } catch (error) {
                console.error('Error fetching market data:', error);
                document.getElementById('status').textContent = `Error: ${error.message}`;
                document.getElementById('cryptoList').innerHTML = '<li style="color: #ff4444;">Failed to load market data</li>';
            }
        }
        
        // Load chart for selected crypto
        function loadChart(symbol, data) {
            document.getElementById('chartTitle').textContent = symbol;
            
            // Generate sample candlestick data
            const candles = [];
            const basePrice = data.price;
            const now = Math.floor(Date.now() / 1000);
            
            for (let i = 0; i < 50; i++) {
                const time = now - (50 - i) * 300; // 5-minute candles
                const open = basePrice * (1 + (Math.random() - 0.5) * 0.01);
                const close = basePrice * (1 + (Math.random() - 0.5) * 0.01);
                const high = Math.max(open, close) * (1 + Math.random() * 0.005);
                const low = Math.min(open, close) * (1 - Math.random() * 0.005);
                
                candles.push({ time, open, high, low, close });
            }
            
            candlestickSeries.setData(candles);
            chart.timeScale().fitContent();
        }
        
        // Update trading data panel
        async function updateTradingData() {
            try {
                console.log('Fetching trading data...');
                const response = await fetch('/api/paper_trading');
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                const data = await response.json();
                
                if (data.error) {
                    throw new Error(data.error);
                }
                
                const panel = document.getElementById('tradingData');
                
                if (data.metrics) {
                    panel.innerHTML = `
                        <div class="signal-item">
                            <strong>Performance</strong><br>
                            Win Rate: ${(data.metrics.win_rate || 0).toFixed(1)}%<br>
                            Total Trades: ${data.metrics.total_trades || 0}<br>
                            P&L: $${(data.metrics.total_pnl || 0).toFixed(2)}
                        </div>
                    `;
                    
                    if (data.trades && data.trades.length > 0) {
                        panel.innerHTML += '<div class="signal-item"><strong>Recent Trades</strong><br>';
                        data.trades.slice(-3).forEach(trade => {
                            panel.innerHTML += `${trade.action} ${trade.symbol} @ $${trade.price}<br>`;
                        });
                        panel.innerHTML += '</div>';
                    }
                } else {
                    panel.innerHTML = '<p>No trading data available yet</p>';
                }
                console.log('Trading data loaded successfully');
            } catch (error) {
                console.error('Error fetching trading data:', error);
                document.getElementById('tradingData').innerHTML = `<p style="color: #ff4444;">Error: ${error.message}</p>`;
            }
        }
        
        // Initialize
        initChart();
        updateMarketData();
        updateTradingData();
        
        // Update every 30 seconds
        setInterval(updateMarketData, 30000);
        setInterval(updateTradingData, 30000);
    </script>
</body>
</html>'''
    return html

# Proxy endpoints to avoid CORS issues
@app.route('/api/market_prices')
def proxy_market_prices():
    try:
        response = requests.get(f"{API_BASE}/market_prices", timeout=10)
        response.raise_for_status()
        return jsonify(response.json())
    except Exception as e:
        print(f"Error fetching market prices: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/paper_trading')
def proxy_paper_trading():
    try:
        response = requests.get(f"{API_BASE}/paper_trading", timeout=10)
        response.raise_for_status()
        return jsonify(response.json())
    except Exception as e:
        print(f"Error fetching paper trading data: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/signals')
def proxy_signals():
    try:
        response = requests.get(f"{API_BASE}/signals", timeout=10)
        response.raise_for_status()
        return jsonify(response.json())
    except Exception as e:
        print(f"Error fetching signals: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/health')
def health():
    return jsonify({"status": "ok", "api_base": API_BASE})

@app.route('/test')
def browser_test():
    """Browser test page"""
    try:
        with open('dashboard_browser_test.html', 'r') as f:
            return f.read()
    except:
        return "Test page not found"

if __name__ == '__main__':
    print("🦞 Starting Fixed Trading View on port 5679...")
    app.run(host='0.0.0.0', port=5679, debug=False)