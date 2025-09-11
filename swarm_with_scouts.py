#!/usr/bin/env python3
"""
🦀 INTELLIGENT SWARM WITH SCOUTS
=================================
80% ride the main current, 20% find new flows
The swarm moves like a school of fish!
"""

import json
import time
from datetime import datetime
from coinbase.rest import RESTClient

print("🦀 QUANTUM SWARM STRATEGY")
print("="*60)
print(f"Time: {datetime.now().strftime('%H:%M')} - PEAK ASIA!")
print()

config = json.load(open('/home/dereadi/.coinbase_config.json'))
client = RESTClient(api_key=config['api_key'], api_secret=config['api_secret'])

# The 7 Quantum Crawdads
crawdads = {
    'Alpha': {'role': None, 'position': None, 'earnings': 0},
    'Beta': {'role': None, 'position': None, 'earnings': 0},
    'Gamma': {'role': None, 'position': None, 'earnings': 0},
    'Delta': {'role': None, 'position': None, 'earnings': 0},
    'Epsilon': {'role': None, 'position': None, 'earnings': 0},
    'Zeta': {'role': None, 'position': None, 'earnings': 0},
    'Omega': {'role': None, 'position': None, 'earnings': 0}
}

print("🔍 ANALYZING CURRENTS...")
print("-"*60)

# Check all three assets for momentum
flows = {}
for symbol in ['BTC', 'ETH', 'SOL']:
    ticker = client.get_product(f'{symbol}-USD')
    price = float(ticker.price if hasattr(ticker, 'price') else ticker.get('price', 0))
    
    # Wait and check again for momentum
    time.sleep(1)
    ticker2 = client.get_product(f'{symbol}-USD')
    price2 = float(ticker2.price if hasattr(ticker2, 'price') else ticker2.get('price', 0))
    
    momentum = ((price2 - price) / price) * 100
    flows[symbol] = {
        'price': price2,
        'momentum': momentum,
        'direction': 'UP' if momentum > 0 else 'DOWN' if momentum < 0 else 'FLAT'
    }
    
    print(f"  {symbol}: ${price2:,.2f} | Momentum: {momentum:+.4f}% | {flows[symbol]['direction']}")

# Find primary and secondary flows
sorted_flows = sorted(flows.items(), key=lambda x: abs(x[1]['momentum']), reverse=True)
primary_flow = sorted_flows[0][0] if abs(sorted_flows[0][1]['momentum']) > 0.01 else None
secondary_flows = [f[0] for f in sorted_flows[1:] if abs(f[1]['momentum']) > 0.005]

print("\n🌊 FLOW ANALYSIS:")
print("-"*60)
if primary_flow:
    print(f"  PRIMARY CURRENT: {primary_flow} ({flows[primary_flow]['momentum']:+.4f}%)")
else:
    print("  PRIMARY CURRENT: None detected")

if secondary_flows:
    print(f"  SECONDARY CURRENTS: {', '.join(secondary_flows)}")
else:
    print("  SECONDARY CURRENTS: None significant")

# DEPLOY THE SWARM!
print("\n🦀 SWARM DEPLOYMENT:")
print("-"*60)

if primary_flow:
    # 80% swarm (5-6 crawdads)
    swarm_size = 5
    scout_size = 2
    
    crawdad_names = list(crawdads.keys())
    
    # Assign swarmers to primary flow
    print(f"\n  🌊 MAIN SWARM → {primary_flow}:")
    for i in range(swarm_size):
        name = crawdad_names[i]
        crawdads[name]['role'] = 'SWARMER'
        crawdads[name]['position'] = primary_flow
        print(f"    🦀 {name}: Swarming {primary_flow}")
    
    # Assign scouts to secondary positions
    print(f"\n  🔍 SCOUTS → Secondary currents:")
    scout_positions = [s for s in ['BTC', 'ETH', 'SOL'] if s != primary_flow]
    for i in range(scout_size):
        name = crawdad_names[swarm_size + i]
        crawdads[name]['role'] = 'SCOUT'
        crawdads[name]['position'] = scout_positions[i % len(scout_positions)]
        print(f"    🦀 {name}: Scouting {crawdads[name]['position']}")
    
    # Execute swarm trades
    print("\n💰 EXECUTING SWARM STRATEGY:")
    print("-"*60)
    
    # Get USD balance
    accounts = client.get_accounts()
    account_list = accounts.accounts if hasattr(accounts, 'accounts') else accounts
    
    usd_balance = 0
    for account in account_list:
        if account['currency'] == 'USD':
            usd_balance = float(account['available_balance']['value'])
            break
    
    print(f"  USD Available: ${usd_balance:.2f}")
    
    # Swarmers get 80% of capital
    swarm_capital = usd_balance * 0.6  # Being conservative
    scout_capital = usd_balance * 0.15
    
    trades_executed = 0
    total_deployed = 0
    
    # Deploy swarmers
    if swarm_capital > 5:
        trade_size = min(swarm_capital / swarm_size, 20)  # Max $20 per crawdad
        trade_size = round(trade_size, 2)
        
        print(f"\n  🌊 SWARM TRADES ({primary_flow}):")
        for name, crawdad in crawdads.items():
            if crawdad['role'] == 'SWARMER' and trade_size >= 1:
                try:
                    print(f"    {name}: Deploying ${trade_size:.2f}")
                    order = client.market_order_buy(
                        client_order_id=f"swarm_{name}_{int(time.time())}",
                        product_id=f"{primary_flow}-USD",
                        quote_size=str(trade_size)
                    )
                    trades_executed += 1
                    total_deployed += trade_size
                    time.sleep(0.3)
                except Exception as e:
                    print(f"      ❌ Failed: {str(e)[:30]}")
    
    # Deploy scouts
    if scout_capital > 2:
        scout_trade_size = min(scout_capital / scout_size, 10)
        scout_trade_size = round(scout_trade_size, 2)
        
        print(f"\n  🔍 SCOUT TRADES:")
        for name, crawdad in crawdads.items():
            if crawdad['role'] == 'SCOUT' and scout_trade_size >= 1:
                try:
                    print(f"    {name}: Scouting ${scout_trade_size:.2f} in {crawdad['position']}")
                    order = client.market_order_buy(
                        client_order_id=f"scout_{name}_{int(time.time())}",
                        product_id=f"{crawdad['position']}-USD",
                        quote_size=str(scout_trade_size)
                    )
                    trades_executed += 1
                    total_deployed += scout_trade_size
                    time.sleep(0.3)
                except Exception as e:
                    print(f"      ❌ Failed: {str(e)[:30]}")
    
    print(f"\n✅ SWARM DEPLOYMENT COMPLETE!")
    print(f"   Trades: {trades_executed}")
    print(f"   Total Deployed: ${total_deployed:.2f}")
    print(f"   Primary Flow: {primary_flow}")
    print(f"   Scouts Active: {scout_size}")
    
else:
    print("  ⏸️ No strong current detected")
    print("  Crawdads remain distributed")
    print("  Waiting for flow to develop")

print("\n✨ SWARM INTELLIGENCE:")
print("-"*60)
print("• 80% ride the strongest current")
print("• 20% scout for new opportunities")
print("• When scouts find gold, swarm pivots")
print("• The swarm flows like water to profit!")
print()
print("🦀 THE QUANTUM SWARM IS LEARNING THE FLOW! 🦀")