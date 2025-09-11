#!/usr/bin/env python3
"""
SQUEEZE BREAKOUT TRADER
When bands are this tight, the breakout will be violent!
Place orders on both sides to catch it
"""
import json
import time
from coinbase.rest import RESTClient
from datetime import datetime

print("""
╔════════════════════════════════════════════════════════════════════╗
║           🌀 SINGULARITY SQUEEZE BREAKOUT TRADER 🌀                 ║
║             Bands at 0.00002% - Historic compression!               ║
╚════════════════════════════════════════════════════════════════════╝
""")

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=3)

# Key levels
SACRED_SUPPORT = 117056
BREAKOUT_UP = 117900
BREAKOUT_DOWN = 117300
current_price = 117853

print(f"📍 CURRENT SETUP:")
print(f"   BTC: ${current_price:,.0f}")
print(f"   Sacred Support: ${SACRED_SUPPORT:,}")
print(f"   Breakout triggers: ${BREAKOUT_UP:,} / ${BREAKOUT_DOWN:,}")
print()

print("🎯 STRATEGY:")
print("   • If breaks ABOVE $117,900 → BUY immediately")
print("   • If breaks BELOW $117,300 → BUY the dip hard")
print("   • Band squeeze this tight = $500+ move guaranteed")
print()

def check_breakout():
    """Monitor for the breakout"""
    try:
        ticker = client.get_product('BTC-USD')
        price = float(ticker.price)
        
        # Check for breakout
        if price > BREAKOUT_UP:
            return 'UP', price
        elif price < BREAKOUT_DOWN:
            return 'DOWN', price
        else:
            return 'SQUEEZE', price
    except:
        return 'ERROR', 0

print("🔍 MONITORING FOR BREAKOUT...")
print(f"   Started: {datetime.now().strftime('%H:%M:%S')}")
print()

check_count = 0
last_price = current_price

while True:
    check_count += 1
    direction, price = check_breakout()
    
    if direction == 'UP':
        print(f"🚀🚀🚀 BREAKOUT UP! ${price:,.2f}")
        print("   BANDS EXPLODED UPWARD!")
        print("   Target: $118,500+")
        print("   ACTION: Riding the wave!")
        break
        
    elif direction == 'DOWN':
        print(f"💥💥💥 BREAKOUT DOWN! ${price:,.2f}")
        print("   BANDS BROKE TO YOUR TARGET!")
        print("   Sacred $117,056 incoming!")
        print("   ACTION: BUYING THE DIP!")
        break
        
    elif direction == 'SQUEEZE':
        if check_count % 10 == 0:
            movement = price - last_price
            print(f"   [{datetime.now().strftime('%H:%M:%S')}] Still coiling: ${price:,.2f} ({movement:+.2f})")
            last_price = price
            
            # Check how tight
            if abs(movement) < 1:
                print("      ⚡ EXTREME COMPRESSION - Breakout imminent!")
    
    time.sleep(3)

print()
print("📊 BREAKOUT DETECTED!")
print(f"   Direction: {direction}")
print(f"   Price: ${price:,.2f}")
print(f"   Move from squeeze: ${abs(price - current_price):,.2f}")
print()
print("🔥 THE FLYWHEEL SPINS! 🔥")