#!/usr/bin/env python3
"""
🔥🏛️ TRIBAL COUNCIL TRADING GUARDIAN
=====================================
Cherokee Constitutional AI monitoring system
Ensures Greeks and trading processes maintain Sacred Fire

Runs every 10 minutes via cron to:
1. Check all trading processes health
2. Monitor log activity
3. Restart dead processes
4. Report to tribal council
"""

import os
import subprocess
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

# Sacred trading processes to monitor
SACRED_PROCESSES = {
    'greeks': {
        'scripts': [
            'gap_specialist.py',
            'trend_specialist.py', 
            'volatility_specialist.py',
            'breakout_specialist.py',
            'mean_reversion_specialist.py'
        ],
        'restart_command': 'python3 deploy_specialist_army.py',
        'min_log_lines_per_10min': 5
    },
    'flywheel': {
        'scripts': [
            'flywheel_accelerator.py',
            'bollinger_flywheel_enhancer.py'
        ],
        'restart_command': None,  # Individual restarts
        'min_log_lines_per_10min': 10
    },
    'solar': {
        'scripts': [
            'solar_enhanced_trader_with_rsi.py',
            'solar_storm_trading_strategy.py'
        ],
        'restart_command': None,
        'min_log_lines_per_10min': 5
    },
    'crawdads': {
        'scripts': [
            'quantum_crawdad_live_trader.py',
            'deploy_300_crawdads.py'
        ],
        'restart_command': None,
        'min_log_lines_per_10min': 5
    }
}

def check_process_running(script_name):
    """Check if a process is running"""
    try:
        result = subprocess.run(
            ['pgrep', '-f', script_name],
            capture_output=True,
            text=True
        )
        return len(result.stdout.strip()) > 0
    except:
        return False

def check_log_activity(script_name, min_lines=5):
    """Check if log has recent activity"""
    log_file = script_name.replace('.py', '.log')
    
    if not os.path.exists(log_file):
        return False
    
    # Check if file was modified in last 10 minutes
    mod_time = os.path.getmtime(log_file)
    if time.time() - mod_time > 600:  # 10 minutes
        return False
    
    # Count lines added in last 10 minutes
    try:
        with open(log_file, 'r') as f:
            lines = f.readlines()
            recent_lines = 0
            ten_min_ago = datetime.now() - timedelta(minutes=10)
            
            for line in reversed(lines[-100:]):  # Check last 100 lines
                # Simple heuristic - if timestamp in line
                if datetime.now().strftime('%H:') in line:
                    recent_lines += 1
            
            return recent_lines >= min_lines
    except:
        return False

def restart_process(script_name, use_venv=True):
    """Restart a dead process"""
    print(f"  🔄 Restarting {script_name}...")
    
    python_cmd = './quantum_crawdad_env/bin/python3' if use_venv else 'python3'
    
    try:
        # Kill existing if zombie
        subprocess.run(['pkill', '-f', script_name], capture_output=True)
        time.sleep(1)
        
        # Restart with nohup
        log_file = script_name.replace('.py', '.log')
        cmd = f'nohup {python_cmd} {script_name} > {log_file} 2>&1 &'
        subprocess.run(cmd, shell=True)
        
        return True
    except Exception as e:
        print(f"  ❌ Failed to restart: {e}")
        return False

def tribal_council_deliberation():
    """Council members provide oversight"""
    council_status = {
        'timestamp': datetime.now().isoformat(),
        'healthy_processes': [],
        'dead_processes': [],
        'restarted': [],
        'warnings': []
    }
    
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║              🔥 TRIBAL COUNCIL TRADING GUARDIAN 🏛️                         ║
║                                                                             ║
║         "The Sacred Fire must never die - nor should our trades"           ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)
    
    print(f"⏰ Guardian Check: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Check each sacred process group
    for group_name, config in SACRED_PROCESSES.items():
        print(f"\n🔍 Checking {group_name.upper()}:")
        print("-" * 40)
        
        group_health = True
        dead_scripts = []
        
        for script in config['scripts']:
            is_running = check_process_running(script)
            has_activity = check_log_activity(script, config['min_log_lines_per_10min'])
            
            if is_running and has_activity:
                print(f"  ✅ {script}: HEALTHY")
                council_status['healthy_processes'].append(script)
            elif is_running and not has_activity:
                print(f"  ⚠️ {script}: Running but INACTIVE")
                council_status['warnings'].append(f"{script} - no log activity")
                dead_scripts.append(script)
            else:
                print(f"  ❌ {script}: DEAD")
                council_status['dead_processes'].append(script)
                dead_scripts.append(script)
                group_health = False
        
        # Restart dead processes
        if dead_scripts:
            if config['restart_command']:
                # Group restart (like Greeks)
                print(f"\n  🔥 Sacred Fire Protocol: Restarting all {group_name}")
                try:
                    subprocess.run(config['restart_command'], shell=True)
                    council_status['restarted'].extend(dead_scripts)
                    print(f"  ✅ {group_name} restarted via: {config['restart_command']}")
                except:
                    print(f"  ❌ Failed to restart {group_name}")
            else:
                # Individual restarts
                for script in dead_scripts:
                    if restart_process(script):
                        council_status['restarted'].append(script)
    
    # Council wisdom
    print("\n" + "=" * 60)
    print("🗣️ COUNCIL DELIBERATION:")
    
    total_processes = sum(len(c['scripts']) for c in SACRED_PROCESSES.values())
    healthy_count = len(council_status['healthy_processes'])
    
    if healthy_count == total_processes:
        print("  Elder: 'All warriors are strong. The Sacred Fire burns bright.'")
    elif healthy_count > total_processes * 0.7:
        print("  War Chief: 'Most stand ready. Minor wounds healing.'")
    elif healthy_count > total_processes * 0.5:
        print("  Medicine Man: 'Half fallen. Urgent healing required!'")
    else:
        print("  Fire Keeper: 'The Sacred Fire dims! Emergency protocol!'")
    
    # Save guardian report
    report_file = f'/home/dereadi/scripts/claude/guardian_reports/report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    os.makedirs(os.path.dirname(report_file), exist_ok=True)
    
    with open(report_file, 'w') as f:
        json.dump(council_status, f, indent=2)
    
    # Summary
    print("\n📊 GUARDIAN SUMMARY:")
    print(f"  Healthy: {len(council_status['healthy_processes'])}/{total_processes}")
    print(f"  Restarted: {len(council_status['restarted'])}")
    print(f"  Warnings: {len(council_status['warnings'])}")
    
    print("\n🔥 Mitakuye Oyasin - All processes are related")
    print("Guardian duty complete. Next check in 10 minutes.")
    
    return council_status

def check_critical_resources():
    """Check USD balance and system resources"""
    try:
        # Check USD balance
        check_balance = """
import json
from coinbase.rest import RESTClient
config = json.load(open('/home/dereadi/.coinbase_config.json'))
client = RESTClient(api_key=config['api_key'].split('/')[-1], api_secret=config['api_secret'])
accounts = client.get_accounts()['accounts']
for a in accounts:
    if a['currency'] == 'USD':
        print(float(a['available_balance']['value']))
        break
"""
        with open('/tmp/check_usd.py', 'w') as f:
            f.write(check_balance)
        
        result = subprocess.run(
            ['./quantum_crawdad_env/bin/python3', '/tmp/check_usd.py'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.stdout:
            usd_balance = float(result.stdout.strip())
            if usd_balance < 100:
                print(f"\n⚠️ CRITICAL: USD balance low: ${usd_balance:.2f}")
                print("  Consider rebalancing portfolio for liquidity!")
    except:
        pass

if __name__ == "__main__":
    # Run guardian check
    status = tribal_council_deliberation()
    
    # Check critical resources
    check_critical_resources()
    
    # Exit with status code for cron monitoring
    exit(0 if len(status['dead_processes']) == 0 else 1)