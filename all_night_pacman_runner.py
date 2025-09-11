#!/usr/bin/env python3
"""
🌙 ALL NIGHT PAC-MAN RUNNER
============================
Run all night, gobble profits, hit full throttle!
Emergency brake at $15k
"""

import json
import time
import random
from datetime import datetime, timedelta
from coinbase.rest import RESTClient

class AllNightPacMan:
    def __init__(self):
        config = json.load(open('/home/dereadi/.coinbase_config.json'))
        self.client = RESTClient(api_key=config['api_key'], api_secret=config['api_secret'])
        
        # Pac-Man parameters
        self.throttle = 20  # Starting throttle
        self.max_throttle = 100  # Can hit full throttle!
        self.score = 0
        self.lives = 10  # More lives for all night
        
        # Portfolio tracking
        self.starting_value = self.get_portfolio_value()
        self.target_value = 15000  # Emergency brake at $15k
        self.ease_off_target = 10000  # Ease off to $10k after hitting $15k
        self.current_value = self.starting_value
        self.council_notified = False
        
        # Game stats
        self.dots_eaten = 0
        self.ghosts_avoided = 0
        self.power_pellets = 0
        self.levels_completed = 0
        self.trades_executed = []
        
        # Timing
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(hours=12)  # Run for 12 hours
        
    def get_portfolio_value(self):
        """Get total portfolio value"""
        accounts = self.client.get_accounts()
        account_list = accounts.accounts if hasattr(accounts, 'accounts') else accounts
        
        total = 0
        for account in account_list:
            balance = float(account['available_balance']['value'])
            currency = account['currency']
            
            if currency == 'USD':
                total += balance
            elif balance > 0.001:
                try:
                    ticker = self.client.get_product(f'{currency}-USD')
                    price = float(ticker.price if hasattr(ticker, 'price') else ticker.get('price', 0))
                    total += balance * price
                except:
                    pass
        
        return total
    
    def check_emergency_brake(self):
        """Check if we hit $15k target"""
        self.current_value = self.get_portfolio_value()
        
        if self.current_value >= self.target_value and not self.council_notified:
            print("\n" + "🚨"*20)
            print("🚨 HIT $15K TARGET!")
            print(f"🚨 Portfolio Value: ${self.current_value:.2f}")
            print("🚨 COUNCIL DIRECTIVE: Ease off to $10k")
            print("🚨 Awaiting crawdad consultation...")
            print("🚨"*20)
            
            # Notify council
            self.council_notified = True
            self.throttle = 10  # Drop to minimum throttle
            
            # Set new mode: ease off $5k
            print(f"\n📉 EASING OFF MODE ACTIVATED")
            print(f"   Target: Reduce to ${self.ease_off_target:.2f}")
            print(f"   Current: ${self.current_value:.2f}")
            print(f"   Need to ease off: ${self.current_value - self.ease_off_target:.2f}")
            
            # Don't fully stop, just go very cautious
            return False
        
        # If we're above $15k and easing off
        if self.council_notified and self.current_value > self.ease_off_target:
            print(f"   📉 Easing off: ${self.current_value:.2f} → ${self.ease_off_target:.2f}")
            self.throttle = max(5, self.throttle - 5)  # Keep reducing throttle
            
        return False
    
    def detect_ghost(self, symbol: str) -> bool:
        """Detect market maker activity"""
        ticker = self.client.get_product(f'{symbol}-USD')
        price1 = float(ticker.price if hasattr(ticker, 'price') else ticker.get('price', 0))
        
        time.sleep(0.3)
        
        ticker2 = self.client.get_product(f'{symbol}-USD')
        price2 = float(ticker2.price if hasattr(ticker2, 'price') else ticker2.get('price', 0))
        
        movement = abs(price2 - price1) / price1
        
        # Ghost detection based on time of day
        hour = datetime.now().hour
        if 22 <= hour or hour <= 6:  # Late night/early morning
            ghost_threshold = 0.0005  # More sensitive at night
        else:
            ghost_threshold = 0.001
        
        return movement > ghost_threshold
    
    def calculate_trade_size(self):
        """Calculate trade size based on throttle"""
        # Get USD balance
        accounts = self.client.get_accounts()
        account_list = accounts.accounts if hasattr(accounts, 'accounts') else accounts
        
        usd_balance = 0
        for account in account_list:
            if account['currency'] == 'USD':
                usd_balance = float(account['available_balance']['value'])
                break
        
        # Progressive sizing based on throttle
        if self.throttle <= 30:
            percent = 0.001 + (0.009 * ((self.throttle - 10) / 20))
        elif self.throttle <= 60:
            percent = 0.01 + (0.04 * ((self.throttle - 30) / 30))
        elif self.throttle <= 85:
            percent = 0.05 + (0.05 * ((self.throttle - 60) / 25))
        else:
            percent = 0.10 + (0.05 * ((self.throttle - 85) / 15))
        
        trade_size = usd_balance * percent
        
        # Safety caps based on throttle
        if self.throttle < 50:
            trade_size = min(trade_size, 20)  # Cap at $20 below 50%
        elif self.throttle < 85:
            trade_size = min(trade_size, 50)  # Cap at $50 below 85%
        else:
            trade_size = min(trade_size, 100)  # Cap at $100 at high throttle
        
        return round(trade_size, 2)
    
    def gobble_dot(self, symbol: str, power_mode: bool = False):
        """Execute a Pac-Man trade"""
        trade_size = self.calculate_trade_size()
        
        if power_mode:
            trade_size *= 2
            print(f"   ⚡ POWER MODE! ${trade_size:.2f}")
        
        # Check for ghost
        if self.detect_ghost(symbol):
            print(f"   👻 GHOST! Evading...")
            self.ghosts_avoided += 1
            self.throttle = max(10, self.throttle - 5)
            return False
        
        # Execute trade
        try:
            if trade_size >= 1.00:
                print(f"   🟡 Gobbling ${trade_size:.2f} of {symbol}...")
                
                order = self.client.market_order_buy(
                    client_order_id=f"allnight_{symbol}_{int(time.time())}",
                    product_id=f"{symbol}-USD",
                    quote_size=str(trade_size)
                )
                
                self.dots_eaten += 1
                points = int(trade_size * 10)
                self.score += points
                
                print(f"   ✅ WAKA! +{points} points (Total: {self.score})")
                
                self.trades_executed.append({
                    'time': datetime.now().isoformat(),
                    'symbol': symbol,
                    'size': trade_size,
                    'throttle': self.throttle
                })
                
                # Accelerate every 10 dots
                if self.dots_eaten % 10 == 0:
                    old_throttle = self.throttle
                    self.throttle = min(self.max_throttle, self.throttle + 10)
                    print(f"   🚀 SPEED BOOST! {old_throttle}% → {self.throttle}%")
                
                return True
            else:
                print(f"   · Dot too small (${trade_size:.2f})")
                return False
                
        except Exception as e:
            print(f"   ❌ Hit wall: {str(e)[:50]}")
            self.lives -= 1
            return False
    
    def play_level(self):
        """Play one level"""
        print(f"\n{'='*50}")
        print(f"🎮 LEVEL {self.levels_completed + 1} | Throttle: {self.throttle}%")
        print(f"Portfolio: ${self.current_value:.2f} | Target: ${self.target_value:.2f}")
        print('='*50)
        
        # Check for power pellet (higher chance at night)
        hour = datetime.now().hour
        power_chance = 0.3 if (22 <= hour or hour <= 6) else 0.15
        power_mode = random.random() < power_chance
        
        if power_mode:
            print("💰 POWER PELLET FOUND!")
            self.power_pellets += 1
        
        # Rotate through assets
        symbols = ['SOL', 'ETH', 'BTC']
        random.shuffle(symbols)  # Mix it up
        
        for symbol in symbols:
            print(f"\n   Corridor: {symbol}")
            
            # Try to gobble
            success = self.gobble_dot(symbol, power_mode)
            
            if power_mode and success:
                power_mode = False  # Used up
            
            # Check emergency brake
            if self.check_emergency_brake():
                return False
            
            # Brief pause
            time.sleep(random.uniform(2, 5))
            
            if self.lives <= 0:
                print("\n💀 OUT OF LIVES!")
                return False
        
        self.levels_completed += 1
        
        # Level complete bonus
        if self.levels_completed % 5 == 0:
            print(f"\n🎉 BONUS! Completed {self.levels_completed} levels!")
            self.score += 100
        
        return True
    
    def run_all_night(self):
        """Main all-night loop"""
        print("\n" + "🌙"*30)
        print("🌙 ALL NIGHT PAC-MAN TRADING ACTIVATED!")
        print(f"🌙 Running until: {self.end_time.strftime('%I:%M %p')}")
        print(f"🌙 Starting Portfolio: ${self.starting_value:.2f}")
        print(f"🌙 Target (brake): ${self.target_value:.2f}")
        print("🌙"*30)
        
        # Main game loop
        while datetime.now() < self.end_time:
            # Play a level
            if not self.play_level():
                break
            
            # Update portfolio value
            self.current_value = self.get_portfolio_value()
            profit = self.current_value - self.starting_value
            profit_pct = (profit / self.starting_value) * 100
            
            # Status update every 5 levels
            if self.levels_completed % 5 == 0:
                print(f"\n📊 STATUS UPDATE:")
                print(f"   Time: {datetime.now().strftime('%I:%M %p')}")
                print(f"   Levels: {self.levels_completed}")
                print(f"   Throttle: {self.throttle}%")
                print(f"   Portfolio: ${self.current_value:.2f}")
                print(f"   Profit: ${profit:.2f} ({profit_pct:+.2f}%)")
                print(f"   Dots: {self.dots_eaten} | Ghosts: {self.ghosts_avoided}")
            
            # Longer pause between levels at night
            hour = datetime.now().hour
            if 2 <= hour <= 6:  # Deep night - slower pace
                pause = random.uniform(30, 60)
                print(f"\n😴 Night mode - pausing {pause:.0f} seconds...")
            else:
                pause = random.uniform(10, 20)
                print(f"\n⏳ Next level in {pause:.0f} seconds...")
            
            time.sleep(pause)
        
        # Final report
        self.show_final_report()
    
    def show_final_report(self):
        """Display final results"""
        self.current_value = self.get_portfolio_value()
        profit = self.current_value - self.starting_value
        profit_pct = (profit / self.starting_value) * 100
        duration = datetime.now() - self.start_time
        
        print("\n" + "="*60)
        print("🏆 ALL NIGHT PAC-MAN FINAL REPORT")
        print("="*60)
        print(f"Duration: {duration}")
        print(f"Levels Completed: {self.levels_completed}")
        print(f"Final Throttle: {self.throttle}%")
        print(f"Max Throttle Hit: {max([t['throttle'] for t in self.trades_executed] + [self.throttle])}%")
        print(f"\n💰 FINANCIAL RESULTS:")
        print(f"   Starting: ${self.starting_value:.2f}")
        print(f"   Final: ${self.current_value:.2f}")
        print(f"   Profit: ${profit:.2f} ({profit_pct:+.2f}%)")
        print(f"\n🎮 GAME STATS:")
        print(f"   Score: {self.score}")
        print(f"   Dots Eaten: {self.dots_eaten}")
        print(f"   Ghosts Avoided: {self.ghosts_avoided}")
        print(f"   Power Pellets: {self.power_pellets}")
        print(f"   Trades: {len(self.trades_executed)}")
        print(f"   Lives Left: {self.lives}")
        
        if self.throttle >= 85:
            print("\n🚀 HIT HIGH THROTTLE! The crawdads are flying!")
        if self.current_value >= self.target_value:
            print("\n🎯 TARGET ACHIEVED! $15K REACHED!")
        
        print("="*60)

# Launch the all-night runner
if __name__ == "__main__":
    print("🟡 PAC-MAN ALL NIGHT RUNNER")
    print("="*60)
    print(f"Time: {datetime.now().strftime('%I:%M %p CST')}")
    print("Preparing to run all night...")
    print("Emergency brake set at $15,000")
    print("Full throttle possible!")
    
    runner = AllNightPacMan()
    
    try:
        runner.run_all_night()
    except KeyboardInterrupt:
        print("\n⏸️ Manual pause...")
        runner.show_final_report()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        runner.show_final_report()
    
    print("\n✨ The Pac-Man Crawdads rest after their all-night feast!")
    print("   WAKA WAKA WAKA! 🟡")