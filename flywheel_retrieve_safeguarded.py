#!/usr/bin/env python3
"""
💰 RETRIEVE FLYWHEEL - SAFEGUARDED VERSION
Harvests profits and maintains liquidity with council oversight
"""

import json
import time
from datetime import datetime
from coinbase.rest import RESTClient
import os

class RetrieveFlywheel:
    def __init__(self):
        self.config = json.load(open("/home/dereadi/.coinbase_config.json"))
        self.key = self.config["api_key"].split("/")[-1]
        self.client = RESTClient(api_key=self.key, api_secret=self.config["api_secret"], timeout=10)
        
        # SAFEGUARDS
        self.MIN_LIQUIDITY_TARGET = 250  # Target minimum cash
        self.EMERGENCY_LIQUIDITY = 100  # Emergency liquidation trigger
        self.PROFIT_TAKE_THRESHOLD = 10  # Take profits at +10%
        self.MAX_POSITION_PERCENT = 40  # Rebalance if any position > 40%
        self.COUNCIL_THRESHOLD = 100  # Council approval for large liquidations
        
        self.cycle_retrieved = 0
        self.start_time = datetime.now()
        
        # Track cost basis for profit calculation
        self.load_cost_basis()
    
    def load_cost_basis(self):
        """Load or initialize cost basis tracking"""
        try:
            with open("cost_basis.json", 'r') as f:
                self.cost_basis = json.load(f)
        except:
            # Initialize with estimates based on recent prices
            self.cost_basis = {
                "SOL": 190,
                "ETH": 3100,
                "BTC": 105000,
                "AVAX": 35,
                "MATIC": 0.70,
                "DOGE": 0.35,
                "XRP": 2.20,
                "LINK": 20
            }
    
    def save_cost_basis(self):
        """Save cost basis for tracking"""
        with open("cost_basis.json", 'w') as f:
            json.dump(self.cost_basis, f, indent=2)
    
    def get_portfolio_state(self):
        """Get current portfolio positions and liquidity"""
        portfolio = {"USD": 0, "positions": {}, "total_value": 0}
        
        try:
            accounts = self.client.get_accounts()["accounts"]
            
            for account in accounts:
                currency = account["currency"]
                balance = float(account["available_balance"]["value"])
                
                if balance > 0.00001:
                    if currency == "USD":
                        portfolio["USD"] = balance
                        portfolio["total_value"] += balance
                    else:
                        # Get current price
                        try:
                            ticker = self.client.get_product(f"{currency}-USD")
                            price = float(ticker.get("price", 0))
                            value = balance * price
                            
                            portfolio["positions"][currency] = {
                                "balance": balance,
                                "price": price,
                                "value": value,
                                "cost_basis": self.cost_basis.get(currency, price),
                                "profit_pct": ((price - self.cost_basis.get(currency, price)) / self.cost_basis.get(currency, price)) * 100
                            }
                            portfolio["total_value"] += value
                        except:
                            pass
            
            # Calculate position percentages
            for coin in portfolio["positions"]:
                portfolio["positions"][coin]["percent"] = (
                    portfolio["positions"][coin]["value"] / portfolio["total_value"] * 100
                )
            
        except Exception as e:
            print(f"❌ Error getting portfolio: {str(e)[:100]}")
        
        return portfolio
    
    def get_council_approval(self, action, coin, amount):
        """Get council approval for large liquidations"""
        print(f"\n🏛️ COUNCIL VOTE REQUESTED:")
        print(f"Action: {action} {coin}")
        print(f"Amount: ${amount:.2f}")
        
        # Simulate council voting
        votes = {
            "Mountain": amount < 200,  # Conservative
            "Thunder": False,  # Doesn't like selling
            "Fire": amount < 150,  # Moderate
            "Eagle": True,  # Practical
            "Turtle": True  # Likes liquidity
        }
        
        approval_count = sum(votes.values())
        print(f"Votes: {approval_count}/5")
        
        if approval_count >= 3:
            print("✅ APPROVED by council")
            return True
        else:
            print("❌ REJECTED by council")
            return False
    
    def identify_harvest_opportunities(self, portfolio):
        """Identify which positions to harvest"""
        opportunities = []
        
        # Check liquidity status
        liquidity_deficit = max(0, self.MIN_LIQUIDITY_TARGET - portfolio["USD"])
        
        for coin, data in portfolio["positions"].items():
            # Priority 1: Take profits on winners
            if data["profit_pct"] > self.PROFIT_TAKE_THRESHOLD:
                opportunities.append({
                    "coin": coin,
                    "action": "profit_take",
                    "reason": f"+{data['profit_pct']:.1f}% profit",
                    "amount": data["value"] * 0.25,  # Take 25% of winners
                    "priority": 1
                })
            
            # Priority 2: Rebalance oversized positions
            elif data["percent"] > self.MAX_POSITION_PERCENT:
                excess = data["percent"] - self.MAX_POSITION_PERCENT
                amount = (excess / 100) * portfolio["total_value"]
                opportunities.append({
                    "coin": coin,
                    "action": "rebalance",
                    "reason": f"{data['percent']:.1f}% of portfolio",
                    "amount": amount,
                    "priority": 2
                })
            
            # Priority 3: Emergency liquidity if needed
            elif portfolio["USD"] < self.EMERGENCY_LIQUIDITY and data["value"] > 50:
                opportunities.append({
                    "coin": coin,
                    "action": "emergency",
                    "reason": "Liquidity emergency",
                    "amount": min(data["value"] * 0.5, liquidity_deficit),
                    "priority": 0  # Highest priority
                })
        
        # Sort by priority (lower number = higher priority)
        opportunities.sort(key=lambda x: x["priority"])
        return opportunities
    
    def execute_harvest(self, opportunity, portfolio):
        """Execute a harvest (sell) order"""
        coin = opportunity["coin"]
        target_usd = opportunity["amount"]
        
        print(f"\n💸 HARVESTING {coin}:")
        print(f"Reason: {opportunity['reason']}")
        print(f"Target: ${target_usd:.2f}")
        
        # Check council approval for large amounts
        if target_usd > self.COUNCIL_THRESHOLD:
            if not self.get_council_approval("Harvest", coin, target_usd):
                return False
        
        try:
            # Calculate how much to sell
            coin_data = portfolio["positions"][coin]
            coin_amount = target_usd / coin_data["price"]
            
            # Don't sell more than we have
            coin_amount = min(coin_amount, coin_data["balance"] * 0.95)
            
            # Round to appropriate decimals
            if coin == "BTC":
                coin_amount = round(coin_amount, 8)
            elif coin in ["ETH", "SOL"]:
                coin_amount = round(coin_amount, 4)
            else:
                coin_amount = round(coin_amount, 2)
            
            # Execute market sell
            order = self.client.market_order_sell(
                client_order_id=f"retrieve_{coin}_{int(time.time()*1000)}",
                product_id=f"{coin}-USD",
                base_size=str(coin_amount)
            )
            
            actual_usd = coin_amount * coin_data["price"]
            print(f"✅ Harvested {coin_amount} {coin} for ~${actual_usd:.2f}")
            
            self.cycle_retrieved += actual_usd
            self.log_harvest(coin, coin_amount, coin_data["price"], opportunity["reason"])
            
            return True
            
        except Exception as e:
            print(f"❌ Harvest failed: {str(e)[:50]}")
            return False
    
    def log_harvest(self, coin, amount, price, reason):
        """Log harvest for tracking"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "coin": coin,
            "amount": amount,
            "price": price,
            "usd_value": amount * price,
            "reason": reason,
            "cycle_total": self.cycle_retrieved
        }
        
        log_file = "flywheel_retrieve_log.json"
        
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
        """Run one retrieval cycle"""
        print("\n" + "=" * 60)
        print(f"💰 RETRIEVE FLYWHEEL CYCLE - {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 60)
        
        # Get portfolio state
        portfolio = self.get_portfolio_state()
        
        print(f"💵 Current liquidity: ${portfolio['USD']:.2f}")
        print(f"📊 Total portfolio: ${portfolio['total_value']:.2f}")
        print(f"🎯 Liquidity target: ${self.MIN_LIQUIDITY_TARGET}")
        print(f"💸 Retrieved this hour: ${self.cycle_retrieved:.2f}")
        
        # Check if we need to harvest
        if portfolio["USD"] >= self.MIN_LIQUIDITY_TARGET:
            print("✅ Liquidity sufficient")
            
            # Still check for profit-taking opportunities
            opportunities = self.identify_harvest_opportunities(portfolio)
            profit_ops = [o for o in opportunities if o["action"] == "profit_take"]
            
            if profit_ops:
                print(f"\n🎯 Found {len(profit_ops)} profit-taking opportunities")
                # Take profits on best opportunity
                if profit_ops[0]["priority"] == 1:  # High profit
                    self.execute_harvest(profit_ops[0], portfolio)
        else:
            liquidity_gap = self.MIN_LIQUIDITY_TARGET - portfolio["USD"]
            print(f"⚠️ Need to raise ${liquidity_gap:.2f}")
            
            # Find harvest opportunities
            opportunities = self.identify_harvest_opportunities(portfolio)
            
            if not opportunities:
                print("📍 No harvest opportunities available")
                if portfolio["USD"] < self.EMERGENCY_LIQUIDITY:
                    print("🚨 EMERGENCY: Liquidity critically low!")
                return
            
            print(f"\n🎯 Found {len(opportunities)} harvest opportunities:")
            for opp in opportunities[:3]:
                print(f"  • {opp['coin']}: {opp['reason']} (${opp['amount']:.2f})")
            
            # Execute best opportunity
            harvested = 0
            for opp in opportunities:
                if portfolio["USD"] + harvested >= self.MIN_LIQUIDITY_TARGET:
                    break
                
                if self.execute_harvest(opp, portfolio):
                    harvested += opp["amount"]
    
    def run(self):
        """Main retrieval loop"""
        print("🚀 RETRIEVE FLYWHEEL INITIALIZED")
        print(f"Liquidity target: ${self.MIN_LIQUIDITY_TARGET}")
        print(f"Emergency threshold: ${self.EMERGENCY_LIQUIDITY}")
        print(f"Profit threshold: +{self.PROFIT_TAKE_THRESHOLD}%")
        print(f"Position limit: {self.MAX_POSITION_PERCENT}%")
        
        while True:
            try:
                # Reset cycle counter every hour
                if (datetime.now() - self.start_time).seconds > 3600:
                    self.cycle_retrieved = 0
                    self.start_time = datetime.now()
                    print("\n🔄 Cycle reset - new hour")
                
                self.run_cycle()
                
                # Wait 5 minutes between cycles
                print("\n⏰ Next check in 5 minutes...")
                time.sleep(300)
                
            except KeyboardInterrupt:
                print("\n🛑 Retrieve Flywheel stopped by user")
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                time.sleep(60)

if __name__ == "__main__":
    flywheel = RetrieveFlywheel()
    flywheel.run()