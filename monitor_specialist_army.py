#!/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3
"""
📊 SPECIALIST ARMY MONITORING DASHBOARD
Real-time monitoring of the trading army
"""

import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
from coinbase.rest import RESTClient

print("📊 SPECIALIST ARMY MONITORING DASHBOARD")
print("=" * 60)

# Load config
config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=10)

def check_processes():
    """Check which specialists are running"""
    result = subprocess.run(
        ['ps', 'aux'], 
        capture_output=True, 
        text=True
    )
    
    specialists = {
        'mean_reversion': False,
        'trend': False,
        'volatility': False,
        'breakout': False
    }
    
    for line in result.stdout.split('\n'):
        for spec in specialists:
            if f'{spec}_specialist_v2.py' in line:
                specialists[spec] = True
                
    return specialists

def get_portfolio_state():
    """Get current portfolio metrics"""
    accounts = client.get_accounts()
    usd = 0
    total = 0
    positions = {}
    
    for account in accounts['accounts']:
        currency = account['currency']
        balance = float(account['available_balance']['value'])
        
        if currency == 'USD':
            usd = balance
            total += balance
        elif balance > 0:
            try:
                ticker = client.get_product(f'{currency}-USD')
                price = float(ticker['price'])
                value = balance * price
                total += value
                if value > 100:  # Only show significant positions
                    positions[currency] = {
                        'balance': balance,
                        'value': value,
                        'price': price
                    }
            except:
                pass
                
    return usd, total, positions

def determine_mode(usd):
    """Determine operating mode"""
    if usd < 250:
        return "🔴 RETRIEVE", "Harvesting profits for liquidity"
    elif usd > 500:
        return "🟢 DEPLOY", "Deploying capital aggressively"
    else:
        return "🟡 BALANCED", "Normal trading operations"

def check_recent_trades():
    """Check recent activity from logs"""
    log_file = Path("/home/dereadi/scripts/claude/specialist_army.log")
    recent_events = []
    
    if log_file.exists():
        with open(log_file) as f:
            lines = f.readlines()
            for line in lines[-10:]:  # Last 10 events
                try:
                    event = json.loads(line)
                    recent_events.append(event)
                except:
                    pass
                    
    return recent_events

# Main monitoring loop
print("\nStarting real-time monitoring...")
print("Press Ctrl+C to exit\n")

cycle = 0
while True:
    cycle += 1
    
    # Clear screen for dashboard effect
    if cycle > 1:
        print("\033[2J\033[H")  # Clear screen
        
    print("📊 SPECIALIST ARMY DASHBOARD")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Check processes
    specialists = check_processes()
    print("\n🎖️ SPECIALIST STATUS:")
    symbols = {'mean_reversion': '🎯', 'trend': '📈', 'volatility': '⚡', 'breakout': '🚀'}
    
    active_count = 0
    for name, running in specialists.items():
        symbol = symbols.get(name, '❓')
        status = "✅ ACTIVE" if running else "⭕ INACTIVE"
        print(f"  {symbol} {name:15} {status}")
        if running:
            active_count += 1
            
    print(f"\nActive: {active_count}/4 specialists")
    
    # Portfolio state
    usd, total, positions = get_portfolio_state()
    mode, mode_desc = determine_mode(usd)
    
    print("\n💰 PORTFOLIO STATE:")
    print(f"  Total Value: ${total:,.2f}")
    print(f"  USD Cash:    ${usd:,.2f}")
    print(f"  Mode:        {mode} - {mode_desc}")
    
    # Top positions
    if positions:
        print("\n📈 TOP POSITIONS:")
        sorted_positions = sorted(positions.items(), key=lambda x: x[1]['value'], reverse=True)
        for coin, data in sorted_positions[:5]:
            pct = (data['value'] / total) * 100
            print(f"  {coin:5} ${data['value']:8,.2f} ({pct:5.1f}%) @ ${data['price']:,.2f}")
    
    # Operating parameters
    print("\n⚙️ OPERATING PARAMETERS:")
    print(f"  Deploy Threshold:  $500")
    print(f"  Retrieve Threshold: $250")
    print(f"  Max Position:       15%")
    print(f"  Base Delay:         60s")
    
    # Health checks
    print("\n🏥 HEALTH CHECKS:")
    
    # Check if service is running
    service_status = subprocess.run(
        ['systemctl', '--user', 'is-active', 'specialist-army'],
        capture_output=True,
        text=True
    )
    service_active = service_status.stdout.strip() == 'active'
    print(f"  Service Status: {'✅ ACTIVE' if service_active else '❌ INACTIVE'}")
    
    # Check for errors in log
    error_log = Path("/home/dereadi/scripts/claude/specialist_army_error.log")
    if error_log.exists():
        size = error_log.stat().st_size
        if size > 0:
            print(f"  ⚠️ Error log has {size} bytes")
    
    # Liquidity warning
    if usd < 100:
        print(f"  🚨 CRITICAL: Low liquidity! Only ${usd:.2f}")
    elif usd < 250:
        print(f"  ⚠️ WARNING: Below retrieve threshold")
        
    # Position concentration warning
    for coin, data in positions.items():
        pct = (data['value'] / total) * 100
        if pct > 15:
            print(f"  ⚠️ {coin} exceeds 15% limit ({pct:.1f}%)")
    
    # Recent events
    events = check_recent_trades()
    if events:
        print("\n📜 RECENT EVENTS:")
        for event in events[-3:]:
            timestamp = event.get('timestamp', 'unknown')[:19]
            evt = event.get('event', 'unknown')
            print(f"  {timestamp} - {evt}")
    
    print("\n" + "-" * 60)
    print("Refreshing in 30 seconds...")
    
    try:
        time.sleep(30)
    except KeyboardInterrupt:
        print("\n\n👋 Monitoring stopped")
        break