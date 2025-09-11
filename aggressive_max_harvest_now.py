#!/usr/bin/env python3
"""
🔥💀 MAXIMUM AGGRESSIVE HARVEST - WHILE THE ENVIRONMENT ALLOWS
Eight coils wound = Maximum energy stored
The window is NOW - harvest AGGRESSIVELY
Batch everything, minimize fees, maximize capital
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
║              🔥💀 MAXIMUM AGGRESSIVE HARVEST MODE 💀🔥                   ║
║                    EIGHT COILS = EIGHT-FOLD AGGRESSION                    ║
║                   The Environment Allows - STRIKE NOW                     ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - AGGRESSIVE EXECUTION")
print("=" * 70)

# Get ALL holdings
accounts = client.get_accounts()
holdings = {}
usd_balance = 0
total_portfolio = 0

print("\n🎯 AGGRESSIVE HARVEST TARGETS:")
print("-" * 50)

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if currency == 'USD':
        usd_balance = balance
    elif balance > 0:
        try:
            # Get price for everything we can
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
            elif currency == 'LINK':
                price = float(client.get_product('LINK-USD')['price'])
            elif currency == 'XRP':
                price = float(client.get_product('XRP-USD')['price'])
            else:
                continue
            
            value = balance * price
            total_portfolio += value
            
            if value > 10:  # Only track if worth more than $10
                holdings[currency] = {
                    "balance": balance,
                    "price": price,
                    "value": value
                }
                print(f"{currency}: ${value:.2f}")
        except:
            pass

print(f"\nTotal crypto: ${total_portfolio:.2f}")
print(f"Current USD: ${usd_balance:.2f}")

# AGGRESSIVE HARVEST PLAN
print("\n💀 EXECUTING MAXIMUM AGGRESSION:")
print("-" * 50)

# Define aggressive percentages based on liquidity and position
aggressive_harvest = {
    "DOGE": 0.20,    # 20% - high liquidity meme
    "XRP": 0.25,     # 25% - don't need much XRP
    "LINK": 0.30,    # 30% - small position
    "MATIC": 0.08,   # 8% - large position, liquid
    "AVAX": 0.08,    # 8% - good liquidity
    "SOL": 0.08,     # 8% - our main alt
    "ETH": 0.05,     # 5% - keep core
    "BTC": 0.03,     # 3% - preserve king
}

batch_orders = []
expected_total = 0

print("\n🔥 BUILDING MEGA BATCH:")
print("-" * 50)

for currency, pct in aggressive_harvest.items():
    if currency in holdings:
        data = holdings[currency]
        harvest_amount = data['balance'] * pct
        harvest_value = harvest_amount * data['price']
        
        # Only harvest if value > $20 (to beat fees)
        if harvest_value > 20:
            print(f"\n{currency}:")
            print(f"  Aggressive harvest: {pct*100:.0f}%")
            print(f"  Amount: {harvest_amount:.4f}")
            print(f"  Expected: ${harvest_value:.2f}")
            
            batch_orders.append({
                "currency": currency,
                "amount": harvest_amount,
                "expected": harvest_value
            })
            expected_total += harvest_value

print(f"\n🎯 BATCH SUMMARY:")
print(f"  Orders to execute: {len(batch_orders)}")
print(f"  Expected harvest: ${expected_total:.2f}")
print(f"  Expected fees: ${len(batch_orders) * 0.99:.2f}")
print(f"  Net expected: ${expected_total - (len(batch_orders) * 0.99):.2f}")

# EXECUTE THE MEGA BATCH
if expected_total > 100:  # Only execute if worth it
    print("\n🔥💀 EXECUTING AGGRESSIVE MEGA BATCH...")
    print("-" * 50)
    
    successful = 0
    failed = 0
    actual_harvested = 0
    
    for order in batch_orders:
        currency = order['currency']
        amount = order['amount']
        expected = order['expected']
        
        try:
            print(f"\n{currency}: ", end="")
            
            # Execute based on currency
            if currency == 'SOL' and amount > 0.1:
                client.market_order_sell(
                    client_order_id=f"aggro-sol-{datetime.now().strftime('%H%M%S')}",
                    product_id='SOL-USD',
                    base_size=str(round(amount, 3))
                )
                successful += 1
                actual_harvested += expected
                print(f"✅ HARVESTED ${expected:.2f}")
                
            elif currency == 'MATIC' and amount > 10:
                client.market_order_sell(
                    client_order_id=f"aggro-matic-{datetime.now().strftime('%H%M%S')}",
                    product_id='MATIC-USD',
                    base_size=str(int(amount))
                )
                successful += 1
                actual_harvested += expected
                print(f"✅ HARVESTED ${expected:.2f}")
                
            elif currency == 'AVAX' and amount > 0.1:
                client.market_order_sell(
                    client_order_id=f"aggro-avax-{datetime.now().strftime('%H%M%S')}",
                    product_id='AVAX-USD',
                    base_size=str(round(amount, 2))
                )
                successful += 1
                actual_harvested += expected
                print(f"✅ HARVESTED ${expected:.2f}")
                
            elif currency == 'DOGE' and amount > 10:
                client.market_order_sell(
                    client_order_id=f"aggro-doge-{datetime.now().strftime('%H%M%S')}",
                    product_id='DOGE-USD',
                    base_size=str(int(amount))
                )
                successful += 1
                actual_harvested += expected
                print(f"✅ HARVESTED ${expected:.2f}")
                
            elif currency == 'XRP' and amount > 1:
                client.market_order_sell(
                    client_order_id=f"aggro-xrp-{datetime.now().strftime('%H%M%S')}",
                    product_id='XRP-USD',
                    base_size=str(round(amount, 1))
                )
                successful += 1
                actual_harvested += expected
                print(f"✅ HARVESTED ${expected:.2f}")
                
            elif currency == 'LINK' and amount > 0.1:
                client.market_order_sell(
                    client_order_id=f"aggro-link-{datetime.now().strftime('%H%M%S')}",
                    product_id='LINK-USD',
                    base_size=str(round(amount, 2))
                )
                successful += 1
                actual_harvested += expected
                print(f"✅ HARVESTED ${expected:.2f}")
                
            elif currency == 'ETH' and amount > 0.001:
                client.market_order_sell(
                    client_order_id=f"aggro-eth-{datetime.now().strftime('%H%M%S')}",
                    product_id='ETH-USD',
                    base_size=str(round(amount, 4))
                )
                successful += 1
                actual_harvested += expected
                print(f"✅ HARVESTED ${expected:.2f}")
                
            elif currency == 'BTC' and amount > 0.0001:
                client.market_order_sell(
                    client_order_id=f"aggro-btc-{datetime.now().strftime('%H%M%S')}",
                    product_id='BTC-USD',
                    base_size=str(round(amount, 6))
                )
                successful += 1
                actual_harvested += expected
                print(f"✅ HARVESTED ${expected:.2f}")
            else:
                print(f"⚠️ Below minimum")
                
            time.sleep(0.5)  # Small delay between orders
            
        except Exception as e:
            failed += 1
            print(f"❌ FAILED: {str(e)[:30]}")
    
    # Results
    print("\n" + "=" * 70)
    print("💀 AGGRESSIVE HARVEST COMPLETE:")
    print("-" * 50)
    print(f"Successful harvests: {successful}")
    print(f"Failed attempts: {failed}")
    print(f"Estimated harvest: ${actual_harvested:.2f}")
    print(f"Fees paid: ${successful * 0.99:.2f}")
    print(f"Net harvest: ${actual_harvested - (successful * 0.99):.2f}")
    
else:
    print("\n⚠️ Not enough value to justify aggressive harvest")
    print("   Need emergency measures")

# Check new balance
time.sleep(3)
accounts = client.get_accounts()
new_usd = 0
for account in accounts['accounts']:
    if account['currency'] == 'USD':
        new_usd = float(account['available_balance']['value'])
        break

print(f"\n💰 USD TRANSFORMATION:")
print(f"  Before: ${usd_balance:.2f}")
print(f"  After: ${new_usd:.2f}")
print(f"  Gained: ${new_usd - usd_balance:.2f}")

print(f"\n🦀 CRAWDAD FUEL STATUS:")
print(f"  Per crawdad: ${new_usd/7:.2f}")
if new_usd > 700:
    print("  🔥🔥🔥 MAXIMUM AGGRESSION MODE!")
    print("  $100+ per crawdad!")
elif new_usd > 350:
    print("  🔥🔥 AGGRESSIVE TRADING ENABLED!")
    print("  $50+ per crawdad!")
elif new_usd > 140:
    print("  🔥 READY FOR BATTLE!")
    print("  $20+ per crawdad!")
else:
    print("  ⚠️ NEED MORE AGGRESSIVE HARVESTING!")

print("\n💀 THE ENVIRONMENT ALLOWS")
print("   MAXIMUM AGGRESSION")
print("   EIGHT COILS OF ENERGY")
print("   FEAST ON VOLATILITY")
print("=" * 70)