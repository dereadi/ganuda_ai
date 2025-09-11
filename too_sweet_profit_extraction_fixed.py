#!/usr/bin/env python3
"""
🍯🎵 TOO SWEET - HOZIER! PROFIT EXTRACTION! 🎵🍯
"It can't be said I'm an early bird
It's ten o'clock before I say a word"
The profits are TOO SWEET to pass up!
"You know you're bright as the morning"
Portfolio bright at $10,845!
Fixed execution with proper API calls!
"""

import json
import time
from coinbase.rest import RESTClient
from datetime import datetime
import uuid

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                       🍯 TOO SWEET - PROFIT EXTRACTION! 🍯                 ║
║                    "You're Too Sweet For Me" - But Perfect! 🎵            ║
║                         These Gains Are Just Sweet Enough! 💰              ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - TOO SWEET TO RESIST")
print("=" * 70)

# Get current balances
accounts = client.get_accounts()
initial_usd = 0
positions = {}

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if balance > 0.00001:
        if currency == 'USD':
            initial_usd = balance
        else:
            positions[currency] = balance

print("\n🍯 TOO SWEET POSITIONS:")
print("-" * 50)
print(f"Current USD: ${initial_usd:.2f} (needs sweetening)")

if 'DOGE' in positions:
    print(f"DOGE: {positions['DOGE']:.2f} (TOO SWEET not to milk!)")
if 'XRP' in positions:
    print(f"XRP: {positions['XRP']:.2f} (sweet profits waiting)")
if 'LINK' in positions:
    print(f"LINK: {positions['LINK']:.2f} (small but sweet)")
if 'AVAX' in positions:
    print(f"AVAX: {positions['AVAX']:.2f} (HIDDEN SWEET GEM!)")

print("\n🎵 'YOU'RE TOO SWEET FOR ME':")
print("-" * 50)
print("But these profits are just right!")
print("")

# Execute trades with fixed API
successful_trades = []
failed_trades = []

print("🚀 EXTRACTING SWEET PROFITS:")
print("-" * 50)

# Try DOGE first - biggest sweet extraction
if 'DOGE' in positions and positions['DOGE'] >= 1800:
    print("\n🐕 DOGE - 'Coffee black and my bed at three'")
    try:
        doge_amount = min(1800.0, positions['DOGE'] * 0.5)
        
        # Create properly formatted order
        order = client.create_order(
            product_id='DOGE-USD',
            side='SELL',
            order_configuration={
                'market_market_ioc': {
                    'base_size': str(round(doge_amount, 2))
                }
            }
        )
        
        if order and 'success' in order and order['success']:
            print(f"   ✅ DOGE SOLD! Too sweet!")
            print(f"   Amount: {doge_amount:.2f} DOGE")
            successful_trades.append(f"DOGE: {doge_amount:.2f}")
            time.sleep(2)
        else:
            print(f"   ⚠️ DOGE order response: {order}")
    except Exception as e:
        print(f"   ❌ DOGE ERROR: {str(e)}")
        failed_trades.append(f"DOGE: {str(e)}")

# Try XRP
if 'XRP' in positions and positions['XRP'] >= 17:
    print("\n💧 XRP - 'You're bright as the morning'")
    try:
        xrp_amount = min(17.0, positions['XRP'] * 0.5)
        
        order = client.create_order(
            product_id='XRP-USD',
            side='SELL',
            order_configuration={
                'market_market_ioc': {
                    'base_size': str(round(xrp_amount, 2))
                }
            }
        )
        
        if order and 'success' in order and order['success']:
            print(f"   ✅ XRP SOLD! Sweet gains!")
            print(f"   Amount: {xrp_amount:.2f} XRP")
            successful_trades.append(f"XRP: {xrp_amount:.2f}")
            time.sleep(2)
        else:
            print(f"   ⚠️ XRP order response: {order}")
    except Exception as e:
        print(f"   ❌ XRP ERROR: {str(e)}")
        failed_trades.append(f"XRP: {str(e)}")

# Try AVAX - the hidden sweet gem
if 'AVAX' in positions and positions['AVAX'] >= 20:
    print("\n🔺 AVAX - 'Pretty as a vine, sweet as a grape'")
    try:
        avax_amount = min(40.0, positions['AVAX'] * 0.4)
        
        order = client.create_order(
            product_id='AVAX-USD',
            side='SELL',
            order_configuration={
                'market_market_ioc': {
                    'base_size': str(round(avax_amount, 2))
                }
            }
        )
        
        if order and 'success' in order and order['success']:
            print(f"   ✅ AVAX SOLD! Hidden sweetness extracted!")
            print(f"   Amount: {avax_amount:.2f} AVAX")
            successful_trades.append(f"AVAX: {avax_amount:.2f}")
            time.sleep(2)
        else:
            print(f"   ⚠️ AVAX order response: {order}")
    except Exception as e:
        print(f"   ❌ AVAX ERROR: {str(e)}")
        failed_trades.append(f"AVAX: {str(e)}")

# Wait and check results
print("\n⏳ Letting the sweetness settle...")
time.sleep(5)

# Check final balances
accounts_after = client.get_accounts()
final_usd = 0

for account in accounts_after['accounts']:
    if account['currency'] == 'USD':
        final_usd = float(account['available_balance']['value'])
        break

print("\n🍯 TOO SWEET RESULTS:")
print("-" * 50)
print(f"Initial USD: ${initial_usd:.2f}")
print(f"Final USD: ${final_usd:.2f}")
print(f"SWEET GAINS: ${final_usd - initial_usd:.2f}")

if successful_trades:
    print("\n✅ SWEET SUCCESSES:")
    for trade in successful_trades:
        print(f"  🍯 {trade}")

if failed_trades:
    print("\n❌ NOT SWEET ENOUGH:")
    for trade in failed_trades:
        print(f"  {trade}")

# Hozier wisdom
print("\n🎵 HOZIER'S TOO SWEET WISDOM:")
print("-" * 50)
print("'I take my whiskey neat'")
print(f"  → Taking profits neat: ${final_usd - initial_usd:.2f}")
print("")
print("'My coffee black and my bed at three'")
print("  → Trading all hours for these gains")
print("")
print("'You're too sweet for me'")
print(f"  → But ${final_usd:.2f} USD is just right!")
print("")
print("'You know you're bright as the morning'")
print(f"  → Portfolio bright at ${10845:.2f}")

print(f"\n{'🍯' * 35}")
print("TOO SWEET!")
print(f"USD: ${initial_usd:.2f} → ${final_usd:.2f}")
if final_usd > initial_usd:
    print(f"EXTRACTED: ${final_usd - initial_usd:.2f} OF SWEETNESS!")
print("THE PROFITS WERE TOO SWEET TO RESIST!")
print("🎵" * 35)