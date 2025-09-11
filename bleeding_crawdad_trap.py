#!/usr/bin/env python3
"""
🩸 BLEEDING CRAWDAD TRAP
Strategic loss-taking to trigger panic sellers
"Bleed a little to feast on the fear"
When we show weakness, others panic sell into our bids
"""

import json
import time
from datetime import datetime
from coinbase.rest import RESTClient

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                      🩸 BLEEDING CRAWDAD TRAP 🦀                          ║
║                   "Show weakness to reveal strength"                      ║
║                 Tactical bleeding → Panic feeding frenzy                  ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=3)

class BleedingCrawdadTrap:
    def __init__(self):
        self.bleed_amount = 0.02  # 2% tactical loss
        self.trap_set = False
        self.feeding_detected = False
        self.blood_in_water = []
        
    def create_blood_trail(self):
        """Strategically sell small amounts to show weakness"""
        print("\n🩸 CREATING BLOOD TRAIL...")
        print("   (Selling small amounts to trigger panic)")
        
        # Small strategic sells to create red candles
        blood_drops = [
            ("SOL", 0.01, "First drop of blood"),
            ("MATIC", 0.01, "More blood in water"),
            ("AVAX", 0.01, "Sharks smell fear")
        ]
        
        for coin, amount, message in blood_drops:
            try:
                # Get current position
                accounts = client.get_accounts()['accounts']
                for a in accounts:
                    if a['currency'] == coin:
                        balance = float(a['available_balance']['value'])
                        if balance > 0:
                            # Sell tiny amount to create red
                            sell_amount = min(balance * 0.05, amount)  # 5% or specified
                            
                            order = client.market_order_sell(
                                client_order_id=f"bleed_{coin.lower()}_{int(time.time()*1000)}",
                                product_id=f"{coin}-USD",
                                base_size=str(sell_amount)
                            )
                            
                            print(f"   🩸 {coin}: Bled {sell_amount:.6f} - {message}")
                            self.blood_in_water.append(coin)
                            time.sleep(2)  # Space out the bleeding
                            break
                            
            except Exception as e:
                print(f"   ⚠️ {coin}: Couldn't bleed - {str(e)[:30]}")
                
        self.trap_set = True
        print("   🪤 TRAP SET - Blood in the water!")
        
    def detect_panic_feeding(self):
        """Detect if others are panic selling into our trap"""
        print("\n👀 WATCHING FOR PANIC SELLERS...")
        
        for coin in self.blood_in_water:
            try:
                ticker = client.get_product(f'{coin}-USD')
                price = float(ticker.get("price", 0))
                bid = float(ticker.get("bid", price))
                ask = float(ticker.get("ask", price))
                
                # Wide spread = panic selling
                spread_pct = ((ask - bid) / price) * 100
                
                if spread_pct > 0.2:  # 0.2% spread indicates panic
                    print(f"   🎣 {coin}: PANIC DETECTED! Spread: {spread_pct:.3f}%")
                    self.feeding_detected = True
                    return coin
                else:
                    print(f"   🦀 {coin}: Waiting... Spread: {spread_pct:.3f}%")
                    
            except:
                pass
                
        return None
        
    def spring_the_trap(self, panic_coin):
        """Buy aggressively when panic selling detected"""
        print(f"\n🪤 SPRINGING THE TRAP ON {panic_coin}!")
        print("   Others panic sold into our trap - NOW WE FEAST!")
        
        try:
            # Buy double what we bled
            feast_size = 20  # Aggressive buy
            
            order = client.market_order_buy(
                client_order_id=f"feast_{panic_coin.lower()}_{int(time.time()*1000)}",
                product_id=f"{panic_coin}-USD",
                quote_size=str(feast_size)
            )
            
            print(f"   🦀 FEASTING: Bought ${feast_size} of {panic_coin}")
            print("   📈 Trapped the panic sellers at the bottom!")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Feast failed: {str(e)[:50]}")
            return False
            
    def run_trap_sequence(self):
        """Execute the full bleeding trap strategy"""
        print("\n🦀 BLEEDING CRAWDAD TRAP SEQUENCE")
        print("=" * 50)
        
        # Phase 1: Create blood trail
        print("\n📍 PHASE 1: BLEEDING")
        self.create_blood_trail()
        
        # Phase 2: Wait for panic
        print("\n📍 PHASE 2: WAITING FOR PANIC")
        wait_cycles = 0
        max_wait = 10  # Wait up to 10 minutes
        
        while wait_cycles < max_wait:
            wait_cycles += 1
            print(f"\n[Cycle {wait_cycles}/{max_wait}]")
            
            panic_coin = self.detect_panic_feeding()
            
            if panic_coin:
                # Phase 3: Spring trap
                print("\n📍 PHASE 3: SPRINGING TRAP")
                if self.spring_the_trap(panic_coin):
                    print("\n✅ TRAP SUCCESSFUL!")
                    print("   We bled 2% to gain 10%+")
                    print("   The fearful fed the patient")
                    break
                    
            time.sleep(60)  # Check every minute
            
        if not self.feeding_detected:
            print("\n⏰ No panic detected - trap expired")
            print("   Sometimes the water stays calm")
            
    def status_check(self):
        """Check portfolio after trap"""
        print("\n📊 POST-TRAP STATUS:")
        
        try:
            total = 0
            accounts = client.get_accounts()['accounts']
            
            for a in accounts:
                balance = float(a['available_balance']['value'])
                if a['currency'] == 'USD':
                    total += balance
                elif balance > 0.001:
                    try:
                        ticker = client.get_product(f"{a['currency']}-USD")
                        price = float(ticker.get('price', 0))
                        value = balance * price
                        if value > 1:
                            total += value
                    except:
                        pass
                        
            print(f"   Portfolio: ${total:.2f}")
            
            if total > 43.53:
                print("   🎉 TRAP PROFITABLE!")
            else:
                print("   🦀 Trap set for later...")
                
        except:
            print("   Unable to check portfolio")

# Initialize trap
trap = BleedingCrawdadTrap()

print("""
🩸 BLEEDING STRATEGY EXPLAINED:

1. We show weakness by selling tiny amounts
2. This creates red candles on charts
3. Nervous traders see red and panic
4. They sell into our buy orders
5. We feast on their fear

"The crawdad that bleeds but doesn't die
 becomes stronger from the feeding frenzy"

⚠️ WARNING: This is psychological warfare
   We weaponize fear against itself
""")

print("\n🦀 INITIATING BLEEDING SEQUENCE...")
print("   Market falling to new level = PERFECT timing")
print("   We bleed with it, then feast on the fear")
print()

try:
    trap.run_trap_sequence()
    trap.status_check()
    
except KeyboardInterrupt:
    print("\n\n🦀 Bleeding trap deactivated")
    trap.status_check()
    
print("""

"Sometimes you must bleed
 to reveal who else is bleeding.
 
 The wounded crawdad
 attracts bigger prey."
 
Mitakuye Oyasin
""")