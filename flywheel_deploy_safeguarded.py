#!/usr/bin/env python3
"""
⚡ DEPLOY FLYWHEEL - SAFEGUARDED VERSION
Aggressive accumulation with council oversight and limits
"""

import json
import time
from datetime import datetime
from coinbase.rest import RESTClient
import os
import subprocess

class DeployFlywheel:
    def __init__(self):
        self.config = json.load(open("/home/dereadi/.coinbase_config.json"))
        self.key = self.config["api_key"].split("/")[-1]
        self.client = RESTClient(api_key=self.key, api_secret=self.config["api_secret"], timeout=10)
        
        # SAFEGUARDS
        self.MAX_DEPLOYMENT_PER_CYCLE = 300  # Maximum $300 per cycle
        self.MAX_SINGLE_TRADE = 150  # Maximum $150 per single trade
        self.MIN_LIQUIDITY_RESERVE = 250  # Always keep $250 minimum
        self.MAX_POSITION_PERCENT = 40  # No asset > 40% of portfolio
        self.COUNCIL_THRESHOLD = 100  # Trades > $100 need approval
        
        self.cycle_deployment = 0
        self.start_time = datetime.now()
        
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
    
    def get_council_approval(self, action, amount):
        """Simulate council voting (in production, would query actual council)"""
        print(f"\n🏛️ COUNCIL VOTE REQUESTED:")
        print(f"Action: {action}")
        print(f"Amount: ${amount:.2f}")
        
        # Check with council components
        votes = {
            "Mountain": amount < 200,  # Conservative
            "Thunder": True,  # Aggressive
            "Fire": amount < 150,  # Moderate
            "Eagle": True,  # Supports action
            "Turtle": amount < 100  # Very conservative
        }
        
        approval_count = sum(votes.values())
        print(f"Votes: {approval_count}/5")
        
        if approval_count >= 3:
            print("✅ APPROVED by council")
            return True
        else:
            print("❌ REJECTED by council")
            return False
    
    def check_safeguards(self, amount):
        """Verify all safeguards before deployment"""
        liquidity = self.check_liquidity()
        
        # Check 1: Minimum liquidity reserve
        if liquidity - amount < self.MIN_LIQUIDITY_RESERVE:
            print(f"❌ Would breach minimum reserve (${self.MIN_LIQUIDITY_RESERVE})")
            return False
        
        # Check 2: Max deployment per cycle
        if self.cycle_deployment + amount > self.MAX_DEPLOYMENT_PER_CYCLE:
            remaining = self.MAX_DEPLOYMENT_PER_CYCLE - self.cycle_deployment
            print(f"⚠️ Cycle limit reached. Only ${remaining:.2f} available")
            return False
        
        # Check 3: Single trade limit
        if amount > self.MAX_SINGLE_TRADE:
            print(f"❌ Exceeds single trade limit (${self.MAX_SINGLE_TRADE})")
            return False
        
        # Check 4: Council approval for large trades
        if amount > self.COUNCIL_THRESHOLD:
            if not self.get_council_approval("Deploy Capital", amount):
                return False
        
        return True
    
    def find_opportunities(self):
        """Identify buying opportunities"""
        opportunities = []
        
        targets = {
            "SOL": {"target": 203, "max_buy": 100},
            "ETH": {"target": 3200, "max_buy": 100},
            "BTC": {"target": 106500, "max_buy": 100}
        }
        
        for coin, params in targets.items():
            try:
                ticker = self.client.get_product(f"{coin}-USD")
                price = float(ticker.get("price", 0))
                
                if price <= params["target"]:
                    discount = ((params["target"] - price) / params["target"]) * 100
                    opportunities.append({
                        "coin": coin,
                        "price": price,
                        "target": params["target"],
                        "discount": discount,
                        "max_buy": params["max_buy"]
                    })
            except:
                pass
        
        # Sort by discount percentage
        opportunities.sort(key=lambda x: x["discount"], reverse=True)
        return opportunities
    
    def execute_deployment(self, opportunity):
        """Execute a buy order with safeguards"""
        coin = opportunity["coin"]
        amount = min(opportunity["max_buy"], self.MAX_SINGLE_TRADE)
        
        print(f"\n💸 DEPLOYING CAPITAL:")
        print(f"Buying {coin} at ${opportunity['price']:.2f} ({opportunity['discount']:.1f}% discount)")
        
        if not self.check_safeguards(amount):
            return False
        
        try:
            # Execute market buy
            order = self.client.market_order_buy(
                client_order_id=f"deploy_{coin}_{int(time.time()*1000)}",
                product_id=f"{coin}-USD",
                quote_size=str(amount)
            )
            
            print(f"✅ Deployed ${amount} into {coin}")
            self.cycle_deployment += amount
            
            # Log the deployment
            self.log_deployment(coin, amount, opportunity["price"])
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
            "cycle_total": self.cycle_deployment
        }
        
        log_file = "flywheel_deploy_log.json"
        
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
        print("\n" + "=" * 60)
        print(f"⚡ DEPLOY FLYWHEEL CYCLE - {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 60)
        
        # Check liquidity
        liquidity = self.check_liquidity()
        print(f"💰 Available liquidity: ${liquidity:.2f}")
        print(f"📊 Cycle deployment so far: ${self.cycle_deployment:.2f}")
        print(f"🎯 Remaining capacity: ${self.MAX_DEPLOYMENT_PER_CYCLE - self.cycle_deployment:.2f}")
        
        if liquidity < self.MIN_LIQUIDITY_RESERVE + 50:
            print("⚠️ Liquidity too low for deployment")
            return
        
        # Find opportunities
        opportunities = self.find_opportunities()
        
        if not opportunities:
            print("📍 No opportunities meeting criteria")
            return
        
        print(f"\n🎯 Found {len(opportunities)} opportunities:")
        for opp in opportunities[:3]:
            print(f"  • {opp['coin']}: ${opp['price']:.2f} ({opp['discount']:.1f}% discount)")
        
        # Deploy to best opportunity
        if opportunities:
            best = opportunities[0]
            if best["discount"] > 1.0:  # Only buy if >1% discount
                self.execute_deployment(best)
            else:
                print("📍 Discounts too small, waiting for better entry")
    
    def run(self):
        """Main flywheel loop"""
        print("🚀 DEPLOY FLYWHEEL INITIALIZED")
        print(f"Max per cycle: ${self.MAX_DEPLOYMENT_PER_CYCLE}")
        print(f"Min reserve: ${self.MIN_LIQUIDITY_RESERVE}")
        print(f"Council threshold: ${self.COUNCIL_THRESHOLD}")
        
        while True:
            try:
                # Reset cycle counter every hour
                if (datetime.now() - self.start_time).seconds > 3600:
                    self.cycle_deployment = 0
                    self.start_time = datetime.now()
                    print("\n🔄 Cycle reset - new hour")
                
                self.run_cycle()
                
                # Wait 5 minutes between cycles
                print("\n⏰ Next check in 5 minutes...")
                time.sleep(300)
                
            except KeyboardInterrupt:
                print("\n🛑 Deploy Flywheel stopped by user")
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                time.sleep(60)

if __name__ == "__main__":
    flywheel = DeployFlywheel()
    flywheel.run()