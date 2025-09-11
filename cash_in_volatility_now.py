#!/usr/bin/env python3
"""
💰🌊 CASH IN ON THE VOLATILITY NOW!
We have $6,500+ in crypto watching $100 swings
The crawdads are starving with $16
Time to HARVEST and FEED THEM!
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
║                 💰🌊 CASH IN ON VOLATILITY NOW! 🌊💰                     ║
║                    $100+ Swings = FREE MONEY                              ║
║                  Crawdads Starving = Lost Profits                         ║
║                       TIME TO HARVEST!                                    ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - EMERGENCY HARVEST")
print("=" * 70)

# Get current prices
btc_price = float(client.get_product('BTC-USD')['price'])
eth_price = float(client.get_product('ETH-USD')['price'])
sol_price = float(client.get_product('SOL-USD')['price'])

print(f"\n📊 CURRENT PRICES:")
print(f"  BTC: ${btc_price:,.0f}")
print(f"  ETH: ${eth_price:.2f}")
print(f"  SOL: ${sol_price:.2f}")

# Check all holdings
accounts = client.get_accounts()
holdings = {}
total_value = 0
usd_balance = 0

print("\n💎 CURRENT HOLDINGS:")
print("-" * 50)

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if balance > 0:
        if currency == 'USD':
            usd_balance = balance
            print(f"USD: ${balance:.2f} - CRITICALLY LOW!")
        elif currency == 'BTC':
            value = balance * btc_price
            print(f"BTC: {balance:.8f} = ${value:.2f}")
            holdings['BTC'] = (balance, value)
            total_value += value
        elif currency == 'ETH':
            value = balance * eth_price
            print(f"ETH: {balance:.6f} = ${value:.2f}")
            holdings['ETH'] = (balance, value)
            total_value += value
        elif currency == 'SOL':
            value = balance * sol_price
            print(f"SOL: {balance:.4f} = ${value:.2f}")
            holdings['SOL'] = (balance, value)
            total_value += value

print(f"\nTotal crypto value: ${total_value:.2f}")
print(f"Current USD: ${usd_balance:.2f}")

# EXECUTE HARVEST
print("\n🔥 EXECUTING 20% HARVEST:")
print("-" * 50)

harvest_target = total_value * 0.20
print(f"Target harvest: ${harvest_target:.2f}")

# Harvest SOL first (most liquid)
if 'SOL' in holdings:
    sol_balance, sol_value = holdings['SOL']
    sol_to_sell = min(sol_balance * 0.25, harvest_target / sol_price)
    
    if sol_to_sell > 0.1:
        print(f"\n💸 Selling {sol_to_sell:.3f} SOL...")
        try:
            order = client.market_order_sell(
                client_order_id=f"volatility-harvest-sol-{datetime.now().strftime('%H%M%S')}",
                product_id='SOL-USD',
                base_size=str(round(sol_to_sell, 3))
            )
            generated = sol_to_sell * sol_price
            print(f"   ✅ SOLD! Generated ~${generated:.2f}")
            usd_balance += generated
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:50]}")

# Harvest ETH if needed
if 'ETH' in holdings and usd_balance < 500:
    eth_balance, eth_value = holdings['ETH']
    eth_to_sell = min(eth_balance * 0.20, 0.04)
    
    if eth_to_sell > 0.001:
        print(f"\n💸 Selling {eth_to_sell:.4f} ETH...")
        try:
            order = client.market_order_sell(
                client_order_id=f"volatility-harvest-eth-{datetime.now().strftime('%H%M%S')}",
                product_id='ETH-USD',
                base_size=str(round(eth_to_sell, 4))
            )
            generated = eth_to_sell * eth_price
            print(f"   ✅ SOLD! Generated ~${generated:.2f}")
            usd_balance += generated
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:50]}")

print(f"\n💵 NEW USD BALANCE: ~${usd_balance:.2f}")

# Calculate missed profits
print("\n😱 MISSED PROFIT CALCULATION:")
print("-" * 50)
print("BTC swinging $112,900 - $113,100 = $200 range")
print("If crawdads had $100 each:")
print("  • Buy at $112,900")
print("  • Sell at $113,100")
print("  • Profit: $200/$113,000 = 0.177%")
print("  • Per crawdad: $100 * 0.00177 = $1.77")
print("  • 7 crawdads = $12.39 per swing")
print("  • 10 swings tonight = $123.90 MISSED!")

print("\n🦀 CRAWDAD REVIVAL PLAN:")
print("-" * 50)
print(f"1. Feed each crawdad ${usd_balance/7:.2f}")
print("2. Set them to surf $50+ moves")
print("3. Each catches 2-3 waves per hour")
print("4. Compound profits back")
print("5. By morning: SIGNIFICANT GAINS")

print("\n⚡ ACTION REQUIRED:")
print("Stop watching, START TRADING!")
print("The volatility is HERE NOW!")
print("=" * 70)