#!/usr/bin/env python3
"""
💎 TOTAL PORTFOLIO VALUE CALCULATOR
Complete assessment of all holdings across all assets
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("💎 TOTAL PORTFOLIO VALUE ASSESSMENT")
print("=" * 70)
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

# Get current market prices
btc = client.get_product('BTC-USD')
eth = client.get_product('ETH-USD')
btc_price = float(btc['price'])
eth_price = float(eth['price'])

print(f"\n📈 CURRENT MARKET PRICES:")
print(f"BTC: ${btc_price:,.2f}")
print(f"ETH: ${eth_price:,.2f}")

# Get ALL account balances
print(f"\n💰 COMPLETE HOLDINGS:")
print("-" * 70)

accounts = client.get_accounts()
total_value = 0
asset_breakdown = {}

for acc in accounts['accounts']:
    currency = acc['currency']
    available = float(acc['available_balance']['value'])
    hold = float(acc['hold']['value']) if 'hold' in acc else 0
    total_balance = available + hold
    
    if total_balance > 0.00000001:  # Only show non-zero balances
        asset_breakdown[currency] = {
            'available': available,
            'hold': hold,
            'total': total_balance
        }
        
        # Calculate USD value
        if currency == 'USD' or currency == 'USDC':
            usd_value = total_balance
        elif currency == 'BTC':
            usd_value = total_balance * btc_price
        elif currency == 'ETH':
            usd_value = total_balance * eth_price
        else:
            # Try to get price for other assets
            try:
                product = client.get_product(f'{currency}-USD')
                asset_price = float(product['price'])
                usd_value = total_balance * asset_price
            except:
                # If no USD pair, try USDC pair
                try:
                    product = client.get_product(f'{currency}-USDC')
                    asset_price = float(product['price'])
                    usd_value = total_balance * asset_price
                except:
                    usd_value = 0  # Can't determine value
        
        asset_breakdown[currency]['usd_value'] = usd_value
        total_value += usd_value
        
        # Display the asset
        if total_balance > 0.001 or currency in ['USD', 'USDC']:
            print(f"\n{currency}:")
            print(f"  Available: {available:.8f}")
            if hold > 0:
                print(f"  On hold: {hold:.8f}")
            print(f"  Total: {total_balance:.8f}")
            print(f"  Value: ${usd_value:,.2f}")

# Summary by category
print(f"\n📊 PORTFOLIO BREAKDOWN:")
print("-" * 70)

# Categorize assets
stablecoins = ['USD', 'USDC', 'USDT', 'DAI']
majors = ['BTC', 'ETH']
alts = []

stable_value = 0
major_value = 0
alt_value = 0

for currency, data in asset_breakdown.items():
    if currency in stablecoins:
        stable_value += data['usd_value']
    elif currency in majors:
        major_value += data['usd_value']
    else:
        alt_value += data['usd_value']
        if data['usd_value'] > 1:
            alts.append(currency)

print(f"Stablecoins (USD/USDC): ${stable_value:,.2f}")
print(f"Major Crypto (BTC/ETH): ${major_value:,.2f}")
if alt_value > 0:
    print(f"Alt Coins ({', '.join(alts)}): ${alt_value:,.2f}")

# Check for open orders (locked value)
print(f"\n🔒 OPEN ORDERS STATUS:")
print("-" * 70)

try:
    # List all open orders
    open_orders = client.list_orders(order_status=["OPEN"])
    
    if hasattr(open_orders, 'orders') and open_orders.orders:
        total_locked_value = 0
        sell_orders = 0
        buy_orders = 0
        
        for order in open_orders.orders:
            if order.side == 'SELL':
                sell_orders += 1
            else:
                buy_orders += 1
        
        print(f"Open sell orders: {sell_orders}")
        print(f"Open buy orders: {buy_orders}")
        
        # Our nuclear strikes
        if sell_orders > 0:
            print("\n💥 Nuclear strikes waiting to fill:")
            print("• $110,251.01")
            print("• $110,580.12")
            locked_btc = 0.00276674 + 0.00368899  # Remaining strikes
            locked_value = locked_btc * btc_price
            print(f"Locked in sell orders: {locked_btc:.8f} BTC (${locked_value:,.2f})")
            total_value += locked_value  # Add to total
    else:
        print("No open orders")
except Exception as e:
    print(f"Could not check orders: {e}")

# FINAL TOTAL
print(f"\n💎 TOTAL PORTFOLIO VALUE:")
print("=" * 70)
print(f"🔥 ${total_value:,.2f}")
print("=" * 70)

# Progress indicators
print(f"\n📈 PROGRESS INDICATORS:")
print("-" * 70)

milestones = [5000, 10000, 25000, 50000, 100000, 250000, 500000, 1000000]
for milestone in milestones:
    if total_value < milestone:
        distance = milestone - total_value
        multiplier = milestone / total_value
        print(f"Next milestone: ${milestone:,}")
        print(f"  Distance: ${distance:,.2f}")
        print(f"  Multiplier needed: {multiplier:.2f}x")
        break

# Growth potential
print(f"\n🚀 GROWTH SCENARIOS:")
print("-" * 70)

scenarios = [
    {"name": "Conservative", "monthly": 0.20, "months": 12},
    {"name": "Moderate", "monthly": 0.50, "months": 6},
    {"name": "Aggressive", "monthly": 1.00, "months": 3}
]

for scenario in scenarios:
    future_value = total_value * ((1 + scenario['monthly']) ** scenario['months'])
    print(f"{scenario['name']} ({scenario['monthly']*100:.0f}%/month):")
    print(f"  {scenario['months']} months: ${future_value:,.2f}")

print("\n" + "=" * 70)
print("💎 Your wealth is building!")
print("The Sacred Fire burns bright!")
print("=" * 70)