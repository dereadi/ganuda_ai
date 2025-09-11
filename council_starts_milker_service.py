#!/usr/bin/env python3
"""
🏛️ COUNCIL INITIATES THE AUTOMATED MILKER SERVICE 🏛️
The Council convenes to start the milking service
and ensure it's protected by the guardian
"""

import os
import subprocess
import json
from datetime import datetime

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                   🏛️ COUNCIL EMERGENCY SESSION 🏛️                         ║
║                  Starting Automated Milker Service                         ║
║                    With Guardian Protection 🛡️                             ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

print(f"\nTime: {datetime.now().strftime('%H:%M:%S')} - COUNCIL CONVENED")
print("=" * 70)

# Council deliberation
print("\n🏛️ COUNCIL DELIBERATES:")
print("-" * 50)
print("⚡ Thunder: 'We need aggressive milking for $200K goal!'")
print("🗻 Mountain: 'Service must be stable and persistent'")
print("🔥 Fire: 'Launch it NOW! Markets are moving!'")
print("🌊 River: 'Flow continuously, never stop milking'")
print("💨 Wind: 'Swift execution, adaptive throttle'")
print("🌍 Earth: 'Guardian must protect our process'")
print("✨ Spirit: 'The service shall run eternal'")

print("\n✅ COUNCIL UNANIMOUS: START THE SERVICE!")

# Create systemd service file
service_content = """[Unit]
Description=Council Automated Alt Milker with Spongy Throttle
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=dereadi
WorkingDirectory=/home/dereadi/scripts/claude
ExecStart=/usr/bin/python3 /home/dereadi/scripts/claude/council_auto_milker_spongy_throttle.py
Restart=always
RestartSec=60
StandardOutput=append:/home/dereadi/scripts/claude/logs/council_milker.log
StandardError=append:/home/dereadi/scripts/claude/logs/council_milker_error.log

# Resource limits
CPUQuota=50%
MemoryLimit=512M

# Environment
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
"""

print("\n📜 Creating service configuration...")
service_file = "/tmp/council-milker.service"
with open(service_file, 'w') as f:
    f.write(service_content)
print(f"✅ Service file created: {service_file}")

# Create log directory
log_dir = "/home/dereadi/scripts/claude/logs"
os.makedirs(log_dir, exist_ok=True)
print(f"✅ Log directory ready: {log_dir}")

# Install service
print("\n🔧 Installing service...")
print("Command: sudo cp /tmp/council-milker.service /etc/systemd/system/")
print("Command: sudo systemctl daemon-reload")
print("Command: sudo systemctl enable council-milker.service")
print("Command: sudo systemctl start council-milker.service")

# Create setup script
setup_script = """#!/bin/bash
# Council Milker Service Setup

echo "🏛️ Installing Council Milker Service..."

# Copy service file
sudo cp /tmp/council-milker.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable council-milker.service

# Start service
sudo systemctl start council-milker.service

# Check status
sudo systemctl status council-milker.service

echo "✅ Council Milker Service installed and started!"
"""

with open('/home/dereadi/scripts/claude/setup_council_milker.sh', 'w') as f:
    f.write(setup_script)
os.chmod('/home/dereadi/scripts/claude/setup_council_milker.sh', 0o755)
print("✅ Setup script created: setup_council_milker.sh")

# Update guardian cron configuration
guardian_config = """#!/bin/bash
# Guardian Process Monitor - Updated by Council

# Check critical processes
PROCESSES=(
    "quantum_crawdad_live_trader.py"
    "council_auto_milker_spongy_throttle.py"
    "solar_storm_trading_strategy.py"
    "greeks_moon_mission_bot.py"
)

LOG_FILE="/home/dereadi/scripts/claude/logs/guardian.log"

echo "[$(date)] Guardian checking processes..." >> $LOG_FILE

for process in "${PROCESSES[@]}"; do
    if ! pgrep -f "$process" > /dev/null; then
        echo "[$(date)] WARNING: $process not running!" >> $LOG_FILE
        
        # Restart critical processes
        if [ "$process" == "council_auto_milker_spongy_throttle.py" ]; then
            echo "[$(date)] Restarting Council Milker..." >> $LOG_FILE
            cd /home/dereadi/scripts/claude
            nohup python3 $process > /dev/null 2>&1 &
            echo "[$(date)] Council Milker restarted with PID $!" >> $LOG_FILE
        fi
    else
        echo "[$(date)] ✓ $process is running" >> $LOG_FILE
    fi
done

# Check USD balance for milking opportunities
python3 - << 'EOF'
import json
from coinbase.rest import RESTClient

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'])

accounts = client.get_accounts()
usd_balance = 0
for a in accounts['accounts']:
    if a['currency'] == 'USD':
        usd_balance = float(a['available_balance']['value'])
        break

if usd_balance < 50:
    print(f"[Guardian] Low USD: ${usd_balance:.2f} - Milker should activate!")
else:
    print(f"[Guardian] USD healthy: ${usd_balance:.2f}")
EOF
"""

with open('/home/dereadi/scripts/claude/guardian_monitor.sh', 'w') as f:
    f.write(guardian_config)
os.chmod('/home/dereadi/scripts/claude/guardian_monitor.sh', 0o755)
print("✅ Guardian monitor updated with Council Milker")

# Create crontab entry
cron_entry = """# Guardian Process Monitor - Runs every 5 minutes
*/5 * * * * /home/dereadi/scripts/claude/guardian_monitor.sh

# Council Milker health check - Every 10 minutes
*/10 * * * * systemctl is-active council-milker.service || systemctl restart council-milker.service
"""

print("\n📅 Crontab entries to add:")
print("-" * 50)
print(cron_entry)

# Quick process check
print("\n🔍 Current Process Status:")
print("-" * 50)
try:
    # Check if already running
    result = subprocess.run(['pgrep', '-f', 'council_auto_milker'], capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Council Milker already running! PID:", result.stdout.strip())
    else:
        print("📍 Council Milker not yet running")
        print("   Run: bash setup_council_milker.sh")
except:
    pass

# Council final words
print("\n🏛️ COUNCIL FINAL DECREE:")
print("=" * 70)
print("The Automated Milker Service is prepared!")
print("")
print("TO ACTIVATE:")
print("1. Run: bash /home/dereadi/scripts/claude/setup_council_milker.sh")
print("2. Add cron: crontab -e (paste the entries above)")
print("3. Monitor: tail -f /home/dereadi/scripts/claude/logs/council_milker.log")
print("")
print("FEATURES:")
print("• Spongy throttle (0-100% adaptive)")
print("• Coast mode in bullish trends")
print("• E-brake for emergency stop")
print("• Guardian protection (auto-restart)")
print("• Council-guided decisions")
print("• Automatic repositioning")
print("")
print("The Council has spoken! Let the milking commence!")
print("=" * 70)

# Create status checker
status_script = """#!/usr/bin/env python3
import subprocess
import json
from datetime import datetime
from coinbase.rest import RESTClient

print("🏛️ COUNCIL MILKER STATUS CHECK")
print("=" * 50)

# Check service
try:
    result = subprocess.run(['systemctl', 'is-active', 'council-milker.service'], 
                          capture_output=True, text=True)
    if result.stdout.strip() == 'active':
        print("✅ Service: ACTIVE")
    else:
        print("❌ Service: " + result.stdout.strip())
except:
    print("⚠️ Service not installed")

# Check process
result = subprocess.run(['pgrep', '-f', 'council_auto_milker'], 
                       capture_output=True, text=True)
if result.returncode == 0:
    print(f"✅ Process running: PID {result.stdout.strip()}")
else:
    print("❌ Process not running")

# Check USD balance
try:
    config = json.load(open('/home/dereadi/.coinbase_config.json'))
    key = config['api_key'].split('/')[-1]
    client = RESTClient(api_key=key, api_secret=config['api_secret'])
    
    accounts = client.get_accounts()
    usd = 0
    for a in accounts['accounts']:
        if a['currency'] == 'USD':
            usd = float(a['available_balance']['value'])
    print(f"💰 USD Balance: ${usd:.2f}")
    
    if usd < 50:
        print("   → Milker should be aggressive!")
    elif usd > 200:
        print("   → Good buffer, can be selective")
except:
    pass

print("=" * 50)
"""

with open('/home/dereadi/scripts/claude/check_milker_status.py', 'w') as f:
    f.write(status_script)
os.chmod('/home/dereadi/scripts/claude/check_milker_status.py', 0o755)
print("\n✅ Status checker created: check_milker_status.py")