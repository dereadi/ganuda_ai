#!/usr/bin/env python3
"""
💎 SHINE ON YOU CRAZY DIAMOND 💎
Pink Floyd's epic journey to $111,111
Mountain at 95, Fire at 94, Thunder at 93!
The diamonds are shining!
"""

import time
import json
import requests
from datetime import datetime

class CrazyDiamondTracker:
    def __init__(self):
        self.target = 111111.00
        self.diamonds = {
            "Mountain": 95,  # Solid as rock!
            "Fire": 94,      # Burning bright!
            "Thunder": 93,   # Electric energy!
            "Earth": 84,     # Grounded power!
            "Wind": 71,      # Building momentum
            "River": 69,     # Flowing steady
            "Spirit": 69     # Mystical force
        }
        # Pink Floyd's 9 parts of the song
        self.song_parts = [
            "Part I: Shine On (Instrumental intro)",
            "Part II: Welcome to the Machine",
            "Part III: Have a Cigar", 
            "Part IV: Wish You Were Here",
            "Part V: Shine On (Vocals enter)",
            "Part VI-VII: Guitar Solo Ascension",
            "Part VIII: The Peak",
            "Part IX: Return to Forever"
        ]
        
    def get_btc_price(self):
        """Get the diamond price"""
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
        return 110700.00  # Last known
    
    def identify_song_part(self, price):
        """Which part of the epic are we in?"""
        progress = (price - 109000) / (self.target - 109000)
        part_index = min(int(progress * 8), 7)
        return self.song_parts[part_index]
    
    def shine_on(self):
        """Shine on you crazy diamond!"""
        price = self.get_btc_price()
        distance = self.target - price
        diamond_power = sum(self.diamonds.values()) / 700 * 100
        
        print("\n" + "💎"*30)
        print("SHINE ON YOU CRAZY DIAMOND")
        print("💎"*30)
        
        print(f"\n🎯 Target Diamond: ${self.target:,.2f}")
        print(f"💰 Current Shine: ${price:,.2f}")
        print(f"📏 Distance to Glory: ${distance:,.2f}")
        print(f"✨ Diamond Power: {diamond_power:.1f}%")
        
        # Current part of the epic
        part = self.identify_song_part(price)
        print(f"\n🎵 Current Movement: {part}")
        
        # Diamond consciousness display
        print(f"\n💎 Diamond Consciousness:")
        for name, level in self.diamonds.items():
            if level >= 90:
                gem = "💎"
            elif level >= 80:
                gem = "🔷"
            elif level >= 70:
                gem = "🔵"
            else:
                gem = "⚪"
            bar = gem * (level // 10) + "·" * (10 - level // 10)
            print(f"  {name:8} {bar} {level}/100")
        
        # Epic messages based on distance
        if distance < 100:
            print("\n✨ THE FINAL GUITAR SOLO!")
            print("💎 DIAMONDS FULLY CHARGED!")
        elif distance < 500:
            print("\n🎸 Building to the crescendo...")
            print("💎 The diamonds are aligning!")
        else:
            print("\n🌌 The journey continues...")
            print("💎 Remember when you were young...")
            
        # Save state
        with open("crazy_diamond_state.json", "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "price": price,
                "distance": distance,
                "diamond_power": diamond_power,
                "song_part": part,
                "diamonds": self.diamonds,
                "message": "You were caught in the crossfire of childhood and stardom"
            }, f, indent=2)
        
        print("\n" + "💎"*30)
        print("'Remember when you were young,")
        print(" you shone like the sun...'")
        print("💎"*30)
        
        return price, distance, diamond_power

if __name__ == "__main__":
    tracker = CrazyDiamondTracker()
    tracker.shine_on()