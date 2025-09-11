#!/usr/bin/env python3
"""
⚡🧽 DEPLOY FLYWHEEL WITH SPONGY THROTTLE
Aggressive but controlled deployment with elastic resistance
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

class SpongyDeployFlywheel:
    def __init__(self):
        self.config = json.load(open("/home/dereadi/.coinbase_config.json"))
        self.key = self.config["api_key"].split("/")[-1]
        self.client = RESTClient(api_key=self.key, api_secret=self.config["api_secret"], timeout=10)
        
        # Initialize spongy throttle
        self.throttle = SpongyThrottle()
        
        # Base parameters (adjusted by throttle)
        self.MIN_LIQUIDITY_RESERVE = 100  # Always keep $100 minimum
        self.OPPORTUNITY_THRESHOLD = 2  # Buy when >2% below target
        
        print("🧽 SPONGY DEPLOY FLYWHEEL INITIALIZED")
        print("=" * 60)
        status = self.throttle.get_status()
        print(f"Throttle Pressure: {status['pressure']:.1f}x")
        print(f"Max Trade Size: ${status['max_trade_size']:.2f}")
        print(f"Trade Delay: {status['next_trade_delay']}s")
        print(f"Status: {status['recommendation']}")
        print("=" * 60)
    
    def check_liquidity(self):
        """Check available liquidity"""
        try:
            accounts = self.client.get_accounts()["accounts"]
            for account in accounts:
                if account["currency"] == "USD":
                    return float(account["available_balance"]["value"])
            return 0
        except:
            return 0
    
    def find_opportunities(self):
        """Find buying opportunities"""
        opportunities = []
        
        # Current market estimates
        targets = {
            "SOL": {"current": 205, "target": 200, "max_position": 20},
            "ETH": {"current": 4350, "target": 4200, "max_position": 0.5},
            "BTC": {"current": 108500, "target": 107000, "max_position": 0.05},
            "AVAX": {"current": 38, "target": 36, "max_position": 100},
            "MATIC": {"current": 0.73, "target": 0.70, "max_position": 10000}
        }
        
        for coin, params in targets.items():
            discount = ((params["target"] - params["current"]) / params["target"]) * 100
            
            if discount > self.OPPORTUNITY_THRESHOLD:
                opportunities.append({
                    "coin": coin,
                    "current_price": params["current"],
                    "target_price": params["target"],
                    "discount": abs(discount),
                    "max_position": params["max_position"]
                })
        
        # Sort by discount
        opportunities.sort(key=lambda x: x["discount"], reverse=True)
        return opportunities
    
    def check_position_size(self, coin):
        """Check current position size"""
        try:
            accounts = self.client.get_accounts()["accounts"]
            for account in accounts:
                if account["currency"] == coin:
                    return float(account["available_balance"]["value"])
            return 0
        except:
            return 0
    
    def execute_deployment(self, opportunity, liquidity):
        """Execute a buy with spongy throttle"""
        coin = opportunity["coin"]
        
        # Get throttle status
        status = self.throttle.get_status()
        max_trade = min(status["max_trade_size"], liquidity - self.MIN_LIQUIDITY_RESERVE)
        
        # Check if we can trade
        can_trade, message = self.throttle.should_trade(max_trade)
        
        if not can_trade:
            print(f"🧽 {message}")
            return False
        
        # Check position limits
        current_position = self.check_position_size(coin)
        if current_position >= opportunity["max_position"] * 0.9:
            print(f"📊 Position limit reached for {coin}")
            return False
        
        # Calculate trade size (decreases with pressure)
        trade_size = min(
            max_trade,
            50 / status["pressure"]  # Base $50 divided by pressure
        )
        
        if trade_size < 20:
            print(f"📉 Trade size too small at current pressure")
            return False
        
        print(f"\n💸 SPONGY DEPLOYMENT:")
        print(f"Coin: {coin}")
        print(f"Amount: ${trade_size:.2f}")
        print(f"Discount: {opportunity['discount']:.1f}%")
        print(f"Throttle: {status['pressure']:.1f}x pressure")
        
        try:
            # Execute market buy
            order = self.client.market_order_buy(
                client_order_id=f"spongy_{coin}_{int(time.time()*1000)}",
                product_id=f"{coin}-USD",
                quote_size=str(trade_size)
            )
            
            print(f"✅ Deployed ${trade_size:.2f} into {coin}")
            
            # Record trade to increase throttle pressure
            self.throttle.record_trade(trade_size)
            
            # Log the deployment
            self.log_deployment(coin, trade_size, opportunity["current_price"])
            return True
            
        except Exception as e:
            print(f"❌ Deployment failed: {str(e)[:50]}")
            return False
    
    def log_deployment(self, coin, amount, price):
        """Log deployment for tracking"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "coin": coin,
            "amount": amount,
            "price": price,
            "pressure": self.throttle.get_pressure()
        }
        
        log_file = "spongy_deploy_log.json"
        
        try:
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            logs.append(log_entry)
            
            with open(log_file, 'w') as f:
                json.dump(logs, f, indent=2)
        except:
            pass
    
    def run_cycle(self):
        """Run one deployment cycle"""
        print(f"\n⚡ SPONGY DEPLOY CYCLE - {datetime.now().strftime('%H:%M:%S')}")
        print("-" * 40)
        
        # Get throttle status
        status = self.throttle.get_status()
        print(f"🧽 Throttle: {status['state']} ({status['pressure']:.1f}x)")
        
        # Check if we should even try
        if status["pressure"] >= 5:
            print("🛑 EMERGENCY BRAKE ENGAGED")
            print("Waiting for pressure to decrease...")
            return
        
        # Check liquidity
        liquidity = self.check_liquidity()
        print(f"💰 Available liquidity: ${liquidity:.2f}")
        
        if liquidity < self.MIN_LIQUIDITY_RESERVE + 20:
            print("⚠️ Insufficient liquidity for trading")
            return
        
        # Find opportunities
        opportunities = self.find_opportunities()
        
        if not opportunities:
            print("📍 No opportunities meeting criteria")
            return
        
        print(f"🎯 Found {len(opportunities)} opportunities")
        
        # Try to execute best opportunity
        for opp in opportunities[:1]:  # Only try the best one
            if self.execute_deployment(opp, liquidity):
                break
            
        # Show next trade timing
        print(f"⏰ Next trade in: {status['next_trade_delay']}s")
    
    def run(self):
        """Main flywheel loop with spongy behavior"""
        print("\n🚀 SPONGY DEPLOY FLYWHEEL STARTED")
        print("The throttle will resist aggressive trading")
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
                print("\n🛑 Spongy Deploy Flywheel stopped")
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                time.sleep(60)

if __name__ == "__main__":
    flywheel = SpongyDeployFlywheel()
    flywheel.run()