#!/usr/bin/env python3
"""
📊 MULTI-LEVEL WATCHER
Monitoring multiple critical levels simultaneously
$116,854 is ONE key level - but there are others
"""

import json
import time
from datetime import datetime
from coinbase.rest import RESTClient

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                       📊 MULTI-LEVEL WATCHER 📊                           ║
║                    "Many levels, many opportunities"                      ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=3)

class MultiLevelWatcher:
    def __init__(self):
        # Key levels to watch
        self.levels = {
            "BOTTOM_TARGET": 116854,      # Your called bottom
            "SUPPORT_1": 117000,          # First support
            "SUPPORT_2": 116500,          # Deeper support
            "RESISTANCE_1": 118000,       # First resistance
            "RESISTANCE_2": 119000,       # Major resistance
            "BREAKOUT": 120000,           # Breakout level
            "PANIC_ZONE": 115000,         # Extreme fear zone
        }
        
        self.current_btc = 0
        self.last_action_level = 0
        
    def get_btc_price(self):
        """Get current BTC price"""
        try:
            ticker = client.get_product('BTC-USD')
            if hasattr(ticker, 'price'):
                self.current_btc = float(ticker.price)
            return self.current_btc
        except:
            return 0
            
    def analyze_levels(self):
        """Analyze position relative to all levels"""
        if self.current_btc == 0:
            return
            
        print(f"\n📊 BTC: ${self.current_btc:,.2f}")
        print("-" * 40)
        
        # Find nearest levels
        nearest_above = None
        nearest_below = None
        min_dist_above = float('inf')
        min_dist_below = float('inf')
        
        for name, level in self.levels.items():
            distance = self.current_btc - level
            
            if distance > 0 and distance < min_dist_above:
                min_dist_above = distance
                nearest_above = (name, level)
            elif distance < 0 and abs(distance) < min_dist_below:
                min_dist_below = abs(distance)
                nearest_below = (name, level)
                
        # Display analysis
        if nearest_below:
            name, level = nearest_below
            print(f"📉 Next support: {name} at ${level:,} (-${min_dist_below:.2f})")
            
        if nearest_above:
            name, level = nearest_above
            print(f"📈 Next resistance: {name} at ${level:,} (+${min_dist_above:.2f})")
            
        # Special alerts
        if self.current_btc <= self.levels["BOTTOM_TARGET"]:
            print("\n🎯🎯🎯 AT YOUR BOTTOM TARGET! DEPLOY!")
        elif self.current_btc <= self.levels["PANIC_ZONE"]:
            print("\n🚨 EXTREME PANIC ZONE - Generational opportunity!")
        elif abs(self.current_btc - self.levels["BOTTOM_TARGET"]) < 500:
            print("\n🔥 Very close to your $116,854 target!")
            
        return nearest_above, nearest_below
        
    def suggest_action(self):
        """Suggest action based on levels"""
        if self.current_btc == 0:
            return None
            
        # Don't repeat actions at same level
        if abs(self.current_btc - self.last_action_level) < 100:
            return None
            
        action = None
        
        # Decision logic
        if self.current_btc <= self.levels["PANIC_ZONE"]:
            action = "BUY_EVERYTHING"
            reason = "Extreme panic = extreme opportunity"
        elif self.current_btc <= self.levels["BOTTOM_TARGET"]:
            action = "BUY_AGGRESSIVE"
            reason = "At your called bottom"
        elif self.current_btc <= self.levels["SUPPORT_2"]:
            action = "BUY_HEAVY"
            reason = "Deep support level"
        elif self.current_btc <= self.levels["SUPPORT_1"]:
            action = "BUY_MODERATE"
            reason = "Testing support"
        elif self.current_btc >= self.levels["BREAKOUT"]:
            action = "BUY_BREAKOUT"
            reason = "Breakout confirmation"
        elif self.current_btc >= self.levels["RESISTANCE_2"]:
            action = "TAKE_PROFIT"
            reason = "Major resistance"
            
        if action:
            self.last_action_level = self.current_btc
            print(f"\n💡 SUGGESTED ACTION: {action}")
            print(f"   Reason: {reason}")
            
        return action
        
    def check_greeks_alignment(self):
        """Check what The Greeks should be seeing"""
        print("\n🏛️ THE GREEKS SHOULD SEE:")
        
        if self.current_btc <= self.levels["BOTTOM_TARGET"]:
            print("  Δ Delta: MASSIVE gap up potential")
            print("  Γ Gamma: Trend reversal imminent")
            print("  Θ Theta: Volatility spike incoming")
            print("  ν Vega: Breakout setup forming")
            print("  ρ Rho: Extreme deviation from mean")
        elif self.current_btc <= self.levels["SUPPORT_1"]:
            print("  Δ Delta: Gap fill opportunity")
            print("  Γ Gamma: Trend weakening")
            print("  Θ Theta: Volatility expanding")
            print("  ν Vega: Consolidation phase")
            print("  ρ Rho: Approaching mean reversion")
        else:
            print("  Greeks in observation mode...")
            
    def monitor_levels(self):
        """Continuous level monitoring"""
        print("\n🔍 MONITORING ALL LEVELS...")
        print(f"   Primary target: ${self.levels['BOTTOM_TARGET']:,}")
        print(f"   Plus {len(self.levels)-1} other key levels")
        
        cycle = 0
        while True:
            cycle += 1
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Get current price
            self.get_btc_price()
            
            if cycle % 5 == 0:  # Full analysis every 5 cycles
                print(f"\n[{timestamp}] Level Analysis #{cycle}")
                self.analyze_levels()
                self.suggest_action()
                
                if cycle % 10 == 0:
                    self.check_greeks_alignment()
                    
            else:  # Quick check
                distance = self.current_btc - self.levels["BOTTOM_TARGET"]
                if abs(distance) < 200:
                    print(f"[{timestamp}] 🎯 ${distance:+.2f} from target!")
                    
            time.sleep(30)

# Initialize watcher
watcher = MultiLevelWatcher()

print("""
📊 KEY LEVELS BEING WATCHED:

1. $116,854 - YOUR BOTTOM TARGET (primary)
2. $117,000 - Support 1
3. $116,500 - Support 2 (deeper)
4. $118,000 - Resistance 1
5. $119,000 - Resistance 2
6. $120,000 - Breakout level
7. $115,000 - Panic zone (extreme buy)

The system watches ALL levels simultaneously.
$116,854 is the KEY level you identified.
But we're ready for any scenario.

The Greeks know these levels.
The crawdads adapt to each one.
""")

# Get initial reading
watcher.get_btc_price()
watcher.analyze_levels()
watcher.suggest_action()
watcher.check_greeks_alignment()

print("\n" + "="*60)
print("Starting continuous monitoring...")

try:
    watcher.monitor_levels()
except KeyboardInterrupt:
    print("\n\nLevel monitoring stopped")
    print(f"Last BTC: ${watcher.current_btc:,.2f}")
    
print("""
"One point on the chart to watch,
 but many points make the map.
 
 The wise trader watches all,
 but acts on the critical few."
 
Mitakuye Oyasin
""")