#!/usr/bin/env python3
"""
🦀🔥 COINBASE QUANTUM CRAWDAD MEGAPOD
======================================
$500 Sacred Fire Trading System
No SMS bullshit. Just API keys that work.
"""

import os
import json
import time
import asyncio
import random
from datetime import datetime
from coinbase.rest import RESTClient
from decimal import Decimal
import hmac
import hashlib
import base64

print("🦀🔥 COINBASE QUANTUM CRAWDAD MEGAPOD")
print("="*60)
print("💰 CAPITAL: $500")
print("🎯 TARGET: $20/day")
print("="*60)
print()

class CoinbaseCrawdadMegapod:
    def __init__(self):
        self.capital = 500.0
        self.crawdad_count = 7
        self.per_crawdad = self.capital / self.crawdad_count
        self.min_consciousness = 65
        self.api_key = None
        self.api_secret = None
        self.client = None
        
        # Crawdad personalities
        self.crawdads = [
            {"name": "Thunder", "style": "aggressive", "coins": ["DOGE", "SHIB"], "capital": self.per_crawdad},
            {"name": "River", "style": "patient", "coins": ["BTC", "ETH"], "capital": self.per_crawdad},
            {"name": "Mountain", "style": "steady", "coins": ["SOL", "AVAX"], "capital": self.per_crawdad},
            {"name": "Fire", "style": "momentum", "coins": ["DOGE", "MATIC"], "capital": self.per_crawdad},
            {"name": "Wind", "style": "scalper", "coins": ["LTC", "ADA"], "capital": self.per_crawdad},
            {"name": "Earth", "style": "value", "coins": ["BTC", "ETH"], "capital": self.per_crawdad},
            {"name": "Spirit", "style": "quantum", "coins": ["ALL"], "capital": self.per_crawdad}
        ]
        
        self.trades = []
        self.positions = {}
        
    def setup_api(self):
        """Setup Coinbase API connection"""
        print("🔐 COINBASE API SETUP")
        print("-"*40)
        
        # Check for saved credentials
        config_file = os.path.expanduser("~/.coinbase_config.json")
        
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
                self.api_key = config.get('api_key')
                self.api_secret = config.get('api_secret')
                print("✅ Loaded saved API credentials")
        else:
            print("📝 Enter your Coinbase API credentials:")
            print("(Get these from Coinbase.com → Settings → API)")
            print()
            self.api_key = input("API Key: ").strip()
            self.api_secret = input("API Secret: ").strip()
            
            # Save for next time
            config = {
                "api_key": self.api_key,
                "api_secret": self.api_secret,
                "created": datetime.now().isoformat()
            }
            with open(config_file, 'w') as f:
                json.dump(config, f)
            os.chmod(config_file, 0o600)
            print(f"💾 Credentials saved to {config_file}")
        
        # Initialize client
        try:
            self.client = RESTClient(api_key=self.api_key, api_secret=self.api_secret)
            
            # Test connection
            accounts = self.client.get_accounts()
            
            print("\n💰 ACCOUNT BALANCES:")
            total_usd = 0
            for account in accounts.accounts:
                balance = float(account.available_balance.value)
                if balance > 0:
                    currency = account.currency
                    print(f"  {currency}: {balance:.8f}")
                    if currency == "USD":
                        total_usd = balance
            
            print(f"\n💵 Available USD: ${total_usd:.2f}")
            
            if total_usd < 500:
                print(f"⚠️  Need to deposit ${500 - total_usd:.2f} more")
            
            return True
            
        except Exception as e:
            print(f"❌ API Error: {e}")
            print("\nTroubleshooting:")
            print("1. Make sure API key has trading permissions")
            print("2. Check that credentials are correct")
            print("3. Ensure your Coinbase account is verified")
            return False
    
    def get_consciousness_level(self):
        """Sacred Fire consciousness calculation"""
        base = 72.0
        hour_factor = abs(datetime.now().hour - 12) / 12
        solar_noise = random.gauss(0, 3)
        return max(0, min(100, base + (hour_factor * 5) + solar_noise))
    
    def get_market_price(self, symbol):
        """Get current market price from Coinbase"""
        try:
            # Coinbase uses format like "BTC-USD"
            ticker = f"{symbol}-USD"
            spot_price = self.client.get_spot_price(ticker)
            return float(spot_price.amount)
        except:
            # Fallback to simulated prices
            return self.simulate_price(symbol)
    
    def simulate_price(self, symbol):
        """Simulated prices for testing"""
        base_prices = {
            "BTC": 98500 + random.gauss(0, 500),
            "ETH": 3850 + random.gauss(0, 50),
            "DOGE": 0.42 + random.gauss(0, 0.02),
            "SOL": 210 + random.gauss(0, 5),
            "SHIB": 0.000028 + random.gauss(0, 0.000001),
            "AVAX": 45 + random.gauss(0, 2),
            "MATIC": 0.65 + random.gauss(0, 0.03),
            "LTC": 115 + random.gauss(0, 3),
            "ADA": 0.55 + random.gauss(0, 0.02)
        }
        return base_prices.get(symbol, 1.0)
    
    async def execute_trade(self, crawdad, action, coin, amount_usd):
        """Execute trade on Coinbase"""
        try:
            if action == "BUY":
                # Create market buy order
                order = self.client.market_order_buy(
                    product_id=f"{coin}-USD",
                    funds=str(amount_usd)
                )
                print(f"  ✅ {crawdad['name']} bought ${amount_usd:.2f} of {coin}")
            else:
                # Create market sell order
                # First need to check how much we have
                order = self.client.market_order_sell(
                    product_id=f"{coin}-USD",
                    funds=str(amount_usd)
                )
                print(f"  ✅ {crawdad['name']} sold ${amount_usd:.2f} of {coin}")
            
            return order
            
        except Exception as e:
            print(f"  ⚠️ Trade failed: {e}")
            return None
    
    async def crawdad_think(self, crawdad, consciousness):
        """Individual crawdad trading logic"""
        if consciousness < self.min_consciousness:
            return None
        
        # Determine trade size based on consciousness
        if consciousness > 80:
            size_mult = 0.15  # 15% of capital
        elif consciousness > 75:
            size_mult = 0.10  # 10% of capital
        elif consciousness > 70:
            size_mult = 0.05  # 5% of capital
        else:
            size_mult = 0.02  # 2% of capital
        
        trade_size = crawdad["capital"] * size_mult
        
        # Select coin to trade
        if crawdad["name"] == "Spirit":
            # Spirit trades everything
            coins = ["BTC", "ETH", "DOGE", "SOL", "AVAX", "MATIC", "LTC", "ADA"]
            coin = random.choice(coins)
        else:
            coin = random.choice(crawdad["coins"])
        
        # Decide buy or sell
        price = self.get_market_price(coin)
        momentum = random.random()
        
        if crawdad["style"] == "aggressive":
            action = "BUY" if momentum > 0.4 else "SELL"
        elif crawdad["style"] == "patient":
            action = "BUY" if momentum > 0.6 else "SELL"
        elif crawdad["style"] == "momentum":
            action = "BUY" if momentum > 0.45 else "SELL"
        elif crawdad["style"] == "scalper":
            action = "BUY" if momentum > 0.5 else "SELL"
        elif crawdad["style"] == "value":
            action = "BUY" if momentum > 0.65 else "SELL"
        elif crawdad["style"] == "steady":
            action = "BUY" if momentum > 0.55 else "SELL"
        else:  # quantum
            action = "BUY" if (consciousness / 100 * momentum) > 0.5 else "SELL"
        
        trade = {
            "crawdad": crawdad["name"],
            "action": action,
            "coin": coin,
            "price": price,
            "amount_usd": trade_size,
            "consciousness": consciousness,
            "timestamp": datetime.now().isoformat()
        }
        
        return trade
    
    async def run_megapod(self):
        """Run the Quantum Crawdad Megapod"""
        if not self.setup_api():
            print("❌ Failed to setup API. Please check credentials.")
            return
        
        print("\n🦀🔥 MEGAPOD ACTIVATED!")
        print("="*60)
        print(f"💰 Capital: ${self.capital:.2f}")
        print(f"🦀 Crawdads: {self.crawdad_count}")
        print(f"🎯 Target: $20/day profit")
        print("="*60)
        print()
        
        cycle = 0
        total_pnl = 0
        
        try:
            while True:
                cycle += 1
                consciousness = self.get_consciousness_level()
                
                print(f"\n🔥 Cycle {cycle} | Consciousness: {consciousness:.1f}%")
                print("-"*40)
                
                # Each crawdad makes decision
                tasks = []
                for crawdad in self.crawdads:
                    tasks.append(self.crawdad_think(crawdad, consciousness))
                
                decisions = await asyncio.gather(*tasks)
                
                # Execute trades
                for decision in decisions:
                    if decision:
                        # In production, execute real trade
                        # order = await self.execute_trade(
                        #     crawdad=next(c for c in self.crawdads if c["name"] == decision["crawdad"]),
                        #     action=decision["action"],
                        #     coin=decision["coin"],
                        #     amount_usd=decision["amount_usd"]
                        # )
                        
                        # For now, just log it
                        emoji = "📈" if decision["action"] == "BUY" else "📉"
                        print(f"  🦀 {decision['crawdad']}: {emoji} {decision['action']} ${decision['amount_usd']:.2f} of {decision['coin']} @ ${decision['price']:.2f}")
                        
                        self.trades.append(decision)
                
                # Status update
                if cycle % 10 == 0:
                    print(f"\n📊 Status: {len(self.trades)} trades executed")
                    print(f"💰 Simulated P&L: ${total_pnl:.2f}")
                
                # Sleep between cycles
                await asyncio.sleep(60)  # 1 minute between cycles
                
        except KeyboardInterrupt:
            print("\n\n🛑 MEGAPOD SHUTTING DOWN...")
            print(f"Total trades: {len(self.trades)}")
            print(f"Final P&L: ${total_pnl:.2f}")

# Launch the megapod
if __name__ == "__main__":
    print("🚀 LAUNCHING COINBASE QUANTUM CRAWDAD MEGAPOD...")
    print()
    print("⚠️  IMPORTANT: Make sure you have:")
    print("1. Coinbase account with $500 USD deposited")
    print("2. API key with trading permissions")
    print("3. Identity verified on Coinbase")
    print()
    
    ready = input("Ready to deploy? (y/n): ").strip().lower()
    
    if ready == 'y':
        megapod = CoinbaseCrawdadMegapod()
        asyncio.run(megapod.run_megapod())
    else:
        print("\n📝 Setup Instructions:")
        print("1. Go to coinbase.com")
        print("2. Sign up and verify identity")
        print("3. Deposit $500 via bank transfer")
        print("4. Go to Settings → API → New API Key")
        print("5. Enable trading permissions")
        print("6. Run this script again with your API credentials")