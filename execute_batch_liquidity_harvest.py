#!/usr/bin/env python3
"""
💰🦀 BATCH LIQUIDITY HARVEST - FEE EFFICIENT EXECUTION
======================================================
Harvest multiple positions in one batch to minimize fees
Target: Generate $750+ liquidity for weekend operations
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
║                  💰 BATCH LIQUIDITY HARVEST EXECUTION 💰                   ║
║                     Fee-Efficient Multi-Asset Milking                      ║
║                      Target: $750 USD for Weekend War                      ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"⏰ Execution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

# Current situation
print("\n📊 CURRENT LIQUIDITY CRISIS:")
print(f"  USD Balance: $6.15 (CRITICALLY LOW!)")
print(f"  Need: $750+ for weekend operations")
print(f"  Solution: Batch harvest profitable positions")

# Batch trades to execute
batch_trades = [
    {
        'asset': 'SOL',
        'amount': 1.3394,  # 10% of position
        'expected': 286.19,
        'reason': 'At resistance, good milk point'
    },
    {
        'asset': 'MATIC', 
        'amount': 1360.32,  # 15% of position
        'expected': 340.49,
        'reason': 'Low volatility weekend ahead'
    },
    {
        'asset': 'DOGE',
        'amount': 576.98,  # 20% of position
        'expected': 127.21,
        'reason': 'Meme volatility, take profits'
    }
]

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
    print(f"  Amount: {trade['amount']:.4f}")
    print(f"  Expected: ${trade['expected']:.2f}")
    print(f"  Fee: ${fee:.2f}")
    print(f"  Net: ${net:.2f}")
    print(f"  Reason: {trade['reason']}")

print("\n" + "=" * 70)
print(f"TOTAL HARVEST: ${total_expected:.2f}")
print(f"TOTAL FEES: ${total_fees:.2f}")
print(f"EFFICIENCY: {(1 - total_fees/sum(t['expected'] for t in batch_trades))*100:.1f}%")

print("\n⚡ EXECUTING BATCH TRADES...")
print("-" * 70)

executed_trades = []
total_actual = 0

for trade in batch_trades:
    try:
        print(f"\nExecuting {trade['asset']} sell...")
        
        # Format amount based on asset
        if trade['asset'] == 'MATIC':
            amount = f"{trade['amount']:.1f}"
        elif trade['asset'] == 'DOGE':
            amount = f"{trade['amount']:.1f}"
        else:
            amount = f"{trade['amount']:.4f}"
        
        # Place market sell order
        order = client.market_order_sell(
            product_id=f"{trade['asset']}-USD",
            base_size=amount
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
            'amount': amount,
            'value': filled_value,
            'order_id': order_id
        })
        
        print(f"  ✅ SOLD {amount} {trade['asset']} for ${filled_value:.2f}")
        
    except Exception as e:
        print(f"  ❌ Failed to sell {trade['asset']}: {str(e)}")

print("\n" + "=" * 70)
print("📊 BATCH EXECUTION COMPLETE:")
print("-" * 70)

for trade in executed_trades:
    print(f"  {trade['asset']}: ${trade['value']:.2f}")

print(f"\nTOTAL LIQUIDITY GENERATED: ${total_actual:.2f}")

# Check new USD balance
time.sleep(3)
accounts = client.get_accounts()['accounts']
new_usd = float([a for a in accounts if a['currency']=='USD'][0]['available_balance']['value'])

print(f"\n💰 NEW USD BALANCE: ${new_usd:.2f}")
print(f"   Increase: ${new_usd - 6.15:.2f}")

print("\n🎯 WEEKEND STRATEGY WITH NEW LIQUIDITY:")
print("-" * 70)
print(f"  1. Set ETH sawtooth orders: $4,420 / $4,480")
print(f"  2. Set BTC flash wick catches: $110,500 / $109,500")
print(f"  3. Keep ${new_usd/3:.2f} for each opportunity")
print(f"  4. Compound profits through weekend")
print(f"  5. Re-enter positions Sunday night dip")

print("\n🏔️ MOUNTAIN WISDOM:")
print("  'Liquidity harvested efficiently in batch.'")
print("  'Weekend powder now loaded and ready.'")
print("  'Patient hunters eat through all seasons.'")

print("\n✅ BATCH LIQUIDITY HARVEST COMPLETE!")
print("=" * 70)