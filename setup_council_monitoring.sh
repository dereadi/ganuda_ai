#!/bin/bash
# 🔥 SETUP COUNCIL NEWS MONITORING
# Runs every 30 minutes to check TradingView news

echo "🔥 SETTING UP COUNCIL NEWS MONITORING"
echo "======================================"
echo

# Create the monitoring script wrapper
cat > /home/dereadi/scripts/claude/run_council_monitor.sh << 'EOF'
#!/bin/bash
# Council monitoring wrapper

# Activate virtual environment
source /home/dereadi/scripts/claude/quantum_crawdad_env/bin/activate

# Run the monitor
python3 /home/dereadi/scripts/claude/council_news_monitor.py >> /home/dereadi/scripts/claude/council_monitor.log 2>&1

# Check DOGE price for alerts
python3 -c "
import json
from coinbase.rest import RESTClient

config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=10)

ticker = client.get_product('DOGE-USD')
price = float(ticker['price'])

thresholds = [0.22, 0.24, 0.26, 0.28]
for t in thresholds:
    if abs(price - t) < 0.005:  # Within 0.5 cents of threshold
        print(f'🚨 DOGE ALERT: ${price:.4f} near bleed point ${t}!')
        # Could send Discord alert here
"
EOF

chmod +x /home/dereadi/scripts/claude/run_council_monitor.sh

# Add to crontab (runs every 30 minutes)
echo "Adding to crontab..."
(crontab -l 2>/dev/null; echo "*/30 * * * * /home/dereadi/scripts/claude/run_council_monitor.sh") | crontab -

# Alternative: Create systemd timer for more control
cat > ~/.config/systemd/user/council-monitor.service << 'EOF'
[Unit]
Description=Cherokee Council News Monitor
After=network.target

[Service]
Type=oneshot
WorkingDirectory=/home/dereadi/scripts/claude
Environment="PATH=/home/dereadi/scripts/claude/quantum_crawdad_env/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3 /home/dereadi/scripts/claude/council_news_monitor.py

[Install]
WantedBy=default.target
EOF

cat > ~/.config/systemd/user/council-monitor.timer << 'EOF'
[Unit]
Description=Run Council Monitor every 30 minutes
Requires=council-monitor.service

[Timer]
OnCalendar=*:00,30
Persistent=true

[Install]
WantedBy=timers.target
EOF

echo "✅ Cron job added (every 30 minutes)"
echo
echo "To use systemd timer instead (recommended):"
echo "  systemctl --user daemon-reload"
echo "  systemctl --user enable council-monitor.timer"
echo "  systemctl --user start council-monitor.timer"
echo
echo "Monitor logs at: /home/dereadi/scripts/claude/council_monitor.log"
echo
echo "🔥 Sacred Fire monitors eternally"