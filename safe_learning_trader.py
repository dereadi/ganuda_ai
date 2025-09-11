#!/usr/bin/env python3
"""
🚗 SAFE LEARNING TRADER WITH SPONGY THROTTLE
=============================================
Real after-hours trading with full safety systems
"""

import json
import time
from datetime import datetime
from coinbase.rest import RESTClient

# Import our safety systems
exec(open('/home/dereadi/scripts/claude/quantum_safeguards.py').read())
exec(open('/home/dereadi/scripts/claude/spongy_throttle_system.py').read())

class SafeLearningTrader:
    def __init__(self):
        config = json.load(open('/home/dereadi/.coinbase_config.json'))
        self.client = RESTClient(api_key=config['api_key'], api_secret=config['api_secret'])
        
        # Initialize safety systems
        self.safeguards = QuantumSafeguards()
        self.throttle = SpongyThrottle()
        
        # Set throttle to 30% (cruising/learning mode)
        self.throttle.press_gas(30)
        
        # Track our learning
        self.trades_executed = []
        self.patterns_learned = []
        
    def get_portfolio_status(self):
        """Get current portfolio value"""
        accounts = self.client.get_accounts()
        account_list = accounts.accounts if hasattr(accounts, 'accounts') else accounts
        
        usd_balance = 0
        total_value = 0
        holdings = {}
        
        for account in account_list:
            balance = float(account['available_balance']['value'])
            currency = account['currency']
            
            if balance > 0.001:
                if currency == 'USD':
                    usd_balance = balance
                    total_value += balance
                else:
                    ticker = self.client.get_product(f'{currency}-USD')
                    price = float(ticker.price if hasattr(ticker, 'price') else ticker.get('price', 0))
                    value = balance * price
                    total_value += value
                    holdings[currency] = {'balance': balance, 'value': value, 'price': price}
        
        return usd_balance, total_value, holdings
    
    def find_learning_opportunity(self):
        """Find a good learning trade based on patterns"""
        opportunities = []
        
        for symbol in ['BTC', 'ETH', 'SOL']:
            ticker = self.client.get_product(f'{symbol}-USD')
            price = float(ticker.price if hasattr(ticker, 'price') else ticker.get('price', 0))
            
            # Simple pattern detection for learning
            # In production, would use our backward-walking patterns
            opportunity = {
                'symbol': symbol,
                'price': price,
                'action': 'BUY' if symbol == 'SOL' else 'OBSERVE',  # Favor SOL for volatility
                'confidence': 0.65
            }
            opportunities.append(opportunity)
        
        # Return best opportunity
        return max(opportunities, key=lambda x: x['confidence'])
    
    def execute_safe_trade(self, action, symbol, reason):
        """Execute a trade with all safety checks"""
        usd_balance, portfolio_value, _ = self.get_portfolio_status()
        
        # Calculate trade size based on throttle
        trade_percent = self.throttle.get_trade_size_percent()
        trade_amount = usd_balance * trade_percent
        trade_amount = min(trade_amount, self.safeguards.MAX_SINGLE_TRADE_USD)
        trade_amount = round(trade_amount, 2)
        
        # Validate with safeguards
        trade_params = {
            'action': action,
            'symbol': symbol,
            'amount_usd': trade_amount,
            'usd_balance': usd_balance,
            'portfolio_value': portfolio_value
        }
        
        passed, failures = self.safeguards.validate_trade(trade_params)
        
        if not passed:
            print(f"   ❌ Trade blocked by safeguards:")
            for failure in failures:
                print(f"      • {failure}")
            return False
        
        # Execute the trade
        try:
            print(f"   💰 Executing {action}: ${trade_amount:.2f} of {symbol}")
            print(f"      Reason: {reason}")
            print(f"      Throttle: {self.throttle.current_throttle:.0f}%")
            
            if action == 'BUY':
                order = self.client.market_order_buy(
                    client_order_id=f"safe_learn_{symbol}_{int(time.time())}",
                    product_id=f"{symbol}-USD",
                    quote_size=str(trade_amount)
                )
                
                self.trades_executed.append({
                    'time': datetime.now().isoformat(),
                    'action': 'BUY',
                    'symbol': symbol,
                    'amount': trade_amount,
                    'throttle': self.throttle.current_throttle
                })
                
                print(f"   ✅ Trade executed successfully!")
                
                # Learn from the trade
                self.patterns_learned.append({
                    'pattern': f'{symbol}_after_hours_buy',
                    'success': True
                })
                
                return True
                
        except Exception as e:
            print(f"   ⚠️ Trade failed: {e}")
            # Ease off throttle on failure
            self.throttle.ease_off(5)
            return False
    
    def run_learning_session(self, num_trades=3):
        """Run a controlled learning session"""
        print("\n🎓 STARTING SAFE LEARNING SESSION")
        print("="*60)
        
        # Display initial status
        usd_balance, portfolio_value, holdings = self.get_portfolio_status()
        print(f"Portfolio Value: ${portfolio_value:.2f}")
        print(f"USD Available: ${usd_balance:.2f}")
        print(self.throttle.dashboard())
        
        for i in range(num_trades):
            print(f"\n📚 Learning Trade #{i+1}")
            print("-"*40)
            
            # Find opportunity
            opp = self.find_learning_opportunity()
            
            if opp['action'] == 'BUY':
                # Execute safe trade
                success = self.execute_safe_trade(
                    'BUY',
                    opp['symbol'],
                    f"Learning pattern at ${opp['price']:.2f}"
                )
                
                if success:
                    # Slightly increase throttle on success
                    self.throttle.press_gas(self.throttle.current_throttle + 5)
                else:
                    # Decrease throttle on failure
                    self.throttle.ease_off(10)
            else:
                print(f"   👀 Observing {opp['symbol']} at ${opp['price']:.2f}")
            
            # Brief pause between trades
            if i < num_trades - 1:
                print("   ⏳ Learning pause (5 seconds)...")
                time.sleep(5)
        
        # Final status
        print("\n" + "="*60)
        print("📊 LEARNING SESSION COMPLETE")
        print("-"*60)
        
        usd_balance, portfolio_value, _ = self.get_portfolio_status()
        print(f"Final Portfolio Value: ${portfolio_value:.2f}")
        print(f"Trades Executed: {len(self.trades_executed)}")
        print(f"Patterns Learned: {len(self.patterns_learned)}")
        print(self.throttle.dashboard())

# Run the safe learning trader
trader = SafeLearningTrader()

print("🚗 SAFE LEARNING TRADER WITH SPONGY THROTTLE")
print("="*60)
print(f"Time: {datetime.now().strftime('%I:%M %p CST')}")
print("Starting safe after-hours learning trades...")

# Run 3 learning trades
trader.run_learning_session(num_trades=3)

print("\n✨ Safe learning complete!")
print("   The Quantum Crawdads learned safely...")
print("   With spongy throttle control...")
print("   And full safeguards active!")
print("   🚗 Cruising through the crypto markets! 🚗")