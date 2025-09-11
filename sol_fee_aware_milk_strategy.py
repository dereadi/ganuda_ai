#!/usr/bin/env python3
"""
☀️🥛 FEE-AWARE SOL MILKING STRATEGY 🥛☀️
Remember: 0.6% fees = Need bigger moves!
Batch selling for efficiency!
Only milk when it's WORTH IT!
"""

import json
from coinbase.rest import RESTClient
from datetime import datetime
import time

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=5)

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                  ☀️ FEE-AWARE SOL MILKING CALCULATOR 🥛                   ║
║                    0.6% fees = Need 1.2% round trip! 📊                    ║
║                      Batch trades for maximum profit! 💰                   ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

# Get current data
sol = client.get_product('SOL-USD')
sol_price = float(sol['price'])

accounts = client.get_accounts()
sol_balance = 0
usd_balance = 0

for account in accounts['accounts']:
    if account['currency'] == 'SOL':
        sol_balance = float(account['available_balance']['value'])
    elif account['currency'] == 'USD':
        usd_balance = float(account['available_balance']['value'])

sol_value = sol_balance * sol_price

print(f"\n📊 CURRENT POSITION:")
print("-" * 50)
print(f"SOL: {sol_balance:.4f} @ ${sol_price:.2f} = ${sol_value:.2f}")
print(f"USD: ${usd_balance:.2f}")

# Calculate fee impact
print(f"\n💸 FEE CALCULATIONS (0.6% Coinbase):")
print("-" * 50)

# Different milk amounts
milk_amounts = [
    (0.5, "Tiny milk - 0.5 SOL"),
    (1.0, "Small milk - 1 SOL"),
    (2.0, "Medium milk - 2 SOL"),
    (3.0, "Large milk - 3 SOL"),
]

for amount, description in milk_amounts:
    if amount <= sol_balance:
        gross_value = amount * sol_price
        fee = gross_value * 0.006
        net_proceeds = gross_value - fee
        
        # Calculate breakeven buy-back price
        breakeven_price = sol_price * 0.988  # Need 1.2% drop to profit
        
        print(f"\n{description}:")
        print(f"  Gross: ${gross_value:.2f}")
        print(f"  Fee: ${fee:.2f}")
        print(f"  Net: ${net_proceeds:.2f}")
        print(f"  Breakeven buyback: ${breakeven_price:.2f}")
        print(f"  Need SOL to drop: ${sol_price - breakeven_price:.2f}")

# Smart milking zones
print(f"\n🎯 SMART MILKING ZONES (Fee-Adjusted):")
print("-" * 50)
print(f"Current SOL: ${sol_price:.2f}")
print("")
print("MILK NOW IF:")
print(f"  • SOL pumped > 3% recently (was below ${sol_price * 0.97:.2f})")
print(f"  • Expecting pullback > 1.5%")
print(f"  • Need USD for other opportunities")
print("")
print("OPTIMAL MILK SIZES:")
if sol_price > 215:
    milk_size = min(2.0, sol_balance * 0.15)
    print(f"  ✅ SOL > $215: Milk {milk_size:.2f} SOL = ${milk_size * sol_price:.2f}")
elif sol_price > 210:
    milk_size = min(1.0, sol_balance * 0.075)
    print(f"  📍 SOL > $210: Consider {milk_size:.2f} SOL = ${milk_size * sol_price:.2f}")
else:
    print(f"  ❌ SOL < $210: HOLD - Wait for pump")

# Batch trading strategy
print(f"\n📦 BATCH TRADING STRATEGY:")
print("-" * 50)
print("AVOID:")
print("  ❌ Multiple small trades (fees stack up)")
print("  ❌ Milking < 0.5 SOL (fees eat profits)")
print("  ❌ Round trips < 2% moves")
print("")
print("DO THIS:")
print("  ✅ Batch milk 2-3 SOL when > $215")
print("  ✅ Wait for 3-5% pumps")
print("  ✅ Buy back only on 2%+ dips")
print("  ✅ Keep core 10+ SOL always")

# Current opportunity analysis
print(f"\n🔍 CURRENT OPPORTUNITY:")
print("-" * 50)

# Check recent high (estimate from current price)
estimated_recent_high = 213.00  # From our previous milk
pump_percent = ((sol_price - estimated_recent_high) / estimated_recent_high) * 100

if pump_percent > 2:
    print(f"✅ MILK OPPORTUNITY!")
    print(f"  SOL pumped {pump_percent:.1f}% from recent")
    optimal_milk = min(2.0, sol_balance * 0.15)
    print(f"  Recommended: Milk {optimal_milk:.2f} SOL")
    print(f"  Expected profit after fees: ${optimal_milk * sol_price * 0.994:.2f}")
elif sol_price > 213:
    print(f"📍 BORDERLINE OPPORTUNITY")
    print(f"  SOL up slightly from $213")
    print(f"  Consider small milk if expecting pullback")
else:
    print(f"❌ NOT OPTIMAL FOR MILKING")
    print(f"  Wait for pump above $215")
    print(f"  Or significant move (>3%)")

# Fee-aware execution
if sol_price > 213 and usd_balance < 100:
    print(f"\n💰 EXECUTING FEE-AWARE MILK:")
    print("-" * 50)
    
    # Calculate optimal milk amount
    milk_amount = min(1.0, sol_balance * 0.075)  # Conservative 7.5% or 1 SOL max
    
    print(f"Milking {milk_amount:.4f} SOL...")
    print(f"Expected after fees: ${milk_amount * sol_price * 0.994:.2f}")
    
    try:
        order = client.market_order_sell(
            client_order_id=f'fee_aware_milk_{int(time.time())}',
            product_id='SOL-USD',
            base_size=str(round(milk_amount, 4))
        )
        print(f"✅ Milked {milk_amount:.4f} SOL!")
        print(f"   Feed the flywheel!")
    except Exception as e:
        print(f"Note: {str(e)[:100]}")
else:
    print(f"\n⏳ WAITING FOR BETTER OPPORTUNITY")
    print(f"   Need SOL > $215 or USD < $100")

print(f"\n{'☀️' * 35}")
print("REMEMBER THE FEES!")
print("0.6% each way = 1.2% round trip!")
print("Only milk meaningful amounts!")
print("Batch trades for efficiency!")
print("🥛" * 35)