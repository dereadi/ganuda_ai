#!/bin/bash
# 🌞 Start Solar Alert Monitoring

echo "🚨 STARTING SOLAR ALERT SYSTEM"
echo "================================"
echo "This will run in the background and create alerts when:"
echo "  • KP index rises above 4"
echo "  • Solar flares detected"
echo "  • Solar wind surges"
echo ""
echo "Alert files will be created:"
echo "  • solar_alerts.json - Full history"
echo "  • URGENT_SOLAR_ALERT.txt - Latest urgent alert"
echo ""
echo "Starting monitor..."

# Run in background
nohup /home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3 /home/dereadi/scripts/claude/solar_storm_alert_system.py > solar_alerts.log 2>&1 &

echo "✅ Alert system running in background!"
echo "PID: $!"
echo ""
echo "To check status: tail -f solar_alerts.log"
echo "To stop: kill $!"