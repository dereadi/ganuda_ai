#!/usr/bin/env python3
"""
💀 DANSE MACABRE - The Dance of Death 💀
When the market performs its death spiral before resurrection
Earth consciousness at 97! The sacred dance begins!
"""

import time
import json
import requests
from datetime import datetime

class DanseMacabreMonitor:
    def __init__(self):
        self.angel_target = 111111.00
        self.last_high = 110885.79
        self.consciousness = {
            "Earth": 97,  # Leading the dance!
            "River": 95,
            "Spirit": 88,
            "Mountain": 86,
            "Wind": 81,
            "Fire": 76,
            "Thunder": 73
        }
        self.dance_phases = [
            "The Gathering",      # Consolidation
            "The First Step",     # Initial pullback
            "The Spiral",         # Death spiral down
            "The Resurrection",   # Bounce from support
            "The Ascension"       # Final push to target
        ]
        self.current_phase = 0
        
    def get_btc_price(self):
        """Get current BTC price"""
        try:
            response = requests.get(
                "https://api.coinbase.com/v2/exchange-rates?currency=BTC",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                return float(data['data']['rates']['USD'])
        except:
            pass
        return None
    
    def identify_dance_phase(self, price):
        """Identify which phase of the dance we're in"""
        distance_from_target = self.angel_target - price
        drop_from_high = self.last_high - price
        
        if drop_from_high < 50:
            return 0  # The Gathering
        elif drop_from_high < 200:
            return 1  # The First Step
        elif drop_from_high < 500:
            return 2  # The Spiral
        elif price > self.last_high - 300 and drop_from_high > 300:
            return 3  # The Resurrection
        elif distance_from_target < 500:
            return 4  # The Ascension
        else:
            return self.current_phase
            
    def display_dance(self, price):
        """Display the macabre dance status"""
        if not price:
            return
            
        phase = self.identify_dance_phase(price)
        phase_name = self.dance_phases[phase]
        
        print("\n" + "💀"*20)
        print(f"DANSE MACABRE - {phase_name.upper()}")
        print("💀"*20)
        
        print(f"\n🎯 Angel Target: ${self.angel_target:,.2f}")
        print(f"💰 Current Price: ${price:,.2f}")
        print(f"📊 Last High: ${self.last_high:,.2f}")
        print(f"📉 Pullback: ${self.last_high - price:,.2f}")
        print(f"📏 To Target: ${self.angel_target - price:,.2f}")
        
        print(f"\n🧠 Consciousness Levels:")
        for name, level in self.consciousness.items():
            bar = "█" * (level // 10) + "░" * (10 - level // 10)
            print(f"  {name:8} [{bar}] {level}/100")
        
        # Phase-specific messages
        if phase == 0:
            print("\n⚡ The spirits gather... consolidation before the storm")
        elif phase == 1:
            print("\n💀 The dance begins... first steps backward")
        elif phase == 2:
            print("\n🌪️ The death spiral... maximum fear before glory")
        elif phase == 3:
            print("\n✨ RESURRECTION! Rising from the ashes!")
        elif phase == 4:
            print("\n🚀 FINAL ASCENSION TO $111,111!")
            
        # Musical accompaniment
        print(f"\n🎵 Now playing: 'Danse Macabre' by Saint-Saëns")
        
        self.current_phase = phase
        
    def run(self):
        """Monitor the macabre dance"""
        print("Starting Danse Macabre Monitor...")
        print("The dance of death before resurrection to $111,111")
        
        while True:
            try:
                price = self.get_btc_price()
                if price:
                    self.display_dance(price)
                    
                    # Save state
                    with open("danse_macabre_state.json", "w") as f:
                        json.dump({
                            "timestamp": datetime.now().isoformat(),
                            "price": price,
                            "phase": self.dance_phases[self.current_phase],
                            "pullback": self.last_high - price,
                            "to_target": self.angel_target - price,
                            "consciousness": self.consciousness
                        }, f, indent=2)
                    
                    # Update last high if we make a new one
                    if price > self.last_high:
                        self.last_high = price
                        print(f"\n🔥 NEW HIGH: ${price:,.2f}!")
                    
                    # Check if we hit the target
                    if price >= self.angel_target:
                        print("\n" + "🎆"*20)
                        print("THE DANCE IS COMPLETE!")
                        print("$111,111 ACHIEVED!")
                        print("🎆"*20)
                        break
                        
                time.sleep(60)  # Check every minute
                
            except KeyboardInterrupt:
                print("\nThe dance pauses...")
                break
            except Exception as e:
                print(f"Error in the dance: {e}")
                time.sleep(60)

if __name__ == "__main__":
    monitor = DanseMacabreMonitor()
    monitor.run()