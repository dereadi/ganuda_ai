#!/usr/bin/env python3
"""
📊 LIQUIDITY MONITOR DASHBOARD
Real-time monitoring of liquidity flow with Greeks & Flywheel
"""
import json
import time
import subprocess
from datetime import datetime
from coinbase.rest import RESTClient

def get_system_status():
    """Check all trading systems status"""
    status = {
        'greeks': 0,
        'flywheel': 0,
        'solar': 0,
        'crawdads': 0,
        'total': 0
    }
    
    # Count running processes
    result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
    for line in result.stdout.split('\n'):
        if 'specialist' in line and 'python' in line:
            status['greeks'] += 1
        elif 'flywheel' in line and 'python' in line:
            status['flywheel'] += 1
        elif 'solar' in line and 'python' in line:
            status['solar'] += 1
        elif 'crawdad' in line and 'python' in line:
            status['crawdads'] += 1
    
    status['total'] = sum([status['greeks'], status['flywheel'], 
                           status['solar'], status['crawdads']])
    return status

def monitor_liquidity():
    """Monitor liquidity in real-time"""
    with open('cdp_api_key_new.json', 'r') as f:
        api_data = json.load(f)
    
    client = RESTClient(
        api_key=api_data['name'].split('/')[-1],
        api_secret=api_data['privateKey']
    )
    
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                  💰 LIQUIDITY FLOW MONITOR DASHBOARD 💰                     ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)
    
    last_usd = 0
    doge_milked_total = 0
    
    while True:
        # Get current USD
        accounts = client.get_accounts()['accounts']
        current_usd = 0
        doge_balance = 0
        
        for account in accounts:
            if account['currency'] == 'USD':
                current_usd = float(account['available_balance']['value'])
            elif account['currency'] == 'DOGE':
                doge_balance = float(account['available_balance']['value'])
        
        # Get system status
        systems = get_system_status()
        
        # Calculate changes
        usd_change = current_usd - last_usd if last_usd > 0 else 0
        
        # Clear screen and display
        print("\033[2J\033[H")  # Clear screen
        print(f"⏰ {datetime.now().strftime('%H:%M:%S')} | LIQUIDITY MONITOR")
        print("=" * 60)
        
        # USD Status
        print(f"\n💵 USD BALANCE: ${current_usd:.2f}")
        if usd_change != 0:
            symbol = "📈" if usd_change > 0 else "📉"
            print(f"   {symbol} Change: ${usd_change:+.2f}")
        
        # Critical warnings
        if current_usd < 50:
            print("   🚨 CRITICAL: USD TOO LOW FOR TRADING!")
        elif current_usd < 200:
            print("   ⚠️ WARNING: Low liquidity")
        else:
            print("   ✅ Liquidity healthy")
        
        # DOGE Status
        print(f"\n🐕 DOGE Available: {doge_balance:,.0f}")
        print(f"   Milk potential: ${doge_balance * 0.10:.2f}")
        
        # Systems Status
        print(f"\n🤖 ACTIVE SYSTEMS: {systems['total']}")
        print(f"   Greeks: {systems['greeks']} | Flywheel: {systems['flywheel']}")
        print(f"   Solar: {systems['solar']} | Crawdads: {systems['crawdads']}")
        
        # Consumption Rate
        if systems['total'] > 0:
            burn_rate = systems['total'] * 10  # Estimate $10/min per system
            print(f"\n🔥 USD BURN RATE: ~${burn_rate}/min")
            if current_usd > 0:
                minutes_left = current_usd / burn_rate
                print(f"   Time until empty: {minutes_left:.1f} minutes")
        
        # Recommendations
        print("\n📋 RECOMMENDATIONS:")
        if current_usd < 100 and doge_balance > 1000:
            print("   → MILK DOGE NOW! (2000 units)")
        if current_usd > 2000:
            print("   → Deploy excess to positions")
        if systems['total'] < 10:
            print("   → Some systems may be down")
        
        print("\n" + "-" * 60)
        print("Press Ctrl+C to exit | Updates every 30 seconds")
        
        last_usd = current_usd
        time.sleep(30)

if __name__ == "__main__":
    try:
        monitor_liquidity()
    except KeyboardInterrupt:
        print("\n\n🛑 Monitor stopped")
