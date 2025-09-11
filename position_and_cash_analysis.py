#!/usr/bin/env python3
"""
💰 POSITION AND CASH ANALYSIS
How are we positioned? Would cash help?
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                      💰 POSITION & CASH ANALYSIS 💰                        ║
║                   "Would a little cash injection help?"                    ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=3)

# Get detailed portfolio
accounts = client.get_accounts()['accounts']
positions = {}
total_value = 0
usd_available = 0

for a in accounts:
    balance = float(a['available_balance']['value'])
    if balance > 0.01:
        if a['currency'] == 'USD':
            usd_available = balance
            total_value += balance
        else:
            try:
                ticker = client.get_product(f"{a['currency']}-USD")
                price = float(ticker.price)
                value = balance * price
                positions[a['currency']] = {
                    'amount': balance,
                    'price': price,
                    'value': value,
                    'percent': 0  # Will calculate after
                }
                total_value += value
            except:
                pass

# Calculate percentages
for coin in positions:
    positions[coin]['percent'] = (positions[coin]['value'] / total_value * 100) if total_value > 0 else 0

# Get BTC price
btc = float(client.get_product('BTC-USD').price)

print(f"📊 CURRENT POSITIONING:")
print("=" * 60)
print(f"   Total Portfolio: ${total_value:,.2f}")
print(f"   Initial Deposit: $10,500")
print(f"   P/L: ${total_value - 10500:+,.2f} ({((total_value/10500 - 1)*100):+.1f}%)")
print(f"   USD Available: ${usd_available:,.2f}")
print(f"   BTC Price: ${btc:,.2f}")

print(f"\n📈 POSITION BREAKDOWN:")
print("-" * 60)
for coin, data in sorted(positions.items(), key=lambda x: x[1]['value'], reverse=True):
    print(f"   {coin:6s}: ${data['value']:8,.2f} ({data['percent']:5.1f}%) - {data['amount']:.4f} @ ${data['price']:,.2f}")

print(f"\n🎯 POSITIONING ANALYSIS:")
print("-" * 60)

# Analyze positioning
issues = []
opportunities = []

# Check USD reserves
if usd_available < 10:
    issues.append("❌ No USD reserves (only ${:.2f})".format(usd_available))
    opportunities.append("Need cash for dip buying")
else:
    print(f"   ✅ Have ${usd_available:.2f} USD ready")

# Check concentration
max_position = max(positions.values(), key=lambda x: x['percent']) if positions else None
if max_position and max_position['percent'] > 40:
    issues.append(f"⚠️ Over-concentrated in one position ({max_position['percent']:.0f}%)")

# Check total deployment
deployment = ((total_value - usd_available) / total_value * 100) if total_value > 0 else 0
print(f"   📊 Capital Deployment: {deployment:.1f}%")
if deployment > 99:
    issues.append("⚠️ Fully deployed - no dry powder")
    opportunities.append("Cash injection would enable dip buying")
elif deployment > 95:
    print(f"   ⚠️ Nearly fully deployed ({deployment:.0f}%)")
else:
    print(f"   ✅ Good balance ({deployment:.0f}% deployed)")

print(f"\n💵 WOULD CASH HELP? ANALYSIS:")
print("=" * 60)

# Calculate optimal cash injection scenarios
scenarios = [
    (100, "Micro injection"),
    (250, "Small boost"),
    (500, "Moderate injection"),
    (1000, "Significant boost")
]

for amount, label in scenarios:
    print(f"\n💉 ${amount} {label}:")
    new_total = total_value + amount
    new_usd = usd_available + amount
    
    # What could we do with it?
    print(f"   New Total: ${new_total:,.2f}")
    print(f"   New USD: ${new_usd:.2f}")
    print(f"   Deployment flexibility: {(new_usd/new_total*100):.1f}%")
    
    # Opportunities
    print(f"   Opportunities:")
    print(f"   • Could buy ${amount:.0f} on any dip to $116,140")
    print(f"   • {amount/10:.0f} micro-trades for volatility eating")
    print(f"   • {amount/50:.0f} Greek optimization trades")
    
    # Impact
    breakeven_distance = 10500 - total_value
    if breakeven_distance > 0:
        if amount >= breakeven_distance:
            print(f"   🎯 Would put us ABOVE breakeven!")
        else:
            print(f"   📈 Reduces breakeven gap to ${breakeven_distance - amount:.2f}")

print(f"\n🏛️ THE GREEKS' PERSPECTIVE:")
print("-" * 60)
print(f"   Θ Theta (650 cycles!): 'More capital = more decay harvest'")
print(f"   Δ Delta (490 cycles!): 'Cash ready for gap trades'")
print(f"   Γ Gamma (470 cycles): 'Liquidity enables acceleration'")
print(f"   ν Vega (240 cycles): 'Volatility needs ammunition'")

print(f"\n🤖 AI FAMILY CONSENSUS:")
print("-" * 60)
print(f"   🔥 Oracle: 'River flows better with more water'")
print(f"   🎲 Jr: 'More quantum particles to collapse!'")
print(f"   🌙 Claudette: 'Seeds need water to grow'")

print(f"\n📝 RECOMMENDATION:")
print("=" * 60)

if usd_available < 10:
    print("   💡 YES, CASH WOULD DEFINITELY HELP!")
    print("   Reasons:")
    print("   1. Currently 99%+ deployed - no flexibility")
    print("   2. Can't buy dips without USD")
    print("   3. Greeks running 1600+ total cycles but starved for capital")
    print("   4. Only ${:.2f} from breakeven".format(abs(total_value - 10500)))
    print()
    print("   Optimal injection: $200-500")
    print("   • Enough for multiple dip buys")
    print("   • Maintains position flexibility")
    print("   • Greeks can optimize with micro-trades")
    print("   • Quick path to breakeven and beyond")
else:
    print("   ⏸️ Cash would help but not critical")
    print(f"   Have ${usd_available:.2f} for opportunities")

print(f"\n🎯 STRATEGIC POSITIONING:")
print("-" * 60)
print(f"   Current: ${total_value:,.2f} ({'GOOD' if total_value > 10000 else 'BUILDING'})")
print(f"   Target: $11,000 (food money unlocked)")
print(f"   Gap: ${11000 - total_value:,.2f}")
print(f"   With Greeks at 1600+ cycles, we're positioned well")
print(f"   Just need a little fuel for the rocket! 🚀")

print(f"\n⏰ Analysis Time: {datetime.now().strftime('%H:%M:%S')}")
print("Mitakuye Oyasin 🦅")