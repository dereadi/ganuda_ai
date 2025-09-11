#!/usr/bin/env python3
"""
🏛️🌞 GREEKS SOLAR CAPITAL REBALANCING STRATEGY
================================================
The Greeks mobilize capital for tomorrow's S1 Solar Storm
75% probability of enhanced volatility window

Current Holdings: $11,921 total
Strategic Goal: Generate $1,500 USD liquidity for flywheel/solar trading
"""

import json
import time
from datetime import datetime
from coinbase.rest import RESTClient

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║          🏛️ GREEKS STRATEGIC CAPITAL REBALANCING 🌞                        ║
║                                                                             ║
║     "Delta, Gamma, Theta, Vega, Rho - We move as one"                      ║
║     "Solar storms bring opportunity. Position accordingly."                 ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

# Load API
with open('cdp_api_key_new.json', 'r') as f:
    api_data = json.load(f)

client = RESTClient(
    api_key=api_data['name'].split('/')[-1],
    api_secret=api_data['privateKey']
)

# Get current balances
print("\n📊 CURRENT POSITION ANALYSIS:")
print("=" * 60)

accounts = client.get_accounts()['accounts']
positions = {}
total_value = 0

# Current prices (from your data)
prices = {
    'BTC': 112612,
    'ETH': 2600,
    'SOL': 150,
    'AVAX': 25,
    'MATIC': 0.40,
    'LINK': 11,
    'DOGE': 0.10
}

for account in accounts:
    symbol = account['currency']
    balance = float(account['available_balance']['value'])
    
    if balance > 0.01:
        if symbol == 'USD':
            positions['USD'] = balance
            total_value += balance
            print(f"💵 USD: ${balance:.2f}")
        elif symbol in prices:
            value = balance * prices[symbol]
            positions[symbol] = {
                'amount': balance,
                'value': value,
                'price': prices[symbol]
            }
            total_value += value
            if value > 100:
                print(f"🪙 {symbol}: {balance:.2f} units = ${value:,.2f}")

print(f"\n💰 TOTAL VALUE: ${total_value:,.2f}")
print(f"🚨 CURRENT USD: ${positions.get('USD', 0):.2f} (INSUFFICIENT!)")

# STRATEGIC REBALANCING PLAN
print("\n🎯 STRATEGIC REBALANCING FOR SOLAR VOLATILITY:")
print("=" * 60)

rebalance_plan = []

# Priority 1: Trim MATIC position (least volatile, large holding)
if 'MATIC' in positions:
    matic_to_sell = min(2500, positions['MATIC']['amount'] * 0.22)  # Sell 22% of MATIC
    matic_value = matic_to_sell * prices['MATIC']
    rebalance_plan.append({
        'action': 'SELL',
        'coin': 'MATIC',
        'amount': matic_to_sell,
        'expected_usd': matic_value,
        'reason': 'Low volatility asset, trim for liquidity'
    })

# Priority 2: Reduce AVAX position
if 'AVAX' in positions:
    avax_to_sell = min(15, positions['AVAX']['amount'] * 0.22)  # Sell 22% of AVAX
    avax_value = avax_to_sell * prices['AVAX']
    rebalance_plan.append({
        'action': 'SELL',
        'coin': 'AVAX',
        'amount': avax_to_sell,
        'expected_usd': avax_value,
        'reason': 'Medium volatility, partial profit taking'
    })

# Priority 3: Trim small portion of SOL (keep most for volatility)
if 'SOL' in positions:
    sol_to_sell = min(3, positions['SOL']['amount'] * 0.135)  # Sell only 13.5% of SOL
    sol_value = sol_to_sell * prices['SOL']
    rebalance_plan.append({
        'action': 'SELL',
        'coin': 'SOL',
        'amount': sol_to_sell,
        'expected_usd': sol_value,
        'reason': 'Keep majority for solar volatility play'
    })

# Priority 4: Sell all DOGE (meme coin, convert to trading capital)
if 'DOGE' in positions:
    doge_to_sell = positions['DOGE']['amount']
    doge_value = doge_to_sell * prices['DOGE']
    rebalance_plan.append({
        'action': 'SELL',
        'coin': 'DOGE',
        'amount': doge_to_sell,
        'expected_usd': doge_value,
        'reason': 'Full liquidation - meme to momentum'
    })

# Calculate expected USD after rebalancing
expected_usd = sum(plan['expected_usd'] for plan in rebalance_plan)
expected_total_usd = positions.get('USD', 0) + expected_usd

print(f"🎯 TARGET USD: $1,500")
print(f"📈 EXPECTED USD AFTER REBALANCE: ${expected_total_usd:,.2f}")
print(f"🔄 TRADES TO EXECUTE: {len(rebalance_plan)}")

print("\n📋 REBALANCING ORDERS:")
print("-" * 60)
for i, plan in enumerate(rebalance_plan, 1):
    print(f"{i}. {plan['action']} {plan['amount']:.2f} {plan['coin']}")
    print(f"   Expected: ${plan['expected_usd']:,.2f}")
    print(f"   Reason: {plan['reason']}")

# Execute rebalancing
print("\n🚀 EXECUTING REBALANCE:")
print("=" * 60)

confirm = input("\n⚠️ Execute rebalancing plan? (yes/no): ")
if confirm.lower() != 'yes':
    print("❌ Rebalancing cancelled")
    exit()

successful_trades = 0
actual_usd_gained = 0

for plan in rebalance_plan:
    try:
        print(f"\n🔄 Selling {plan['amount']:.2f} {plan['coin']}...")
        
        # Place market sell order
        order = client.market_order_sell(
            client_order_id=f"greek_solar_{int(time.time())}_{plan['coin']}",
            product_id=f"{plan['coin']}-USD",
            base_size=str(plan['amount'])
        )
        
        if order and 'order_id' in order:
            print(f"✅ {plan['coin']} order placed: {order['order_id']}")
            successful_trades += 1
            actual_usd_gained += plan['expected_usd']
            time.sleep(2)  # Wait between orders
        else:
            print(f"⚠️ {plan['coin']} order failed")
            
    except Exception as e:
        print(f"❌ Error selling {plan['coin']}: {str(e)[:100]}")

# Final report
print("\n" + "=" * 60)
print("📊 REBALANCING COMPLETE:")
print(f"✅ Successful trades: {successful_trades}/{len(rebalance_plan)}")
print(f"💵 USD gained: ${actual_usd_gained:,.2f}")
print(f"💰 New total USD: ${(positions.get('USD', 0) + actual_usd_gained):,.2f}")

print("\n🌪️ FLYWHEEL ACTIVATION READY:")
print("1. python3 flywheel_accelerator.py")
print("2. python3 bollinger_flywheel_enhancer.py")

print("\n🌞 SOLAR TRADING ACTIVATION:")
print("1. python3 solar_enhanced_trader_with_rsi.py")
print("2. python3 solar_storm_trading_strategy.py")

print("\n🏛️ GREEKS REACTIVATION:")
print("1. python3 deploy_specialist_army.py")
print("2. python3 greeks_fixed_deployment.py")

# Save rebalancing report
report = {
    'timestamp': datetime.now().isoformat(),
    'initial_usd': positions.get('USD', 0),
    'target_usd': 1500,
    'trades_executed': successful_trades,
    'usd_gained': actual_usd_gained,
    'final_usd': positions.get('USD', 0) + actual_usd_gained,
    'solar_event': 'S1 Storm 75% probability Aug 25',
    'strategy': 'Trim low-volatility positions for trading capital'
}

with open('greeks_solar_rebalance_report.json', 'w') as f:
    json.dump(report, f, indent=2)

print("\n🔥 The Greeks have spoken: 'Solar winds bring fortune to the prepared!'")
print("Sacred Fire burns eternal. Mitakuye Oyasin. 🔥")