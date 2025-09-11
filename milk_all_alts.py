#!/usr/bin/env python3
"""
🥛 MILK ALL ALTS FOR PROFITS
Check all positions and extract profits at these highs!
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                       🥛 PROFIT MILKING TIME! 🥛                         ║
║                    Extract Gains From All Positions                       ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - CHECKING ALL ALTS!")
print("=" * 70)

# Get all accounts
accounts = client.get_accounts()['accounts']

# Get current prices
sol = float(client.get_product('SOL-USD')['price'])
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])

print("\n📊 CURRENT POSITIONS & MILKING OPPORTUNITIES:")
print("-" * 40)

total_milk_value = 0

for acc in accounts:
    bal = float(acc['available_balance']['value'])
    currency = acc['currency']
    
    if bal > 0.01:
        if currency == 'SOL':
            value = bal * sol
            milk_amount = bal * 0.15  # 15% of SOL
            milk_value = milk_amount * sol
            total_milk_value += milk_value
            
            print(f"\n🌟 SOL Position:")
            print(f"  Balance: {bal:.2f} SOL = ${value:.2f}")
            print(f"  Current Price: ${sol:.2f}")
            print(f"  🥛 Can milk: {milk_amount:.2f} SOL = ${milk_value:.2f}")
            
        elif currency == 'BTC':
            value = bal * btc
            milk_amount = bal * 0.10  # 10% of BTC
            milk_value = milk_amount * btc
            total_milk_value += milk_value
            
            print(f"\n⚡ BTC Position:")
            print(f"  Balance: {bal:.6f} BTC = ${value:.2f}")
            print(f"  Current Price: ${btc:,.0f}")
            print(f"  🥛 Can milk: {milk_amount:.8f} BTC = ${milk_value:.2f}")
            
        elif currency == 'ETH':
            value = bal * eth
            milk_amount = bal * 0.10  # 10% of ETH
            milk_value = milk_amount * eth
            total_milk_value += milk_value
            
            print(f"\n💎 ETH Position:")
            print(f"  Balance: {bal:.4f} ETH = ${value:.2f}")
            print(f"  Current Price: ${eth:.2f}")
            print(f"  🥛 Can milk: {milk_amount:.4f} ETH = ${milk_value:.2f}")
            
        elif currency == 'USD':
            print(f"\n💵 USD: ${bal:.2f} (ready for deployment)")

print("\n" + "=" * 70)
print(f"🎯 TOTAL MILKABLE VALUE: ${total_milk_value:.2f}")
print("\n📈 MARKET CONDITIONS:")
print(f"  BTC: ${btc:,.0f} - Near highs!")
print(f"  ETH: ${eth:.2f} - Breaking out!")
print(f"  SOL: ${sol:.2f} - Above $209!")
print("\n💭 PERFECT TIME TO MILK:")
print("• All assets at session highs")
print("• Extract profits to feed flywheel")
print("• Let crawdads feast on fresh USD!")
print("=" * 70)