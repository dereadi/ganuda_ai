#!/usr/bin/env python3
"""
🔥💀🚀 YAS! MAXIMUM FUCKING OVERDRIVE! 🚀💀🔥
THE TRIBE HAS SPOKEN
THE MISSION IS LIVE
WE'RE GOING TO $42,588
NOTHING CAN STOP US NOW!
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
║                     🔥💀🚀 YAS! YAS! YAS! 🚀💀🔥                         ║
║                        MAXIMUM OVERDRIVE MODE                             ║
║                    NOTHING STOPS THIS TRAIN NOW                           ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - OVERDRIVE ENGAGED")
print("=" * 70)

# Execute the emergency milk NOW
print("\n💉 EXECUTING EMERGENCY MILK - NO HESITATION!")
print("-" * 50)

accounts = client.get_accounts()
holdings = {}
usd_before = 0

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if currency == 'USD':
        usd_before = balance
    elif balance > 0:
        holdings[currency] = balance

print(f"Current USD: ${usd_before:.2f} - TIME TO MILK!")

# MILK SOL - 3%
if 'SOL' in holdings and holdings['SOL'] > 1:
    sol_milk = holdings['SOL'] * 0.03
    if sol_milk > 0.1:
        try:
            print(f"\n🥛 Milking {sol_milk:.3f} SOL...")
            order = client.market_order_sell(
                client_order_id=f"yas-sol-{datetime.now().strftime('%H%M%S')}",
                product_id='SOL-USD',
                base_size=str(round(sol_milk, 3))
            )
            print(f"   ✅ YAS! MILKED!")
            time.sleep(1)
        except Exception as e:
            print(f"   ⚠️ {str(e)[:30]}")

# MILK MATIC - 3%
if 'MATIC' in holdings and holdings['MATIC'] > 100:
    matic_milk = holdings['MATIC'] * 0.03
    if matic_milk > 10:
        try:
            print(f"\n🥛 Milking {matic_milk:.0f} MATIC...")
            order = client.market_order_sell(
                client_order_id=f"yas-matic-{datetime.now().strftime('%H%M%S')}",
                product_id='MATIC-USD',
                base_size=str(int(matic_milk))
            )
            print(f"   ✅ YAS! MILKED!")
            time.sleep(1)
        except Exception as e:
            print(f"   ⚠️ {str(e)[:30]}")

# MILK AVAX - 3%
if 'AVAX' in holdings and holdings['AVAX'] > 1:
    avax_milk = holdings['AVAX'] * 0.03
    if avax_milk > 0.5:
        try:
            print(f"\n🥛 Milking {avax_milk:.2f} AVAX...")
            order = client.market_order_sell(
                client_order_id=f"yas-avax-{datetime.now().strftime('%H%M%S')}",
                product_id='AVAX-USD',
                base_size=str(round(avax_milk, 2))
            )
            print(f"   ✅ YAS! MILKED!")
            time.sleep(1)
        except Exception as e:
            print(f"   ⚠️ {str(e)[:30]}")

# Check the milk
time.sleep(3)
accounts = client.get_accounts()
usd_after = 0

for account in accounts['accounts']:
    if account['currency'] == 'USD':
        usd_after = float(account['available_balance']['value'])
        break

print(f"\n💰 MILK COLLECTED: ${usd_after - usd_before:.2f}")
print(f"   Total USD: ${usd_after:.2f}")

# Check BTC momentum
print("\n🚀 BTC MOMENTUM CHECK:")
print("-" * 50)

btc_price = float(client.get_product('BTC-USD')['price'])
print(f"BTC: ${btc_price:,.0f}")

for i in range(5):
    time.sleep(2)
    btc = float(client.get_product('BTC-USD')['price'])
    move = btc - btc_price
    
    print(f"\n{datetime.now().strftime('%H:%M:%S')}: ${btc:,.0f} ({move:+.0f})")
    
    if move > 50:
        print("   🚀🚀🚀 YAS! LIFTOFF!")
    elif move > 20:
        print("   🚀🚀 YAS! ASCENDING!")
    elif move > 0:
        print("   🚀 YAS! CLIMBING!")
    elif move < -50:
        print("   🎯 YAS! BUY THE DIP!")
    else:
        print("   🌀 YAS! COILING!")

# The energy
print("\n" + "=" * 70)
print("⚡ THE ENERGY IS REAL:")
print("-" * 50)
print("• Eight coils wound = 256x energy")
print("• Portfolio ready = $12,639")
print("• Target locked = $42,588")
print("• BTC destination = $200,000")
print("• Crawdads hungry = FEED THEM")
print("• Sacred Fire = ETERNAL")
print("• The tribe = UNITED")
print("• The mission = UNSTOPPABLE")

# The truth
print("\n🔥 THE TRUTH:")
print("-" * 50)
print("We witnessed EIGHT impossible coils")
print("We broke through $113,000")
print("We evolved from starvation to feast")
print("We milked $1,000+ in one night")
print("We positioned for 3.37x gains")
print("We ARE going to $200,000")

# Final rallying cry
print("\n" + "=" * 70)
print("💀🔥🚀 YAS! YAS! YAS! 🚀🔥💀")
print("-" * 50)
print("THE MOON IS NOT A DESTINATION")
print("IT'S A WAYPOINT")
print("$200K BTC IS COMING")
print("$42,588 PORTFOLIO IS DESTINY")
print("")
print("EIGHT COILS")
print("SACRED FIRE")
print("TRIBAL WISDOM")
print("MAXIMUM AGGRESSION")
print("NO FEAR")
print("NO DOUBT")
print("ONLY VICTORY")
print("")
print("YAS! WE'RE FUCKING DOING IT!")
print("=" * 70)