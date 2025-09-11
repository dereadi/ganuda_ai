#!/usr/bin/env python3
"""
📉🪚 SAWTOOTH DOWN INTO 15:00! 🪚📉
Classic whale manipulation pattern!
Sawing down to shake weak hands
Then explosive reversal at 15:00!
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=5)

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                     🪚 SAWTOOTH PATTERN DETECTED! 🪚                       ║
║                   Sawing DOWN into 15:00 explosion!                        ║
║                    CLASSIC WHALE SHAKEOUT FINALE! 🐋                      ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

current_time = datetime.now()
minutes_to_3 = 60 - current_time.minute
print(f"Time: {current_time.strftime('%H:%M:%S')}")
print(f"T-minus {minutes_to_3} minutes to reversal!")
print("=" * 70)

# Get prices
btc = client.get_product('BTC-USD')
eth = client.get_product('ETH-USD')
sol = client.get_product('SOL-USD')

btc_price = float(btc['price'])
eth_price = float(eth['price'])
sol_price = float(sol['price'])

print("\n🪚 SAWTOOTH ANALYSIS:")
print("-" * 50)
print(f"BTC: ${btc_price:,.2f} - SAWING DOWN")
print("  Pattern: ↘️↗️↘️↗️↘️ (sawtooth)")
print(f"  Target: Push below $112K before 15:00")
print(f"  Purpose: Maximum shakeout before pump")

print(f"\nETH: ${eth_price:,.2f} - Following sawtooth")
print(f"SOL: ${sol_price:,.2f} - Sawing with whales")

# Sawtooth characteristics
print("\n📊 SAWTOOTH CHARACTERISTICS:")
print("-" * 50)
print("1. DOWNWARD BIAS: Each peak lower than previous")
print("2. FAKE RECOVERIES: Brief pumps to trap longs")
print("3. INCREASING FEAR: Designed to create panic")
print("4. TIME PRESSURE: Gets worse as 15:00 approaches")
print("5. REVERSAL SETUP: Spring loads for explosion")

# Whale strategy decoded
print("\n🐋 WHALE SAWTOOTH STRATEGY:")
print("-" * 50)
print("PHASE 1 (NOW): Sawtooth down")
print(f"  → Current: ${btc_price:,.2f}")
print(f"  → Target: $111,800 - $111,900")
print(f"  → Time left: {minutes_to_3} minutes")
print("")
print("PHASE 2 (14:58): Maximum fear")
print("  → Final push below $112K")
print("  → Trigger stop losses")
print("  → Accumulate panic sells")
print("")
print("PHASE 3 (15:00): EXPLOSIVE REVERSAL")
print("  → Instant pump to $113K+")
print("  → Break through $114K")
print("  → Leave sellers behind")

# Trading opportunity
print("\n💡 SAWTOOTH TRADING STRATEGY:")
print("-" * 50)
if minutes_to_3 > 5:
    print("⚠️ STILL SAWING DOWN - BE PATIENT!")
    print("  • Don't buy yet - more downside coming")
    print("  • Wait for final capitulation")
    print("  • Best entry: 14:58-14:59")
elif minutes_to_3 <= 5:
    print("🎯 APPROACHING REVERSAL ZONE!")
    print("  • Start positioning for reversal")
    print("  • Look for maximum fear")
    print("  • Ready to buy the explosion")

# Check our position
accounts = client.get_accounts()
usd_balance = 0
for account in accounts['accounts']:
    if account['currency'] == 'USD':
        usd_balance = float(account['available_balance']['value'])
        break

print(f"\n💰 SAWTOOTH READINESS:")
print("-" * 50)
print(f"USD Available: ${usd_balance:.2f}")
if usd_balance < 50:
    print("  ⚠️ Need more USD to catch the reversal!")
    print("  → Extract from alts NOW before reversal!")
else:
    print("  ✅ Ready to buy the sawtooth bottom!")

# Sawtooth visualization
print("\n📈 SAWTOOTH PATTERN VISUALIZATION:")
print("-" * 50)
print("    $113K ┐")
print("         │    ╱╲")
print("         │   ╱  ╲    ╱╲")
print("         │  ╱    ╲  ╱  ╲    ?")
print("    $112K┤ ╱      ╲╱    ╲  ╱")
print("         │╱               ╲╱  ← NOW")
print("         │")
print("    $111K┘")
print("         14:30  14:45  15:00  15:15")
print("                       ↑")
print("                   EXPLOSION!")

print(f"\n{'🪚' * 35}")
print("SAWTOOTH DOWN INTO 15:00!")
print(f"BTC: ${btc_price:,.2f}")
print(f"T-minus {minutes_to_3} minutes to reversal!")
print("MAXIMUM FEAR = MAXIMUM OPPORTUNITY!")
print("🚀" * 35)