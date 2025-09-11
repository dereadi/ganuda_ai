#!/bin/bash

# 🛡️ FLYWHEEL GUARDIAN - PROCESS MONITOR & RESTARTER
# Watches critical trading processes and restarts them if they die

LOG_FILE="/home/dereadi/scripts/claude/logs/flywheel_guardian.log"
mkdir -p /home/dereadi/scripts/claude/logs

echo "[$(date)] 🛡️ Flywheel Guardian checking processes..." >> $LOG_FILE

# Critical processes to monitor
declare -A PROCESSES=(
    ["flywheel_deploy_safeguarded.py"]="Deploy Flywheel (Aggressive Wolf)"
    ["flywheel_retrieve_safeguarded.py"]="Retrieve Flywheel (Wise Wolf)"
    ["portfolio_alerts_enhanced.py"]="Portfolio Alerts (30min updates)"
    ["discord_llm_chat.py"]="Discord LLM Council Bot"
)

# Check each process
for script in "${!PROCESSES[@]}"; do
    description="${PROCESSES[$script]}"
    
    if ! pgrep -f "$script" > /dev/null; then
        echo "[$(date)] ❌ $description NOT RUNNING!" >> $LOG_FILE
        
        # Restart based on script type
        case "$script" in
            "flywheel_deploy_safeguarded.py")
                # Check liquidity before restarting Deploy Flywheel
                LIQUIDITY=$(python3 -c "
import json
from coinbase.rest import RESTClient
config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=10)
try:
    accounts = client.get_accounts()['accounts']
    for a in accounts:
        if a['currency'] == 'USD':
            print(float(a['available_balance']['value']))
            break
except:
    print(0)
" 2>/dev/null)
                
                if (( $(echo "$LIQUIDITY > 300" | bc -l) )); then
                    echo "[$(date)] 💸 Liquidity sufficient ($LIQUIDITY), restarting Deploy Flywheel..." >> $LOG_FILE
                    cd /home/dereadi/scripts/claude
                    nohup python3 $script > deploy_flywheel.log 2>&1 &
                    echo "[$(date)] ✅ Deploy Flywheel restarted with PID $!" >> $LOG_FILE
                else
                    echo "[$(date)] ⚠️  Low liquidity ($LIQUIDITY), skipping Deploy Flywheel restart" >> $LOG_FILE
                fi
                ;;
                
            "flywheel_retrieve_safeguarded.py")
                echo "[$(date)] 💰 Restarting Retrieve Flywheel..." >> $LOG_FILE
                cd /home/dereadi/scripts/claude
                nohup python3 $script > retrieve_flywheel.log 2>&1 &
                echo "[$(date)] ✅ Retrieve Flywheel restarted with PID $!" >> $LOG_FILE
                ;;
                
            "portfolio_alerts_enhanced.py")
                # Check if systemd service is running instead
                if ! systemctl --user is-active portfolio-alerts >/dev/null 2>&1; then
                    echo "[$(date)] 📊 Restarting Portfolio Alerts service..." >> $LOG_FILE
                    systemctl --user restart portfolio-alerts
                    echo "[$(date)] ✅ Portfolio Alerts service restarted" >> $LOG_FILE
                fi
                ;;
                
            "discord_llm_chat.py")
                # Check if systemd service is running
                if ! systemctl --user is-active discord-llm-council >/dev/null 2>&1; then
                    echo "[$(date)] 🤖 Discord bot not running as service, checking process..." >> $LOG_FILE
                    cd /home/dereadi/scripts/claude
                    nohup python3 $script > discord_bot.log 2>&1 &
                    echo "[$(date)] ✅ Discord bot restarted with PID $!" >> $LOG_FILE
                fi
                ;;
        esac
    else
        echo "[$(date)] ✅ $description is running" >> $LOG_FILE
    fi
done

# Check liquidity status
echo "[$(date)] 💰 Checking liquidity status..." >> $LOG_FILE
python3 - << 'EOF' >> $LOG_FILE 2>&1
import json
from coinbase.rest import RESTClient
from datetime import datetime

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=10)

try:
    accounts = client.get_accounts()['accounts']
    usd_balance = 0
    total_value = 0
    
    for a in accounts['accounts']:
        if a['currency'] == 'USD':
            usd_balance = float(a['available_balance']['value'])
            total_value += usd_balance
        elif float(a['available_balance']['value']) > 0.00001:
            # Get value of other assets
            try:
                ticker = client.get_product(f"{a['currency']}-USD")
                price = float(ticker.get("price", 0))
                value = float(a['available_balance']['value']) * price
                total_value += value
            except:
                pass
    
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Liquidity Report:")
    print(f"  • USD Balance: ${usd_balance:.2f}")
    print(f"  • Total Portfolio: ${total_value:.2f}")
    
    if usd_balance < 100:
        print(f"  ⚠️  CRITICAL: Low liquidity! Retrieve Flywheel should activate!")
    elif usd_balance < 250:
        print(f"  ⚠️  WARNING: Below target liquidity ($250)")
    else:
        print(f"  ✅ Liquidity healthy")
        
except Exception as e:
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Error checking liquidity: {e}")
EOF

# Check for runaway processes (too many instances)
echo "[$(date)] 🔍 Checking for runaway processes..." >> $LOG_FILE
for script in "${!PROCESSES[@]}"; do
    COUNT=$(pgrep -f "$script" | wc -l)
    if [ "$COUNT" -gt 1 ]; then
        echo "[$(date)] ⚠️  Multiple instances of $script detected: $COUNT" >> $LOG_FILE
        # Kill all but the most recent
        pgrep -f "$script" | head -n -1 | xargs -r kill
        echo "[$(date)] 🔧 Cleaned up duplicate processes" >> $LOG_FILE
    fi
done

echo "[$(date)] ✅ Guardian check complete" >> $LOG_FILE
echo "----------------------------------------" >> $LOG_FILE