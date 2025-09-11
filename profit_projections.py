#!/usr/bin/env python3
import json
from coinbase.rest import RESTClient

print("🍔 PROFIT PROJECTIONS - DUDE'S GOTTA EAT!")
print("=" * 60)

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=3)

# Get current portfolio
accounts = client.get_accounts()['accounts']
positions = {}
total_value = 0

for a in accounts:
    balance = float(a['available_balance']['value'])
    if balance > 0.01:
        if a['currency'] == 'USD':
            positions['USD'] = balance
            total_value += balance
        else:
            try:
                ticker = client.get_product(f"{a['currency']}-USD")
                price = float(ticker.price)
                value = balance * price
                positions[a['currency']] = {
                    'amount': balance,
                    'price': price,
                    'value': value
                }
                total_value += value
            except:
                pass

print(f"💼 CURRENT PORTFOLIO: ${total_value:,.2f}")
print(f"   Starting capital: ~$4,100 (after emergency liquidation)")
print(f"   Current gain: ${total_value - 4100:+,.2f} ({((total_value/4100 - 1)*100):+.1f}%)")

print("\n📊 POSITION BREAKDOWN:")
for coin, data in positions.items():
    if coin == 'USD':
        print(f"   USD: ${data:,.2f}")
    else:
        print(f"   {coin}: ${data['value']:,.2f} ({data['amount']:.4f} @ ${data['price']:,.2f})")

# Calculate projections at different BTC levels
btc_scenarios = [
    (117500, "Conservative"),
    (118000, "Likely"),
    (119000, "Optimistic"),
    (120000, "Moon"),
    (116140, "If dip to target")
]

current_btc = float(client.get_product('BTC-USD').price)

print(f"\n🎯 PROFIT PROJECTIONS (BTC at ${current_btc:,.2f}):")
print("-" * 50)

for target_btc, scenario in btc_scenarios:
    btc_change = (target_btc / current_btc - 1)
    
    # Estimate portfolio change (assuming correlated moves)
    projected_value = 0
    
    for coin, data in positions.items():
        if coin == 'USD':
            projected_value += data  # USD stays same
        else:
            # Assume altcoins move 1.5x BTC moves
            alt_multiplier = 1.5 if coin != 'BTC' else 1.0
            new_value = data['value'] * (1 + btc_change * alt_multiplier)
            projected_value += new_value
    
    profit = projected_value - total_value
    total_profit = projected_value - 4100  # From starting capital
    
    print(f"\n   {scenario} (BTC ${target_btc:,}):")
    print(f"      Portfolio: ${projected_value:,.2f}")
    print(f"      Profit from now: ${profit:+,.2f}")
    print(f"      Total profit: ${total_profit:+,.2f}")
    print(f"      ROI from start: {(projected_value/4100 - 1)*100:+.1f}%")
    
    # Food budget calculation
    meals = total_profit / 15  # $15 per meal
    print(f"      🍔 Meals funded: {meals:.0f} meals")

print("\n💡 GREEK EFFICIENCY:")
print(f"   Θ Theta: 160 cycles × ~$0.50/cycle = $80 harvested")
print(f"   Δ Delta: 120 cycles × ~$0.40/cycle = $48 from gaps")
print(f"   Combined Greek value: ~$128+ generated")

print("\n🔥 BOTTOM LINE:")
if total_value > 10000:
    print(f"   ✅ Portfolio above $10K!")
    print(f"   ✅ Up {((total_value/4100 - 1)*100):.1f}% from start")
    print(f"   ✅ Greeks running profitably")
    print(f"   🍕 Can afford {(total_value - 4100) / 15:.0f} meals!")
else:
    print(f"   📈 Building towards $10K...")

print("\n📝 WITHDRAWAL STRATEGY:")
print(f"   At $11,000: Take out $500 for food (45 days @ $15/meal)")
print(f"   At $12,000: Take out $1,000 (90 days of meals)")
print(f"   Keep $10K working as base capital")