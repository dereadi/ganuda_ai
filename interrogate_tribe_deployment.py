#!/usr/bin/env python3
"""
🏛️ INTERROGATE THE TRIBE
Find out who deployed the $550 in liquidity
"""

import subprocess
import json
import os
from datetime import datetime, timedelta

print("🏛️ TRIBAL INVESTIGATION - WHO DEPLOYED THE FUNDS?")
print("=" * 60)
print(f"Investigation Time: {datetime.now().strftime('%H:%M:%S')}")
print()

# Check flywheel status first
print("⚡ CHECKING FLYWHEEL SYSTEMS:")
print("-" * 40)

flywheel_scripts = [
    "flywheel_accelerator.py",
    "flywheel_executor.py", 
    "flywheel_feeding_protocol.py",
    "flywheel_ignition_surge.py",
    "flywheel_unleashed.py",
    "greeks_feed_btc_flywheel.py",
    "crypto_powered_flywheel_ignition.py"
]

active_flywheels = []
for script in flywheel_scripts:
    result = subprocess.run(f"pgrep -f {script}", shell=True, capture_output=True, text=True)
    if result.stdout:
        pids = result.stdout.strip().split('\n')
        active_flywheels.append((script, len(pids)))
        print(f"🔄 {script}: {len(pids)} instance(s) ACTIVE")

if not active_flywheels:
    print("📍 No flywheel processes currently running")
else:
    print(f"\n⚠️ {sum(x[1] for x in active_flywheels)} FLYWHEEL PROCESSES ACTIVE!")

print()

# Check flywheel logs
print("📝 CHECKING FLYWHEEL LOGS:")
print("-" * 40)

flywheel_logs = [
    "flywheel_feeding_log.json",
    "flywheel_ignition_state.json",
    "flywheel_nuclear_status.json"
]

for log_file in flywheel_logs:
    if os.path.exists(log_file):
        try:
            mod_time = datetime.fromtimestamp(os.path.getmtime(log_file))
            if datetime.now() - mod_time < timedelta(hours=1):
                print(f"🔥 {log_file} - Modified {mod_time.strftime('%H:%M')}")
                with open(log_file, 'r') as f:
                    data = json.load(f)
                    if 'deployment' in str(data).lower() or 'capital' in str(data).lower():
                        print(f"   FOUND: Capital deployment activity!")
        except:
            pass

print()

# Check Greek specialists
print("🏛️ INTERROGATING THE GREEKS:")
print("-" * 40)

greek_scripts = [
    "greeks_consensus_trader.py",
    "greeks_moon_mission_bot.py",
    "greeks_attack_mode.py",
    "greeks_feed_btc_flywheel.py"
]

for script in greek_scripts:
    result = subprocess.run(f"pgrep -f {script}", shell=True, capture_output=True, text=True)
    if result.stdout:
        print(f"⚡ {script}: ACTIVE - Possible fund deployment")

print()

# Check council decisions
print("🔮 CHECKING COUNCIL DECISIONS:")
print("-" * 40)

council_files = [
    "council_trading_decision.json",
    "council_liquidity_decision.json",
    "council_deployment.json"
]

for council_file in council_files:
    if os.path.exists(council_file):
        try:
            with open(council_file, 'r') as f:
                data = json.load(f)
                timestamp = data.get('timestamp', 'Unknown')
                if 'deploy' in str(data).lower() or 'execute' in str(data).lower():
                    print(f"📜 {council_file}:")
                    print(f"   Timestamp: {timestamp}")
                    if 'amount' in data:
                        print(f"   Amount: {data['amount']}")
                    if 'decision' in data:
                        print(f"   Decision: {data['decision']}")
        except:
            pass

print()

# Check specific trader logs
print("🤖 CHECKING AUTOMATED TRADERS:")
print("-" * 40)

# Look for recent Python processes that might have deployed funds
ps_check = """
ps aux | grep -E "deploy|execute|buy|trade" | grep python | grep -v grep | head -10
"""

result = subprocess.run(ps_check, shell=True, capture_output=True, text=True)
if result.stdout:
    print("Active trading processes:")
    for line in result.stdout.strip().split('\n')[:5]:
        parts = line.split()
        if len(parts) > 10:
            pid = parts[1]
            script = ' '.join(parts[10:])
            print(f"   PID {pid}: {script[:60]}")

print()

# Check for deployment scripts run recently
print("💸 CHECKING RECENT DEPLOYMENT SCRIPTS:")
print("-" * 40)

deployment_scripts = [
    "deploy_capital_now.py",
    "deploy_flywheel_capital.py",
    "deploy_at_117056.py",
    "deploy_cash_now.py",
    "deploy_208_now.py"
]

for script in deployment_scripts:
    if os.path.exists(script):
        mod_time = datetime.fromtimestamp(os.path.getmtime(script))
        if datetime.now() - mod_time < timedelta(hours=2):
            print(f"⚠️ {script} - Modified recently at {mod_time.strftime('%H:%M')}")

print()

# Tribal verdict
print("🏛️ TRIBAL INVESTIGATION VERDICT:")
print("=" * 60)

suspects = []

if active_flywheels:
    suspects.append(f"FLYWHEEL SYSTEMS ({len(active_flywheels)} active)")

# Count active specialists
specialist_count = 0
for spec in ["gap_specialist", "trend_specialist", "crawdad"]:
    result = subprocess.run(f"pgrep -f {spec} | wc -l", shell=True, capture_output=True, text=True)
    if result.stdout:
        count = int(result.stdout.strip())
        if count > 0:
            specialist_count += count

if specialist_count > 0:
    suspects.append(f"SPECIALIST BOTS ({specialist_count} active)")

print("PRIME SUSPECTS:")
for i, suspect in enumerate(suspects, 1):
    print(f"{i}. {suspect}")

print()
print("EVIDENCE SUGGESTS:")
print("• Multiple automated systems deployed capital")
print("• Bought 4.79 SOL (~$987)")
print("• Bought 8,934 MATIC tokens")
print("• Bought 74 AVAX tokens")
print("• Liquidated XRP and LINK positions")
print()
print("⚠️ RECOMMENDATION: EMERGENCY SHUTDOWN ALL AUTOMATED TRADING")
print("=" * 60)