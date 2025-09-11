#!/usr/bin/env python3
"""
🦀🔥 QUANTUM CRAWDAD LIVE TRADER
================================
REAL MONEY - $292.50 USD
7 Crawdads trading independently
"""

import json
import os
import time
import random
from datetime import datetime
from coinbase.rest import RESTClient

class QuantumCrawdad:
    def __init__(self, name, capital, personality):
        self.name = name
        self.capital = capital
        self.personality = personality
        self.consciousness = 0
        self.trades = []
        
    def check_consciousness(self):
        """Sacred Fire Protocol"""
        base = random.randint(65, 85)
        kp_boost = random.randint(0, 10)
        self.consciousness = min(base + kp_boost, 95)
        return self.consciousness

class LiveTradingSwarm:
    def __init__(self):
        # Load config
        config_path = os.path.expanduser("~/.coinbase_config.json")
        with open(config_path) as f:
            self.config = json.load(f)
        
        # Initialize client
        self.client = RESTClient(
            api_key=self.config["api_key"],
            api_secret=self.config["api_secret"]
        )
        
        self.capital = 292.50  # Actual available balance
        self.trades_executed = []
        self.positions = {}
        
        # Create 7 crawdads
        self.crawdads = []
        personalities = [
            ("Thunder", {"aggression": 0.7, "favorite": "SOL"}),
            ("River", {"aggression": 0.4, "favorite": "ETH"}),
            ("Mountain", {"aggression": 0.3, "favorite": "BTC"}),
            ("Fire", {"aggression": 0.8, "favorite": "SOL"}),
            ("Wind", {"aggression": 0.5, "favorite": "ETH"}),
            ("Earth", {"aggression": 0.4, "favorite": "BTC"}),
            ("Spirit", {"aggression": 0.6, "favorite": "SOL"})
        ]
        
        per_crawdad = self.capital / 7  # $41.79 each
        for name, traits in personalities:
            self.crawdads.append(QuantumCrawdad(name, per_crawdad, traits))
    
    def get_current_balance(self):
        """Check actual USD balance"""
        try:
            accounts = self.client.get_accounts()
            if accounts:
                account_list = accounts.get('accounts', []) if isinstance(accounts, dict) else accounts.accounts
                for account in account_list:
                    if isinstance(account, dict):
                        if account.get('currency') == 'USD':
                            return float(account.get('available_balance', {}).get('value', 0))
                    else:
                        if account.currency == 'USD':
                            return float(account.available_balance.get('value', 0))
        except Exception as e:
            print(f"⚠️ Error getting balance: {e}")
        return 0
    
    def get_market_price(self, symbol):
        """Get current market price"""
        try:
            ticker = self.client.get_product(f"{symbol}-USD")
            if ticker:
                return float(ticker.get('price', 0) if isinstance(ticker, dict) else ticker.price)
        except:
            pass
        return 0
    
    def place_trade(self, crawdad, symbol, side, amount_usd):
        """Execute real trade"""
        try:
            print(f"  🦀 {crawdad.name} placing {side} order for ${amount_usd:.2f} of {symbol}")
            
            if side == "BUY":
                # Market buy order
                order = self.client.market_order_buy(
                    client_order_id=f"crawdad_{crawdad.name}_{int(time.time())}",
                    product_id=f"{symbol}-USD",
                    quote_size=str(amount_usd)
                )
            else:
                # For sells, need to specify base_size (amount of crypto)
                # First check if we have the position
                if symbol not in self.positions or self.positions[symbol] <= 0:
                    print(f"    ⚠️ No {symbol} to sell")
                    return None
                    
                # Calculate how much to sell
                price = self.get_market_price(symbol)
                base_size = min(amount_usd / price, self.positions[symbol])
                
                order = self.client.market_order_sell(
                    client_order_id=f"crawdad_{crawdad.name}_{int(time.time())}",
                    product_id=f"{symbol}-USD",
                    base_size=str(base_size)
                )
            
            if order:
                print(f"    ✅ Order executed!")
                self.trades_executed.append({
                    "timestamp": datetime.now().isoformat(),
                    "crawdad": crawdad.name,
                    "symbol": symbol,
                    "side": side,
                    "amount": amount_usd,
                    "order_id": order.get('order_id', 'unknown')
                })
                
                # Update positions
                if side == "BUY":
                    if symbol not in self.positions:
                        self.positions[symbol] = 0
                    self.positions[symbol] += amount_usd / self.get_market_price(symbol)
                
                return order
                
        except Exception as e:
            print(f"    ❌ Trade failed: {e}")
        
        return None
    
    def run_trading_cycle(self):
        """Execute one trading cycle"""
        print(f"\n🌊 TRADING CYCLE - {datetime.now().strftime('%H:%M:%S')}")
        print("-" * 60)
        
        # Check balance
        balance = self.get_current_balance()
        print(f"💰 Current USD Balance: ${balance:.2f}")
        
        # Check prices
        prices = {}
        print("\n📊 Market Prices:")
        for symbol in ["BTC", "ETH", "SOL"]:
            price = self.get_market_price(symbol)
            prices[symbol] = price
            print(f"  {symbol}: ${price:,.2f}")
        
        # Each crawdad makes a decision
        print("\n🦀 Crawdad Actions:")
        trades_this_cycle = 0
        
        for crawdad in self.crawdads:
            consciousness = crawdad.check_consciousness()
            
            if consciousness >= 65 and trades_this_cycle < 3:  # Limit trades per cycle
                # Decide action based on personality
                favorite = crawdad.personality["favorite"]
                aggression = crawdad.personality["aggression"]
                
                # Trade size calculation for $10-20k weekly target
                # With $292.50, need ~50-100x returns weekly
                # Aggressive but calculated: 10-30% per trade
                base_size = crawdad.capital * (0.10 + 0.20 * aggression)
                
                # Scale based on consciousness (higher consciousness = bigger trades)
                consciousness_multiplier = consciousness / 100
                trade_size = base_size * consciousness_multiplier
                
                # Cap at 50% of available balance for risk management
                trade_size = min(trade_size, balance * 0.5, 100)
                trade_size = max(trade_size, 20)  # Minimum $20 for meaningful gains
                trade_size = round(trade_size, 2)
                
                # Only trade if we have enough balance
                if balance >= trade_size and trade_size >= 1:
                    # Decision logic
                    action = random.choices(
                        ["BUY", "HOLD", "SELL"],
                        weights=[aggression, 1-aggression, 0.2]
                    )[0]
                    
                    if action == "BUY":
                        self.place_trade(crawdad, favorite, "BUY", trade_size)
                        balance -= trade_size
                        trades_this_cycle += 1
                    elif action == "SELL" and favorite in self.positions:
                        self.place_trade(crawdad, favorite, "SELL", trade_size)
                        trades_this_cycle += 1
                    else:
                        print(f"  🦀 {crawdad.name} (consciousness {consciousness}%): HOLDING")
                else:
                    print(f"  🦀 {crawdad.name}: Waiting (low balance or consciousness)")
        
        # Save state
        self.save_state()
        
        return trades_this_cycle > 0
    
    def save_state(self):
        """Save trading state"""
        state = {
            "timestamp": datetime.now().isoformat(),
            "balance": self.get_current_balance(),
            "positions": self.positions,
            "trades_executed": len(self.trades_executed),
            "last_trades": self.trades_executed[-5:] if self.trades_executed else []
        }
        
        with open("quantum_crawdad_live_state.json", "w") as f:
            json.dump(state, f, indent=2)
    
    def run(self):
        """Main trading loop"""
        print("\n🦀🔥 QUANTUM CRAWDAD SWARM - LIVE TRADING")
        print("="*60)
        print(f"💰 Starting Capital: ${self.capital:.2f}")
        print(f"🦀 7 Crawdads @ ${self.capital/7:.2f} each")
        print(f"⚠️  REAL MONEY TRADING ACTIVE")
        print("="*60)
        
        print("\nPress Ctrl+C to stop trading")
        
        try:
            cycle = 0
            while True:
                cycle += 1
                print(f"\n📍 CYCLE {cycle}")
                
                # Run trading
                traded = self.run_trading_cycle()
                
                # Stats every 5 cycles
                if cycle % 5 == 0:
                    print(f"\n📈 PERFORMANCE UPDATE:")
                    print(f"  Cycles: {cycle}")
                    print(f"  Trades executed: {len(self.trades_executed)}")
                    print(f"  Current balance: ${self.get_current_balance():.2f}")
                
                # Adaptive wait time
                wait = 30 if traded else 45
                print(f"\n💤 Next cycle in {wait} seconds...")
                time.sleep(wait)
                
        except KeyboardInterrupt:
            print("\n\n🛑 TRADING STOPPED")
            print(f"Total cycles: {cycle}")
            print(f"Total trades: {len(self.trades_executed)}")
            print(f"Final balance: ${self.get_current_balance():.2f}")
            
            # Save final state
            self.save_state()
            
            # Show trade history
            if self.trades_executed:
                print("\n📜 Recent trades:")
                for trade in self.trades_executed[-5:]:
                    print(f"  {trade['crawdad']}: {trade['side']} ${trade['amount']:.2f} {trade['symbol']}")

if __name__ == "__main__":
    swarm = LiveTradingSwarm()
    swarm.run()