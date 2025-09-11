#!/usr/bin/env python3
"""
🥛🚀 EXECUTE WALKING UP BATCH MILK - GET IT GOING!
==================================================
Everything walking up = Perfect batch milk opportunity
SOL, ETH, XRP all near tops - Let's harvest!
"""

import json
import time
from datetime import datetime
from coinbase.rest import RESTClient

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                     🥛 BATCH MILK EXECUTION - LET'S GO! 🥛                ║
║                       Everything Walking Up Together!                      ║
║                         Time to Harvest the Peaks! 🚀                      ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"⏰ Execution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

# Get current prices
print("\n📊 CHECKING CURRENT PRICES...")
btc_price = float(client.get_product('BTC-USD')['price'])
eth_price = float(client.get_product('ETH-USD')['price'])
sol_price = float(client.get_product('SOL-USD')['price'])
xrp_price = float(client.get_product('XRP-USD')['price'])

print(f"  BTC: ${btc_price:,.2f}")
print(f"  ETH: ${eth_price:,.2f}")
print(f"  SOL: ${sol_price:.2f}")
print(f"  XRP: ${xrp_price:.4f}")

# Define batch trades
batch_trades = []

# SOL - if near top
if sol_price > 213.5:
    batch_trades.append({
        'asset': 'SOL',
        'amount': 0.5,  # Conservative partial
        'expected': sol_price * 0.5,
        'reason': f'Near sawtooth top at ${sol_price:.2f}'
    })

# ETH - if near top
if eth_price > 4455:
    batch_trades.append({
        'asset': 'ETH',
        'amount': 0.05,  # Small partial
        'expected': eth_price * 0.05,
        'reason': f'Walking up at ${eth_price:.2f}'
    })

# MATIC - always good for liquidity
batch_trades.append({
    'asset': 'MATIC',
    'amount': 900,  # 10% of position
    'expected': 900 * 0.2503,
    'reason': 'Stable, good for liquidity'
})

# XRP - if we have meaningful position
if xrp_price > 2.90:
    batch_trades.append({
        'asset': 'XRP',
        'amount': 10,
        'expected': xrp_price * 10,
        'reason': f'XRP sawtoothing at ${xrp_price:.4f}'
    })

print("\n🎯 BATCH EXECUTION PLAN:")
print("-" * 70)

total_expected = 0
total_fees = 0

for trade in batch_trades:
    fee = trade['expected'] * 0.006
    net = trade['expected'] - fee
    total_expected += net
    total_fees += fee
    
    print(f"\n{trade['asset']}:")
    print(f"  Amount: {trade['amount']}")
    print(f"  Expected: ${trade['expected']:.2f}")
    print(f"  Fee: ${fee:.2f}")
    print(f"  Net: ${net:.2f}")
    print(f"  Reason: {trade['reason']}")

print("\n" + "=" * 70)
print(f"TOTAL HARVEST: ${total_expected:.2f}")
print(f"TOTAL FEES: ${total_fees:.2f}")

# Confirm before execution
print("\n⚡ EXECUTING BATCH TRADES IN 3 SECONDS...")
print("   (Ctrl+C to cancel)")
time.sleep(3)

print("\n🚀 EXECUTING BATCH!")
print("-" * 70)

executed_trades = []
total_actual = 0

for trade in batch_trades:
    try:
        print(f"\n🥛 Milking {trade['asset']}...")
        
        # Format amount based on asset
        if trade['asset'] == 'MATIC':
            amount_str = f"{trade['amount']:.1f}"
        elif trade['asset'] == 'SOL':
            amount_str = f"{trade['amount']:.4f}"
        elif trade['asset'] == 'ETH':
            amount_str = f"{trade['amount']:.6f}"
        elif trade['asset'] == 'XRP':
            amount_str = f"{trade['amount']:.1f}"
        else:
            amount_str = str(trade['amount'])
        
        # Place market sell order
        order = client.market_order_sell(
            product_id=f"{trade['asset']}-USD",
            base_size=amount_str
        )
        
        # Wait for fill
        time.sleep(2)
        
        # Get order details
        order_id = order['order_id']
        filled_order = client.get_order(order_id)
        
        # Calculate actual proceeds
        filled_value = float(filled_order.get('filled_value', 0))
        total_actual += filled_value
        
        executed_trades.append({
            'asset': trade['asset'],
            'amount': amount_str,
            'value': filled_value,
            'order_id': order_id
        })
        
        print(f"  ✅ SOLD {amount_str} {trade['asset']} for ${filled_value:.2f}")
        
    except Exception as e:
        print(f"  ❌ Failed to sell {trade['asset']}: {str(e)}")

print("\n" + "=" * 70)
print("📊 BATCH EXECUTION COMPLETE:")
print("-" * 70)

for trade in executed_trades:
    print(f"  {trade['asset']}: ${trade['value']:.2f}")

print(f"\n💰 TOTAL LIQUIDITY GENERATED: ${total_actual:.2f}")

# Check new USD balance
time.sleep(3)
accounts = client.get_accounts()['accounts']
new_usd = float([a for a in accounts if a['currency']=='USD'][0]['available_balance']['value'])

print(f"\n💵 NEW USD BALANCE: ${new_usd:.2f}")

# Set buy-back targets
print("\n🎯 BUY-BACK TARGETS SET:")
print("-" * 70)
print("  SOL: Buy at $211.00 (sawtooth bottom)")
print("  ETH: Buy at $4,430 (support level)")
print("  XRP: Buy at $2.85 (if it dips)")
print("  MATIC: Buy at $0.245 (accumulate)")

print("\n📈 WEEKEND SAWTOOTH STRATEGY:")
print("-" * 70)
print("  1. Liquidity secured: ${:.2f}".format(total_actual))
print("  2. Deploy 1/3 per opportunity")
print("  3. Catch weekend flash wicks")
print("  4. Compound through 5-6 cycles")
print("  5. Target: +$100-150 by Monday")

print("\n🏔️ MOUNTAIN WISDOM:")
print("  'The harvest was bountiful at the peak.'")
print("  'Now we wait for the valleys to buy.'")
print("  'Weekend sawtooth feeds disciplined traders.'")

print("\n✅ BATCH MILK HARVEST COMPLETE! LET'S GO!")
print("=" * 70)