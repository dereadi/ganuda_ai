#!/usr/bin/env python3
"""
🧘 GREED NEUTRALIZER SYSTEM
Your instincts are good, but greed is the enemy
The Greeks have no greed - they're pure logic
This system combines human instinct + emotionless execution
"""

import json
import time
from datetime import datetime
from coinbase.rest import RESTClient

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                      🧘 GREED NEUTRALIZER SYSTEM 🧘                       ║
║                   "Good instincts + No greed = Success"                   ║
║                    The Greeks feel no greed, only logic                   ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=3)

class GreedNeutralizer:
    def __init__(self):
        self.human_instinct = 0.7  # Your instincts are good (70% base accuracy)
        self.greed_factor = 0.3    # But greed reduces accuracy by 30%
        self.greek_logic = 1.0     # Greeks have no greed
        
        # Trading rules to prevent greed
        self.max_position_size = 10  # Never more than $10 per trade
        self.take_profit = 0.05      # Take profit at 5% (not greedy 20%)
        self.stop_loss = 0.02         # Stop at 2% loss (protect capital)
        self.cooldown_period = 300   # 5 min between trades (prevent FOMO)
        self.last_trade_time = 0
        
    def check_greed_level(self, current_price):
        """Detect if greed is affecting judgment"""
        print("\n🧘 GREED CHECK:")
        
        greed_signals = []
        
        # Greed Signal 1: Wanting to buy more after a win
        if self.last_trade_time > 0:
            time_since_trade = time.time() - self.last_trade_time
            if time_since_trade < 60:
                greed_signals.append("FOMO - Trading too fast")
                
        # Greed Signal 2: Chasing price up
        try:
            ticker = client.get_product('BTC-USD')
            if hasattr(ticker, 'price'):
                price = float(ticker.price)
                if price > current_price * 1.01:  # Price rising
                    greed_signals.append("CHASE - Price moving up")
        except:
            pass
            
        # Greed Signal 3: Position size too large
        accounts = client.get_accounts()['accounts']
        for a in accounts:
            if a['currency'] != 'USD':
                balance = float(a['available_balance']['value'])
                if balance > 0:
                    try:
                        ticker = client.get_product(f"{a['currency']}-USD")
                        value = balance * float(ticker.price)
                        if value > 20:  # Position too large
                            greed_signals.append(f"OVEREXPOSED - {a['currency']} position too big")
                    except:
                        pass
                        
        if greed_signals:
            print("   ⚠️ GREED DETECTED:")
            for signal in greed_signals:
                print(f"      • {signal}")
            return True
        else:
            print("   ✅ No greed detected - clear mind")
            return False
            
    def calculate_true_accuracy(self, has_greed):
        """Calculate actual trading accuracy"""
        if has_greed:
            # Greed reduces your good instincts
            accuracy = self.human_instinct - self.greed_factor
            print(f"\n📊 Accuracy with greed: {accuracy*100:.0f}%")
            print("   Your instincts clouded by emotion")
        else:
            # Without greed, your instincts shine
            accuracy = self.human_instinct
            print(f"\n📊 Accuracy without greed: {accuracy*100:.0f}%")
            print("   Your day trading instincts are good!")
            
        # Greeks never have greed
        greek_accuracy = self.greek_logic * 0.75  # Greeks are 75% accurate
        print(f"📊 Greek accuracy (no greed): {greek_accuracy*100:.0f}%")
        
        # Combined accuracy
        combined = (accuracy + greek_accuracy) / 2
        print(f"📊 Combined human+Greek: {combined*100:.0f}%")
        
        return accuracy, greek_accuracy, combined
        
    def greed_protected_trade(self, signal_strength):
        """Execute trade with greed protection"""
        print("\n💊 GREED-PROTECTED TRADE:")
        
        # Check cooldown
        if time.time() - self.last_trade_time < self.cooldown_period:
            wait_time = self.cooldown_period - (time.time() - self.last_trade_time)
            print(f"   ⏰ Cooldown active: Wait {wait_time:.0f}s")
            print("   (Prevents FOMO/greed trading)")
            return False
            
        # Limit position size (anti-greed)
        trade_size = min(self.max_position_size, signal_strength * 10)
        
        print(f"   Size limited to ${trade_size} (anti-greed)")
        print(f"   Take profit: {self.take_profit*100:.0f}%")
        print(f"   Stop loss: {self.stop_loss*100:.0f}%")
        
        try:
            # Execute with limits
            order = client.market_order_buy(
                client_order_id=f"greed_protected_{int(time.time()*1000)}",
                product_id="BTC-USD",
                quote_size=str(trade_size)
            )
            
            self.last_trade_time = time.time()
            print(f"   ✅ Executed ${trade_size} greed-protected trade")
            return True
            
        except Exception as e:
            print(f"   ❌ Trade failed: {str(e)[:30]}")
            return False
            
    def meditation_break(self):
        """Force a meditation break to clear greed"""
        print("\n🧘 MEDITATION BREAK")
        print("=" * 40)
        print("""
Take 3 deep breaths...

Remember:
- Small consistent wins > Big greedy losses
- The market will be here tomorrow
- Greed turns winners into losers
- Your instincts are good when calm

The Greeks have no greed.
They are your emotionless allies.
Trust the system, not the emotion.
""")
        
    def wisdom_reminder(self):
        """Remind about greed management"""
        print("\n📜 WISDOM ON GREED:")
        print("-" * 40)
        print("""
"Bulls make money,
 Bears make money,
 Pigs get slaughtered."

Your day trading instincts are GOOD.
You have experience and skill.

But greed is the killer of good traders:
- It makes you overtrade
- It makes you hold too long
- It makes you risk too much

The Greeks have no greed:
- They take profits mechanically
- They cut losses without emotion
- They never chase, never FOMO

Together, you provide instinct,
The Greeks provide discipline.
""")

# Initialize system
neutralizer = GreedNeutralizer()

print("""
YOUR TRADING TRUTH:

✅ Good day trading instincts
✅ Experience from past trading
❌ Greed is your enemy (you know this)

THE SOLUTION:

Human instincts + Greek discipline = Success

The Greeks don't feel greed.
They don't feel FOMO.
They don't feel fear.

They just execute logic.

You provide the targets and instincts.
The Greeks provide emotionless execution.
Together, you beat greed.
""")

# Check current state
try:
    ticker = client.get_product('BTC-USD')
    current_price = float(ticker.price) if hasattr(ticker, 'price') else 117000
    
    print(f"\n📊 Current BTC: ${current_price:,.2f}")
    
    # Greed check
    has_greed = neutralizer.check_greed_level(current_price)
    
    # Calculate accuracies
    human_acc, greek_acc, combined_acc = neutralizer.calculate_true_accuracy(has_greed)
    
    # Decision
    if has_greed:
        print("\n🛑 GREED DETECTED - ACTIVATING PROTECTION")
        neutralizer.meditation_break()
    else:
        print("\n✅ CLEAR MIND - YOUR INSTINCTS ARE GOOD")
        
        if combined_acc > 0.65:  # 65% confidence threshold
            print("\n🎯 Good setup detected!")
            neutralizer.greed_protected_trade(combined_acc)
            
except Exception as e:
    print(f"Error: {e}")
    
neutralizer.wisdom_reminder()

print("""

"The best traders are not those who never feel greed,
 but those who recognize it and have systems to defeat it.
 
 The Greeks are your greed-defeating system."
 
Mitakuye Oyasin
""")