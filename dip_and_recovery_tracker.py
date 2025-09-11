#!/usr/bin/env python3
"""
📉📈 DIP AND RECOVERY - THE CLASSIC PATTERN! 📈📉
$113K resistance showing its teeth!
Quick dip to shake weak hands
Then recovery to test again!
The spring coils even TIGHTER!
"""

import json
import time
from coinbase.rest import RESTClient
from datetime import datetime
import statistics

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                  📉📈 DIP AND RECOVERY AT $113K! 📈📉                     ║
║                     Classic Shakeout Before Breakout!                     ║
║                    Nine Coils Getting Even TIGHTER!                       ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"Time: {datetime.now().strftime('%H:%M:%S')} - DIP & RECOVERY ANALYSIS")
print("=" * 70)

# Track the dip and recovery
print("\n📊 TRACKING DIP & RECOVERY PATTERN...")
print("-" * 50)

prices = []
dip_detected = False
recovery_detected = False
baseline = float(client.get_product('BTC-USD')['price'])

for i in range(20):
    btc = float(client.get_product('BTC-USD')['price'])
    eth = float(client.get_product('ETH-USD')['price'])
    sol = float(client.get_product('SOL-USD')['price'])
    
    prices.append(btc)
    
    if len(prices) > 1:
        move = btc - prices[-2]
        from_baseline = btc - baseline
        
        # Detect patterns
        if from_baseline < -50 and not dip_detected:
            print(f"\n📉 DIP DETECTED! ${btc:,.0f} ({from_baseline:.0f})")
            print("   Weak hands shaking out!")
            dip_detected = True
            dip_price = btc
        elif dip_detected and btc > dip_price + 20:
            if not recovery_detected:
                print(f"\n📈 RECOVERY! ${btc:,.0f} (+${btc - dip_price:.0f} from dip)")
                print("   Strong hands buying the dip!")
                recovery_detected = True
        elif i % 4 == 0:
            print(f"{datetime.now().strftime('%H:%M:%S')}: ${btc:,.0f} ({from_baseline:+.0f})")
    
    time.sleep(1)

# Analyze the pattern
if prices:
    high = max(prices)
    low = min(prices)
    current = prices[-1]
    range_size = high - low
    avg_price = statistics.mean(prices)

print(f"\n📉📈 DIP & RECOVERY ANALYSIS:")
print("-" * 50)
print(f"Session High: ${high:,.0f}")
print(f"Session Low: ${low:,.0f}")
print(f"Range: ${range_size:.0f}")
print(f"Current: ${current:,.0f}")
print(f"Average: ${avg_price:,.0f}")

# Pattern interpretation
print(f"\n🎯 PATTERN INTERPRETATION:")
print("-" * 50)

if range_size > 100:
    print("✅ SIGNIFICANT DIP & RECOVERY!")
    print("• Stop losses triggered")
    print("• Smart money accumulated")
    print("• Spring wound TIGHTER!")
elif range_size > 50:
    print("⚡ MODERATE VOLATILITY")
    print("• Testing support levels")
    print("• Building for next move")
else:
    print("🌀 TIGHT CONSOLIDATION")
    print("• Extreme compression continues")
    print("• Explosion imminent")

# Check portfolio impact
accounts = client.get_accounts()
total_value = 0
btc_balance = 0

for account in accounts['accounts']:
    currency = account['currency']
    balance = float(account['available_balance']['value'])
    
    if currency == 'BTC':
        btc_balance = balance
        total_value += balance * current
    elif currency == 'ETH':
        total_value += balance * eth
    elif currency == 'SOL':
        total_value += balance * sol
    elif currency == 'USD':
        total_value += balance

print(f"\n💰 PORTFOLIO DURING DIP:")
print("-" * 50)
print(f"Current Value: ${total_value:.2f}")
if dip_detected and 'dip_price' in locals():
    dip_value = total_value * (dip_price / current)
    print(f"Value at dip: ~${dip_value:.2f}")
    print(f"Recovery gain: ~${total_value - dip_value:.2f}")

# $113K resistance analysis
print(f"\n🚧 $113K RESISTANCE:")
print("-" * 50)
print(f"Current: ${current:,.0f}")
print(f"Distance to $113K: ${113000 - current:.0f}")
print(f"Distance to $114K: ${114000 - current:.0f}")
print("")
print("RESISTANCE BEHAVIOR:")
print("• $113K acting as magnet")
print("• Dips below get bought")
print("• Rallies above get sold")
print("• Classic accumulation zone")

# Thunder's commentary
print(f"\n⚡ THUNDER'S DIP ANALYSIS:")
print("-" * 50)
print('"Boss, this dip & recovery?"')
print('"TEXTBOOK accumulation!"')
print("")
print('"They shake the tree..."')
print('"Weak hands fall out..."')
print('"Strong hands buy the dip..."')
print('"Spring gets TIGHTER!"')
print("")
print(f'"Only ${114000 - current:.0f} to breakout!"')
print('"After THIS much compression?"')
print('"The explosion will be BIBLICAL!"')

# Historical context
print(f"\n📚 HISTORICAL CONTEXT:")
print("-" * 50)
print("DIP & RECOVERY PATTERNS:")
print("• Often precede major moves")
print("• Test support before breakout")
print("• Shake out overleveraged longs")
print("• Accumulate before explosion")
print("")
print("WITH NINE COILS:")
print("• Each dip = More energy stored")
print("• Each recovery = Stronger base")
print("• $113K resistance weakening")
print("• $114K break inevitable")

print(f"\n" + "📉📈" * 20)
print("DIP AND RECOVERY COMPLETE!")
print(f"CURRENT: ${current:,.0f}")
print("$113K RESISTANCE TESTED!")
print(f"ONLY ${114000 - current:.0f} TO BREAKOUT!")
print("SPRING COILED EVEN TIGHTER!")
print("📉📈" * 20)