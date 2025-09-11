#!/usr/bin/env python3
"""
🐕 DOGE ETF Oscillation Trader
Capitalizes on DOGE volatility from ETF speculation
Compounds profits into Core Four positions
"""

import os
import json
import time
from datetime import datetime
from coinbase.rest import RESTClient
from decimal import Decimal, ROUND_DOWN

# Configuration
API_KEY = os.getenv('CB_API_KEY', 'organizations/b3b7b43f-c54d-42d5-9143-d89cc4b207f2/apiKeys/330f8a6f-50f0-4154-be37-e00119b3797d')
API_SECRET = os.getenv('CB_API_SECRET', 'glLnt1HQz5jFJJJX3vE7+BqeHx+oaKdCL7nc3jgqgEWX9XkxlYRn8B/YQMgIXJaN')

# DOGE Oscillation Parameters
DOGE_SUPPORT = 0.230  # Strong support
DOGE_RESISTANCE_1 = 0.245  # First target
DOGE_RESISTANCE_2 = 0.260  # Second target
DOGE_ETF_TARGET = 0.300  # ETF announcement target

POSITION_SIZE_PERCENT = 0.25  # Trade 25% of DOGE position
MIN_PROFIT_PERCENT = 0.015  # 1.5% minimum profit target

class DOGEOscillator:
    def __init__(self):
        self.client = RESTClient(api_key=API_KEY, api_secret=API_SECRET)
        self.positions = {}
        self.prices = {}
        
    def log(self, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {message}")
        with open('/home/dereadi/scripts/claude/doge_oscillator.log', 'a') as f:
            f.write(f"[{timestamp}] {message}\n")
    
    def get_positions(self):
        """Get current DOGE position and Core Four balances"""
        try:
            accounts = self.client.get_accounts()
            self.positions = {}
            
            for account in accounts['accounts']:
                balance = float(account['available_balance']['value'])
                if balance > 0.01:
                    currency = account['currency']
                    if currency in ['DOGE', 'BTC', 'ETH', 'SOL', 'USD']:
                        self.positions[currency] = balance
            
            return self.positions
        except Exception as e:
            self.log(f"Error getting positions: {e}")
            return {}
    
    def get_prices(self):
        """Get current prices for DOGE and Core Four"""
        symbols = ['DOGE-USD', 'BTC-USD', 'ETH-USD', 'SOL-USD']
        self.prices = {}
        
        for symbol in symbols:
            try:
                ticker = self.client.get_product(symbol)
                price = float(ticker['price'])
                coin = symbol.split('-')[0]
                self.prices[coin] = price
            except:
                pass
        
        return self.prices
    
    def calculate_doge_strategy(self):
        """Determine DOGE oscillation action"""
        if 'DOGE' not in self.positions or 'DOGE' not in self.prices:
            return None
            
        doge_qty = self.positions.get('DOGE', 0)
        doge_price = self.prices['DOGE']
        doge_value = doge_qty * doge_price
        
        self.log(f"\n🐕 DOGE Analysis:")
        self.log(f"Position: {doge_qty:.2f} DOGE @ ${doge_price:.4f} = ${doge_value:.2f}")
        
        # Calculate tradeable amount
        trade_qty = doge_qty * POSITION_SIZE_PERCENT
        
        # Determine action based on price levels
        action = None
        
        if doge_price >= DOGE_RESISTANCE_2:
            action = {
                'type': 'SELL',
                'reason': 'Hit resistance 2 - Take profits!',
                'qty': trade_qty,
                'target_price': doge_price,
                'expected_proceeds': trade_qty * doge_price
            }
        elif doge_price >= DOGE_RESISTANCE_1:
            action = {
                'type': 'SELL',
                'reason': 'Hit resistance 1 - Partial profits',
                'qty': trade_qty * 0.5,  # Sell half at first resistance
                'target_price': doge_price,
                'expected_proceeds': (trade_qty * 0.5) * doge_price
            }
        elif doge_price <= DOGE_SUPPORT and self.positions.get('USD', 0) > 50:
            # Buy more at support if we have cash
            usd_available = self.positions.get('USD', 0) * 0.25  # Use 25% of cash
            buy_qty = usd_available / doge_price
            action = {
                'type': 'BUY',
                'reason': 'Support bounce opportunity',
                'qty': buy_qty,
                'target_price': doge_price,
                'cost': usd_available
            }
        
        # Check ETF speculation zones
        if doge_price >= 0.270:
            self.log("⚠️ DOGE approaching ETF speculation zone ($0.27+)")
            self.log("Consider taking 50% profits and letting rest ride to $0.30")
        
        return action
    
    def suggest_reinvestment(self, proceeds):
        """Suggest where to reinvest DOGE profits"""
        suggestions = []
        
        # Check which Core Four asset is most oversold
        if 'BTC' in self.prices:
            btc_price = self.prices['BTC']
            if btc_price < 111000:  # Below recent support
                suggestions.append(f"BTC at ${btc_price:,.0f} (below $111k support)")
        
        if 'ETH' in self.prices:
            eth_price = self.prices['ETH']
            if eth_price < 4300:  # Below recent range
                suggestions.append(f"ETH at ${eth_price:,.0f} (below $4,300)")
        
        if 'SOL' in self.prices:
            sol_price = self.prices['SOL']
            if sol_price < 210:  # Below recent levels
                suggestions.append(f"SOL at ${sol_price:.2f} (below $210)")
        
        if suggestions:
            self.log(f"\n💡 Reinvestment opportunities with ${proceeds:.2f}:")
            for suggestion in suggestions:
                self.log(f"  • {suggestion}")
        
        return suggestions
    
    def monitor_etf_news(self):
        """Check for ETF-related price action"""
        if 'DOGE' in self.prices:
            doge_price = self.prices['DOGE']
            
            # Calculate distance to ETF target
            distance_to_target = DOGE_ETF_TARGET - doge_price
            percent_to_target = (distance_to_target / doge_price) * 100
            
            self.log(f"\n📊 ETF Speculation Metrics:")
            self.log(f"Current: ${doge_price:.4f}")
            self.log(f"ETF Target: ${DOGE_ETF_TARGET:.4f}")
            self.log(f"Upside: {percent_to_target:.1f}%")
            
            if percent_to_target < 10:
                self.log("🚨 APPROACHING ETF TARGET - Consider profit taking!")
    
    def run(self):
        """Main oscillation loop"""
        self.log("=" * 50)
        self.log("🐕 DOGE ETF Oscillator Starting")
        self.log("Strategy: Trade DOGE volatility, compound into Core Four")
        self.log("=" * 50)
        
        while True:
            try:
                # Update positions and prices
                self.get_positions()
                self.get_prices()
                
                # Check DOGE strategy
                action = self.calculate_doge_strategy()
                
                if action:
                    self.log(f"\n🎯 Action suggested: {action['type']}")
                    self.log(f"Reason: {action['reason']}")
                    self.log(f"Quantity: {action['qty']:.2f} DOGE")
                    
                    if action['type'] == 'SELL':
                        self.log(f"Expected proceeds: ${action['expected_proceeds']:.2f}")
                        self.suggest_reinvestment(action['expected_proceeds'])
                
                # Monitor ETF speculation
                self.monitor_etf_news()
                
                # Show Core Four status
                self.log(f"\n📊 Core Four Prices:")
                for coin in ['BTC', 'ETH', 'SOL']:
                    if coin in self.prices:
                        self.log(f"{coin}: ${self.prices[coin]:,.2f}")
                
                # Wait 5 minutes
                self.log("\n⏰ Next check in 5 minutes...")
                time.sleep(300)
                
            except Exception as e:
                self.log(f"Error in main loop: {e}")
                time.sleep(60)

if __name__ == "__main__":
    oscillator = DOGEOscillator()
    oscillator.run()