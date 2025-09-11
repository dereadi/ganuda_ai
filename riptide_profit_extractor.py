#!/usr/bin/env python3
"""
🌊 RIPTIDE - VANCE JOY! PROFIT EXTRACTOR! 🌊
"I was scared of dentists and the dark"
But not scared of extracting profits!
Using the WORKING API signature from lunch time
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
║                       🌊 RIPTIDE PROFIT EXTRACTOR! 🌊                      ║
║                   "Lady, running down to the riptide"                       ║
║                     Pulling profits from the current! 💰                    ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - CAUGHT IN THE RIPTIDE")
print("=" * 70)

# Get current balances
accounts = client.get_accounts()
initial_usd = 0
positions = {}

for account in accounts.accounts:
    currency = account.currency
    balance = float(account.available_balance.value)
    
    if balance > 0.00001:
        if currency == 'USD':
            initial_usd = balance
        else:
            positions[currency] = balance

print("\n🌊 RIPTIDE POSITIONS:")
print("-" * 50)
print(f"Current USD: ${initial_usd:.2f} (need to reach $100+)")

if 'DOGE' in positions:
    print(f"DOGE: {positions['DOGE']:.2f} (riding the riptide)")
if 'XRP' in positions:
    print(f"XRP: {positions['XRP']:.2f} (caught in the current)")
if 'AVAX' in positions:
    print(f"AVAX: {positions['AVAX']:.2f} (HIDDEN IN THE TIDE!)")

print("\n🎵 'I LOVE YOU WHEN YOU'RE SINGING THAT SONG':")
print("-" * 50)
print("And the market's singing profit extraction!")
print("")

# Execute trades using WORKING API format from emergency_capital_liberation.py
successful_trades = []
total_extracted = 0

print("🚀 EXTRACTING FROM THE RIPTIDE:")
print("-" * 50)

# DOGE extraction - biggest current
if 'DOGE' in positions and positions['DOGE'] >= 1800:
    print("\n🐕 DOGE - 'Taken away to the dark side'")
    try:
        doge_amount = min(1800, int(positions['DOGE'] * 0.5))
        
        # Use the EXACT format from emergency_capital_liberation.py
        order = client.market_order_sell(
            client_order_id='riptide_doge_' + str(int(time.time())),
            product_id='DOGE-USD',
            base_size=str(doge_amount)
        )
        
        print(f"   ✅ DOGE EXTRACTED FROM RIPTIDE!")
        print(f"   Amount: {doge_amount} DOGE")
        
        # Estimate value
        ticker = client.get_product('DOGE-USD')
        price = float(ticker.price)
        value = doge_amount * price
        total_extracted += value
        successful_trades.append(f"DOGE: {doge_amount} (~${value:.2f})")
        time.sleep(2)
        
    except Exception as e:
        print(f"   ❌ DOGE caught in undertow: {str(e)[:100]}")

# XRP extraction
if 'XRP' in positions and positions['XRP'] >= 17:
    print("\n💧 XRP - 'I got a lump in my throat'")
    try:
        xrp_amount = min(17, int(positions['XRP'] * 0.5))
        
        order = client.market_order_sell(
            client_order_id='riptide_xrp_' + str(int(time.time())),
            product_id='XRP-USD',
            base_size=str(xrp_amount)
        )
        
        print(f"   ✅ XRP PULLED FROM THE CURRENT!")
        print(f"   Amount: {xrp_amount} XRP")
        
        ticker = client.get_product('XRP-USD')
        price = float(ticker.price)
        value = xrp_amount * price
        total_extracted += value
        successful_trades.append(f"XRP: {xrp_amount} (~${value:.2f})")
        time.sleep(2)
        
    except Exception as e:
        print(f"   ❌ XRP stuck in riptide: {str(e)[:100]}")

# AVAX extraction - the hidden treasure
if 'AVAX' in positions and positions['AVAX'] >= 20:
    print("\n🔺 AVAX - 'Oh lady, running down to the riptide'")
    try:
        avax_amount = round(min(40.0, positions['AVAX'] * 0.4), 2)
        
        order = client.market_order_sell(
            client_order_id='riptide_avax_' + str(int(time.time())),
            product_id='AVAX-USD',
            base_size=str(avax_amount)
        )
        
        print(f"   ✅ AVAX TREASURE RECOVERED!")
        print(f"   Amount: {avax_amount:.2f} AVAX")
        
        ticker = client.get_product('AVAX-USD')
        price = float(ticker.price)
        value = avax_amount * price
        total_extracted += value
        successful_trades.append(f"AVAX: {avax_amount:.2f} (~${value:.2f})")
        time.sleep(2)
        
    except Exception as e:
        print(f"   ❌ AVAX lost in riptide: {str(e)[:100]}")

# Try SOL if we need more
if total_extracted < 85 and 'SOL' in positions and positions['SOL'] >= 5:
    print("\n☀️ SOL - 'I was scared of pretty girls'")
    try:
        sol_amount = round(min(0.5, positions['SOL'] * 0.1), 3)
        
        order = client.market_order_sell(
            client_order_id='riptide_sol_' + str(int(time.time())),
            product_id='SOL-USD',
            base_size=str(sol_amount)
        )
        
        print(f"   ✅ SOL SURFACED FROM DEPTHS!")
        print(f"   Amount: {sol_amount:.3f} SOL")
        
        ticker = client.get_product('SOL-USD')
        price = float(ticker.price)
        value = sol_amount * price
        total_extracted += value
        successful_trades.append(f"SOL: {sol_amount:.3f} (~${value:.2f})")
        
    except Exception as e:
        print(f"   ❌ SOL swept away: {str(e)[:100]}")

# Wait and check results
print("\n⏳ Letting the riptide settle...")
time.sleep(5)

# Check final balances
accounts_after = client.get_accounts()
final_usd = 0

for account in accounts_after.accounts:
    if account.currency == 'USD':
        final_usd = float(account.available_balance.value)
        break

print("\n🌊 RIPTIDE RESULTS:")
print("-" * 50)
print(f"Initial USD: ${initial_usd:.2f}")
print(f"Final USD: ${final_usd:.2f}")
print(f"EXTRACTED: ${final_usd - initial_usd:.2f}")
print(f"Estimated Total: ${total_extracted:.2f}")

if successful_trades:
    print("\n✅ SUCCESSFUL EXTRACTIONS:")
    for trade in successful_trades:
        print(f"  🌊 {trade}")

# Vance Joy wisdom
print("\n🎵 VANCE JOY'S RIPTIDE WISDOM:")
print("-" * 50)
print("'I love you when you're singing that song'")
print(f"  → The market sang and gave us ${final_usd - initial_usd:.2f}")
print("")
print("'Lady, running down to the riptide'")
print(f"  → Running our USD up to ${final_usd:.2f}")
print("")
print("'Taken away to the dark side'")
print("  → Taking profits from the alt side")
print("")
print("'I wanna be your left hand man'")
print(f"  → Now we have ${final_usd:.2f} to support BTC!")

print(f"\n{'🌊' * 35}")
print("CAUGHT THE RIPTIDE!")
print(f"USD: ${initial_usd:.2f} → ${final_usd:.2f}")
if final_usd > 100:
    print("🎯 TARGET ACHIEVED! $100+ USD FOR FLYWHEEL!")
elif final_usd > initial_usd:
    print(f"PROGRESS: +${final_usd - initial_usd:.2f}")
print("THE RIPTIDE DELIVERED!")
print("🎵" * 35)

# Save state
state = {
    'timestamp': datetime.now().isoformat(),
    'initial_usd': initial_usd,
    'final_usd': final_usd,
    'extracted': final_usd - initial_usd,
    'successful_trades': successful_trades,
    'song': 'Riptide - Vance Joy'
}

with open('riptide_extraction_state.json', 'w') as f:
    json.dump(state, f, indent=2)