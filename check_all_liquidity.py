#!/usr/bin/env python3
"""
💵 LIQUIDITY CHECK - Where's Our Ammo?
=======================================
Find every dollar we can deploy
"""

import json
from datetime import datetime
from coinbase.rest import RESTClient

config = json.load(open('/home/dereadi/.coinbase_config.json'))
client = RESTClient(api_key=config['api_key'].split('/')[-1], api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                        💵 LIQUIDITY ANALYSIS 💵                            ║
║                     Where's Our Trading Capital?                           ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"⏰ {datetime.now().strftime('%H:%M:%S')} - SCANNING ALL ASSETS")
print("=" * 70)

# Get all accounts
accounts = client.get_accounts()['accounts']

# Separate USD and crypto
usd_positions = []
crypto_positions = []
total_liquidity = 0
total_crypto_value = 0

for acc in accounts:
    balance = float(acc['available_balance']['value'])
    currency = acc['currency']
    
    if balance > 0.001:
        if currency in ['USD', 'USDC']:
            usd_positions.append({'currency': currency, 'balance': balance})
            total_liquidity += balance
        else:
            # Get USD value
            try:
                price = float(client.get_product(f'{currency}-USD')['price'])
                value = balance * price
                if value > 1:  # Only show positions worth > $1
                    crypto_positions.append({
                        'currency': currency,
                        'balance': balance,
                        'price': price,
                        'value': value
                    })
                    total_crypto_value += value
            except:
                pass

# Sort crypto by value
crypto_positions.sort(key=lambda x: x['value'], reverse=True)

print("\n💵 IMMEDIATE LIQUIDITY (USD):")
print("-" * 50)
for pos in usd_positions:
    print(f"  {pos['currency']}: ${pos['balance']:.2f}")
print(f"\n  TOTAL USD AVAILABLE: ${total_liquidity:.2f}")

if total_liquidity < 100:
    print("  ⚠️ LOW LIQUIDITY WARNING!")

print("\n🪙 CRYPTO POSITIONS (Can Milk):")
print("-" * 50)
print(f"{'Asset':<8} {'Balance':<15} {'Price':<12} {'Value':<12} {'10% Milk':<12}")
print("-" * 50)

for pos in crypto_positions[:10]:  # Top 10 positions
    milk_10pct = pos['value'] * 0.1
    if pos['price'] > 100:
        price_str = f"${pos['price']:,.0f}"
    elif pos['price'] > 1:
        price_str = f"${pos['price']:.2f}"
    else:
        price_str = f"${pos['price']:.4f}"
    
    print(f"{pos['currency']:<8} {pos['balance']:<15.6f} {price_str:<12} ${pos['value']:>10.2f} ${milk_10pct:>10.2f}")

print("-" * 50)
print(f"TOTAL CRYPTO VALUE: ${total_crypto_value:,.2f}")

# Calculate milking potential
print("\n🥛 MILKING POTENTIAL (Quick Liquidity):")
print("-" * 50)

# Conservative: Milk 5% of everything
milk_5pct = total_crypto_value * 0.05
print(f"  Conservative (5% of all): ${milk_5pct:.2f}")

# Moderate: Milk 10% of top 3
top3_value = sum(pos['value'] for pos in crypto_positions[:3])
milk_10pct_top3 = top3_value * 0.1
print(f"  Moderate (10% of top 3): ${milk_10pct_top3:.2f}")

# Aggressive: Milk 20% of non-BTC/ETH
non_core = [p for p in crypto_positions if p['currency'] not in ['BTC', 'ETH']]
non_core_value = sum(p['value'] for p in non_core)
milk_20pct_alts = non_core_value * 0.2
print(f"  Aggressive (20% of alts): ${milk_20pct_alts:.2f}")

print("\n⚡ RECOMMENDED QUICK LIQUIDITY PLAYS:")
print("-" * 50)

# Find overweight positions
recommendations = []
for pos in crypto_positions:
    pct_of_portfolio = (pos['value'] / total_crypto_value) * 100
    if pct_of_portfolio > 25:
        recommendations.append(f"  • {pos['currency']} is {pct_of_portfolio:.1f}% of portfolio - Consider trimming")
    elif pos['currency'] in ['XRP', 'MATIC'] and pos['value'] > 100:
        recommendations.append(f"  • {pos['currency']} near resistance - Good to milk ${pos['value']*0.15:.2f}")

if recommendations:
    for rec in recommendations:
        print(rec)
else:
    print("  • All positions balanced")

# Check if any stablecoins
stables = ['USDC', 'USDT', 'DAI']
for pos in crypto_positions:
    if pos['currency'] in stables:
        print(f"  • Convert {pos['currency']} to USD: ${pos['value']:.2f}")

print("\n📊 LIQUIDITY SUMMARY:")
print("=" * 70)
print(f"  Immediate USD: ${total_liquidity:.2f}")
print(f"  Quick Milk (5 min): ${milk_10pct_top3:.2f}")
print(f"  Total Available: ${total_liquidity + milk_10pct_top3:.2f}")
print(f"  Total Portfolio: ${total_liquidity + total_crypto_value:.2f}")

print("\n🎯 ACTION PLAN:")
print("-" * 50)

if total_liquidity < 50:
    print("  1. URGENT: Need liquidity for the dip!")
    print("  2. Milk 10% of SOL immediately")
    print("  3. Trim any position over 25% of portfolio")
    print("  4. Convert any stablecoins to USD")
    print("  5. Target: Generate $200-300 liquidity NOW")
else:
    print("  1. Deploy existing USD to catch dips")
    print("  2. Set limit orders at support")
    print("  3. Keep some powder dry")

print("\n🔥 COUNCIL GUIDANCE: 'Generate liquidity, buy the dip!'")
print("=" * 70)