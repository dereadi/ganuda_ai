#!/usr/bin/env python3
"""
🔥 EXECUTE COUNCIL LADDER - FIRST TRANCHE
==========================================
Seven hands, seven levels
First hand deploys now
"""

import json
import uuid
from datetime import datetime
from coinbase.rest import RESTClient

config = json.load(open('/home/dereadi/.coinbase_config.json'))
client = RESTClient(api_key=config['api_key'].split('/')[-1], api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                   🔥 COUNCIL EXECUTION - TRANCHE 1 🔥                      ║
║                         First Hand Catches First Knife                     ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"⏰ {datetime.now().strftime('%H:%M:%S')} - EXECUTING COUNCIL ORDERS")
print("=" * 70)

# First, generate liquidity via milking
accounts = client.get_accounts()['accounts']
usd_before = float([a for a in accounts if a['currency']=='USD'][0]['available_balance']['value'])
sol_bal = float([a for a in accounts if a['currency']=='SOL'][0]['available_balance']['value'])
matic_bal = float([a for a in accounts if a['currency']=='MATIC'][0]['available_balance']['value'])
avax_bal = float([a for a in accounts if a['currency']=='AVAX'][0]['available_balance']['value'])

print(f"\n💵 CURRENT LIQUIDITY: ${usd_before:.2f}")
print("\n🥛 STEP 1: GENERATE LIQUIDITY (MILK POSITIONS)")
print("-" * 50)

trades_executed = []
total_generated = 0

# Milk SOL - 10%
sol_amount = round(sol_bal * 0.1, 4)
if sol_amount > 0.1:
    print(f"\n  Milking SOL: {sol_amount} SOL")
    try:
        order_id = str(uuid.uuid4())
        response = client.market_order_sell(
            client_order_id=order_id,
            product_id='SOL-USD',
            base_size=str(sol_amount)
        )
        sol_price = float(client.get_product('SOL-USD')['price'])
        value = sol_amount * sol_price
        total_generated += value
        trades_executed.append(f"Sold {sol_amount} SOL for ~${value:.2f}")
        print(f"  ✅ Success! Generated ~${value:.2f}")
    except Exception as e:
        print(f"  ⚠️ Error: {str(e)[:100]}")

# Milk MATIC - 15%
matic_amount = int(matic_bal * 0.15)
if matic_amount > 100:
    print(f"\n  Milking MATIC: {matic_amount} MATIC")
    try:
        order_id = str(uuid.uuid4())
        response = client.market_order_sell(
            client_order_id=order_id,
            product_id='MATIC-USD',
            base_size=str(matic_amount)
        )
        matic_price = float(client.get_product('MATIC-USD')['price'])
        value = matic_amount * matic_price
        total_generated += value
        trades_executed.append(f"Sold {matic_amount} MATIC for ~${value:.2f}")
        print(f"  ✅ Success! Generated ~${value:.2f}")
    except Exception as e:
        print(f"  ⚠️ Error: {str(e)[:100]}")

# Milk AVAX - 10%
avax_amount = round(avax_bal * 0.1, 4)
if avax_amount > 0.5:
    print(f"\n  Milking AVAX: {avax_amount} AVAX")
    try:
        order_id = str(uuid.uuid4())
        response = client.market_order_sell(
            client_order_id=order_id,
            product_id='AVAX-USD',
            base_size=str(avax_amount)
        )
        avax_price = float(client.get_product('AVAX-USD')['price'])
        value = avax_amount * avax_price
        total_generated += value
        trades_executed.append(f"Sold {avax_amount} AVAX for ~${value:.2f}")
        print(f"  ✅ Success! Generated ~${value:.2f}")
    except Exception as e:
        print(f"  ⚠️ Error: {str(e)[:100]}")

print(f"\n  TOTAL LIQUIDITY GENERATED: ${total_generated:.2f}")

# Wait for orders to settle
import time
print("\n⏳ Waiting for liquidity to settle...")
time.sleep(5)

# Check new USD balance
accounts = client.get_accounts()['accounts']
usd_after = float([a for a in accounts if a['currency']=='USD'][0]['available_balance']['value'])
actual_generated = usd_after - usd_before

print(f"\n💰 LIQUIDITY UPDATE:")
print(f"  Before: ${usd_before:.2f}")
print(f"  After: ${usd_after:.2f}")
print(f"  Generated: ${actual_generated:.2f}")

print("\n" + "="*70)
print("🎯 STEP 2: DEPLOY FIRST TRANCHE (15% of $850 = $127.50)")
print("="*70)

# Get current prices
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

print(f"\n📊 CURRENT PRICES:")
print(f"  BTC: ${btc:,.0f}")
print(f"  ETH: ${eth:,.0f}")
print(f"  SOL: ${sol:.2f}")

# Calculate deployment (using actual available USD)
available = min(usd_after, 127.50)  # Use up to first tranche amount
btc_allocation = available * 0.5
eth_allocation = available * 0.3
sol_allocation = available * 0.2

print(f"\n💎 DEPLOYING ${available:.2f}:")
print(f"  • ${btc_allocation:.2f} → BTC")
print(f"  • ${eth_allocation:.2f} → ETH")
print(f"  • ${sol_allocation:.2f} → SOL")

# Execute buys
print("\n⚡ EXECUTING BUYS:")
print("-" * 50)

if btc_allocation > 10:
    btc_amount = btc_allocation / btc
    print(f"\n  Buying {btc_amount:.8f} BTC")
    try:
        order_id = str(uuid.uuid4())
        response = client.market_order_buy(
            client_order_id=order_id,
            product_id='BTC-USD',
            quote_size=str(round(btc_allocation, 2))
        )
        trades_executed.append(f"Bought ~{btc_amount:.8f} BTC for ${btc_allocation:.2f}")
        print(f"  ✅ Success!")
    except Exception as e:
        print(f"  ⚠️ Error: {str(e)[:100]}")

if eth_allocation > 10:
    eth_amount = eth_allocation / eth
    print(f"\n  Buying {eth_amount:.6f} ETH")
    try:
        order_id = str(uuid.uuid4())
        response = client.market_order_buy(
            client_order_id=order_id,
            product_id='ETH-USD',
            quote_size=str(round(eth_allocation, 2))
        )
        trades_executed.append(f"Bought ~{eth_amount:.6f} ETH for ${eth_allocation:.2f}")
        print(f"  ✅ Success!")
    except Exception as e:
        print(f"  ⚠️ Error: {str(e)[:100]}")

if sol_allocation > 10:
    sol_amount = sol_allocation / sol
    print(f"\n  Buying {sol_amount:.4f} SOL")
    try:
        order_id = str(uuid.uuid4())
        response = client.market_order_buy(
            client_order_id=order_id,
            product_id='SOL-USD',
            quote_size=str(round(sol_allocation, 2))
        )
        trades_executed.append(f"Bought ~{sol_amount:.4f} SOL for ${sol_allocation:.2f}")
        print(f"  ✅ Success!")
    except Exception as e:
        print(f"  ⚠️ Error: {str(e)[:100]}")

print("\n" + "="*70)
print("📜 EXECUTION SUMMARY:")
print("="*70)

if trades_executed:
    print("\n✅ TRADES EXECUTED:")
    for trade in trades_executed:
        print(f"  • {trade}")
else:
    print("\n⚠️ No trades executed")

print("\n🔥 REMAINING TRANCHES (6 of 7):")
print("-" * 50)
print("  Level 1: $127.50 at -1% (BTC $108,698)")
print("  Level 2: $127.50 at -2% (BTC $107,600)")
print("  Level 3: $127.50 at -3% (BTC $106,502)")
print("  Level 4: $85.00 at -5% (BTC $104,306)")
print("  Monday: $170.00 for capitulation")
print("  Emergency: $85.00 kept dry")

print("\n🎯 NEXT ACTIONS:")
print("-" * 50)
print("  1. Set alerts at each level")
print("  2. Don't chase - let prices come to us")
print("  3. Keep 50% for Monday/Tuesday")
print("  4. Trust the Council's wisdom")

print("\n🔥 First hand deployed. Six hands remain.")
print("   'Seven hands make light work'")
print("=" * 70)