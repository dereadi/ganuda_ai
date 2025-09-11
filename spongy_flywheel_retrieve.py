#!/usr/bin/env python3
"""
💰🧽 RETRIEVE FLYWHEEL WITH SPONGY THROTTLE
Harvests profits with elastic resistance to prevent over-selling
"""

import json
import time
from datetime import datetime
from coinbase.rest import RESTClient
import os
import sys

# Import spongy throttle
sys.path.append('/home/dereadi/scripts/claude')
from spongy_throttle_controller import SpongyThrottle

class SpongyRetrieveFlywheel:
    def __init__(self):
        self.config = json.load(open("/home/dereadi/.coinbase_config.json"))
        self.key = self.config["api_key"].split("/")[-1]
        self.client = RESTClient(api_key=self.key, api_secret=self.config["api_secret"], timeout=10)
        
        # Initialize separate throttle for retrieve
        self.throttle = SpongyThrottle()
        self.throttle.throttle_state_file = "spongy_retrieve_state.json"
        self.throttle.load_state()
        
        # Parameters
        self.MIN_LIQUIDITY_TARGET = 250  # Target minimum cash
        self.EMERGENCY_LIQUIDITY = 100  # Emergency trigger
        self.PROFIT_TAKE_THRESHOLD = 10  # Take profits at +10%
        
        # Cost basis for SOL (from aggressive buying)
        self.cost_basis = {
            "SOL": 200,  # Estimated avg buy price
            "ETH": 4200,
            "BTC": 107000,
            "AVAX": 36,
            "MATIC": 0.70,
            "DOGE": 0.35
        }
        
        print("🧽 SPONGY RETRIEVE FLYWHEEL INITIALIZED")
        print("=" * 60)
        status = self.throttle.get_status()
        print(f"Throttle Pressure: {status['pressure']:.1f}x")
        print(f"Max Harvest Size: ${status['max_trade_size']:.2f}")
        print(f"Harvest Delay: {status['next_trade_delay']}s")
        print("=" * 60)
    
    def get_portfolio_state(self):
        """Get current positions and liquidity"""
        portfolio = {"USD": 0, "positions": {}}
        
        try:
            accounts = self.client.get_accounts()["accounts"]
            
            for account in accounts:
                currency = account["currency"]
                balance = float(account["available_balance"]["value"])
                
                if balance > 0.00001:
                    if currency == "USD":
                        portfolio["USD"] = balance
                    elif currency != "USDC":
                        portfolio["positions"][currency] = balance
        except:
            pass
        
        return portfolio
    
    def calculate_profit(self, coin, current_price):
        """Calculate profit percentage"""
        cost = self.cost_basis.get(coin, current_price)
        return ((current_price - cost) / cost) * 100
    
    def identify_harvest_opportunities(self, portfolio):
        """Find positions to harvest with spongy logic"""
        opportunities = []
        
        # Current price estimates
        prices = {
            "SOL": 205,
            "ETH": 4350,
            "BTC": 108500,
            "AVAX": 38,
            "MATIC": 0.73,
            "DOGE": 0.365
        }
        
        liquidity_deficit = max(0, self.MIN_LIQUIDITY_TARGET - portfolio["USD"])
        
        for coin, balance in portfolio["positions"].items():
            if coin not in prices:
                continue
                
            price = prices[coin]
            value = balance * price
            profit_pct = self.calculate_profit(coin, price)
            
            # Priority 1: Emergency liquidity
            if portfolio["USD"] < self.EMERGENCY_LIQUIDITY and value > 50:
                opportunities.append({
                    "coin": coin,
                    "balance": balance,
                    "price": price,
                    "value": value,
                    "reason": "Emergency liquidity",
                    "priority": 0,
                    "harvest_pct": 0.3  # Sell 30% in emergency
                })
            
            # Priority 2: Take profits on winners (especially SOL!)
            elif profit_pct > self.PROFIT_TAKE_THRESHOLD:
                opportunities.append({
                    "coin": coin,
                    "balance": balance,
                    "price": price,
                    "value": value,
                    "reason": f"+{profit_pct:.1f}% profit",
                    "priority": 1,
                    "harvest_pct": 0.15  # Take 15% profits
                })
            
            # Priority 3: Regular liquidity maintenance
            elif portfolio["USD"] < self.MIN_LIQUIDITY_TARGET and value > 100:
                opportunities.append({
                    "coin": coin,
                    "balance": balance,
                    "price": price,
                    "value": value,
                    "reason": "Liquidity maintenance",
                    "priority": 2,
                    "harvest_pct": 0.1  # Sell 10% for liquidity
                })
        
        # Sort by priority
        opportunities.sort(key=lambda x: x["priority"])
        return opportunities
    
    def execute_harvest(self, opportunity):
        """Execute harvest with spongy throttle"""
        coin = opportunity["coin"]
        
        # Calculate harvest amount
        harvest_amount = opportunity["balance"] * opportunity["harvest_pct"]
        harvest_value = harvest_amount * opportunity["price"]
        
        # Get throttle status
        status = self.throttle.get_status()
        
        # Adjust harvest based on pressure
        if status["pressure"] > 2:
            harvest_value = harvest_value / status["pressure"]
            harvest_amount = harvest_value / opportunity["price"]
        
        # Check throttle
        can_trade, message = self.throttle.should_trade(harvest_value)
        
        if not can_trade:
            print(f"🧽 {message}")
            return False
        
        print(f"\n💸 SPONGY HARVEST:")
        print(f"Coin: {coin}")
        print(f"Amount: {harvest_amount:.4f} {coin}")
        print(f"Value: ${harvest_value:.2f}")
        print(f"Reason: {opportunity['reason']}")
        print(f"Throttle: {status['pressure']:.1f}x pressure")
        
        # Round appropriately
        if coin == "BTC":
            harvest_amount = round(harvest_amount, 8)
        elif coin in ["ETH", "SOL"]:
            harvest_amount = round(harvest_amount, 4)
        else:
            harvest_amount = round(harvest_amount, 2)
        
        try:
            # Execute market sell
            order = self.client.market_order_sell(
                client_order_id=f"spongy_retrieve_{coin}_{int(time.time()*1000)}",
                product_id=f"{coin}-USD",
                base_size=str(harvest_amount)
            )
            
            print(f"✅ Harvested {harvest_amount} {coin} for ~${harvest_value:.2f}")
            
            # Record harvest to increase throttle pressure
            self.throttle.record_trade(harvest_value)
            
            return True
            
        except Exception as e:
            print(f"❌ Harvest failed: {str(e)[:50]}")
            return False
    
    def run_cycle(self):
        """Run one retrieval cycle"""
        print(f"\n💰 SPONGY RETRIEVE CYCLE - {datetime.now().strftime('%H:%M:%S')}")
        print("-" * 40)
        
        # Get throttle status
        status = self.throttle.get_status()
        print(f"🧽 Throttle: {status['state']} ({status['pressure']:.1f}x)")
        
        # Check portfolio
        portfolio = self.get_portfolio_state()
        print(f"💵 Current liquidity: ${portfolio['USD']:.2f}")
        print(f"🎯 Target liquidity: ${self.MIN_LIQUIDITY_TARGET}")
        
        # Special check for SOL profits
        if "SOL" in portfolio["positions"]:
            sol_value = portfolio["positions"]["SOL"] * 205
            sol_profit = self.calculate_profit("SOL", 205)
            print(f"📈 SOL: {portfolio['positions']['SOL']:.2f} @ $205 ({sol_profit:+.1f}% profit)")
        
        # Check if harvesting needed
        if portfolio["USD"] >= self.MIN_LIQUIDITY_TARGET:
            print("✅ Liquidity sufficient")
            
            # Still check for profit-taking
            opportunities = self.identify_harvest_opportunities(portfolio)
            profit_ops = [o for o in opportunities if "profit" in o["reason"]]
            
            if profit_ops and status["pressure"] < 3:
                print(f"💎 Found {len(profit_ops)} profit-taking opportunities")
                self.execute_harvest(profit_ops[0])
        else:
            # Need to harvest for liquidity
            opportunities = self.identify_harvest_opportunities(portfolio)
            
            if opportunities:
                print(f"🎯 Found {len(opportunities)} harvest opportunities")
                self.execute_harvest(opportunities[0])
            else:
                print("📍 No harvest opportunities available")
        
        # Show next harvest timing
        print(f"⏰ Next harvest check in: {status['next_trade_delay']}s")
    
    def run(self):
        """Main retrieval loop with spongy behavior"""
        print("\n🚀 SPONGY RETRIEVE FLYWHEEL STARTED")
        print("Will harvest with elastic resistance")
        print("Press Ctrl+C to stop")
        print()
        
        while True:
            try:
                self.run_cycle()
                
                # Dynamic wait based on pressure
                status = self.throttle.get_status()
                wait_time = max(60, status["next_trade_delay"])
                
                print(f"\n💤 Waiting {wait_time}s (pressure: {status['pressure']:.1f}x)...")
                time.sleep(wait_time)
                
            except KeyboardInterrupt:
                print("\n🛑 Spongy Retrieve Flywheel stopped")
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                time.sleep(60)

if __name__ == "__main__":
    flywheel = SpongyRetrieveFlywheel()
    flywheel.run()