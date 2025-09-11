#!/usr/bin/env python3
"""
🔍 COMPREHENSIVE SERVICE AUDIT
Check all trading-related services and processes
"""

import subprocess
import os
from datetime import datetime

print("🔍 COMPREHENSIVE TRADING SERVICE AUDIT")
print("=" * 60)
print(f"Audit Time: {datetime.now().strftime('%H:%M:%S')}")
print()

# Check systemd services
print("⚙️ SYSTEMD SERVICES:")
print("-" * 40)

services = [
    "portfolio-alerts",
    "qbees-deadman", 
    "greeks-moon-mission",
    "cherokee-portal",
    "discord-llm-council"
]

for service in services:
    result = subprocess.run(
        f"systemctl --user status {service} --no-pager 2>/dev/null | head -3",
        shell=True,
        capture_output=True,
        text=True
    )
    if "Active:" in result.stdout:
        if "active (running)" in result.stdout:
            print(f"✅ {service}: RUNNING")
        elif "inactive" in result.stdout:
            print(f"⚪ {service}: STOPPED")
        elif "failed" in result.stdout:
            print(f"❌ {service}: FAILED")
        else:
            print(f"❓ {service}: UNKNOWN")

print()

# Check running Python processes
print("🐍 PYTHON TRADING PROCESSES:")
print("-" * 40)

trading_keywords = [
    "flywheel", "greek", "crawdad", "specialist", "trader",
    "deploy", "execute", "milk", "harvest", "moon"
]

for keyword in trading_keywords:
    result = subprocess.run(
        f"pgrep -f {keyword} | wc -l",
        shell=True,
        capture_output=True,
        text=True
    )
    count = int(result.stdout.strip())
    if count > 0:
        print(f"• {keyword}: {count} process(es)")
        # Get details of first few
        detail = subprocess.run(
            f"ps aux | grep {keyword} | grep -v grep | head -2",
            shell=True,
            capture_output=True,
            text=True
        )
        if detail.stdout:
            for line in detail.stdout.strip().split('\n'):
                parts = line.split()
                if len(parts) > 10:
                    script = ' '.join(parts[10:])[:60]
                    print(f"    └─ {script}")

print()

# Check cron jobs
print("⏰ CRON JOBS:")
print("-" * 40)

cron_result = subprocess.run("crontab -l 2>/dev/null", shell=True, capture_output=True, text=True)
if cron_result.stdout:
    trading_crons = []
    for line in cron_result.stdout.split('\n'):
        if any(word in line.lower() for word in ['python', 'trade', 'crawdad', 'greek', 'flywheel']):
            if not line.startswith('#'):
                trading_crons.append(line)
    
    if trading_crons:
        print("Active trading cron jobs:")
        for cron in trading_crons[:5]:
            print(f"  • {cron[:80]}")
    else:
        print("No active trading cron jobs")
else:
    print("No crontab configured")

print()

# Check for running shell scripts
print("🔧 SHELL SCRIPT MONITORS:")
print("-" * 40)

shell_scripts = [
    "monitor_crawdads.sh",
    "guardian_monitor.sh",
    "emergency_stop_buyers.sh",
    "start_cherokee_portal.sh"
]

for script in shell_scripts:
    result = subprocess.run(f"pgrep -f {script}", shell=True, capture_output=True, text=True)
    if result.stdout:
        print(f"✅ {script}: RUNNING")

print()

# Identify the tribal components
print("🏛️ TRIBAL COMPONENT STATUS:")
print("-" * 40)

components = {
    "🏔️ Mountain (Thunder)": ["thunder", "mountain"],
    "🔥 Sacred Fire": ["fire", "thermal", "memory"],
    "🦅 Peace Eagle": ["eagle", "peace"],
    "🐢 Turtle Wisdom": ["turtle", "wisdom"],
    "🦀 Crawdad Gang": ["crawdad", "quantum"],
    "🏛️ Greeks": ["greek", "alpha", "beta", "gamma"],
    "⚡ Flywheel Deploy": ["flywheel.*deploy", "flywheel.*capital"],
    "💰 Flywheel Retrieve": ["flywheel.*harvest", "flywheel.*milk", "flywheel.*profit"]
}

for component, keywords in components.items():
    found = False
    for keyword in keywords:
        result = subprocess.run(f"pgrep -f '{keyword}' 2>/dev/null | head -1", 
                              shell=True, capture_output=True, text=True)
        if result.stdout:
            print(f"{component}: ACTIVE")
            found = True
            break
    if not found:
        print(f"{component}: INACTIVE")

print()

# Recommendations
print("🎯 RECOMMENDED TRIBAL CONFIGURATION:")
print("=" * 60)

print("PHASE 1 - Core Council:")
print("  1. Mountain/Thunder - Market oversight")
print("  2. Sacred Fire - Thermal memory management")
print("  3. Peace Eagle - Pattern recognition")
print("  These provide wisdom without trading")
print()

print("PHASE 2 - Dual Flywheel System:")
print("  1. Deploy Flywheel - Aggressive position building")
print("     • Set max deployment: $300 per cycle")
print("     • Require 3+ council votes")
print("     • Stop-loss at -5%")
print()
print("  2. Retrieve Flywheel - Liquidity harvesting")
print("     • Maintain minimum $250 cash")
print("     • Take profits at +10%")
print("     • Emergency liquidation if < $100")
print()

print("SAFEGUARDS TO IMPLEMENT:")
print("  • Hard limit: Max 50% of liquidity per trade")
print("  • Council voting: 3/5 approval for >$100")
print("  • Circuit breaker: Stop all if -10% in 1 hour")
print("  • Liquidity floor: Always keep $250 minimum")
print("  • Position limits: No single asset >40% of portfolio")
print()

print("=" * 60)
print("Ready to implement two-flywheel system with safeguards?")
print("=" * 60)