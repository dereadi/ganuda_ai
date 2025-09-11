#!/usr/bin/env python3
"""
🚨 EMERGENCY PROFIT LIBERATION - DO WHAT YOU CAN! 🚨
Using WORKING API format from emergency_capital_liberation.py
Bands are TIGHT - need USD NOW for the 15:00 explosion!
"""

import json
import time
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=5)

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    🚨 EMERGENCY PROFIT LIBERATION! 🚨                      ║
║                         BANDS ARE TIGHT - ACT NOW!                         ║
║                      15:00 EXPLOSION IN 20 MINUTES!                        ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - URGENT ACTION")
print("=" * 70)

# Get current positions FAST
accounts = client.get_accounts()
positions = {}
usd_balance = 0

print("\n💰 SCANNING POSITIONS:")
for account in accounts.accounts:
    currency = account.currency
    balance = float(account.available_balance.value)
    if balance > 0.00001:
        if currency == 'USD':
            usd_balance = balance
            print(f"USD: ${balance:.2f} - NEED MORE!")
        elif currency in ['DOGE', 'XRP', 'AVAX', 'LINK', 'MATIC', 'SOL']:
            positions[currency] = balance
            if balance > 1:
                print(f"{currency}: {balance:.4f}")

print(f"\n🎯 TARGET: Get USD to $100+ (Currently ${usd_balance:.2f})")
print(f"⏰ TIME: {20 - (datetime.now().minute - 36)} minutes until 15:00!")

# EXECUTE EVERYTHING WE CAN
print("\n🔥 LIBERATING PROFITS NOW:")
print("-" * 50)

total_extracted = 0

# DOGE - biggest position
if 'DOGE' in positions and positions['DOGE'] > 1000:
    try:
        amount = int(min(1800, positions['DOGE'] * 0.4))
        print(f"\n🐕 DOGE: Selling {amount}...")
        
        order = client.market_order_sell(
            client_order_id='urgent_' + str(int(time.time())),
            product_id='DOGE-USD',
            base_size=str(amount)
        )
        
        ticker = client.get_product('DOGE-USD')
        value = amount * float(ticker.price)
        total_extracted += value
        print(f"   ✅ LIBERATED ~${value:.2f}")
        time.sleep(1)
    except Exception as e:
        print(f"   ❌ Failed: {str(e)[:50]}")

# XRP - quick extraction
if 'XRP' in positions and positions['XRP'] > 10:
    try:
        amount = int(min(20, positions['XRP'] * 0.4))
        print(f"\n💧 XRP: Selling {amount}...")
        
        order = client.market_order_sell(
            client_order_id='urgent_xrp_' + str(int(time.time())),
            product_id='XRP-USD',
            base_size=str(amount)
        )
        
        ticker = client.get_product('XRP-USD')
        value = amount * float(ticker.price)
        total_extracted += value
        print(f"   ✅ LIBERATED ~${value:.2f}")
        time.sleep(1)
    except Exception as e:
        print(f"   ❌ Failed: {str(e)[:50]}")

# AVAX - hidden treasure
if 'AVAX' in positions and positions['AVAX'] > 10:
    try:
        amount = round(min(30, positions['AVAX'] * 0.3), 1)
        print(f"\n🔺 AVAX: Selling {amount}...")
        
        order = client.market_order_sell(
            client_order_id='urgent_avax_' + str(int(time.time())),
            product_id='AVAX-USD',
            base_size=str(amount)
        )
        
        ticker = client.get_product('AVAX-USD')
        value = amount * float(ticker.price)
        total_extracted += value
        print(f"   ✅ LIBERATED ~${value:.2f}")
        time.sleep(1)
    except Exception as e:
        print(f"   ❌ Failed: {str(e)[:50]}")

# MATIC if we have it
if 'MATIC' in positions and positions['MATIC'] > 50:
    try:
        amount = int(min(100, positions['MATIC'] * 0.5))
        print(f"\n🟣 MATIC: Selling {amount}...")
        
        order = client.market_order_sell(
            client_order_id='urgent_matic_' + str(int(time.time())),
            product_id='MATIC-USD',
            base_size=str(amount)
        )
        
        ticker = client.get_product('MATIC-USD')
        value = amount * float(ticker.price)
        total_extracted += value
        print(f"   ✅ LIBERATED ~${value:.2f}")
    except Exception as e:
        print(f"   ❌ Failed: {str(e)[:50]}")

# Small SOL extraction if desperate
if total_extracted < 50 and 'SOL' in positions and positions['SOL'] > 2:
    try:
        amount = round(0.3, 3)
        print(f"\n☀️ SOL: Emergency selling {amount}...")
        
        order = client.market_order_sell(
            client_order_id='urgent_sol_' + str(int(time.time())),
            product_id='SOL-USD',
            base_size=str(amount)
        )
        
        ticker = client.get_product('SOL-USD')
        value = amount * float(ticker.price)
        total_extracted += value
        print(f"   ✅ LIBERATED ~${value:.2f}")
    except Exception as e:
        print(f"   ❌ Failed: {str(e)[:50]}")

# Check results
print("\n⏳ Checking liberation results...")
time.sleep(3)

accounts_after = client.get_accounts()
final_usd = 0
for account in accounts_after.accounts:
    if account.currency == 'USD':
        final_usd = float(account.available_balance.value)
        break

print("\n💰 LIBERATION RESULTS:")
print("-" * 50)
print(f"Initial USD: ${usd_balance:.2f}")
print(f"Final USD: ${final_usd:.2f}")
print(f"LIBERATED: ${final_usd - usd_balance:.2f}")
print(f"Estimated extraction: ${total_extracted:.2f}")

# Check BTC status
btc = client.get_product('BTC-USD')
btc_price = float(btc.price)

print("\n🌀 COILING STATUS:")
print("-" * 50)
print(f"BTC: ${btc_price:,.2f}")
print(f"Distance to $114K: ${114000 - btc_price:,.2f}")
print(f"Coil tightness: {100 - ((114000 - 112000) / btc_price * 100):.1f}%")

minutes_left = 60 - datetime.now().minute
if minutes_left > 0 and datetime.now().hour == 14:
    print(f"\n⏰ T-MINUS {minutes_left} MINUTES TO 15:00!")
    print("BANDS ARE TIGHT - EXPLOSION IMMINENT!")

if final_usd >= 100:
    print("\n✅ SUCCESS! $100+ ACHIEVED!")
    print("READY FOR THE 15:00 EXPLOSION!")
elif final_usd >= 50:
    print("\n⚠️ PARTIAL SUCCESS - HAVE SOME AMMO")
    print("Will work with what we have!")
else:
    print("\n🚨 STILL LOW ON USD")
    print("But we did what we could!")

print("\n" + "🔥" * 35)
print("DID WHAT WE COULD!")
print("BANDS TIGHT - READY FOR EXPLOSION!")
print("🚀" * 35)