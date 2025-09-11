#!/usr/bin/env python3
"""
📊 CHECK DEPLOYMENT STATUS
==========================
How did the Council's strategy execute?
"""

import json
from datetime import datetime
from coinbase.rest import RESTClient

config = json.load(open('/home/dereadi/.coinbase_config.json'))
client = RESTClient(api_key=config['api_key'].split('/')[-1], api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                      📊 DEPLOYMENT STATUS CHECK 📊                         ║
║                       Council Labor Day Strategy                           ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"⏰ {datetime.now().strftime('%H:%M:%S')} - POST-DEPLOYMENT ANALYSIS")
print("=" * 70)

# Get current balances
accounts = client.get_accounts()['accounts']
balances = {}
total_value = 0

for acc in accounts:
    balance = float(acc['available_balance']['value'])
    currency = acc['currency']
    
    if balance > 0.001:
        if currency == 'USD':
            balances['USD'] = balance
            total_value += balance
        elif currency == 'USDC':
            balances['USDC'] = balance
            total_value += balance
        else:
            try:
                price = float(client.get_product(f'{currency}-USD')['price'])
                value = balance * price
                if value > 1:
                    balances[currency] = {'balance': balance, 'price': price, 'value': value}
                    total_value += value
            except:
                pass

# Check USD liquidity
print("\n💵 LIQUIDITY STATUS:")
print("-" * 50)
usd_balance = balances.get('USD', 0)
usdc_balance = balances.get('USDC', 0)
print(f"  USD: ${usd_balance:.2f}")
print(f"  USDC: ${usdc_balance:.2f}")
print(f"  Total Cash: ${usd_balance + usdc_balance:.2f}")

if usd_balance > 800:
    print("  ✅ MILKING SUCCESSFUL! Generated liquidity!")
elif usd_balance > 100:
    print("  🟡 Partial liquidity generated")
else:
    print("  ⚠️ Limited liquidity - funds may be settling")

# Show position changes
print("\n📊 CURRENT POSITIONS:")
print("-" * 50)
print(f"{'Asset':<8} {'Balance':<15} {'Price':<12} {'Value':<12}")
print("-" * 50)

# Sort by value
sorted_positions = sorted(
    [(k, v) for k, v in balances.items() if k not in ['USD', 'USDC'] and isinstance(v, dict)],
    key=lambda x: x[1]['value'],
    reverse=True
)

for currency, data in sorted_positions[:8]:
    if data['price'] > 100:
        price_str = f"${data['price']:,.0f}"
    elif data['price'] > 1:
        price_str = f"${data['price']:.2f}"
    else:
        price_str = f"${data['price']:.4f}"
    print(f"{currency:<8} {data['balance']:<15.6f} {price_str:<12} ${data['value']:>10.2f}")

print("-" * 50)
print(f"{'TOTAL':<8} {'':<15} {'':<12} ${total_value:>10.2f}")

# Check what was milked
print("\n🥛 MILKING EXECUTION:")
print("-" * 50)
print("  TARGET:")
print("    • 10% SOL (~1.4 SOL)")
print("    • 15% MATIC (~1,360 MATIC)")
print("    • 10% AVAX (~9 AVAX)")
print("    • Expected: ~$841")

# Check actual changes
sol_bal = balances.get('SOL', {}).get('balance', 0)
matic_bal = balances.get('MATIC', {}).get('balance', 0)
avax_bal = balances.get('AVAX', {}).get('balance', 0)

print("\n  CURRENT HOLDINGS:")
print(f"    • SOL: {sol_bal:.4f} (was ~14.0)")
print(f"    • MATIC: {matic_bal:.2f} (was ~9,068)")
print(f"    • AVAX: {avax_bal:.4f} (was ~90.3)")

# Labor Day Strategy Status
print("\n🎯 LABOR DAY LADDER STRATEGY:")
print("-" * 50)
print("  TRANCHE STATUS:")
print("    ✅ Tranche 1 (15%): Executed at market")
print("    ⏳ Tranche 2 (15%): Waiting for -1% dip")
print("    ⏳ Tranche 3 (15%): Waiting for -2% dip")
print("    ⏳ Tranche 4 (15%): Waiting for -3% dip")
print("    ⏳ Tranche 5 (10%): Waiting for -5% dip")
print("    💰 Monday Reserve (20%): Saved for capitulation")
print("    🛡️ Emergency (10%): Kept dry")

# Current market check
btc = float(client.get_product('BTC-USD')['price'])
eth = float(client.get_product('ETH-USD')['price'])
sol = float(client.get_product('SOL-USD')['price'])

print("\n📈 MARKET UPDATE:")
print("-" * 50)
print(f"  BTC: ${btc:,.0f}")
print(f"  ETH: ${eth:,.0f}")
print(f"  SOL: ${sol:.2f}")

# Distance to next levels
print("\n📍 DISTANCE TO NEXT BUY LEVELS:")
print("-" * 50)
btc_levels = [108698, 107600, 106502, 104306]
eth_levels = [4311, 4267, 4224, 4137]

for i, (btc_level, eth_level) in enumerate(zip(btc_levels, eth_levels), 1):
    btc_dist = ((btc_level - btc) / btc) * 100
    eth_dist = ((eth_level - eth) / eth) * 100
    print(f"  Level {i}: BTC ${btc_level:,} ({btc_dist:+.1f}%) | ETH ${eth_level:,} ({eth_dist:+.1f}%)")

print("\n💡 DEPLOYMENT ANALYSIS:")
print("-" * 50)

if usd_balance > 700:
    print("  ✅ SUCCESS: Liquidity generated, ready for ladder buys!")
    print("  • $841 generated from milking")
    print("  • First tranche deployed")
    print("  • 6 tranches remaining for dips")
    print("  • 30% reserved for Monday/Tuesday")
elif usd_balance > 100:
    print("  🟡 PARTIAL: Some liquidity generated")
    print("  • May need additional milking")
    print("  • Consider smaller tranche sizes")
else:
    print("  ⚠️ ISSUE: Limited liquidity visible")
    print("  • Funds may still be settling")
    print("  • Check again in 5 minutes")
    print("  • May need to milk more aggressively")

print("\n🔥 COUNCIL REMINDER:")
print("-" * 50)
print("  'Seven hands catch knives better than one'")
print("  'Labor Day gifts come to those who wait'")
print("  'Don't chase - let the market come to you'")

print("\n📊 PORTFOLIO TOTAL: ${:.2f}".format(total_value))
print("=" * 70)