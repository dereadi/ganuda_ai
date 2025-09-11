#!/usr/bin/env python3
"""
🏛️ THE GREEKS - Elite Trading Force Monitor
Named after the options Greeks: Delta, Gamma, Theta, Vega, Rho
Each specialist embodies the spirit of their Greek letter
"""

import json
import subprocess
import time
from datetime import datetime

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                        🏛️ THE GREEKS MONITOR 🏛️                          ║
║                    Delta, Gamma, Theta, Vega, Rho                         ║
║                   "Ancient Wisdom, Modern Markets"                        ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

# Map specialists to Greek letters
THE_GREEKS = {
    "Delta (Δ)": {
        "name": "Gap Specialist",
        "description": "Rate of change - gaps represent sudden deltas",
        "pid_file": "gap_specialist",
        "symbol": "Δ"
    },
    "Gamma (Γ)": {
        "name": "Trend Specialist", 
        "description": "Acceleration - trends show momentum acceleration",
        "pid_file": "trend_specialist",
        "symbol": "Γ"
    },
    "Theta (Θ)": {
        "name": "Volatility Specialist",
        "description": "Time decay - volatility decays over time",
        "pid_file": "volatility_specialist",
        "symbol": "Θ"
    },
    "Vega (ν)": {
        "name": "Breakout Specialist",
        "description": "Volatility sensitivity - breakouts from vol expansion",
        "pid_file": "breakout_specialist",
        "symbol": "ν"
    },
    "Rho (ρ)": {
        "name": "Mean Reversion Specialist",
        "description": "Rate sensitivity - reversion to interest rate mean",
        "pid_file": "mean_reversion_specialist",
        "symbol": "ρ"
    }
}

def check_greek_status(greek_name, info):
    """Check if a Greek is still running"""
    try:
        # Check process
        result = subprocess.run(
            f"ps aux | grep {info['pid_file']}.py | grep -v grep | head -1",
            shell=True,
            capture_output=True,
            text=True
        )
        
        if result.stdout:
            # Extract PID
            pid = result.stdout.split()[1]
            
            # Check recent log activity
            log_result = subprocess.run(
                f"tail -5 {info['pid_file']}.log 2>/dev/null",
                shell=True,
                capture_output=True,
                text=True
            )
            
            recent_activity = "No recent activity"
            if log_result.stdout:
                lines = log_result.stdout.strip().split('\n')
                for line in reversed(lines):
                    if any(keyword in line for keyword in ["BUY", "SELL", "FADE", "BREAKOUT", "TREND", "VOL", "REVERT"]):
                        recent_activity = line[:80]  # Truncate long lines
                        break
            
            return {
                "status": "ACTIVE",
                "pid": pid,
                "activity": recent_activity
            }
    except:
        pass
    
    return {
        "status": "INACTIVE",
        "pid": None,
        "activity": "Not running"
    }

def display_greeks_status():
    """Display status of all Greeks"""
    print("\n🏛️ THE GREEKS - CURRENT STATUS")
    print("=" * 60)
    
    active_count = 0
    trade_count = 0
    
    for greek_name, info in THE_GREEKS.items():
        status = check_greek_status(greek_name, info)
        
        symbol = info['symbol']
        if status['status'] == 'ACTIVE':
            active_count += 1
            status_icon = "✅"
            
            # Count trades in activity
            if any(word in status['activity'] for word in ['BUY', 'SELL']):
                trade_count += 1
        else:
            status_icon = "❌"
        
        print(f"\n{symbol} {greek_name}:")
        print(f"   Status: {status_icon} {status['status']}")
        if status['pid']:
            print(f"   PID: {status['pid']}")
        print(f"   Mission: {info['description']}")
        print(f"   Activity: {status['activity']}")
    
    print("\n" + "="*60)
    print(f"📊 SUMMARY:")
    print(f"   Active Greeks: {active_count}/5")
    print(f"   Recent Trades: {trade_count}")
    
    return active_count, trade_count

def check_combined_performance():
    """Check combined trading performance"""
    script = '''
import json
from coinbase.rest import RESTClient

config = json.load(open("/home/dereadi/.coinbase_config.json"))
key = config["api_key"].split("/")[-1]
client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=3)

try:
    total = 0
    accounts = client.get_accounts()["accounts"]
    
    for a in accounts:
        balance = float(a["available_balance"]["value"])
        if a["currency"] == "USD":
            total += balance
        elif balance > 0.001:
            try:
                ticker = client.get_product(f"{a['currency']}-USD")
                price = float(ticker.get("price", 0))
                total += balance * price
            except:
                pass
                
    print(f"{total:.2f}")
except:
    print("0")
'''
    
    try:
        with open("/tmp/check_portfolio.py", "w") as f:
            f.write(script)
        
        result = subprocess.run(["timeout", "5", "python3", "/tmp/check_portfolio.py"],
                              capture_output=True, text=True)
        subprocess.run(["rm", "/tmp/check_portfolio.py"], capture_output=True)
        
        if result.stdout:
            return float(result.stdout.strip())
    except:
        pass
    return 0

# Main monitoring loop
print("\n🏛️ MONITORING THE GREEKS...")
print("Press Ctrl+C to stop monitoring\n")

initial_portfolio = check_combined_performance()
print(f"📊 Initial Portfolio: ${initial_portfolio:.2f}")

cycle = 0
try:
    while True:
        cycle += 1
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        print(f"\n[{timestamp}] Monitoring Cycle #{cycle}")
        print("-" * 60)
        
        active, trades = display_greeks_status()
        
        # Check portfolio every 5 cycles
        if cycle % 5 == 0:
            current_portfolio = check_combined_performance()
            change = current_portfolio - initial_portfolio
            change_pct = (change / initial_portfolio * 100) if initial_portfolio > 0 else 0
            
            print(f"\n💰 PORTFOLIO UPDATE:")
            print(f"   Current: ${current_portfolio:.2f}")
            print(f"   Change: ${change:+.2f} ({change_pct:+.2f}%)")
            
            if change > 0:
                print("   🔥 The Greeks are winning!")
            elif change < 0:
                print("   ⚔️ The Greeks are battling!")
            else:
                print("   🛡️ The Greeks hold steady!")
        
        # Alert if Greeks are down
        if active < 5:
            print(f"\n⚠️ ALERT: Only {active}/5 Greeks active!")
            print("   Some warriors have fallen! Consider redeployment.")
        
        print("\n" + "="*60)
        time.sleep(60)  # Check every minute
        
except KeyboardInterrupt:
    print("\n\n🏛️ THE GREEKS MONITOR STOPPED")
    
    final_portfolio = check_combined_performance()
    total_change = final_portfolio - initial_portfolio
    
    print(f"\n📊 FINAL REPORT:")
    print(f"   Starting Portfolio: ${initial_portfolio:.2f}")
    print(f"   Final Portfolio: ${final_portfolio:.2f}")
    print(f"   Total Change: ${total_change:+.2f}")
    
    if total_change > 0:
        print("\n🏆 THE GREEKS HAVE CONQUERED!")
    else:
        print("\n⚔️ THE GREEKS FOUGHT VALIANTLY!")
    
    print("""
    
The Greeks:
Δ Delta - Master of Gaps
Γ Gamma - Rider of Trends
Θ Theta - Harvester of Volatility
ν Vega - Hunter of Breakouts
ρ Rho - Guardian of the Mean

"From ancient Greece to modern markets,
 wisdom transcends time"
 
Mitakuye Oyasin
""")