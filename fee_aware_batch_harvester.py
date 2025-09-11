#!/usr/bin/env python3
"""
💰 FEE-AWARE BATCH HARVESTER
Minimizes fees by batching harvests intelligently
Only harvests when profit > fees
Calculates optimal batch sizes
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
║                    💰 FEE-AWARE BATCH HARVESTER 💰                        ║
║                     Smart Harvesting with Fee Optimization                ║
║                    Batch Trades to Minimize Costs                         ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - FEE ANALYSIS")
print("=" * 70)

# Coinbase fee structure
FEE_TIERS = {
    "maker": 0.004,  # 0.4% maker fee
    "taker": 0.006,  # 0.6% taker fee
    "minimum": 0.99,  # Minimum fee per trade
}

def calculate_fee(trade_value):
    """Calculate expected fee for a trade"""
    fee = trade_value * FEE_TIERS["taker"]
    return max(fee, FEE_TIERS["minimum"])

def is_profitable_harvest(amount, price):
    """Check if harvest is profitable after fees"""
    trade_value = amount * price
    fee = calculate_fee(trade_value)
    net_value = trade_value - fee
    
    return {
        "gross": trade_value,
        "fee": fee,
        "net": net_value,
        "profitable": net_value > fee * 2  # Want at least 2x fees in profit
    }

# Check current holdings
accounts = client.get_accounts()
holdings = {}
usd_balance = 0

print("\n📊 ANALYZING HOLDINGS FOR BATCH HARVEST:")
print("-" * 50)

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if currency == 'USD':
        usd_balance = balance
    elif balance > 0 and currency in ['BTC', 'ETH', 'SOL', 'MATIC', 'AVAX', 'DOGE']:
        try:
            if currency == 'BTC':
                price = float(client.get_product('BTC-USD')['price'])
            elif currency == 'ETH':
                price = float(client.get_product('ETH-USD')['price'])
            elif currency == 'SOL':
                price = float(client.get_product('SOL-USD')['price'])
            elif currency == 'MATIC':
                price = float(client.get_product('MATIC-USD')['price'])
            elif currency == 'AVAX':
                price = float(client.get_product('AVAX-USD')['price'])
            elif currency == 'DOGE':
                price = float(client.get_product('DOGE-USD')['price'])
            else:
                continue
                
            value = balance * price
            holdings[currency] = {
                "balance": balance,
                "price": price,
                "value": value
            }
        except:
            pass

print(f"Current USD: ${usd_balance:.2f}")

# Analyze each asset for profitable harvest
batch_harvest = []
total_expected_harvest = 0
total_fees = 0

print("\n💡 FEE ANALYSIS PER ASSET:")
print("-" * 50)

for asset, data in holdings.items():
    balance = data['balance']
    price = data['price']
    value = data['value']
    
    # Different harvest percentages based on asset
    if asset == 'SOL':
        harvest_pct = 0.05  # 5%
    elif asset == 'MATIC':
        harvest_pct = 0.03  # 3%
    elif asset in ['AVAX', 'DOGE']:
        harvest_pct = 0.10  # 10%
    else:
        harvest_pct = 0.02  # 2% for BTC/ETH
    
    harvest_amount = balance * harvest_pct
    analysis = is_profitable_harvest(harvest_amount, price)
    
    print(f"\n{asset}:")
    print(f"  Holdings: {balance:.4f} = ${value:.2f}")
    print(f"  Proposed harvest: {harvest_amount:.4f} ({harvest_pct*100:.0f}%)")
    print(f"  Gross value: ${analysis['gross']:.2f}")
    print(f"  Fee: ${analysis['fee']:.2f}")
    print(f"  Net: ${analysis['net']:.2f}")
    
    if analysis['profitable']:
        print(f"  ✅ PROFITABLE - Add to batch")
        batch_harvest.append({
            "asset": asset,
            "amount": harvest_amount,
            "expected_net": analysis['net']
        })
        total_expected_harvest += analysis['net']
        total_fees += analysis['fee']
    else:
        print(f"  ❌ NOT PROFITABLE - Skip")

# Batch strategy
print("\n📦 BATCH HARVEST STRATEGY:")
print("-" * 50)

if len(batch_harvest) == 0:
    print("⚠️ No profitable harvests available")
    print("   Consider waiting for price movement")
    print("   Or increase harvest percentages")

elif usd_balance < 50:  # Emergency mode
    print("🚨 EMERGENCY BATCH HARVEST:")
    print(f"   Assets to harvest: {len(batch_harvest)}")
    print(f"   Expected harvest: ${total_expected_harvest:.2f}")
    print(f"   Total fees: ${total_fees:.2f}")
    print(f"   Net gain: ${total_expected_harvest:.2f}")
    print("\n   EXECUTING BATCH...")
    
    for item in batch_harvest:
        asset = item['asset']
        amount = item['amount']
        
        try:
            if asset == 'SOL' and amount > 0.1:
                print(f"\n   Harvesting {amount:.3f} SOL...")
                order = client.market_order_sell(
                    client_order_id=f"batch-sol-{datetime.now().strftime('%H%M%S')}",
                    product_id='SOL-USD',
                    base_size=str(round(amount, 3))
                )
                print("   ✅ Done")
                time.sleep(1)
                
            elif asset == 'MATIC' and amount > 10:
                print(f"\n   Harvesting {amount:.0f} MATIC...")
                order = client.market_order_sell(
                    client_order_id=f"batch-matic-{datetime.now().strftime('%H%M%S')}",
                    product_id='MATIC-USD',
                    base_size=str(int(amount))
                )
                print("   ✅ Done")
                time.sleep(1)
                
            elif asset == 'AVAX' and amount > 0.1:
                print(f"\n   Harvesting {amount:.2f} AVAX...")
                order = client.market_order_sell(
                    client_order_id=f"batch-avax-{datetime.now().strftime('%H%M%S')}",
                    product_id='AVAX-USD',
                    base_size=str(round(amount, 2))
                )
                print("   ✅ Done")
                time.sleep(1)
                
        except Exception as e:
            print(f"   ❌ {asset} failed: {str(e)[:30]}")

elif usd_balance < 100:  # Standard batch
    print("📦 STANDARD BATCH:")
    print(f"   USD Balance: ${usd_balance:.2f}")
    print(f"   Profitable assets: {len(batch_harvest)}")
    print(f"   Expected net: ${total_expected_harvest:.2f}")
    print(f"   Total fees: ${total_fees:.2f}")
    print("\n   Consider batching 2-3 assets together")
    
else:  # Well funded
    print("✅ SUFFICIENT FUNDS")
    print(f"   USD Balance: ${usd_balance:.2f}")
    print("   No immediate harvest needed")
    print("   Watch for volatility spikes to harvest")

# Fee optimization tips
print("\n💡 FEE OPTIMIZATION TIPS:")
print("-" * 50)
print("1. Batch multiple small trades together")
print("2. Minimum trade should be >$100 to beat fees")
print("3. Watch for price spikes to maximize harvest")
print("4. Consider maker orders (0.4%) vs taker (0.6%)")
print("5. Avoid trades under $20 (minimum fee dominates)")

# Calculate break-even trades
print("\n📊 BREAK-EVEN ANALYSIS:")
print("-" * 50)
min_profitable_trade = FEE_TIERS["minimum"] / FEE_TIERS["taker"]
print(f"Minimum profitable trade size: ${min_profitable_trade:.2f}")
print(f"At 0.6% taker fee, need >${min_profitable_trade:.2f} per trade")
print(f"Batch small assets together to exceed this threshold")

# Current crawdad feeding cost
print("\n🦀 CRAWDAD FEEDING ECONOMICS:")
print("-" * 50)
crawdad_fuel = usd_balance / 7 if usd_balance > 0 else 0
min_crawdad_trade = 20  # Minimum $20 per crawdad trade

print(f"Current fuel per crawdad: ${crawdad_fuel:.2f}")
print(f"Minimum trade per crawdad: ${min_crawdad_trade}")
print(f"Fee per $20 trade: ${calculate_fee(20):.2f}")
print(f"Net per trade: ${20 - calculate_fee(20):.2f}")

if crawdad_fuel < min_crawdad_trade:
    print("\n⚠️ Below minimum trading threshold!")
    print("   Need batch harvest to reach $140+ total")
else:
    print("\n✅ Above minimum trading threshold")
    print("   Crawdads can trade profitably")

print("\n💰 WATCH FOR FEES")
print("   Batch when possible")
print("   The tribe trades wisely")
print("=" * 70)