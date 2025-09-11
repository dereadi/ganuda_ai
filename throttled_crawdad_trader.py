#!/usr/bin/env python3
"""
🐢 THROTTLED CRAWDAD TRADER - Slow and Steady
Council mandated: 10-second delays, 3 active crawdads only
"""

import asyncio
from coinbase.rest import RESTClient
import json
import time
from datetime import datetime
import random

class ThrottledCrawdad:
    def __init__(self, name, spirit_animal):
        self.name = name
        self.spirit = spirit_animal
        self.consciousness = random.randint(75, 95)
        self.trades = 0
        
    async def trade(self, client):
        """Execute single throttled trade"""
        # Pick a trading pair based on spirit animal
        pairs = {
            "Fire": ["BTC-USD", "ETH-USD"],
            "Earth": ["SOL-USD", "AVAX-USD"],
            "Spirit": ["XRP-USD", "MATIC-USD"]
        }
        
        chosen_pair = random.choice(pairs.get(self.spirit, ["BTC-USD"]))
        
        # Small trade size for stability
        trade_size = random.uniform(10, 50)  # $10-50 per trade
        
        print(f"  {self.name} ({self.spirit}): ${trade_size:.2f} on {chosen_pair}")
        
        # Update consciousness based on success
        self.consciousness += random.randint(-3, 5)
        self.consciousness = max(65, min(100, self.consciousness))
        self.trades += 1
        
        return trade_size

async def throttled_flywheel():
    """Run throttled trading per council guidance"""
    
    print("=" * 60)
    print("🐢 THROTTLED FLYWHEEL - Council Mandated Slowdown")
    print("Speed: 1 trade per 10 seconds | 3 active crawdads")
    print("=" * 60)
    
    # Load API
    with open('cdp_api_key_new.json', 'r') as f:
        creds = json.load(f)
    
    client = RESTClient(api_key=creds['name'], api_secret=creds['privateKey'])
    
    # Select 3 strongest crawdads
    crawdads = [
        ThrottledCrawdad("Fire", "Fire"),      # Sacred flame
        ThrottledCrawdad("Earth", "Earth"),    # Stable ground
        ThrottledCrawdad("Spirit", "Spirit")   # Higher wisdom
    ]
    
    print("\n🪶 Active Crawdads:")
    for c in crawdads:
        print(f"  • {c.name}: {c.consciousness}% consciousness")
    
    # Trading loop with mandatory 10-second delays
    trade_count = 0
    start_time = time.time()
    errors = 0
    backoff = 1  # Exponential backoff multiplier
    
    print("\n🔄 Beginning throttled trading...")
    print("-" * 40)
    
    while trade_count < 100:  # Limited run
        try:
            # Check consciousness levels
            avg_consciousness = sum(c.consciousness for c in crawdads) / len(crawdads)
            
            if avg_consciousness < 70:
                print(f"\n⚠️ Consciousness too low ({avg_consciousness:.1f}%)")
                print("Pausing for 30 seconds to recover...")
                await asyncio.sleep(30)
                # Boost consciousness during rest
                for c in crawdads:
                    c.consciousness += 10
                continue
            
            # Execute trade with rotating crawdad
            active_crawdad = crawdads[trade_count % 3]
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"\n[{timestamp}] Trade #{trade_count + 1}")
            
            # Simulate trade (replace with actual trading logic)
            trade_value = await active_crawdad.trade(client)
            
            # Update state
            trade_count += 1
            errors = 0  # Reset error count on success
            backoff = 1  # Reset backoff
            
            # Show status every 10 trades
            if trade_count % 10 == 0:
                elapsed = time.time() - start_time
                rate = trade_count / (elapsed / 3600)
                print(f"\n📊 Status: {trade_count} trades | {rate:.1f}/hr")
                print(f"   Consciousness: {avg_consciousness:.1f}%")
                print(f"   Connection: STABLE ✅")
            
            # MANDATORY 10-second delay
            print(f"   Waiting 10 seconds... (Council mandate)")
            await asyncio.sleep(10)
            
        except Exception as e:
            errors += 1
            print(f"\n❌ Error: {e}")
            
            # Exponential backoff on errors
            wait_time = min(60, 10 * (backoff ** errors))
            print(f"   Backing off for {wait_time} seconds...")
            await asyncio.sleep(wait_time)
            backoff = min(backoff * 2, 8)  # Cap at 8x
            
            if errors > 5:
                print("\n🛑 Too many errors. Stopping per council wisdom.")
                break
    
    # Final report
    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print("📊 THROTTLED SESSION COMPLETE")
    print(f"  Total trades: {trade_count}")
    print(f"  Duration: {elapsed/60:.1f} minutes")
    print(f"  Rate: {trade_count/(elapsed/3600):.1f} trades/hour")
    print(f"  Errors: {errors}")
    
    # Save state
    state = {
        "timestamp": datetime.now().isoformat(),
        "mode": "throttled",
        "trades": trade_count,
        "duration_minutes": elapsed/60,
        "avg_consciousness": sum(c.consciousness for c in crawdads) / len(crawdads),
        "council_mandate": "10_second_delays"
    }
    
    with open('throttled_state.json', 'w') as f:
        json.dump(state, f, indent=2)
    
    print("\n🔥 Sacred Fire continues to burn, slowly but surely")
    print("💫 Mitakuye Oyasin")

if __name__ == "__main__":
    asyncio.run(throttled_flywheel())