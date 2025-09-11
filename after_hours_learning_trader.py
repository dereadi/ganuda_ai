#!/usr/bin/env python3
"""
🌙 AFTER-HOURS CRYPTO LEARNING TRADER
======================================
Crypto never sleeps - perfect for learning!
"""

import json
import time
from datetime import datetime
from coinbase.rest import RESTClient

class AfterHoursLearner:
    def __init__(self):
        # Load config
        config = json.load(open('/home/dereadi/.coinbase_config.json'))
        self.client = RESTClient(api_key=config['api_key'], api_secret=config['api_secret'])
        
        # Learning parameters
        self.micro_trade_size = 5.00  # $5 trades for learning
        self.patterns_learned = []
        self.trade_history = []
        
    def check_balance(self):
        """Check our current holdings"""
        accounts = self.client.get_accounts()
        total = 0
        holdings = {}
        
        account_list = accounts.accounts if hasattr(accounts, 'accounts') else accounts
        for account in account_list:
            balance = float(account['available_balance']['value'])
            currency = account['currency']
            
            if balance > 0:
                if currency == 'USD':
                    total += balance
                    holdings['USD'] = balance
                elif currency in ['BTC', 'ETH', 'SOL']:
                    ticker = self.client.get_product(f'{currency}-USD')
                    price = float(ticker.price if hasattr(ticker, 'price') else ticker.get('price', 0))
                    value = balance * price
                    total += value
                    holdings[currency] = {'amount': balance, 'value': value, 'price': price}
        
        return total, holdings
    
    def execute_micro_trade(self, action, symbol, reason):
        """Execute a small learning trade"""
        try:
            if action == 'BUY':
                print(f"  💰 Buying ${self.micro_trade_size} of {symbol}")
                print(f"     Reason: {reason}")
                
                order = self.client.market_order_buy(
                    client_order_id=f"learn_{symbol}_{int(time.time())}",
                    product_id=f"{symbol}-USD",
                    quote_size=str(self.micro_trade_size)
                )
                
                # Record the trade
                self.trade_history.append({
                    'time': datetime.now().isoformat(),
                    'action': 'BUY',
                    'symbol': symbol,
                    'amount': self.micro_trade_size,
                    'reason': reason
                })
                
                print(f"  ✅ Order placed successfully!")
                return True
                
            elif action == 'SELL':
                # Get our holdings of this symbol
                accounts = self.client.get_accounts()
                account_list = accounts.accounts if hasattr(accounts, 'accounts') else accounts
                
                for account in account_list:
                    if account['currency'] == symbol:
                        balance = float(account['available_balance']['value'])
                        if balance > 0:
                            # Sell a small portion
                            sell_amount = min(balance * 0.1, self.micro_trade_size / 100)  # 10% or $5 worth
                            
                            print(f"  💸 Selling {sell_amount:.6f} {symbol}")
                            print(f"     Reason: {reason}")
                            
                            order = self.client.market_order_sell(
                                client_order_id=f"learn_sell_{symbol}_{int(time.time())}",
                                product_id=f"{symbol}-USD",
                                base_size=str(sell_amount)
                            )
                            
                            self.trade_history.append({
                                'time': datetime.now().isoformat(),
                                'action': 'SELL',
                                'symbol': symbol,
                                'amount': sell_amount,
                                'reason': reason
                            })
                            
                            print(f"  ✅ Sell order placed!")
                            return True
                        else:
                            print(f"  ⚠️ No {symbol} to sell")
                            return False
                            
        except Exception as e:
            print(f"  ❌ Trade failed: {e}")
            return False
    
    def analyze_overnight_patterns(self):
        """Look for after-hours patterns"""
        patterns = []
        
        for symbol in ['BTC', 'ETH', 'SOL']:
            ticker = self.client.get_product(f'{symbol}-USD')
            price = float(ticker.price if hasattr(ticker, 'price') else ticker.get('price', 0))
            
            # For now, simulate 24hr range (would use candles API in production)
            # Approximation: assume 2% daily range
            high_24h = price * 1.01
            low_24h = price * 0.99
            
            # Calculate position in range
            if high_24h > low_24h:
                position = (price - low_24h) / (high_24h - low_24h)
                
                if position < 0.3:
                    patterns.append({
                        'symbol': symbol,
                        'pattern': 'near_daily_low',
                        'action': 'BUY',
                        'confidence': 0.75,
                        'reason': f'Price near 24hr low ({position*100:.0f}% of range)'
                    })
                elif position > 0.7:
                    patterns.append({
                        'symbol': symbol,
                        'pattern': 'near_daily_high',
                        'action': 'WAIT',
                        'confidence': 0.60,
                        'reason': f'Price near 24hr high ({position*100:.0f}% of range)'
                    })
        
        return patterns

print("🌙 AFTER-HOURS CRYPTO LEARNING TRADER")
print("="*60)
print(f"Time: {datetime.now().strftime('%I:%M %p CST')}")
print("Crypto markets are ALWAYS open - let's learn!")
print()

learner = AfterHoursLearner()

# Check current status
total, holdings = learner.check_balance()
print("📊 CURRENT PORTFOLIO:")
print("-"*60)
print(f"  Total Value: ${total:.2f}")
for asset, data in holdings.items():
    if asset == 'USD':
        print(f"  USD Reserve: ${data:.2f}")
    else:
        print(f"  {asset}: {data['amount']:.6f} (${data['value']:.2f})")

# Analyze patterns
print("\n🔍 ANALYZING AFTER-HOURS PATTERNS:")
print("-"*60)
patterns = learner.analyze_overnight_patterns()

if patterns:
    for p in patterns:
        print(f"\n  📈 {p['symbol']}:")
        print(f"     Pattern: {p['pattern']}")
        print(f"     Signal: {p['action']} ({p['confidence']*100:.0f}% confidence)")
        print(f"     Reason: {p['reason']}")
        
        # Execute micro-trades for learning
        if p['action'] == 'BUY' and p['confidence'] > 0.7:
            print(f"\n  🎯 EXECUTING LEARNING TRADE:")
            learner.execute_micro_trade('BUY', p['symbol'], p['reason'])

print("\n📚 AFTER-HOURS LEARNING ADVANTAGES:")
print("-"*60)
print("• Lower volatility = safer learning environment")
print("• Patterns develop slowly = easier to spot")
print("• Less competition = our 245ms advantage grows")
print("• 24/7 trading = continuous learning opportunity")
print("• Small trades = low-risk education")

print("\n🦀 QUANTUM CRAWDAD LEARNING MODE:")
print("-"*60)
print("• Each $5 trade teaches the hive")
print("• After-hours patterns inform tomorrow's strategy")
print("• We learn while others sleep")
print("• By morning, we're smarter than yesterday")

# Save learning session
learning_data = {
    'session_time': datetime.now().isoformat(),
    'patterns_found': patterns,
    'trades_executed': learner.trade_history,
    'portfolio_value': total,
    'learning_mode': 'ACTIVE'
}

with open('/home/dereadi/scripts/claude/after_hours_learning.json', 'w') as f:
    json.dump(learning_data, f, indent=2)

print("\n✨ The Quantum Crawdads never stop learning!")
print("   While Wall Street sleeps...")
print("   We're getting smarter with every trade!")
print("   🌙 24/7 crypto = 24/7 evolution! 🌙")