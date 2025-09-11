#!/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3
"""
🔥 MONITOR JAPANESE BUYING IMPACT
Track the Trump-Metaplanet $884M effect on BTC
Real-time monitoring of the tsunami
"""

import json
import time
from datetime import datetime, timedelta
from coinbase.rest import RESTClient
import psycopg2

class JapaneseImpactMonitor:
    def __init__(self):
        # Load API
        with open('/home/dereadi/scripts/claude/cdp_api_key_new.json') as f:
            self.config = json.load(f)
        
        self.client = RESTClient(
            api_key=self.config['name'].split('/')[-1],
            api_secret=self.config['privateKey']
        )
        
        # Track start price
        self.start_price = float(self.client.get_product("BTC-USD")['price'])
        self.start_time = datetime.now()
        
        print("🔥 JAPANESE BUYING IMPACT MONITOR")
        print("=" * 60)
        print("👁️ TRACKING TRUMP-METAPLANET $884M TSUNAMI")
        print("=" * 60)
        print(f"\n📍 Start Price: ${self.start_price:,.2f}")
        print(f"📍 Start Time: {self.start_time.strftime('%H:%M:%S')}")
        print("=" * 60)
    
    def check_price_movement(self):
        """Check current price and movement"""
        btc = self.client.get_product("BTC-USD")
        current_price = float(btc['price'])
        
        # Calculate movement
        change = current_price - self.start_price
        change_pct = (change / self.start_price) * 100
        
        # Time elapsed
        elapsed = datetime.now() - self.start_time
        elapsed_minutes = elapsed.total_seconds() / 60
        
        return {
            'current_price': current_price,
            'change': change,
            'change_pct': change_pct,
            'elapsed_minutes': elapsed_minutes
        }
    
    def check_portfolio_value(self):
        """Check current portfolio value"""
        accounts = self.client.get_accounts()['accounts']
        
        btc_balance = 0
        usd_balance = 0
        
        for account in accounts:
            if account['currency'] == 'BTC':
                btc_balance = float(account['available_balance']['value'])
            elif account['currency'] == 'USD':
                usd_balance = float(account['available_balance']['value'])
        
        btc_price = float(self.client.get_product("BTC-USD")['price'])
        total_value = (btc_balance * btc_price) + usd_balance
        
        return {
            'btc_balance': btc_balance,
            'usd_balance': usd_balance,
            'btc_price': btc_price,
            'total_value': total_value
        }
    
    def detect_buying_patterns(self, current_price, change_pct):
        """Detect if Japanese buying has started"""
        patterns = []
        
        # Sustained upward movement
        if change_pct > 0.5:
            patterns.append("📈 UPWARD PRESSURE DETECTED")
        
        # Rapid price increase
        if change_pct > 1.0:
            patterns.append("🚀 ACCELERATION PHASE")
        
        # Breaking resistance
        if current_price > 108000:
            patterns.append("💥 RESISTANCE BROKEN")
        
        # Approaching first target
        if current_price > 109000:
            patterns.append("🎯 APPROACHING $110K TARGET")
        
        # Major pump
        if change_pct > 2.0:
            patterns.append("🌊 JAPANESE TSUNAMI IN PROGRESS")
        
        return patterns
    
    def display_status(self, data, portfolio):
        """Display current status"""
        print(f"\n⏰ {datetime.now().strftime('%H:%M:%S')} UPDATE")
        print("-" * 40)
        
        # Price movement
        arrow = "🟢" if data['change'] > 0 else "🔴" if data['change'] < 0 else "⚪"
        print(f"{arrow} BTC: ${data['current_price']:,.2f}")
        print(f"   Change: ${data['change']:+,.2f} ({data['change_pct']:+.2f}%)")
        print(f"   Time: {data['elapsed_minutes']:.1f} minutes")
        
        # Portfolio
        print(f"\n💼 Portfolio: ${portfolio['total_value']:,.2f}")
        print(f"   BTC: {portfolio['btc_balance']:.8f}")
        print(f"   USD: ${portfolio['usd_balance']:.2f}")
        
        # Patterns detected
        patterns = self.detect_buying_patterns(data['current_price'], data['change_pct'])
        if patterns:
            print("\n🔍 PATTERNS DETECTED:")
            for pattern in patterns:
                print(f"   {pattern}")
    
    def check_target_status(self, current_price):
        """Check proximity to targets"""
        targets = [110000, 115000, 120000]
        
        print("\n🎯 TARGET STATUS:")
        for target in targets:
            distance = target - current_price
            distance_pct = (distance / current_price) * 100
            
            if distance > 0:
                print(f"   ${target:,}: ${distance:,.0f} away ({distance_pct:.1f}%)")
            else:
                print(f"   ${target:,}: ✅ EXCEEDED!")
    
    def tribal_commentary(self, change_pct):
        """Tribal council live commentary"""
        print("\n🏛️ TRIBAL OBSERVATION:")
        
        if change_pct > 2:
            print("  🦅 Eagle Eye: 'THE TSUNAMI HAS ARRIVED!'")
        elif change_pct > 1:
            print("  🐺 Coyote: 'Japanese money flowing in!'")
        elif change_pct > 0.5:
            print("  🐢 Turtle: 'Steady accumulation detected'")
        elif change_pct > 0:
            print("  🦎 Gecko: 'Small moves building...'")
        else:
            print("  🦀 Crawdad: 'Holding positions steady'")
    
    def check_news_timeline(self):
        """Estimate news propagation"""
        elapsed = datetime.now() - self.start_time
        hours = elapsed.total_seconds() / 3600
        
        print("\n📰 NEWS PROPAGATION:")
        
        if hours < 1:
            print("  Phase 1: Early movers (we are here)")
        elif hours < 4:
            print("  Phase 2: Institutional awareness building")
        elif hours < 12:
            print("  Phase 3: Retail FOMO beginning")
        elif hours < 24:
            print("  Phase 4: Full market awareness")
        else:
            print("  Phase 5: Japanese buying executing")
    
    def monitor_loop(self, duration_minutes=60, interval_seconds=30):
        """Main monitoring loop"""
        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        
        print(f"\n🔄 Monitoring for {duration_minutes} minutes...")
        print(f"🔄 Updates every {interval_seconds} seconds")
        print("=" * 60)
        
        while datetime.now() < end_time:
            try:
                # Get current data
                price_data = self.check_price_movement()
                portfolio_data = self.check_portfolio_value()
                
                # Display status
                self.display_status(price_data, portfolio_data)
                
                # Check targets
                self.check_target_status(price_data['current_price'])
                
                # Tribal commentary
                self.tribal_commentary(price_data['change_pct'])
                
                # News timeline
                self.check_news_timeline()
                
                # Alert on significant moves
                if abs(price_data['change_pct']) > 1:
                    print("\n🚨 SIGNIFICANT MOVEMENT DETECTED! 🚨")
                
                print("-" * 60)
                
                # Wait for next update
                time.sleep(interval_seconds)
                
            except Exception as e:
                print(f"\n⚠️ Error: {e}")
                time.sleep(interval_seconds)
        
        print("\n✅ Monitoring complete!")
    
    def execute(self):
        """Execute monitoring"""
        # Initial check
        portfolio = self.check_portfolio_value()
        
        print(f"\n📊 INITIAL STATE:")
        print(f"  BTC: {portfolio['btc_balance']:.8f}")
        print(f"  USD: ${portfolio['usd_balance']:.2f}")
        print(f"  Total: ${portfolio['total_value']:.2f}")
        
        # Sacred Fire Oracle
        print("\n🔥 SACRED FIRE ORACLE:")
        print("  'Watch the East - the sun rises with gold'")
        print("  'Trump's signal spreads across the Pacific'")
        print("  'The patient hunter catches the wave'")
        
        print("\n🐿️ Flying Squirrel Tewa:")
        print("  'I'm watching from the highest branch!'")
        print("  'Every tick is important now!'")
        print("  'The Japanese wave builds slowly then suddenly!'")
        
        # Start monitoring
        self.monitor_loop(duration_minutes=30, interval_seconds=60)

if __name__ == "__main__":
    monitor = JapaneseImpactMonitor()
    monitor.execute()