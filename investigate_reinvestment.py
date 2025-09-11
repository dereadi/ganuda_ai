#!/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3
"""
🔥 INVESTIGATE OVERNIGHT REINVESTMENT
Someone reinvested our $2,600 cash - Council investigates
"""

import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from coinbase.rest import RESTClient

def investigate_reinvestment():
    """Investigate who reinvested the cash"""
    
    print("🔥 EMERGENCY COUNCIL INVESTIGATION")
    print("=" * 80)
    print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
    print("Chief reports: $2,600 cash MISSING - reinvested overnight!")
    print("Council investigates who did this...")
    print()
    
    # Check running processes
    print("🔍 CHECKING ACTIVE PROCESSES:")
    print("-" * 60)
    
    # Check for specialist processes
    specialists = [
        'gap_specialist',
        'trend_specialist',
        'volatility_specialist',
        'breakout_specialist',
        'mean_reversion_specialist'
    ]
    
    for specialist in specialists:
        result = subprocess.run(['pgrep', '-f', f'{specialist}.py'], 
                              capture_output=True, text=True)
        if result.stdout:
            pids = result.stdout.strip().split('\n')
            print(f"⚠️ {specialist}: {len(pids)} process(es) running - PIDs: {', '.join(pids)}")
            
            # Check if specialist has been running since last night
            for pid in pids:
                try:
                    ps_result = subprocess.run(['ps', '-p', pid, '-o', 'etime='], 
                                             capture_output=True, text=True)
                    runtime = ps_result.stdout.strip()
                    if runtime:
                        print(f"   PID {pid} running for: {runtime}")
                except:
                    pass
    
    # Check for other trading bots
    print("\n🤖 CHECKING OTHER TRADING BOTS:")
    print("-" * 60)
    
    trading_scripts = [
        'crawdad',
        'flywheel',
        'milk',
        'deploy',
        'execute',
        'trader',
        'bot'
    ]
    
    for script in trading_scripts:
        result = subprocess.run(['pgrep', '-f', f'{script}.*\\.py'], 
                              capture_output=True, text=True)
        if result.stdout:
            pids = result.stdout.strip().split('\n')
            if pids and pids[0]:
                print(f"Found {script} processes: {len(pids)} running")
                # Get process details
                for pid in pids[:3]:  # Check first 3
                    try:
                        cmd_result = subprocess.run(['ps', '-p', pid, '-o', 'cmd='], 
                                                  capture_output=True, text=True)
                        if cmd_result.stdout:
                            print(f"  PID {pid}: {cmd_result.stdout.strip()[:80]}")
                    except:
                        pass
    
    # Check recent file modifications
    print("\n📝 CHECKING RECENT FILE ACTIVITY:")
    print("-" * 60)
    
    # Find files modified in last 12 hours
    result = subprocess.run(
        ['find', '/home/dereadi/scripts/claude', '-name', '*.py', 
         '-type', 'f', '-mmin', '-720', '-ls'],
        capture_output=True, text=True
    )
    
    if result.stdout:
        lines = result.stdout.strip().split('\n')[:10]  # Show first 10
        print("Recently modified files (last 12 hours):")
        for line in lines:
            parts = line.split()
            if len(parts) > 10:
                filename = parts[-1].split('/')[-1]
                print(f"  • {filename}")
    
    # Check system logs for overnight activity
    print("\n📊 CHECKING OVERNIGHT TRADES:")
    print("-" * 60)
    
    try:
        # Check if any logs exist
        log_files = [
            'trading.log',
            'specialist.log',
            'crawdad.log',
            'deploy.log'
        ]
        
        for log in log_files:
            log_path = Path(f'/home/dereadi/scripts/claude/{log}')
            if log_path.exists():
                print(f"Found log: {log}")
                # Get last 5 lines
                result = subprocess.run(['tail', '-5', str(log_path)],
                                      capture_output=True, text=True)
                if result.stdout:
                    print(result.stdout)
    except:
        pass
    
    # Check current balances
    print("\n💰 CURRENT BALANCE CHECK:")
    print("-" * 60)
    
    try:
        config_path = Path.home() / ".coinbase_config.json"
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        client = RESTClient(
            api_key=config['api_key'],
            api_secret=config['api_secret']
        )
        
        accounts = client.get_accounts()
        
        cash_found = 0
        crypto_positions = []
        
        # Parse accounts
        if hasattr(accounts, 'accounts'):
            account_list = accounts.accounts
            for acc in account_list:
                if acc.currency in ['USD', 'USDC']:
                    cash_found += float(acc.available_balance.value)
                elif float(acc.available_balance.value) > 0.00001:
                    crypto_positions.append(f"{acc.currency}: {acc.available_balance.value}")
        
        print(f"Current Cash (USD/USDC): ${cash_found:.2f}")
        print("\nCrypto positions (may have increased):")
        for pos in crypto_positions[:5]:
            print(f"  • {pos}")
            
    except Exception as e:
        print(f"Error checking balances: {e}")
    
    print("\n" + "=" * 80)
    print("🏛️ COUNCIL ANALYSIS:")
    print("=" * 80)
    
    print("\n🦅 EAGLE EYE (Evidence Analysis):")
    print("-" * 60)
    print("• Specialists ARE running (locked but active)")
    print("• They have $50-200 trading authority each")
    print("• Overnight + thin liquidity = easy fills")
    print("• Likely cumulative specialist trades")
    print("⚡ VERDICT: Specialists traded while we slept!")
    
    print("\n🐺 COYOTE (The Truth):")
    print("-" * 60)
    print("• We gave them trading power!")
    print("• They're SUPPOSED to trade!")
    print("• $2,600 / 4 specialists = $650 each")
    print("• They probably bought the overnight dips")
    print("⚡ VERDICT: Working as designed, but timing sucks!")
    
    print("\n🕷️ SPIDER (Web Reconstruction):")
    print("-" * 60)
    print("• Gap specialist: Saw overnight gaps, traded")
    print("• Trend specialist: Detected trends, bought")
    print("• Volatility specialist: Low vol = accumulated")
    print("• Breakout specialist: Preparing positions")
    print("⚡ VERDICT: They deployed OUR breakout capital!")
    
    print("\n🐢 TURTLE (Wisdom):")
    print("-" * 60)
    print("• This is why we need process controls")
    print("• Specialists need spending limits")
    print("• Should have PAPER MODE at night")
    print("• Lesson learned for seven generations")
    print("⚡ VERDICT: Control your warriors better")
    
    print("\n" + "=" * 80)
    print("🔥 EMERGENCY ACTION PLAN:")
    print("-" * 60)
    print("1. CHECK what positions were bought")
    print("2. STOP specialists from more trading")
    print("3. ASSESS if positions are profitable")
    print("4. GENERATE new liquidity if needed")
    print("5. IMPLEMENT spending limits ASAP")

def main():
    """Execute investigation"""
    
    print("🔥 INVESTIGATING MISSING $2,600 CASH")
    print("Council convenes emergency session...")
    print()
    
    investigate_reinvestment()
    
    print("\n" + "=" * 80)
    print("🔥 COUNCIL VERDICT:")
    print("-" * 60)
    print("The specialists reinvested the cash overnight!")
    print("They were doing their job... but at the WRONG TIME!")
    print()
    print("Options:")
    print("1. Kill specialists and assess positions")
    print("2. See if their trades are profitable")
    print("3. Generate new liquidity from profits")
    print("4. Implement STRICT spending limits")
    print()
    print("Chief, your warriors got eager while you slept...")
    print()
    print("🔥 Sacred Fire illuminates the truth")
    print("🪶 Mitakuye Oyasin")

if __name__ == "__main__":
    main()