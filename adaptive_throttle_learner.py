#!/usr/bin/env python3
"""
🚀 ADAPTIVE THROTTLE LEARNING SYSTEM
=====================================
Automatically increases throttle as confidence grows
Start slow, learn fast, accelerate with success!
"""

import json
import time
from datetime import datetime
from coinbase.rest import RESTClient
from collections import deque

class AdaptiveThrottleLearner:
    def __init__(self):
        config = json.load(open('/home/dereadi/.coinbase_config.json'))
        self.client = RESTClient(api_key=config['api_key'], api_secret=config['api_secret'])
        
        # Adaptive throttle parameters
        self.current_throttle = 10.0  # Start at 10% (very cautious)
        self.min_throttle = 10.0
        self.max_throttle = 85.0  # Never go above 85% (redline protection)
        
        # Learning metrics
        self.wins = 0
        self.losses = 0
        self.confidence = 0.5
        self.pattern_accuracy = deque(maxlen=20)  # Last 20 predictions
        
        # Throttle adjustment rules
        self.THROTTLE_UP_RATE = 5.0    # Increase by 5% on success
        self.THROTTLE_DOWN_RATE = 10.0  # Decrease by 10% on failure
        self.CONFIDENCE_THRESHOLD = 0.65  # Need 65% confidence to accelerate
        
    def calculate_confidence(self):
        """Calculate current confidence based on recent performance"""
        if len(self.pattern_accuracy) == 0:
            return 0.5
        
        accuracy = sum(self.pattern_accuracy) / len(self.pattern_accuracy)
        
        # Boost confidence if on a winning streak
        if len(self.pattern_accuracy) >= 3:
            recent = list(self.pattern_accuracy)[-3:]
            if all(recent):  # Last 3 were correct
                accuracy *= 1.2  # 20% confidence boost
        
        return min(1.0, accuracy)
    
    def adjust_throttle(self, success: bool):
        """Automatically adjust throttle based on performance"""
        old_throttle = self.current_throttle
        
        if success:
            self.wins += 1
            self.pattern_accuracy.append(1)
            
            # Calculate new confidence
            self.confidence = self.calculate_confidence()
            
            # Accelerate if confident
            if self.confidence >= self.CONFIDENCE_THRESHOLD:
                self.current_throttle += self.THROTTLE_UP_RATE
                self.current_throttle = min(self.current_throttle, self.max_throttle)
                print(f"   🚀 THROTTLE UP: {old_throttle:.0f}% → {self.current_throttle:.0f}%")
                print(f"      Confidence: {self.confidence*100:.1f}%")
        else:
            self.losses += 1
            self.pattern_accuracy.append(0)
            
            # Recalculate confidence
            self.confidence = self.calculate_confidence()
            
            # Ease off on failure
            self.current_throttle -= self.THROTTLE_DOWN_RATE
            self.current_throttle = max(self.current_throttle, self.min_throttle)
            print(f"   🛑 THROTTLE DOWN: {old_throttle:.0f}% → {self.current_throttle:.0f}%")
            print(f"      Confidence: {self.confidence*100:.1f}%")
    
    def get_trade_size(self, usd_balance: float) -> float:
        """Calculate trade size based on current throttle"""
        # Convert throttle to trade percentage
        if self.current_throttle <= 10:
            percent = 0.001
        elif self.current_throttle <= 30:
            percent = 0.001 + (0.009 * ((self.current_throttle - 10) / 20))
        elif self.current_throttle <= 60:
            percent = 0.01 + (0.04 * ((self.current_throttle - 30) / 30))
        elif self.current_throttle <= 85:
            percent = 0.05 + (0.05 * ((self.current_throttle - 60) / 25))
        else:
            percent = 0.10
        
        trade_size = usd_balance * percent
        return min(trade_size, 50.0)  # Safety cap
    
    def predict_movement(self, symbol: str) -> tuple:
        """Predict next micro-movement"""
        # Get current price
        ticker = self.client.get_product(f'{symbol}-USD')
        price = float(ticker.price if hasattr(ticker, 'price') else ticker.get('price', 0))
        
        # Simple prediction based on recent momentum
        # In production, would use our backward-walking patterns
        time.sleep(1)
        ticker2 = self.client.get_product(f'{symbol}-USD')
        price2 = float(ticker2.price if hasattr(ticker2, 'price') else ticker2.get('price', 0))
        
        momentum = price2 - price
        
        if momentum > 0:
            prediction = 'UP'
        elif momentum < 0:
            prediction = 'DOWN'
        else:
            prediction = 'FLAT'
        
        return prediction, price
    
    def execute_learning_trade(self, symbol: str):
        """Execute a trade and learn from the result"""
        # Get balance
        accounts = self.client.get_accounts()
        account_list = accounts.accounts if hasattr(accounts, 'accounts') else accounts
        
        usd_balance = 0
        for account in account_list:
            if account['currency'] == 'USD':
                usd_balance = float(account['available_balance']['value'])
                break
        
        # Calculate trade size based on throttle
        trade_size = self.get_trade_size(usd_balance)
        trade_size = round(trade_size, 2)
        
        print(f"\n📊 Trade Size at {self.current_throttle:.0f}% throttle: ${trade_size:.2f}")
        
        # Make prediction
        prediction, entry_price = self.predict_movement(symbol)
        print(f"   Prediction: {symbol} will go {prediction}")
        
        # Execute trade
        try:
            if trade_size >= 1.00:  # Minimum $1 trade
                order = self.client.market_order_buy(
                    client_order_id=f"adaptive_{symbol}_{int(time.time())}",
                    product_id=f"{symbol}-USD",
                    quote_size=str(trade_size)
                )
                print(f"   ✅ Bought ${trade_size:.2f} of {symbol} at ${entry_price:.2f}")
                
                # Wait and check result
                print("   ⏳ Monitoring for 10 seconds...")
                time.sleep(10)
                
                # Check if prediction was correct
                ticker = self.client.get_product(f'{symbol}-USD')
                exit_price = float(ticker.price if hasattr(ticker, 'price') else ticker.get('price', 0))
                
                actual_movement = exit_price - entry_price
                pct_change = (actual_movement / entry_price) * 100
                
                print(f"   📈 Result: ${exit_price:.2f} ({pct_change:+.4f}%)")
                
                # Determine success
                success = False
                if prediction == 'UP' and actual_movement > 0:
                    success = True
                elif prediction == 'DOWN' and actual_movement < 0:
                    success = True
                elif prediction == 'FLAT' and abs(actual_movement) < entry_price * 0.0001:
                    success = True
                
                if success:
                    print(f"   ✅ CORRECT PREDICTION!")
                else:
                    print(f"   ❌ Wrong prediction")
                
                # Adjust throttle based on result
                self.adjust_throttle(success)
                
                return success
            else:
                print(f"   ⚠️ Trade size too small at current throttle")
                return None
                
        except Exception as e:
            print(f"   ❌ Trade failed: {e}")
            self.adjust_throttle(False)  # Failure, reduce throttle
            return False
    
    def display_dashboard(self):
        """Show current learning status"""
        win_rate = self.wins / (self.wins + self.losses) if (self.wins + self.losses) > 0 else 0
        
        # Visual throttle meter
        meter_width = 40
        filled = int((self.current_throttle / 100) * meter_width)
        empty = meter_width - filled
        meter = "█" * filled + "░" * empty
        
        print("\n" + "="*60)
        print("🚀 ADAPTIVE THROTTLE DASHBOARD")
        print("-"*60)
        print(f"Throttle: [{meter}] {self.current_throttle:.0f}%")
        print(f"Confidence: {self.confidence*100:.1f}%")
        print(f"Wins: {self.wins} | Losses: {self.losses} | Win Rate: {win_rate*100:.1f}%")
        print(f"Recent Accuracy: {len([x for x in self.pattern_accuracy if x])}/{len(self.pattern_accuracy)}")
        print("="*60)

# Run the adaptive system
print("🚀 ADAPTIVE THROTTLE LEARNING SYSTEM")
print("="*60)
print("Starting cautious, accelerating with success...")
print(f"Time: {datetime.now().strftime('%I:%M %p CST')}")

learner = AdaptiveThrottleLearner()

# Initial status
learner.display_dashboard()

# Run 5 learning cycles
print("\n📚 RUNNING ADAPTIVE LEARNING CYCLES:")
print("-"*60)

for i in range(5):
    print(f"\n🔄 Learning Cycle {i+1}")
    
    # Rotate through assets
    symbols = ['SOL', 'ETH', 'BTC']
    symbol = symbols[i % 3]
    
    success = learner.execute_learning_trade(symbol)
    
    # Show updated dashboard
    learner.display_dashboard()
    
    if i < 4:
        print("\n⏳ Next cycle in 5 seconds...")
        time.sleep(5)

print("\n✨ ADAPTIVE LEARNING COMPLETE!")
print("-"*60)
print(f"Final Throttle: {learner.current_throttle:.0f}%")
print(f"Final Confidence: {learner.confidence*100:.1f}%")
print(f"Total Trades: {learner.wins + learner.losses}")

if learner.current_throttle > 30:
    print("\n🚀 The crawdads gained confidence and accelerated!")
elif learner.current_throttle < 20:
    print("\n🛑 The crawdads stayed cautious - more learning needed")
else:
    print("\n🚗 The crawdads are cruising at optimal learning speed")

print("\n💡 As we learn more, we step on the throttle!")
print("   Success → More gas → Bigger trades")
print("   Failure → Ease off → Smaller trades")
print("   🚀 Adaptive acceleration for the win! 🚀")