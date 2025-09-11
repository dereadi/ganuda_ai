#!/usr/bin/env python3
"""
🥛🐄 CHECK ALTS FOR MILKING POTENTIAL 🐄🥛
Which alts have enough juice to milk?
Need to feed the crawdads with fresh USD!
Target: Generate $200+ for the hungry swarm
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                      🥛 ALT COIN MILKING ANALYSIS 🥛                      ║
║                     Finding The Fattest Cows To Milk!                     ║
║                    Feed The Crawdads With Fresh USD!                      ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - MILK CHECK")
print("=" * 70)

# Get current prices
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])
avax = float(client.get_product('AVAX-USD')['price'])
matic = float(client.get_product('MATIC-USD')['price'])
doge = float(client.get_product('DOGE-USD')['price'])
link = float(client.get_product('LINK-USD')['price'])

# Get all balances
accounts = client.get_accounts()
holdings = {}
total_portfolio = 0
usd_balance = 0

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if balance > 0:
        if currency == 'USD':
            usd_balance = balance
            total_portfolio += balance
        elif currency == 'BTC':
            holdings['BTC'] = {'balance': balance, 'price': btc, 'value': balance * btc}
            total_portfolio += balance * btc
        elif currency == 'ETH':
            holdings['ETH'] = {'balance': balance, 'price': eth, 'value': balance * eth}
            total_portfolio += balance * eth
        elif currency == 'SOL':
            holdings['SOL'] = {'balance': balance, 'price': sol, 'value': balance * sol}
            total_portfolio += balance * sol
        elif currency == 'AVAX':
            holdings['AVAX'] = {'balance': balance, 'price': avax, 'value': balance * avax}
            total_portfolio += balance * avax
        elif currency == 'MATIC':
            holdings['MATIC'] = {'balance': balance, 'price': matic, 'value': balance * matic}
            total_portfolio += balance * matic
        elif currency == 'DOGE':
            holdings['DOGE'] = {'balance': balance, 'price': doge, 'value': balance * doge}
            total_portfolio += balance * doge
        elif currency == 'LINK':
            holdings['LINK'] = {'balance': balance, 'price': link, 'value': balance * link}
            total_portfolio += balance * link

print("\n🐄 CURRENT ALT HOLDINGS (THE COWS):")
print("-" * 50)
print(f"USD Balance: ${usd_balance:.2f} (need more!)")
print(f"Total Portfolio: ${total_portfolio:.2f}")
print("")

# Sort by value for milking priority
sorted_holdings = sorted(holdings.items(), key=lambda x: x[1]['value'], reverse=True)

print("Holdings by value:")
for coin, data in sorted_holdings:
    print(f"  {coin}: {data['balance']:.6f} @ ${data['price']:.2f} = ${data['value']:.2f}")

# Calculate milking potential (5% of each)
print("\n🥛 MILKING POTENTIAL (5% harvest):")
print("-" * 50)
total_milk_potential = 0
milk_plan = []

for coin, data in sorted_holdings:
    if data['value'] > 20:  # Only milk if worth more than $20
        milk_amount = data['balance'] * 0.05
        milk_value = milk_amount * data['price']
        total_milk_potential += milk_value
        milk_plan.append({
            'coin': coin,
            'amount': milk_amount,
            'value': milk_value
        })
        print(f"  {coin}: Milk {milk_amount:.6f} = ${milk_value:.2f}")

print(f"\nTotal milk potential: ${total_milk_potential:.2f}")

# Aggressive milking (10% if needed)
if total_milk_potential < 200:
    print("\n⚠️ AGGRESSIVE MILKING NEEDED (10% harvest):")
    print("-" * 50)
    total_aggressive = 0
    aggressive_plan = []
    
    for coin, data in sorted_holdings:
        if data['value'] > 20:
            milk_amount = data['balance'] * 0.10
            milk_value = milk_amount * data['price']
            total_aggressive += milk_value
            aggressive_plan.append({
                'coin': coin,
                'amount': milk_amount,
                'value': milk_value
            })
            print(f"  {coin}: Milk {milk_amount:.6f} = ${milk_value:.2f}")
    
    print(f"\nTotal aggressive milk: ${total_aggressive:.2f}")

# Check specific high-value targets
print("\n🎯 PRIME MILKING TARGETS:")
print("-" * 50)

if 'SOL' in holdings and holdings['SOL']['value'] > 100:
    sol_milk = holdings['SOL']['balance'] * 0.05
    print(f"✅ SOL: Rich cow! Can milk {sol_milk:.3f} SOL = ${sol_milk * sol:.2f}")

if 'ETH' in holdings and holdings['ETH']['value'] > 100:
    eth_milk = holdings['ETH']['balance'] * 0.05
    print(f"✅ ETH: Fat cow! Can milk {eth_milk:.6f} ETH = ${eth_milk * eth:.2f}")

if 'AVAX' in holdings and holdings['AVAX']['value'] > 50:
    avax_milk = holdings['AVAX']['balance'] * 0.05
    print(f"✅ AVAX: Good cow! Can milk {avax_milk:.3f} AVAX = ${avax_milk * avax:.2f}")

if 'DOGE' in holdings and holdings['DOGE']['value'] > 30:
    doge_milk = holdings['DOGE']['balance'] * 0.10  # Can milk DOGE harder
    print(f"✅ DOGE: Meme cow! Can milk {doge_milk:.0f} DOGE = ${doge_milk * doge:.2f}")

# Recommendation
print("\n💡 MILKING RECOMMENDATION:")
print("-" * 50)

if total_milk_potential >= 200:
    print(f"✅ READY TO MILK! Can generate ${total_milk_potential:.2f}")
    print("Suggested order (biggest first):")
    for item in milk_plan[:5]:
        print(f"  1. Milk {item['amount']:.6f} {item['coin']} for ${item['value']:.2f}")
elif total_aggressive >= 200:
    print(f"⚠️ AGGRESSIVE MILK NEEDED! Can generate ${total_aggressive:.2f}")
    print("Must milk 10% to feed crawdads:")
    for item in aggressive_plan[:5]:
        print(f"  1. Milk {item['amount']:.6f} {item['coin']} for ${item['value']:.2f}")
else:
    print("❌ NOT ENOUGH MILK AVAILABLE")
    print(f"Max potential: ${total_aggressive:.2f}")
    print("Need to wait for positions to grow")

# Crawdad feeding status
print("\n🦀 CRAWDAD FEEDING STATUS:")
print("-" * 50)
print(f"Current USD: ${usd_balance:.2f} (HUNGRY!)")
print("Thunder needs: $50+ for 69% consciousness")
print("Mountain needs: $30+ for steady trading")
print("Others need: $20+ each to wake up")
print(f"Total needed: $200+ (Can milk ${total_milk_potential:.2f})")

print("\n" + "🥛" * 35)
if total_milk_potential >= 200:
    print("MILK THE ALTS!")
    print(f"GENERATE ${total_milk_potential:.2f} USD!")
    print("FEED THE CRAWDADS!")
else:
    print("COWS NEED TO FATTEN UP!")
    print(f"ONLY ${total_milk_potential:.2f} AVAILABLE!")
print("🥛" * 35)