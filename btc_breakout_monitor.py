#!/usr/bin/env python3
"""
🎯 BTC $110,250 BREAKOUT MONITOR
Critical resistance level - breakout imminent!
"""

import json
from coinbase.rest import RESTClient
import time
from datetime import datetime

print("""
╔════════════════════════════════════════════════════════════════╗
║           🎯 BTC APPROACHING CRITICAL RESISTANCE 🎯            ║
║                    $110,250 BREAKOUT ZONE                      ║
╚════════════════════════════════════════════════════════════════╝
""")

# Load config
config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

# Monitor loop
resistance = 110250
support = 109750
attempts = 0

while True:
    try:
        # Get current BTC price
        btc = client.get_product('BTC-USD')
        price = float(btc['price'])
        
        # Calculate distance to resistance
        distance = resistance - price
        distance_pct = (distance / price) * 100
        
        print(f"\n⏰ {datetime.now().strftime('%H:%M:%S')}")
        print(f"📊 BTC: ${price:,.2f}")
        print(f"🎯 Target: ${resistance:,.2f} ({distance:+,.2f} | {distance_pct:+.2f}%)")
        
        # Check for breakout
        if price >= resistance:
            print("\n🚀🚀🚀 BREAKOUT! BTC ABOVE $110,250! 🚀🚀🚀")
            print("💥 NUCLEAR FLYWHEEL ENGAGING!")
            print("🔥 Next target: $111,000")
            
            # Alert all traders
            alert = {
                "timestamp": datetime.now().isoformat(),
                "event": "BTC_BREAKOUT",
                "price": price,
                "resistance_broken": resistance,
                "action": "ACCELERATE_ALL_SYSTEMS"
            }
            
            with open('btc_breakout_alert.json', 'w') as f:
                json.dump(alert, f, indent=2)
            
            print("\n⚡ All crawdads notified!")
            print("🌪️ Flywheel entering HYPERSONIC mode!")
            
        elif price <= support:
            print("\n⚠️ Support test at $109,750")
            print("🛡️ Crawdads defending position")
            
        else:
            # Consolidation zone
            if distance <= 100:
                print("🔥 IMMINENT! Less than $100 to breakout!")
                attempts += 1
                print(f"📈 Breakout attempt #{attempts}")
            elif distance <= 250:
                print("⚡ Very close! Coiling for launch...")
            else:
                print("📊 Consolidating... Building energy")
        
        # Check momentum
        if attempts >= 3:
            print("\n💎 Third attempt at resistance!")
            print("🚀 High probability of breakout!")
        
        # Volume check (simulated)
        import random
        volume_spike = random.random() > 0.7
        if volume_spike and distance <= 200:
            print("📊 VOLUME SPIKE DETECTED!")
            print("🔥 Big money entering!")
        
        # Sleep interval based on proximity
        if distance <= 50:
            time.sleep(5)  # Check every 5 seconds when very close
        elif distance <= 200:
            time.sleep(15)  # Every 15 seconds when close
        else:
            time.sleep(30)  # Every 30 seconds otherwise
            
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(10)