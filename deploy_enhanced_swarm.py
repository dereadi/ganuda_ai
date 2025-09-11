#!/usr/bin/env python3
"""
🦀 DEPLOY ENHANCED SWARM - COUNCIL APPROVED
============================================
80/20 with all enhancements - PEAK ASIA IMMINENT!
"""

import json
import time
from datetime import datetime
from coinbase.rest import RESTClient
import random

print("🦀 ENHANCED SWARM DEPLOYMENT")
print("="*60)
print(f"Time: {datetime.now().strftime('%H:%M')} - T-MINUS 5 TO PEAK!")
print("Council Approved Strategy: ACTIVE")
print()

config = json.load(open('/home/dereadi/.coinbase_config.json'))
client = RESTClient(api_key=config['api_key'], api_secret=config['api_secret'])

# The 7 Quantum Crawdads
crawdads = ['Alpha', 'Beta', 'Gamma', 'Delta', 'Epsilon', 'Zeta', 'Omega']

# Get current portfolio status
accounts = client.get_accounts()
account_list = accounts.accounts if hasattr(accounts, 'accounts') else accounts

usd_balance = 0
for account in account_list:
    if account['currency'] == 'USD':
        usd_balance = float(account['available_balance']['value'])
        break

print(f"💰 CAPITAL AVAILABLE: ${usd_balance:.2f}")
print()

# COUNCIL APPROVED ALLOCATION
swarm_capital = usd_balance * 0.60  # 60% to swarmers
scout_capital = usd_balance * 0.15  # 15% to scouts
reserve_capital = usd_balance * 0.25  # 25% reserve

print("📊 COUNCIL ALLOCATION:")
print(f"  Swarm Fund: ${swarm_capital:.2f} (60%)")
print(f"  Scout Fund: ${scout_capital:.2f} (15%)")
print(f"  Reserve: ${reserve_capital:.2f} (25%)")
print()

# ANALYZE CURRENT FLOWS
print("🌊 FLOW DETECTION:")
print("-"*60)

flows = {}
for symbol in ['BTC', 'ETH', 'SOL']:
    ticker = client.get_product(f'{symbol}-USD')
    price1 = float(ticker.price if hasattr(ticker, 'price') else ticker.get('price', 0))
    
    time.sleep(0.5)
    
    ticker2 = client.get_product(f'{symbol}-USD')
    price2 = float(ticker2.price if hasattr(ticker2, 'price') else ticker2.get('price', 0))
    
    momentum = ((price2 - price1) / price1) * 100
    
    # Asia loves SOL - boost its signal
    if symbol == 'SOL':
        momentum *= 1.2  # Council wisdom: Asia session boost
    
    flows[symbol] = {
        'price': price2,
        'momentum': momentum,
        'alert': 'GREEN' if abs(momentum) < 0.5 else 'YELLOW' if abs(momentum) < 1.0 else 'RED'
    }
    
    alert_symbol = '🟢' if flows[symbol]['alert'] == 'GREEN' else '🟡' if flows[symbol]['alert'] == 'YELLOW' else '🔴'
    print(f"  {symbol}: ${price2:,.2f} | {momentum:+.4f}% | {alert_symbol} {flows[symbol]['alert']}")

# DETERMINE PRIMARY FLOW
sorted_flows = sorted(flows.items(), key=lambda x: abs(x[1]['momentum']), reverse=True)
primary = sorted_flows[0][0]
secondary = sorted_flows[1][0] if len(sorted_flows) > 1 else None

print(f"\n🎯 PRIMARY FLOW: {primary}")
print(f"🔍 SCOUT TARGET: {secondary if secondary else 'All positions'}")

# 80/20 DEPLOYMENT (5 swarmers, 2 scouts)
swarmers = crawdads[:5]  # 80% - actually 71% with 7 crawdads
scouts = crawdads[5:]     # 20% - actually 29% with 7 crawdads

print("\n🦀 SWARM ASSIGNMENT:")
print("-"*60)
print(f"  SWARMERS → {primary}: {', '.join(swarmers)}")
print(f"  SCOUTS → Secondary: {', '.join(scouts)}")

# EXECUTE SWARM TRADES
print("\n💥 EXECUTING ENHANCED SWARM:")
print("-"*60)

total_deployed = 0
trades_executed = 0

# DEPLOY SWARMERS
if swarm_capital > 10:
    swarm_size = len(swarmers)
    trade_per_swarmer = min(swarm_capital / swarm_size, 25)  # Max $25 per crawdad
    trade_per_swarmer = round(trade_per_swarmer, 2)
    
    print(f"\n🌊 SWARM ATTACK ({primary}):")
    for crawdad in swarmers:
        if trade_per_swarmer >= 1:
            try:
                print(f"  🦀 {crawdad}: SWARMING with ${trade_per_swarmer:.2f}")
                
                order = client.market_order_buy(
                    client_order_id=f"swarm_{crawdad}_{int(time.time())}",
                    product_id=f"{primary}-USD",
                    quote_size=str(trade_per_swarmer)
                )
                
                trades_executed += 1
                total_deployed += trade_per_swarmer
                time.sleep(0.2)  # Rapid deployment
                
            except Exception as e:
                print(f"    ❌ {crawdad} blocked: {str(e)[:30]}")

# DEPLOY SCOUTS
if scout_capital > 5:
    scout_size = len(scouts)
    trade_per_scout = min(scout_capital / scout_size, 15)  # Max $15 per scout
    trade_per_scout = round(trade_per_scout, 2)
    
    # Scouts go to different positions
    scout_targets = [s for s in ['BTC', 'ETH', 'SOL'] if s != primary]
    
    print(f"\n🔍 SCOUT DEPLOYMENT:")
    for i, crawdad in enumerate(scouts):
        target = scout_targets[i % len(scout_targets)]
        if trade_per_scout >= 1:
            try:
                print(f"  🦀 {crawdad}: SCOUTING {target} with ${trade_per_scout:.2f}")
                
                order = client.market_order_buy(
                    client_order_id=f"scout_{crawdad}_{int(time.time())}",
                    product_id=f"{target}-USD",
                    quote_size=str(trade_per_scout)
                )
                
                trades_executed += 1
                total_deployed += trade_per_scout
                time.sleep(0.2)
                
            except Exception as e:
                print(f"    ❌ {crawdad} lost: {str(e)[:30]}")

print("\n" + "="*60)
print("✅ ENHANCED SWARM DEPLOYED!")
print("-"*60)
print(f"  Trades Executed: {trades_executed}")
print(f"  Capital Deployed: ${total_deployed:.2f}")
print(f"  Reserve Maintained: ${reserve_capital:.2f}")
print(f"  Primary Flow: {primary}")
print(f"  Scouts Active: {len(scouts)}")

# ALERT LEVELS
if any(f['alert'] == 'RED' for f in flows.values()):
    print("\n🔴 RED ALERT: High volatility detected!")
    print("   Swarm ready to pivot on scout signal!")
elif any(f['alert'] == 'YELLOW' for f in flows.values()):
    print("\n🟡 YELLOW ALERT: Moderate movement")
    print("   Monitoring for pivot opportunity")
else:
    print("\n🟢 GREEN: Steady flow")
    print("   Swarm maintaining position")

print("\n⏰ NEXT ACTIONS:")
print("-"*60)
print("• 2100 (2 minutes): PEAK VOLATILITY EXPECTED")
print("• Scout rotation in 5 minutes")
print("• Monitor for RED alerts → instant pivot")
print("• Reserve ready for explosive moves")

print("\n🦀 THE ENHANCED SWARM IS ALIVE!")
print("   Council wisdom guides us...")
print("   Scouts watch, swarmers strike...")
print("   The flow becomes profit!")
print("   🦀🦀🦀 SWARM INTELLIGENCE ACTIVE! 🦀🦀🦀")