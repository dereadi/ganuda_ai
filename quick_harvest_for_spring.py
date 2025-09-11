#!/usr/bin/env python3
"""
💰 QUICK HARVEST TO SPRING ETH
Extract from winners to create momentum
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
║                   💰 HARVESTING TO SPRING ETH! 💰                         ║
║                 Extract → Deploy → Create Cascade!                        ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

# Get prices
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

print(f"\n📊 EXTRACTING FROM WINNERS:")
print("-" * 50)

# Small extractions from multiple positions
orders = [
    ("SOL-USD", 1.0, "SOL quick harvest"),
    ("BTC-USD", 0.001, "BTC micro harvest"),
    ("ETH-USD", 0.05, "ETH profit slice")
]

total_generated = 0
for product, amount, desc in orders:
    try:
        print(f"\n📤 {desc}: {amount}")
        order = client.market_order_sell(
            client_order_id=f"harvest_{int(time.time()*1000)}",
            product_id=product,
            base_size=str(amount)
        )
        value = amount * (sol if 'SOL' in product else btc if 'BTC' in product else eth)
        total_generated += value
        print(f"   ✅ ~${value:.2f} generated")
        time.sleep(1)
    except Exception as e:
        print(f"   ⚠️ {str(e)[:50]}")

print(f"\n💰 TOTAL GENERATED: ~${total_generated:.2f}")

# Now spring ETH with the fresh capital
time.sleep(2)
accounts = client.get_accounts()['accounts']
for acc in accounts:
    if acc['currency'] == 'USD':
        usd_now = float(acc['available_balance']['value'])
        break

print(f"\n🚀 SPRINGING ETH WITH ${usd_now:.2f}!")
print("-" * 50)

if usd_now > 100:
    # Deploy in aggressive waves
    waves = [
        ("ETH-USD", usd_now * 0.4, "Wave 1 - Initial push"),
        ("ETH-USD", usd_now * 0.3, "Wave 2 - Momentum build"),
        ("BTC-USD", usd_now * 0.2, "Wave 3 - BTC support"),
        ("ETH-USD", usd_now * 0.1, "Wave 4 - Final spring")
    ]
    
    for product, amount, desc in waves:
        if amount > 10:
            try:
                print(f"\n💥 {desc}: ${amount:.2f} → {product.split('-')[0]}")
                order = client.market_order_buy(
                    client_order_id=f"spring_{int(time.time()*1000)}",
                    product_id=product,
                    quote_size=str(amount)
                )
                print("   ✅ Deployed!")
                
                # Check impact
                time.sleep(2)
                if 'ETH' in product:
                    new_eth = float(client.get_product('ETH-USD')['price'])
                    print(f"   ETH: ${new_eth:.2f} ({new_eth - eth:+.2f})")
                    if new_eth > 4585:
                        print("   🚀 ETH BREAKING FREE!")
                else:
                    new_btc = float(client.get_product('BTC-USD')['price'])
                    print(f"   BTC: ${new_btc:,.0f} ({new_btc - btc:+.0f})")
                    if new_btc > 113100:
                        print("   🔥 BTC CASCADE TRIGGERED!")
                
                time.sleep(2)
            except Exception as e:
                print(f"   ⚠️ {str(e)[:50]}")

print("\n" + "=" * 70)
print("🎯 ETH → BTC CASCADE STRATEGY:")
print("• Push ETH through resistance")
print("• Creates FOMO in ETH")
print("• Money rotates to BTC")
print("• Both break higher together!")
print("=" * 70)