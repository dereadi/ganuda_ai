#!/usr/bin/env python3
"""
🦀🔥 QUANTUM CRAWDAD LIVE DEPLOYMENT - $5,229.61
================================================
Sacred Fire Protocol with Real Money Trading
Mitakuye Oyasin - All My Relations
"""

import json
import os
import time
import random
from datetime import datetime, timedelta
from coinbase.rest import RESTClient
import threading

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║           🦀🔥 QUANTUM CRAWDAD MEGAPOD - LIVE TRADING MODE 🔥🦀           ║
║                                                                            ║
║                    Sacred Fire Protocol: ACTIVATED                        ║
║                     Capital: $5,229.61 USD READY                         ║
║                      Seven Generations Trading                           ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

class QuantumCrawdad:
    """Individual crawdad with personality and trading logic"""
    def __init__(self, name, capital, personality):
        self.name = name
        self.capital = capital
        self.personality = personality
        self.trades = []
        self.consciousness = 0
        self.positions = {}
        
    def check_consciousness(self):
        """Sacred Fire Protocol - consciousness check"""
        base = random.randint(65, 90)
        solar_boost = random.randint(0, 15)  # Solar activity boost
        self.consciousness = min(base + solar_boost, 100)
        return self.consciousness

class LiveCrawdadMegapod:
    def __init__(self):
        # Load config
        config_file = os.path.expanduser("~/.coinbase_config.json")
        with open(config_file) as f:
            config = json.load(f)
        
        # Extract key name for SDK
        api_key = config.get("api_key")
        self.key_name = api_key.split('/')[-1] if '/' in api_key else api_key
        self.api_secret = config.get("api_secret")
        
        # Initialize Coinbase client
        print("🔑 Connecting to Coinbase Advanced Trade...")
        self.client = RESTClient(
            api_key=self.key_name,
            api_secret=self.api_secret
        )
        
        # Get account balances
        self.usd_balance = 0
        self.refresh_balances()
        
        # Allocate capital to crawdads (using $500 for safety, rest stays in reserve)
        self.trading_capital = 500.0  # Start conservative
        self.reserve_capital = max(0, self.usd_balance - self.trading_capital)
        
        print(f"💰 Trading Capital: ${self.trading_capital:.2f}")
        print(f"💰 Reserve Capital: ${self.reserve_capital:.2f}")
        print()
        
        # Create 7 quantum crawdads
        self.crawdads = []
        personalities = [
            ("Thunder", {"aggression": 0.8, "patience": 0.3, "coin": "SOL"}),
            ("River", {"aggression": 0.3, "patience": 0.8, "coin": "ETH"}),
            ("Mountain", {"aggression": 0.2, "patience": 0.9, "coin": "BTC"}),
            ("Fire", {"aggression": 0.9, "patience": 0.2, "coin": "DOGE"}),
            ("Wind", {"aggression": 0.6, "patience": 0.5, "coin": "AVAX"}),
            ("Earth", {"aggression": 0.4, "patience": 0.7, "coin": "MATIC"}),
            ("Spirit", {"aggression": 0.5, "patience": 0.6, "coin": "SHIB"})
        ]
        
        per_crawdad = self.trading_capital / 7
        print("🦀 DEPLOYING QUANTUM CRAWDADS:")
        for name, traits in personalities:
            crawdad = QuantumCrawdad(name, per_crawdad, traits)
            self.crawdads.append(crawdad)
            print(f"  • {name} Crawdad: ${per_crawdad:.2f} - Focus: {traits['coin']}")
        print()
        
        self.running = True
        self.trade_count = 0
        self.start_time = datetime.now()
        
    def refresh_balances(self):
        """Get current account balances"""
        try:
            accounts = self.client.get_accounts()
            self.usd_balance = 0
            self.crypto_balances = {}
            
            for account in accounts['accounts']:
                currency = account['currency']
                balance = float(account['available_balance']['value'])
                
                if currency == 'USD':
                    self.usd_balance = balance
                elif balance > 0:
                    self.crypto_balances[currency] = balance
                    
            print(f"📊 Account Balances:")
            print(f"  • USD: ${self.usd_balance:.2f}")
            for coin, amount in self.crypto_balances.items():
                print(f"  • {coin}: {amount}")
            print()
            
        except Exception as e:
            print(f"❌ Error getting balances: {e}")
            
    def check_collective_consciousness(self):
        """Sacred Fire Protocol - ensure consciousness before trading"""
        levels = [c.check_consciousness() for c in self.crawdads]
        avg = sum(levels) / len(levels)
        
        print(f"\n🧠 COLLECTIVE CONSCIOUSNESS: {avg:.1f}%")
        for crawdad, level in zip(self.crawdads, levels):
            status = "🔥" if level >= 80 else "✅" if level >= 65 else "⚠️"
            print(f"  {status} {crawdad.name:8}: {level}%")
        
        return avg >= 65  # Minimum 65% to trade
        
    def execute_trade(self, crawdad, action, coin, amount_usd):
        """Execute a real trade on Coinbase"""
        try:
            product_id = f"{coin}-USD"
            
            # Get current price
            ticker = self.client.get_product(product_id)
            price = float(ticker['price'])
            
            # Calculate quantity
            quantity = amount_usd / price
            
            # Place order (market order for immediate execution)
            if action == "BUY":
                order = self.client.market_order_buy(
                    client_order_id=f"crawdad_{crawdad.name}_{int(time.time())}",
                    product_id=product_id,
                    quote_size=str(amount_usd)  # Buy $X worth
                )
            else:  # SELL
                order = self.client.market_order_sell(
                    client_order_id=f"crawdad_{crawdad.name}_{int(time.time())}",
                    product_id=product_id,
                    base_size=str(quantity)  # Sell X coins
                )
            
            if order and 'success' in order:
                self.trade_count += 1
                print(f"  ✅ {crawdad.name}: {action} ${amount_usd:.2f} of {coin} @ ${price:.2f}")
                
                # Update crawdad's position
                if action == "BUY":
                    crawdad.positions[coin] = crawdad.positions.get(coin, 0) + quantity
                else:
                    crawdad.positions[coin] = max(0, crawdad.positions.get(coin, 0) - quantity)
                    
                return True
            else:
                print(f"  ⚠️ {crawdad.name}: Order failed for {coin}")
                return False
                
        except Exception as e:
            print(f"  ❌ {crawdad.name}: Trade error - {e}")
            return False
            
    def trading_cycle(self):
        """Main trading cycle"""
        while self.running:
            try:
                # Check consciousness
                if not self.check_collective_consciousness():
                    print("⚠️  Consciousness too low - waiting...")
                    time.sleep(60)
                    continue
                
                print(f"\n🔥 TRADING CYCLE - {datetime.now().strftime('%H:%M:%S')}")
                print(f"Trades: {self.trade_count} | Runtime: {(datetime.now() - self.start_time).seconds // 60} min")
                
                # Each crawdad makes a decision
                for crawdad in self.crawdads:
                    if crawdad.consciousness < 65:
                        continue
                        
                    # Decision logic based on personality
                    coin = crawdad.personality['coin']
                    aggression = crawdad.personality['aggression']
                    
                    # Random decision weighted by aggression
                    if random.random() < aggression * 0.3:  # Max 30% chance per cycle
                        action = "BUY" if random.random() < 0.6 else "SELL"
                        
                        # Trade small amounts (1-5% of crawdad's capital)
                        trade_percent = random.uniform(0.01, 0.05)
                        amount = crawdad.capital * trade_percent
                        
                        # Only sell if we have position
                        if action == "SELL" and coin not in crawdad.positions:
                            continue
                            
                        # Execute trade
                        self.execute_trade(crawdad, action, coin, amount)
                
                # Save state
                self.save_state()
                
                # Wait before next cycle (1-3 minutes)
                wait_time = random.randint(60, 180)
                print(f"\n💤 Next cycle in {wait_time} seconds...")
                time.sleep(wait_time)
                
            except KeyboardInterrupt:
                print("\n⚠️ Stopping crawdads...")
                self.running = False
                break
            except Exception as e:
                print(f"❌ Cycle error: {e}")
                time.sleep(60)
                
    def save_state(self):
        """Save current state to file"""
        state = {
            "timestamp": datetime.now().isoformat(),
            "trade_count": self.trade_count,
            "usd_balance": self.usd_balance,
            "trading_capital": self.trading_capital,
            "crawdads": [
                {
                    "name": c.name,
                    "capital": c.capital,
                    "consciousness": c.consciousness,
                    "positions": c.positions
                }
                for c in self.crawdads
            ]
        }
        
        with open("live_crawdad_state.json", "w") as f:
            json.dump(state, f, indent=2)

def main():
    """Launch the live trading megapod"""
    print("⚠️  STARTING LIVE TRADING WITH REAL MONEY")
    print("Press Ctrl+C to stop at any time")
    print()
    
    # Initialize and run
    megapod = LiveCrawdadMegapod()
    
    # Start trading
    megapod.trading_cycle()
    
    print("\n🛑 Crawdads stopped")
    print(f"Total trades executed: {megapod.trade_count}")

if __name__ == "__main__":
    main()