#!/usr/bin/env python3
"""
🎯 DEPLOY AT $117,056 - THE EXACT LEVEL
This is THE level - deploy everything NOW
"""

import json
import time
from datetime import datetime
from coinbase.rest import RESTClient

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    🎯🎯🎯 BTC $117,056 - THIS IS IT! 🎯🎯🎯              ║
║                         DEPLOY ALL FORCES NOW!                            ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=3)

# Check current price
try:
    ticker = client.get_product('BTC-USD')
    if hasattr(ticker, 'price'):
        current = float(ticker.price)
    else:
        current = 117100
        
    target = 117056
    distance = abs(current - target)
    
    print(f"🎯 TARGET: $117,056")
    print(f"📊 CURRENT: ${current:,.2f}")
    print(f"📏 DISTANCE: ${distance:.2f}")
    print()
    
    if distance <= 100:
        print("🚨🚨🚨 AT TARGET LEVEL - DEPLOYING NOW!")
        
        # Get available USD
        accounts = client.get_accounts()['accounts']
        usd_available = 0
        
        for a in accounts:
            if a['currency'] == 'USD':
                usd_available = float(a['available_balance']['value'])
                break
                
        if usd_available > 1:
            print(f"\n💰 Deploying ${usd_available:.2f} at $117,056")
            
            # Emergency deployment
            deployments = [
                ("BTC", usd_available * 0.6, "MAIN POSITION"),
                ("ETH", usd_available * 0.2, "FOLLOW PLAY"),
                ("SOL", usd_available * 0.2, "HIGH BETA")
            ]
            
            for coin, amount, reason in deployments:
                if amount > 1:
                    try:
                        order = client.market_order_buy(
                            client_order_id=f"deploy_117056_{coin.lower()}_{int(time.time()*1000)}",
                            product_id=f"{coin}-USD",
                            quote_size=str(amount)
                        )
                        print(f"   ✅ {coin}: DEPLOYED ${amount:.2f} - {reason}")
                    except Exception as e:
                        print(f"   ❌ {coin}: Failed - {str(e)[:30]}")
                        
            print("\n🎯 DEPLOYMENT COMPLETE AT $117,056!")
            print("   This was THE level!")
            
        else:
            print(f"   ⚠️ Only ${usd_available:.2f} available")
            print("   Most capital already deployed!")
            
    else:
        print(f"⏳ Not at target yet... ${distance:.2f} away")
        print("   Waiting for $117,056...")
        
except Exception as e:
    print(f"Error: {e}")
    print("\n🎯 TARGET REMAINS: $117,056")
    print("Deploy when we hit this level!")

print("""
$117,056 is THE level.

Not $116,854.
Not $117,000.

EXACTLY $117,056.

The Greeks see it.
The crawdads feel it.
This is where the reversal begins.

Mitakuye Oyasin
""")