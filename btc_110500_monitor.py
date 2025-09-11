#!/usr/bin/env python3
"""
🎯 BTC $110,500 TARGET MONITOR
Next resistance after breaking $110,250!
"""

import json
from coinbase.rest import RESTClient
import time
from datetime import datetime

print("""
╔══════════════════════════════════════════════════════════════╗
║         🎯 BTC TARGETING $110,500 RESISTANCE 🎯             ║
║            Broke $110,250 → Now hunting $110,500            ║
╚══════════════════════════════════════════════════════════════╝
""")

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

# Key levels
first_resistance = 110250  # BROKEN! ✅
target = 110500            # Next target
mega_target = 111000       # After that

print(f"✅ First resistance BROKEN: ${first_resistance:,}")
print(f"🎯 Current target: ${target:,}")
print(f"🚀 Mega target: ${mega_target:,}")
print("\n" + "="*60)

while True:
    try:
        # Get current BTC price
        btc = client.get_product('BTC-USD')
        price = float(btc['price'])
        
        # Calculate distances
        distance_to_target = target - price
        distance_pct = (distance_to_target / price) * 100
        
        # Progress from breakout
        progress_from_breakout = price - first_resistance
        
        print(f"\n⏰ {datetime.now().strftime('%H:%M:%S')}")
        print(f"📊 BTC: ${price:,.2f}")
        print(f"📈 Progress: +${progress_from_breakout:,.2f} from breakout")
        print(f"🎯 To $110,500: {distance_to_target:+,.2f} ({distance_pct:+.3f}%)")
        
        # Status messages based on price
        if price >= target:
            print("\n🚀🚀🚀 TARGET HIT! $110,500 CONQUERED! 🚀🚀🚀")
            print(f"💥 NEXT: ${mega_target:,}")
            print("🔥 NUCLEAR FLYWHEEL IN OVERDRIVE!")
            
            # Update targets
            first_resistance = target
            target = mega_target
            mega_target = 112000
            
        elif distance_to_target <= 50:
            print("🔥🔥🔥 IMMINENT! Less than $50 away!")
            print("⚡ FINAL PUSH INCOMING!")
            
        elif distance_to_target <= 100:
            print("🔥 VERY CLOSE! Under $100 to target!")
            print("💪 Momentum building...")
            
        elif distance_to_target <= 200:
            print("⚡ Approaching target zone...")
            print("📈 Consolidating for next leg up")
            
        else:
            print("📊 Building energy...")
            
        # Check momentum
        if progress_from_breakout > 100:
            print("\n💎 STRONG BREAKOUT! +$100 from resistance!")
            
        # Check for USD balance to feed more
        accounts = client.get_accounts()['accounts']
        for acc in accounts:
            if acc['currency'] == 'USD':
                usd = float(acc['available_balance']['value'])
                if usd > 100:
                    print(f"\n💰 ${usd:.2f} USD available!")
                    print("   Consider feeding BTC flywheel!")
                break
        
        # Sleep based on proximity
        if distance_to_target <= 25:
            time.sleep(3)   # Very close - check every 3 seconds
        elif distance_to_target <= 100:
            time.sleep(10)  # Close - every 10 seconds
        else:
            time.sleep(20)  # Normal - every 20 seconds
            
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(10)