#!/usr/bin/env python3
"""
💰 DEPLOY $250 INTO SAWTOOTH OPPORTUNITIES
===========================================
Fresh capital deployed at perfect levels
Let's work these sawteeth!
"""

import json
import uuid
import time
from datetime import datetime
from coinbase.rest import RESTClient

config = json.load(open('/home/dereadi/.coinbase_config.json'))
client = RESTClient(api_key=config['api_key'].split('/')[-1], api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    💰 $250 DEPLOYMENT EXECUTION 💰                         ║
║                      Working The Post-Selloff Sawteeth                     ║
║                         Time To Print Money!                               ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"⏰ {datetime.now().strftime('%H:%M:%S')} - DEPLOYING FRESH CAPITAL")
print("=" * 70)

# Check current USD balance (should be ~$268 with injection)
time.sleep(2)  # Avoid rate limit
accounts = client.get_accounts()['accounts']
usd_balance = float([a for a in accounts if a['currency']=='USD'][0]['available_balance']['value'])

print(f"\n💵 CAPITAL STATUS:")
print(f"  Available USD: ${usd_balance:.2f}")
if usd_balance > 250:
    print(f"  ✅ $250 INJECTION CONFIRMED!")
else:
    print(f"  ⏳ Injection may still be processing...")

# Get current prices with rate limit protection
print("\n📊 CHECKING SAWTOOTH POSITIONS:")
print("-" * 70)

time.sleep(2)
btc = float(client.get_product('BTC-USD')['price'])
print(f"  BTC: ${btc:,.0f}")

time.sleep(1)
eth = float(client.get_product('ETH-USD')['price'])
print(f"  ETH: ${eth:,.0f}")

time.sleep(1)
sol = float(client.get_product('SOL-USD')['price'])
print(f"  SOL: ${sol:.2f}")

time.sleep(1)
avax = float(client.get_product('AVAX-USD')['price'])
print(f"  AVAX: ${avax:.2f}")

time.sleep(1)
matic = float(client.get_product('MATIC-USD')['price'])
print(f"  MATIC: ${matic:.4f}")

# Deployment strategy based on positions
print("\n🎯 STRATEGIC DEPLOYMENT:")
print("=" * 70)

# Allocate the $250 (or available amount)
deploy_amount = min(usd_balance, 250)
allocations = {
    'BTC': 0.30,   # 30% to BTC
    'ETH': 0.25,   # 25% to ETH
    'SOL': 0.20,   # 20% to SOL
    'AVAX': 0.15,  # 15% to AVAX
    'MATIC': 0.10  # 10% to MATIC
}

print(f"\n💎 DEPLOYING ${deploy_amount:.2f} AS FOLLOWS:")
print("-" * 50)

deployment_plan = []
for asset, pct in allocations.items():
    amount = deploy_amount * pct
    deployment_plan.append((asset, amount))
    print(f"  {asset}: ${amount:.2f} ({pct*100:.0f}%)")

print("\n⚡ EXECUTING DEPLOYMENT:")
print("-" * 50)

trades_executed = []

# Deploy into BTC
if deploy_amount >= 50:
    btc_amount = deploy_amount * allocations['BTC']
    print(f"\n  Deploying ${btc_amount:.2f} into BTC...")
    try:
        order_id = str(uuid.uuid4())
        response = client.market_order_buy(
            client_order_id=order_id,
            product_id='BTC-USD',
            quote_size=str(round(btc_amount, 2))
        )
        trades_executed.append(f"BTC: ${btc_amount:.2f}")
        print(f"  ✅ Success!")
    except Exception as e:
        print(f"  ⚠️ Error: {str(e)[:50]}")
    time.sleep(2)

# Deploy into ETH
if deploy_amount >= 50:
    eth_amount = deploy_amount * allocations['ETH']
    print(f"\n  Deploying ${eth_amount:.2f} into ETH...")
    try:
        order_id = str(uuid.uuid4())
        response = client.market_order_buy(
            client_order_id=order_id,
            product_id='ETH-USD',
            quote_size=str(round(eth_amount, 2))
        )
        trades_executed.append(f"ETH: ${eth_amount:.2f}")
        print(f"  ✅ Success!")
    except Exception as e:
        print(f"  ⚠️ Error: {str(e)[:50]}")
    time.sleep(2)

# Deploy into SOL
if deploy_amount >= 50:
    sol_amount = deploy_amount * allocations['SOL']
    print(f"\n  Deploying ${sol_amount:.2f} into SOL...")
    try:
        order_id = str(uuid.uuid4())
        response = client.market_order_buy(
            client_order_id=order_id,
            product_id='SOL-USD',
            quote_size=str(round(sol_amount, 2))
        )
        trades_executed.append(f"SOL: ${sol_amount:.2f}")
        print(f"  ✅ Success!")
    except Exception as e:
        print(f"  ⚠️ Error: {str(e)[:50]}")
    time.sleep(2)

# Deploy into AVAX
if deploy_amount >= 50:
    avax_amount = deploy_amount * allocations['AVAX']
    print(f"\n  Deploying ${avax_amount:.2f} into AVAX...")
    try:
        order_id = str(uuid.uuid4())
        response = client.market_order_buy(
            client_order_id=order_id,
            product_id='AVAX-USD',
            quote_size=str(round(avax_amount, 2))
        )
        trades_executed.append(f"AVAX: ${avax_amount:.2f}")
        print(f"  ✅ Success!")
    except Exception as e:
        print(f"  ⚠️ Error: {str(e)[:50]}")
    time.sleep(2)

# Deploy into MATIC
if deploy_amount >= 50:
    matic_amount = deploy_amount * allocations['MATIC']
    print(f"\n  Deploying ${matic_amount:.2f} into MATIC...")
    try:
        order_id = str(uuid.uuid4())
        response = client.market_order_buy(
            client_order_id=order_id,
            product_id='MATIC-USD',
            quote_size=str(round(matic_amount, 2))
        )
        trades_executed.append(f"MATIC: ${matic_amount:.2f}")
        print(f"  ✅ Success!")
    except Exception as e:
        print(f"  ⚠️ Error: {str(e)[:50]}")

print("\n" + "="*70)
print("📜 DEPLOYMENT SUMMARY:")
print("="*70)

if trades_executed:
    print("\n✅ SUCCESSFULLY DEPLOYED:")
    for trade in trades_executed:
        print(f"  • {trade}")
    print(f"\n  TOTAL: ${len(trades_executed) * (deploy_amount/5):.2f}")
else:
    print("\n⚠️ Deployment pending or needs manual execution")

print("\n🦷 SAWTOOTH PROFIT TARGETS:")
print("-" * 70)
print(f"  BTC: Sell at $110,000 (+{((110000-btc)/btc*100):.1f}%)")
print(f"  ETH: Sell at $4,380 (+{((4380-eth)/eth*100):.1f}%)")
print(f"  SOL: Sell at $212 (+{((212-sol)/sol*100):.1f}%)")
print(f"  AVAX: Sell at $24.50 (+{((24.50-avax)/avax*100):.1f}%)")
print(f"  MATIC: Sell at $0.250 (+{((0.250-matic)/matic*100):.1f}%)")

print("\n🎯 WEEKEND GAME PLAN:")
print("-" * 70)
print("  1. ✅ $250 deployed at mid-range levels")
print("  2. Set sell orders at range tops")
print("  3. When sells trigger, buy back at bottoms")
print("  4. Repeat every 4-6 hours")
print("  5. Compound all profits")
print("  6. Target: Turn $250 into $350 by Monday")

print("\n🔥 FLYWHEEL STATUS: SUPERCHARGED WITH FRESH CAPITAL!")
print("=" * 70)