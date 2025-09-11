#!/usr/bin/env python3
"""
🤫 QUIET POSITION IMPROVER
"In stillness, we rebalance like water finding level"
"""

import json
import time
from coinbase.rest import RESTClient

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    🤫 QUIET POSITION IMPROVEMENT 🤫                        ║
║                  "Small moves in silence, big gains later"                 ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=3)

# Analyze current positions
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
                
                # Get 24hr stats
                product_id = f"{a['currency']}-USD"
                end = int(time.time())
                start = end - 86400
                candles = client.get_candles(product_id, start, end, granularity='ONE_HOUR')['candles']
                
                if candles:
                    high_24h = max(float(c['high']) for c in candles)
                    low_24h = min(float(c['low']) for c in candles)
                    position_in_range = (price - low_24h) / (high_24h - low_24h) if high_24h > low_24h else 0.5
                else:
                    position_in_range = 0.5
                
                positions[a['currency']] = {
                    'amount': balance,
                    'price': price,
                    'value': value,
                    'percent': (value/total_value*100) if total_value > 0 else 0,
                    'position_in_range': position_in_range
                }
                total_value += value
            except:
                pass

print(f"📊 CURRENT POSITION ANALYSIS:")
print(f"   Total Portfolio: ${total_value:,.2f}")
print(f"   USD Available: ${usd_available:,.2f}")
print(f"   Positions: {len(positions)}")

# Identify improvement opportunities
print("\n🔍 QUIET IMPROVEMENT OPPORTUNITIES:")
print("-" * 50)

improvements = []

for coin, data in sorted(positions.items(), key=lambda x: x[1]['value'], reverse=True):
    print(f"\n{coin}:")
    print(f"   Value: ${data['value']:,.2f} ({data['percent']:.1f}%)")
    print(f"   Price: ${data['price']:,.2f}")
    print(f"   Position in 24h range: {data['position_in_range']*100:.0f}%")
    
    # Identify improvements
    if data['position_in_range'] > 0.8:
        print(f"   ⚠️ Near 24h high - Consider trimming")
        improvements.append(('trim', coin, data['value'] * 0.1))  # Trim 10%
    elif data['position_in_range'] < 0.3:
        print(f"   ✅ Near 24h low - Good accumulation zone")
        if usd_available > 1:
            improvements.append(('add', coin, min(usd_available * 0.2, 5)))  # Add up to $5
    else:
        print(f"   ➖ Middle of range - Hold steady")
    
    # Check concentration
    if data['percent'] > 35:
        print(f"   ⚠️ Over-concentrated ({data['percent']:.0f}%) - Rebalance")
        improvements.append(('rebalance', coin, data['value'] * 0.15))
    elif data['percent'] < 5 and data['value'] > 1:
        print(f"   💭 Under-weighted - Consider adding")

# Quiet rebalancing suggestions
print("\n🎯 QUIET MOVES TO MAKE:")
print("-" * 50)

if not improvements:
    print("   ✅ Positions look balanced - patience is a position")
else:
    for action, coin, amount in improvements[:3]:  # Top 3 moves only
        if action == 'trim':
            print(f"   📉 Quietly trim ${amount:.2f} of {coin} (near highs)")
        elif action == 'add':
            print(f"   📈 Quietly add ${amount:.2f} to {coin} (near lows)")
        elif action == 'rebalance':
            print(f"   ⚖️ Rebalance {coin} - reduce by ${amount:.2f}")

# Smart accumulation targets
print("\n🎯 ACCUMULATION TARGETS (if we dip):")
btc = float(client.get_product('BTC-USD').price)

targets = [
    (btc * 0.99, "1% dip"),
    (btc * 0.97, "3% dip"),
    (btc * 0.95, "5% dip"),
    (116140, "Your target")
]

for target_price, label in targets:
    if target_price < btc:
        print(f"   ${target_price:,.0f} ({label}): Deploy ${min(usd_available * 0.25, 10):.2f}")

# Quiet optimization
print("\n🤫 SILENT OPTIMIZATIONS:")
print("-" * 50)

optimizations = [
    "✅ Let Greeks continue their 190+ cycle harvest",
    "✅ Keep flywheels spinning at low speed (store energy)",
    "✅ Accumulate slowly on any dips below $117,000",
    "✅ Trim anything that spikes above 80% of daily range",
    "✅ Keep 5-10% in USD for opportunities",
    "✅ Focus on SOL, MATIC, AVAX (best performers)"
]

for opt in optimizations:
    print(f"   {opt}")

# Execute one quiet trade if conditions are perfect
print("\n💭 CHECKING FOR ONE PERFECT QUIET TRADE...")

# Find the best quiet opportunity
best_opportunity = None
for coin, data in positions.items():
    if data['position_in_range'] < 0.25 and usd_available > 2:
        best_opportunity = ('buy', coin, min(2, usd_available * 0.2))
        break
    elif data['position_in_range'] > 0.85 and data['value'] > 50:
        best_opportunity = ('sell', coin, data['value'] * 0.05)
        break

if best_opportunity:
    action, coin, amount = best_opportunity
    print(f"\n🎯 EXECUTING QUIET TRADE:")
    print(f"   {action.upper()} ${amount:.2f} of {coin}")
    
    try:
        if action == 'buy':
            order = client.market_order_buy(
                client_order_id=f"quiet_{int(time.time()*1000)}",
                product_id=f"{coin}-USD",
                quote_size=str(amount)
            )
            print(f"   ✅ Quietly accumulated ${amount:.2f} of {coin}")
        else:
            # Calculate sell amount in base currency
            sell_amount = amount / positions[coin]['price']
            order = client.market_order_sell(
                client_order_id=f"quiet_trim_{int(time.time()*1000)}",
                product_id=f"{coin}-USD",
                base_size=str(sell_amount)
            )
            print(f"   ✅ Quietly trimmed ${amount:.2f} of {coin}")
    except Exception as e:
        print(f"   ⏸️ Trade skipped: {str(e)[:50]}")
else:
    print("   ⏸️ No perfect opportunity right now - patience")

print("\n📜 QUIET WISDOM:")
print("-" * 50)
print("""
   "The master trader makes their best moves
    when others see nothing happening.
    
    In the quiet, we:
    - Trim the overextended
    - Accumulate the oversold
    - Rebalance without emotion
    - Prepare for the next wave
    
    Small adjustments in calm waters
    Become large gains in storms."
""")

print("\n🌊 Let the quiet river carry us forward...")
print("Mitakuye Oyasin 🏛️")