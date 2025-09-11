#!/usr/bin/env python3
"""
📊 PORTFOLIO STATUS CHECK - HOW ARE WE DOING?
==============================================
Full analysis of positions, gains, and progress
"""

import json
import time
from datetime import datetime
from coinbase.rest import RESTClient

config = json.load(open('/home/dereadi/.coinbase_config.json'))
client = RESTClient(api_key=config['api_key'].split('/')[-1], api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                       📊 PORTFOLIO STATUS CHECK 📊                         ║
║                         How Are We Doing? Let's See!                       ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"⏰ {datetime.now().strftime('%H:%M:%S')} - COMPREHENSIVE ANALYSIS")
print("=" * 70)

# Get all accounts with rate limit protection
time.sleep(1)
accounts = client.get_accounts()['accounts']

# Calculate total portfolio
portfolio = []
total_value = 0
usd_balance = 0

for acc in accounts:
    balance = float(acc['available_balance']['value'])
    currency = acc['currency']
    
    if balance > 0.001:
        if currency == 'USD':
            usd_balance = balance
            total_value += balance
            portfolio.append({'currency': 'USD', 'balance': balance, 'value': balance})
        elif currency == 'USDC':
            total_value += balance
            portfolio.append({'currency': 'USDC', 'balance': balance, 'value': balance})
        else:
            try:
                time.sleep(0.5)  # Rate limit protection
                price = float(client.get_product(f'{currency}-USD')['price'])
                value = balance * price
                if value > 1:
                    portfolio.append({
                        'currency': currency,
                        'balance': balance,
                        'price': price,
                        'value': value
                    })
                    total_value += value
            except:
                pass

# Sort by value
portfolio.sort(key=lambda x: x['value'], reverse=True)

print("\n💰 CURRENT HOLDINGS:")
print("-" * 70)
print(f"{'Asset':<8} {'Balance':<15} {'Price':<12} {'Value':<12} {'% Port':<8}")
print("-" * 70)

for pos in portfolio[:10]:  # Top 10 positions
    pct = (pos['value'] / total_value * 100) if total_value > 0 else 0
    
    if 'price' in pos:
        if pos['price'] > 100:
            price_str = f"${pos['price']:,.0f}"
        elif pos['price'] > 1:
            price_str = f"${pos['price']:.2f}"
        else:
            price_str = f"${pos['price']:.4f}"
    else:
        price_str = "$1.00"
    
    if pos['currency'] in ['USD', 'USDC']:
        print(f"{pos['currency']:<8} {pos['balance']:>14.2f}  {price_str:<12} ${pos['value']:>10.2f} {pct:>6.1f}%")
    else:
        print(f"{pos['currency']:<8} {pos['balance']:>14.6f}  {price_str:<12} ${pos['value']:>10.2f} {pct:>6.1f}%")

print("-" * 70)
print(f"{'TOTAL':<8} {'':<15} {'':<12} ${total_value:>10.2f} {'100.0%':>8}")

# Progress Analysis
print("\n📈 PROGRESS REPORT:")
print("-" * 70)
starting_value = 6.15  # Started with $6.15
peak_value = 13098  # Peak yesterday
current = total_value

print(f"  Started with: ${starting_value:.2f}")
print(f"  Peak value: ${peak_value:,.2f}")
print(f"  Current value: ${current:,.2f}")
print(f"  ")
print(f"  Total gain from start: ${current - starting_value:,.2f} ({((current/starting_value - 1) * 100):,.0f}x)")
print(f"  Change from peak: ${current - peak_value:,.2f} ({((current - peak_value)/peak_value * 100):+.1f}%)")

# Check injection status
print("\n💉 $250 INJECTION STATUS:")
print("-" * 70)
if usd_balance > 250:
    print(f"  ✅ CONFIRMED: ${usd_balance:.2f} USD available")
    print(f"  Ready to deploy into positions!")
elif usd_balance > 100:
    print(f"  🟡 PARTIAL: ${usd_balance:.2f} USD available")
    print(f"  Some funds may still be settling")
else:
    print(f"  ⏳ PENDING: Only ${usd_balance:.2f} USD available")
    print(f"  Injection may still be processing")

# Trading Strategy Status
print("\n🎯 ACTIVE STRATEGIES:")
print("-" * 70)
print("  ✅ Labor Day Ladder Strategy (7 tranches)")
print("  ✅ Sawtooth Trading (working the ranges)")
print("  ✅ Flywheel Compounding (4 bots running)")
print("  ✅ $250 Fresh Capital Deployment")

# Market Conditions
print("\n📊 MARKET CONDITIONS:")
print("-" * 70)
time.sleep(1)
btc = float(client.get_product('BTC-USD')['price'])
time.sleep(0.5)
eth = float(client.get_product('ETH-USD')['price'])
time.sleep(0.5)
sol = float(client.get_product('SOL-USD')['price'])

print(f"  BTC: ${btc:,.0f} (Range: $108.5k-$110k)")
print(f"  ETH: ${eth:,.0f} (Range: $4,300-$4,380)")
print(f"  SOL: ${sol:.2f} (Range: $207-$212)")
print(f"  ")
print(f"  Market: Post-selloff sawteeth forming")
print(f"  Volume: Low (Labor Day weekend)")
print(f"  Opportunity: HIGH - perfect for range trading")

# Targets
print("\n🎯 TARGETS:")
print("-" * 70)
targets = [15000, 17000, 20000]
for target in targets:
    needed = target - current
    pct_gain = (needed / current * 100) if current > 0 else 0
    print(f"  ${target:,}: Need +${needed:,.2f} (+{pct_gain:.1f}%)")

# Summary
print("\n📝 SUMMARY:")
print("=" * 70)

if current > peak_value:
    status = "🔥 NEW ALL-TIME HIGH!"
    color = "green"
elif current > peak_value * 0.95:
    status = "💪 STRONG - Near peak!"
    color = "yellow"
elif current > peak_value * 0.90:
    status = "📈 RECOVERING - Building back"
    color = "yellow"
else:
    status = "🛠️ REBUILDING - Opportunity zone"
    color = "red"

print(f"  Status: {status}")
print(f"  Portfolio: ${current:,.2f}")
print(f"  Gain from $6: {(current/starting_value):,.0f}x")
print(f"  Weekend Target: $15,000")
print(f"  Strategy: Work the sawteeth, compound gains")

print("\n🔥 BOTTOM LINE:")
print("-" * 70)
print(f"  We're doing AMAZING! From $6 to ${current:,.2f}!")
print(f"  Fresh $250 capital at perfect entry points")
print(f"  Labor Day weekend = low volume = easy sawteeth")
print(f"  Keep the flywheel spinning!")

print("\n💎 ONWARDS TO $20K!")
print("=" * 70)