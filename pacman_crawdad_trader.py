#!/usr/bin/env python3
"""
🟡 PAC-MAN QUANTUM CRAWDAD TRADER
==================================
Gobble profits, avoid ghosts, collect power pellets!
"""

import json
import time
import random
from datetime import datetime
from coinbase.rest import RESTClient

class PacManCrawdad:
    def __init__(self):
        config = json.load(open('/home/dereadi/.coinbase_config.json'))
        self.client = RESTClient(api_key=config['api_key'], api_secret=config['api_secret'])
        
        # Pac-Man parameters
        self.throttle = 20  # Start at 20% for viable trades
        self.score = 0
        self.lives = 3
        self.power_mode = False
        self.ghosts_nearby = False
        
        # Market entities
        self.dots_eaten = 0  # Micro-profits collected
        self.ghosts_avoided = 0
        self.power_pellets = 0
        
    def detect_ghost(self, symbol: str) -> bool:
        """Detect market maker activity (ghosts)"""
        # Check for suspicious patterns
        ticker = self.client.get_product(f'{symbol}-USD')
        price1 = float(ticker.price if hasattr(ticker, 'price') else ticker.get('price', 0))
        
        time.sleep(0.5)
        
        ticker2 = self.client.get_product(f'{symbol}-USD')
        price2 = float(ticker2.price if hasattr(ticker2, 'price') else ticker2.get('price', 0))
        
        # Ghost = sudden price movement (potential market maker)
        movement = abs(price2 - price1) / price1
        
        if movement > 0.001:  # 0.1% instant movement
            return True
        return False
    
    def find_dots(self, symbol: str) -> float:
        """Find micro-profits to gobble"""
        ticker = self.client.get_product(f'{symbol}-USD')
        price = float(ticker.price if hasattr(ticker, 'price') else ticker.get('price', 0))
        
        # Dots = small predictable movements
        return price
    
    def check_power_pellet(self) -> bool:
        """Check if power pellet available (volatility spike)"""
        # Power pellet = high volatility opportunity
        # Random for now, would check actual volatility
        return random.random() < 0.2  # 20% chance
    
    def gobble_profits(self, symbol: str):
        """Execute a Pac-Man trade"""
        # Get balance
        accounts = self.client.get_accounts()
        account_list = accounts.accounts if hasattr(accounts, 'accounts') else accounts
        
        usd_balance = 0
        for account in account_list:
            if account['currency'] == 'USD':
                usd_balance = float(account['available_balance']['value'])
                break
        
        # Calculate trade size based on throttle
        percent = 0.001 + (0.009 * ((self.throttle - 10) / 20)) if self.throttle <= 30 else 0.01
        trade_size = min(usd_balance * percent, 10.0)  # Cap at $10 for safety
        
        if self.power_mode:
            trade_size *= 2  # Double size in power mode
            print("   ⚡ POWER MODE! Double points!")
        
        trade_size = round(trade_size, 2)
        
        print(f"   🟡 Gobbling ${trade_size:.2f} of {symbol}...")
        
        # Check for ghost
        if self.detect_ghost(symbol):
            print("   👻 GHOST DETECTED! Evading...")
            self.ghosts_avoided += 1
            self.throttle = max(10, self.throttle - 5)
            print(f"   Throttle down to {self.throttle}%")
            return
        
        # Execute trade
        try:
            if trade_size >= 1.00:
                order = self.client.market_order_buy(
                    client_order_id=f"pacman_{symbol}_{int(time.time())}",
                    product_id=f"{symbol}-USD",
                    quote_size=str(trade_size)
                )
                
                self.dots_eaten += 1
                points = int(trade_size * 10)
                self.score += points
                
                print(f"   🟡 WAKA WAKA! +{points} points!")
                print(f"   Score: {self.score}")
                
                # Speed up after eating
                if self.dots_eaten % 5 == 0:
                    self.throttle = min(50, self.throttle + 5)
                    print(f"   🚀 SPEED UP! Throttle now {self.throttle}%")
                
                return True
            else:
                print(f"   · Dot too small to eat")
                return False
                
        except Exception as e:
            print(f"   💀 Hit a wall! {e}")
            self.lives -= 1
            print(f"   Lives remaining: {self.lives}")
            return False
    
    def play_level(self):
        """Play one level of Pac-Man trading"""
        print("\n" + "="*50)
        print("🟡 PAC-MAN LEVEL START!")
        print("="*50)
        
        # Check for power pellet
        if self.check_power_pellet():
            print("💰 POWER PELLET AVAILABLE!")
            self.power_mode = True
            self.power_pellets += 1
        
        # Rotate through crypto maze
        symbols = ['SOL', 'ETH', 'BTC']
        
        for symbol in symbols:
            print(f"\n🎮 Entering {symbol} corridor...")
            
            # Find dots
            price = self.find_dots(symbol)
            print(f"   · Dots at ${price:.2f}")
            
            # Try to gobble
            self.gobble_profits(symbol)
            
            # Power mode wears off
            if self.power_mode:
                self.power_mode = False
                print("   Power mode ended")
            
            time.sleep(2)  # Pac-Man movement delay
            
            if self.lives <= 0:
                print("\n💀 GAME OVER!")
                break
    
    def show_stats(self):
        """Display Pac-Man stats"""
        print("\n" + "="*50)
        print("🟡 PAC-MAN STATS")
        print("-"*50)
        print(f"Score: {self.score}")
        print(f"Dots Eaten: {self.dots_eaten}")
        print(f"Ghosts Avoided: {self.ghosts_avoided}")
        print(f"Power Pellets: {self.power_pellets}")
        print(f"Lives: {self.lives}")
        print(f"Current Throttle: {self.throttle}%")
        print("="*50)

# Start the game
print("🟡 PAC-MAN QUANTUM CRAWDAD TRADER")
print("="*60)
print("Navigate the crypto maze, gobble profits, avoid ghosts!")
print(f"Time: {datetime.now().strftime('%I:%M %p CST')}")

pacman = PacManCrawdad()

# Play 2 levels
for level in range(2):
    print(f"\n🎮 LEVEL {level + 1}")
    pacman.play_level()
    
    if pacman.lives <= 0:
        break
    
    if level < 1:
        print("\n⏳ Next level in 5 seconds...")
        time.sleep(5)

# Final stats
pacman.show_stats()

print("\n✨ PAC-MAN TRADING COMPLETE!")
print("   The Quantum Crawdads gobbled profits...")
print("   Avoided the market maker ghosts...")
print("   And accelerated through the maze!")
print("   🟡 WAKA WAKA WAKA! 🟡")