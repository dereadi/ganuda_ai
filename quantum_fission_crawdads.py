#!/usr/bin/env python3
"""
⚛️ QUANTUM FISSION CRAWDADS
Strategic loss-taking for explosive gains
"Sometimes you must split the atom to release the energy"
Crawdads that intentionally take small losses to catch nuclear moves
"""

import json
import subprocess
import time
from datetime import datetime
from coinbase.rest import RESTClient

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    ⚛️ QUANTUM FISSION CRAWDADS ⚛️                        ║
║                  "Split to Multiply Exponentially"                        ║
║              Small Strategic Losses → Nuclear Chain Reaction              ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

class FissionCrawdad:
    def __init__(self):
        config = json.load(open("/home/dereadi/.coinbase_config.json"))
        key = config["api_key"].split("/")[-1]
        self.client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=3)
        
        self.fission_threshold = 0.02  # 2% loss acceptable for fission
        self.chain_reaction_target = 0.10  # 10% explosive gain target
        self.uranium_coins = []  # Coins ready to go nuclear
        self.fission_attempts = 0
        self.chain_reactions = 0
        
    def detect_fission_opportunity(self, coin):
        """Detect when a small loss could trigger a chain reaction"""
        try:
            ticker = self.client.get_product(f'{coin}-USD')
            price = float(ticker.get("price", 0))
            bid = float(ticker.get("bid", price))
            ask = float(ticker.get("ask", price))
            
            # Calculate indicators
            spread = (ask - bid) / price
            
            # Fission conditions:
            # 1. Tight spread (coiled spring)
            # 2. Price consolidating (building energy)
            # 3. Volume building (chain reaction potential)
            
            if spread < 0.001:  # Super tight spread = energy building
                return {
                    "coin": coin,
                    "type": "NUCLEAR_READY",
                    "price": price,
                    "energy_level": "CRITICAL",
                    "action": "PREPARE_FISSION"
                }
            elif spread < 0.002:
                return {
                    "coin": coin,
                    "type": "ENRICHING",
                    "price": price,
                    "energy_level": "BUILDING",
                    "action": "MONITOR"
                }
            else:
                return {
                    "coin": coin,
                    "type": "STABLE",
                    "price": price,
                    "energy_level": "LOW",
                    "action": "WAIT"
                }
                
        except Exception as e:
            return {"coin": coin, "type": "ERROR", "action": "SKIP"}
            
    def execute_fission_trade(self, opportunity):
        """Take strategic loss to trigger chain reaction"""
        if opportunity["action"] != "PREPARE_FISSION":
            return None
            
        coin = opportunity["coin"]
        price = opportunity["price"]
        
        print(f"\n⚛️ INITIATING FISSION on {coin}")
        print(f"   Current Price: ${price:.2f}")
        print(f"   Energy Level: {opportunity['energy_level']}")
        
        try:
            # FISSION STRATEGY:
            # 1. Buy slightly above market (take small loss)
            # 2. This pushes through resistance
            # 3. Triggers stop losses above
            # 4. Creates chain reaction
            
            # Buy aggressively (accepting small loss)
            fission_size = 20  # Start small
            order = self.client.market_order_buy(
                client_order_id=f"fission_{int(time.time()*1000)}",
                product_id=f"{coin}-USD",
                quote_size=str(fission_size)
            )
            
            self.fission_attempts += 1
            print(f"   ⚛️ FISSION INITIATED: ${fission_size} into {coin}")
            print(f"   Accepting tactical loss for chain reaction...")
            
            # Monitor for chain reaction
            time.sleep(2)
            
            # Check if chain reaction started
            new_ticker = self.client.get_product(f'{coin}-USD')
            new_price = float(new_ticker.get("price", price))
            
            reaction = ((new_price - price) / price) * 100
            
            if reaction > 0.5:  # 0.5% immediate move
                print(f"   ☢️ CHAIN REACTION DETECTED! +{reaction:.2f}%")
                self.chain_reactions += 1
                
                # Add more fuel to the reaction
                fuel_order = self.client.market_order_buy(
                    client_order_id=f"fuel_{int(time.time()*1000)}",
                    product_id=f"{coin}-USD",
                    quote_size=str(fission_size * 2)
                )
                print(f"   🔥 ADDING FUEL: ${fission_size * 2} more!")
                
                return "CHAIN_REACTION_ACTIVE"
                
            elif reaction < -self.fission_threshold:
                print(f"   💥 Fission loss: {reaction:.2f}% (tactical)")
                return "FISSION_LOSS_ACCEPTED"
            else:
                print(f"   ⚡ Energy building... {reaction:+.2f}%")
                return "ENERGY_ACCUMULATING"
                
        except Exception as e:
            print(f"   ❌ Fission failed: {str(e)[:50]}")
            return "FISSION_FAILED"
            
    def scan_for_uranium(self):
        """Find coins ready to go nuclear"""
        uranium_candidates = ["SOL", "AVAX", "MATIC", "ATOM", "NEAR"]
        
        for coin in uranium_candidates:
            opportunity = self.detect_fission_opportunity(coin)
            
            if opportunity["energy_level"] == "CRITICAL":
                self.uranium_coins.append(coin)
                print(f"☢️ {coin} added to uranium list - CRITICAL MASS")
            elif opportunity["energy_level"] == "BUILDING":
                print(f"⚡ {coin} enriching... {opportunity['energy_level']}")
                
    def run_fission_protocol(self):
        """Main fission trading loop"""
        print("\n⚛️ FISSION PROTOCOL ACTIVE")
        print("=" * 60)
        print("Strategy: Accept small tactical losses to trigger chain reactions")
        print("Target: 2% loss → 10% explosive gain")
        print()
        
        cycle = 0
        
        while True:
            cycle += 1
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Scan for uranium (nuclear-ready coins)
            if cycle % 5 == 0:
                print(f"\n[{timestamp}] ☢️ Scanning for uranium...")
                self.scan_for_uranium()
                
            # Check each uranium coin for fission opportunity
            for coin in self.uranium_coins[:]:  # Copy list to modify during iteration
                opportunity = self.detect_fission_opportunity(coin)
                
                if opportunity["action"] == "PREPARE_FISSION":
                    print(f"\n[{timestamp}] ⚛️ FISSION OPPORTUNITY: {coin}")
                    result = self.execute_fission_trade(opportunity)
                    
                    if result == "CHAIN_REACTION_ACTIVE":
                        print(f"   ☢️☢️☢️ NUCLEAR CHAIN REACTION ON {coin}!")
                        # Keep this coin hot
                    elif result == "FISSION_LOSS_ACCEPTED":
                        print(f"   💥 Tactical loss taken on {coin}")
                        # Remove from immediate list, let it cool
                        self.uranium_coins.remove(coin)
                        
            # Status update
            if cycle % 10 == 0:
                print(f"\n[{timestamp}] ⚛️ FISSION STATUS:")
                print(f"   Fission Attempts: {self.fission_attempts}")
                print(f"   Chain Reactions: {self.chain_reactions}")
                print(f"   Success Rate: {(self.chain_reactions/max(1,self.fission_attempts))*100:.1f}%")
                print(f"   Uranium Coins: {len(self.uranium_coins)}")
                
                if self.chain_reactions > 0:
                    print(f"   🔥 NUCLEAR REACTIONS ACHIEVED!")
                    
            time.sleep(30)  # Quick cycles for fission detection

# Initialize Fission Crawdad
fission = FissionCrawdad()

print("⚛️ QUANTUM FISSION CRAWDAD INITIALIZED")
print("-" * 60)
print("Philosophy: Sometimes you must break things to release energy")
print("Tactic: Take 2% losses to trigger 10% chain reactions")
print("Warning: This crawdad trades aggressively!")
print()

try:
    fission.run_fission_protocol()
except KeyboardInterrupt:
    print(f"\n\n⚛️ FISSION PROTOCOL COMPLETE")
    print(f"   Total Attempts: {fission.fission_attempts}")
    print(f"   Chain Reactions: {fission.chain_reactions}")
    
    if fission.chain_reactions > 0:
        print(f"\n☢️ NUCLEAR SUCCESS!")
        print("   The crawdads split atoms and multiplied energy!")
    else:
        print(f"\n⚡ Energy accumulated for future fission")
        
    print("""
    
"In nuclear physics, controlled fission releases massive energy.
 In markets, strategic losses can trigger explosive gains.
 
 The crawdads understand: Sometimes you lose 2% to gain 20%.
 
 Split the atom. Start the reaction. Multiply exponentially."
 
 Mitakuye Oyasin
    """)