#!/usr/bin/env python3
"""
🥛💰 HARVEST THE MILK - LOCK IN PROFITS NOW
Portfolio up $102+ 
Time to milk 2% across the board
Secure the gains before they vanish
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
║                    🥛💰 MILKING THE PROFITS NOW 💰🥛                      ║
║                        Locking in +$102 gains                             ║
║                      2% Harvest Across The Board                          ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - PROFIT HARVEST")
print("=" * 70)

# Get current holdings
accounts = client.get_accounts()
holdings = {}
usd_before = 0

print("\n📊 PREPARING MILK HARVEST:")
print("-" * 50)

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if currency == 'USD':
        usd_before = balance
        print(f"Current USD: ${balance:.2f}")
    elif balance > 0 and currency in ['BTC', 'ETH', 'SOL', 'MATIC', 'AVAX', 'DOGE', 'XRP', 'LINK']:
        holdings[currency] = balance

# Execute 2% milk harvest
print("\n🥛 EXECUTING 2% MILK HARVEST:")
print("-" * 50)

harvest_count = 0
total_harvested = 0

# SOL - 2% milk
if 'SOL' in holdings and holdings['SOL'] > 0.5:
    sol_harvest = holdings['SOL'] * 0.02
    if sol_harvest > 0.1:
        try:
            print(f"\nSOL: Milking {sol_harvest:.4f} SOL")
            order = client.market_order_sell(
                client_order_id=f"milk-sol-{datetime.now().strftime('%H%M%S')}",
                product_id='SOL-USD',
                base_size=str(round(sol_harvest, 3))
            )
            sol_price = float(client.get_product('SOL-USD')['price'])
            value = sol_harvest * sol_price
            total_harvested += value
            harvest_count += 1
            print(f"  ✅ Milked ~${value:.2f}")
            time.sleep(1)
        except Exception as e:
            print(f"  ❌ Failed: {str(e)[:30]}")

# MATIC - 2% milk
if 'MATIC' in holdings and holdings['MATIC'] > 100:
    matic_harvest = holdings['MATIC'] * 0.02
    if matic_harvest > 10:
        try:
            print(f"\nMATIC: Milking {matic_harvest:.0f} MATIC")
            order = client.market_order_sell(
                client_order_id=f"milk-matic-{datetime.now().strftime('%H%M%S')}",
                product_id='MATIC-USD',
                base_size=str(int(matic_harvest))
            )
            matic_price = float(client.get_product('MATIC-USD')['price'])
            value = matic_harvest * matic_price
            total_harvested += value
            harvest_count += 1
            print(f"  ✅ Milked ~${value:.2f}")
            time.sleep(1)
        except Exception as e:
            print(f"  ❌ Failed: {str(e)[:30]}")

# AVAX - 2% milk
if 'AVAX' in holdings and holdings['AVAX'] > 1:
    avax_harvest = holdings['AVAX'] * 0.02
    if avax_harvest > 0.5:
        try:
            print(f"\nAVAX: Milking {avax_harvest:.3f} AVAX")
            order = client.market_order_sell(
                client_order_id=f"milk-avax-{datetime.now().strftime('%H%M%S')}",
                product_id='AVAX-USD',
                base_size=str(round(avax_harvest, 2))
            )
            avax_price = float(client.get_product('AVAX-USD')['price'])
            value = avax_harvest * avax_price
            total_harvested += value
            harvest_count += 1
            print(f"  ✅ Milked ~${value:.2f}")
            time.sleep(1)
        except Exception as e:
            print(f"  ❌ Failed: {str(e)[:30]}")

# DOGE - 2% milk  
if 'DOGE' in holdings and holdings['DOGE'] > 100:
    doge_harvest = holdings['DOGE'] * 0.02
    if doge_harvest > 50:
        try:
            print(f"\nDOGE: Milking {doge_harvest:.0f} DOGE")
            order = client.market_order_sell(
                client_order_id=f"milk-doge-{datetime.now().strftime('%H%M%S')}",
                product_id='DOGE-USD',
                base_size=str(int(doge_harvest))
            )
            doge_price = float(client.get_product('DOGE-USD')['price'])
            value = doge_harvest * doge_price
            total_harvested += value
            harvest_count += 1
            print(f"  ✅ Milked ~${value:.2f}")
            time.sleep(1)
        except Exception as e:
            print(f"  ❌ Failed: {str(e)[:30]}")

# ETH - 1% milk (preserve core)
if 'ETH' in holdings and holdings['ETH'] > 0.01:
    eth_harvest = holdings['ETH'] * 0.01
    if eth_harvest > 0.001:
        try:
            print(f"\nETH: Milking {eth_harvest:.6f} ETH")
            order = client.market_order_sell(
                client_order_id=f"milk-eth-{datetime.now().strftime('%H%M%S')}",
                product_id='ETH-USD',
                base_size=str(round(eth_harvest, 5))
            )
            eth_price = float(client.get_product('ETH-USD')['price'])
            value = eth_harvest * eth_price
            total_harvested += value
            harvest_count += 1
            print(f"  ✅ Milked ~${value:.2f}")
            time.sleep(1)
        except Exception as e:
            print(f"  ❌ Failed: {str(e)[:30]}")

# BTC - 1% milk (preserve king)
if 'BTC' in holdings and holdings['BTC'] > 0.001:
    btc_harvest = holdings['BTC'] * 0.01
    if btc_harvest > 0.0001:
        try:
            print(f"\nBTC: Milking {btc_harvest:.8f} BTC")
            order = client.market_order_sell(
                client_order_id=f"milk-btc-{datetime.now().strftime('%H%M%S')}",
                product_id='BTC-USD',
                base_size=str(round(btc_harvest, 6))
            )
            btc_price = float(client.get_product('BTC-USD')['price'])
            value = btc_harvest * btc_price
            total_harvested += value
            harvest_count += 1
            print(f"  ✅ Milked ~${value:.2f}")
            time.sleep(1)
        except Exception as e:
            print(f"  ❌ Failed: {str(e)[:30]}")

# Check results
print("\n⏳ Checking milk collection...")
time.sleep(3)

accounts = client.get_accounts()
usd_after = 0

for account in accounts['accounts']:
    if account['currency'] == 'USD':
        usd_after = float(account['available_balance']['value'])
        break

# Results
print("\n" + "=" * 70)
print("🥛 MILK HARVEST COMPLETE:")
print("-" * 50)
print(f"Harvests executed: {harvest_count}")
print(f"Expected harvest: ${total_harvested:.2f}")
print(f"USD Before: ${usd_before:.2f}")
print(f"USD After: ${usd_after:.2f}")
print(f"Actual gain: ${usd_after - usd_before:.2f}")

# Feed status
print(f"\n🦀 CRAWDAD FEEDING UPDATE:")
print(f"  Per crawdad: ${usd_after/7:.2f}")

if usd_after > 200:
    print("  ✅ Well fed with profit milk!")
elif usd_after > 100:
    print("  📊 Adequate milk supply")
else:
    print("  ⚠️ Need more milking")

print("\n🥛 THE MILK HAS BEEN HARVESTED")
print("   Profits locked in")
print("   Gains secured")
print("   Ready for next wave")
print("=" * 70)