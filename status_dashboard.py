#!/usr/bin/env python3
"""
📊 TRADING ARMY STATUS DASHBOARD
Shows all active bots and their status
"""

import subprocess
import json
from datetime import datetime
from coinbase.rest import RESTClient

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                      📊 TRADING ARMY STATUS DASHBOARD                     ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

# Check portfolio
try:
    config = json.load(open('/home/dereadi/.coinbase_config.json'))
    key = config['api_key'].split('/')[-1]
    client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=3)
    
    total = 0
    accounts = client.get_accounts()['accounts']
    for a in accounts:
        balance = float(a['available_balance']['value'])
        if a['currency'] == 'USD':
            total += balance
        elif balance > 0.001:
            try:
                ticker = client.get_product(f"{a['currency']}-USD")
                price = float(ticker.get('price', 0))
                total += balance * price
            except:
                pass
    
    print(f"💰 PORTFOLIO: ${total:.2f}")
    change = total - 43.53
    print(f"   Change from start: ${change:+.2f} ({(change/43.53*100):+.1f}%)")
except:
    print("💰 PORTFOLIO: Unable to fetch")

print("\n" + "="*60)

# Check all running bots
result = subprocess.run(
    "ps aux | grep -E 'delta|gamma|theta|vega|rho|fission|bollinger|solar|flywheel|trailing|crawdad|specialist' | grep python | grep -v grep",
    shell=True,
    capture_output=True,
    text=True
)

if result.stdout:
    lines = result.stdout.strip().split('\n')
    print(f"🤖 ACTIVE BOTS: {len(lines)}")
    print("\n📊 BREAKDOWN:")
    
    # Count bot types
    greeks = 0
    crawdads = 0
    specialists = 0
    others = 0
    
    bot_list = []
    
    for line in lines:
        parts = line.split()
        if len(parts) > 10:
            script = parts[11] if len(parts) > 11 else parts[10]
            pid = parts[1]
            
            if 'greek' in script.lower():
                greeks += 1
                name = script.split('/')[-1].replace('.py', '').replace('_', ' ').title()
                bot_list.append(f"  🏛️ {name} (PID: {pid})")
            elif 'crawdad' in script.lower():
                crawdads += 1
                name = script.split('/')[-1].replace('.py', '').replace('_', ' ').title()
                bot_list.append(f"  🦀 {name} (PID: {pid})")
            elif 'specialist' in script.lower():
                specialists += 1
                name = script.split('/')[-1].replace('.py', '').replace('_', ' ').title()
                bot_list.append(f"  🎯 {name} (PID: {pid})")
            else:
                others += 1
                name = script.split('/')[-1].replace('.py', '').replace('_', ' ').title()
                bot_list.append(f"  🔧 {name} (PID: {pid})")
    
    print(f"\n🏛️ Greeks: {greeks}")
    print(f"🦀 Crawdads: {crawdads}")
    print(f"🎯 Specialists: {specialists}")
    print(f"🔧 Others: {others}")
    
    print("\n📋 ACTIVE BOTS:")
    for bot in bot_list[:15]:  # Show first 15
        print(bot)
    
    if len(bot_list) > 15:
        print(f"  ... and {len(bot_list) - 15} more")

print("\n" + "="*60)
print("📈 MARKET CONDITIONS:")

# Quick market check
for coin in ['BTC', 'ETH', 'SOL']:
    try:
        ticker = client.get_product(f'{coin}-USD')
        price = float(ticker.get('price', 0))
        print(f"  {coin}: ${price:,.2f}")
    except:
        pass

print("\n" + "="*60)
print("🎯 ASSESSMENT:")

if total > 43.53:
    print("✅ WINNING - Bots are generating profits!")
elif total == 43.53:
    print("⏳ POSITIONING - Bots scanning for opportunities")
else:
    print("🛡️ DEFENDING - Managing correction")

print("\n💡 RECOMMENDATIONS:")
print("1. Fix crashed bots (Fission, Rho)")
print("2. Check API rate limits")
print("3. Consider more aggressive settings")
print("4. Monitor for breakout signals")

print(f"\nTimestamp: {datetime.now().strftime('%H:%M:%S')}")