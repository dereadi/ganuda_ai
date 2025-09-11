#!/usr/bin/env python3
"""
🌏 ASIAN SESSION IMPACT ON PORTFOLIO
Real-time analysis of Asia's effect on positions
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime, timezone
import pytz

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=10)

print("🌏 ASIAN SESSION IMPACT ANALYSIS")
print("=" * 60)

# Get current Asian market status
tokyo = pytz.timezone('Asia/Tokyo')
seoul = pytz.timezone('Asia/Seoul')
singapore = pytz.timezone('Asia/Singapore')

now_utc = datetime.now(timezone.utc)
tokyo_time = now_utc.astimezone(tokyo)
seoul_time = now_utc.astimezone(seoul)

print(f"Tokyo: {tokyo_time.strftime('%H:%M')} | Seoul: {seoul_time.strftime('%H:%M')}")
print()

# Determine session phase
hour_utc = now_utc.hour
if 22 <= hour_utc or hour_utc < 7:
    session = "🔥 PEAK ASIAN SESSION"
    impact = "Maximum volatility expected"
elif 7 <= hour_utc < 10:
    session = "🌅 LATE ASIAN SESSION"
    impact = "Winding down, Europe waking"
else:
    session = "💤 ASIAN SESSION QUIET"
    impact = "Minimal Asian impact"

print(f"Status: {session}")
print(f"Impact: {impact}")
print("-" * 40)

# Check actual prices and positions
print("\n📊 PORTFOLIO POSITIONS:")

coins_to_check = ['SOL', 'ETH', 'BTC', 'DOGE']
total_value = 0

for coin in coins_to_check:
    try:
        # Get price
        ticker = client.get_product(f'{coin}-USD')
        price = float(ticker['price'])
        
        # Get balance
        accounts = client.get_accounts()
        balance = 0
        for account in accounts['accounts']:
            if account['currency'] == coin:
                balance = float(account['available_balance']['value'])
                break
        
        value = balance * price
        total_value += value
        
        if balance > 0:
            print(f"{coin}: {balance:.4f} @ ${price:,.2f} = ${value:,.2f}")
            
            # Special notes for SOL
            if coin == 'SOL' and balance > 15:
                print(f"  ⚠️ HEAVY SOL POSITION ({balance:.2f} tokens)")
                print(f"  🌏 Asian sessions often pump SOL")
                if 22 <= hour_utc or hour_utc < 7:
                    print(f"  🚀 PRIME TIME for SOL movement!")
                    
    except Exception as e:
        print(f"{coin}: Error - {str(e)[:50]}")

print(f"\nTotal crypto value: ${total_value:,.2f}")

# Get USD balance
try:
    for account in accounts['accounts']:
        if account['currency'] == 'USD':
            usd = float(account['available_balance']['value'])
            print(f"USD Cash: ${usd:,.2f}")
            if usd < 250:
                print("  ⚠️ Low liquidity for Asian volatility")
            break
except:
    pass

print("\n🎯 ASIAN SESSION STRATEGY:")
if 22 <= hour_utc or hour_utc < 7:
    print("✅ ACTIVE TRADING WINDOW")
    print("  - SOL typically sees 2-5% moves")
    print("  - Korean retail often drives altcoins")
    print("  - Watch for whale accumulation")
    print("  - Your 18.16 SOL position is well-timed")
elif 7 <= hour_utc < 10:
    print("🔄 TRANSITION PERIOD")
    print("  - Asia closing positions")
    print("  - Europe taking over")
    print("  - Expect choppiness")
else:
    print("⏳ WAITING FOR ASIA")
    print(f"  - {22 - hour_utc} hours until peak session")
    print("  - Position building time")

print("\n💡 ETH/SOL DIVERGENCE EXPLAINED:")
print("  - SOL is Asia's favorite (Korea/Japan love it)")
print("  - ETH moves more with US institutions")
print("  - Weekend + Asian session = SOL outperformance")
print("  - Your aggressive SOL buys aligned with this pattern")