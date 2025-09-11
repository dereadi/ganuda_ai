#!/usr/bin/env python3
"""
🚀 SPRING ETH - BREAK THE FLATNESS!
Deploy capital to push ETH through resistance
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
║                      💎 SPRINGING ETH! 💎                                 ║
║                    Breaking Through The Flatness                          ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - INJECTING MOMENTUM!")
print("=" * 70)

# Check current state
eth = float(client.get_product('ETH-USD')['price'])
btc = float(client.get_product('BTC-USD')['price'])

# Check available USD
accounts = client.get_accounts()['accounts']
usd_available = 0
for acc in accounts:
    if acc['currency'] == 'USD':
        usd_available = float(acc['available_balance']['value'])
        break

print(f"\n📊 CURRENT SITUATION:")
print(f"  ETH: ${eth:.2f} - FLAT AND NEEDS A PUSH!")
print(f"  BTC: ${btc:,.0f}")
print(f"  Available USD: ${usd_available:.2f}")

if usd_available > 100:
    print(f"\n🎯 SPRING STRATEGY:")
    print("-" * 40)
    
    # Deploy in waves to create momentum
    eth_allocation = min(200, usd_available * 0.5)  # Use up to 50% of available
    waves = 3
    wave_size = eth_allocation / waves
    
    print(f"• Total deployment: ${eth_allocation:.2f}")
    print(f"• Waves: {waves} x ${wave_size:.2f}")
    print(f"• Target: Push ETH above $4,585")
    
    print(f"\n💥 EXECUTING SPRING ATTACK:")
    print("-" * 40)
    
    for i in range(waves):
        try:
            print(f"\n🌊 Wave {i+1}: ${wave_size:.2f} → ETH")
            order = client.market_order_buy(
                client_order_id=f"spring_eth_{int(time.time()*1000)}",
                product_id="ETH-USD",
                quote_size=str(wave_size)
            )
            print(f"   ✅ Deployed!")
            
            # Check immediate impact
            time.sleep(2)
            new_eth = float(client.get_product('ETH-USD')['price'])
            impact = new_eth - eth
            print(f"   📈 ETH now: ${new_eth:.2f} ({impact:+.2f})")
            
            if new_eth > 4585:
                print(f"   🚀 BROKE $4,585! MOMENTUM ACHIEVED!")
            elif new_eth > 4580:
                print(f"   ⚡ Above $4,580! Keep pushing!")
            
            eth = new_eth  # Update reference
            time.sleep(3)
            
        except Exception as e:
            print(f"   ⚠️ {str(e)[:50]}")
    
    # Check final impact
    time.sleep(3)
    final_eth = float(client.get_product('ETH-USD')['price'])
    total_impact = final_eth - eth
    
    print(f"\n🎯 SPRING RESULTS:")
    print("-" * 40)
    print(f"ETH pushed to: ${final_eth:.2f}")
    print(f"Total move: ${total_impact:.2f}")
    
    if final_eth > 4585:
        print("✅ SUCCESS! ETH BREAKING FREE!")
        print("🔥 Others will now chase the momentum!")
    elif final_eth > 4580:
        print("⚡ Good progress! Almost there!")
    else:
        print("💭 Building pressure for next attempt...")

elif usd_available > 20:
    print(f"\n💡 MICRO SPRING with ${usd_available:.2f}:")
    try:
        order = client.market_order_buy(
            client_order_id=f"micro_spring_{int(time.time()*1000)}",
            product_id="ETH-USD",
            quote_size=str(usd_available * 0.9)
        )
        print("✅ Micro push deployed!")
        time.sleep(2)
        new_eth = float(client.get_product('ETH-USD')['price'])
        print(f"ETH: ${new_eth:.2f} ({new_eth - eth:+.2f})")
    except Exception as e:
        print(f"⚠️ {str(e)[:50]}")
else:
    print("\n⚠️ Low USD balance - need to harvest profits first!")
    print("Run profit extraction to generate spring capital!")

print("\n" + "=" * 70)
print("💎 ETH SPRING COMPLETE!")
print("Watch for follow-through momentum!")
print("=" * 70)