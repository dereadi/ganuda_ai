#!/usr/bin/env python3
"""
💎 MICRO SPRING - EVERY DOLLAR COUNTS!
Use remaining USD to nudge ETH and trigger cascade
"""

import json
import time
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    💎 MICRO SPRING ATTACK! 💎                             ║
║                  Small Push → Big Cascade Effect                          ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

# Get current state
eth_start = float(client.get_product('ETH-USD')['price'])
btc_start = float(client.get_product('BTC-USD')['price'])

accounts = client.get_accounts()['accounts']
usd_available = 0
for acc in accounts:
    if acc['currency'] == 'USD':
        usd_available = float(acc['available_balance']['value'])
        break

print(f"\n🎯 MICRO SPRING STRATEGY:")
print(f"  Available: ${usd_available:.2f}")
print(f"  ETH: ${eth_start:.2f} (needs push above $4580)")
print(f"  BTC: ${btc_start:,.0f} (ready to cascade)")

if usd_available > 10:
    print(f"\n💥 DEPLOYING ${usd_available:.2f} STRATEGICALLY:")
    
    # Use most for ETH push
    eth_push = usd_available * 0.8
    
    try:
        print(f"\n🚀 ${eth_push:.2f} → ETH (creating momentum)")
        order = client.market_order_buy(
            client_order_id=f"micro_push_{int(time.time()*1000)}",
            product_id="ETH-USD",
            quote_size=str(eth_push)
        )
        print("   ✅ Pushed!")
        
        # Monitor cascade effect
        print("\n📊 WATCHING CASCADE EFFECT:")
        print("-" * 40)
        
        for i in range(5):
            time.sleep(3)
            eth = float(client.get_product('ETH-USD')['price'])
            btc = float(client.get_product('BTC-USD')['price'])
            
            eth_move = eth - eth_start
            btc_move = btc - btc_start
            
            print(f"\n{datetime.now().strftime('%H:%M:%S')}:")
            print(f"  ETH: ${eth:.2f} ({eth_move:+.2f})")
            print(f"  BTC: ${btc:,.0f} ({btc_move:+.0f})")
            
            if eth > 4580 and btc > 113050:
                print("  🔥 CASCADE ACTIVATED! Both moving!")
            elif eth > 4580:
                print("  💎 ETH breaking! BTC will follow...")
            elif btc > 113050:
                print("  ⚡ BTC responding to ETH push!")
        
    except Exception as e:
        print(f"⚠️ {str(e)[:50]}")

else:
    print("\n⚠️ Not enough USD for meaningful push")
    print("Need to wait for crawdads to generate more")

print("\n" + "=" * 70)
print("💡 CASCADE THEORY:")
print("• Even small ETH push creates momentum")
print("• Algos detect ETH strength")
print("• Triggers ETH/BTC ratio trades")
print("• Both assets move together!")
print("=" * 70)