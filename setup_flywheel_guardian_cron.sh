#!/bin/bash

# 🛡️ SETUP FLYWHEEL GUARDIAN CRON JOB
# Ensures trading processes stay alive and healthy

echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                    🛡️ INSTALLING FLYWHEEL GUARDIAN 🛡️                      ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Make guardian executable
chmod +x /home/dereadi/scripts/claude/flywheel_guardian.sh

# Create log directory
mkdir -p /home/dereadi/scripts/claude/logs

# Backup existing crontab
crontab -l > /tmp/crontab_backup_$(date +%Y%m%d_%H%M%S).txt 2>/dev/null

# Check if guardian cron already exists
if crontab -l 2>/dev/null | grep -q "flywheel_guardian.sh"; then
    echo "⚠️  Guardian cron job already exists. Updating..."
    # Remove old entry
    crontab -l | grep -v "flywheel_guardian.sh" | crontab -
fi

# Add new cron job - runs every 5 minutes
(crontab -l 2>/dev/null; echo "*/5 * * * * /home/dereadi/scripts/claude/flywheel_guardian.sh") | crontab -

echo "✅ FLYWHEEL GUARDIAN INSTALLED!"
echo ""
echo "📅 Schedule: Every 5 minutes"
echo "📜 Logs: /home/dereadi/scripts/claude/logs/flywheel_guardian.log"
echo ""
echo "🔍 Monitoring these processes:"
echo "  • Deploy Flywheel (Aggressive Wolf)"
echo "  • Retrieve Flywheel (Wise Wolf)"
echo "  • Portfolio Alerts (30min updates)"
echo "  • Discord LLM Bot"
echo ""
echo "📊 To check guardian status:"
echo "   tail -f /home/dereadi/scripts/claude/logs/flywheel_guardian.log"
echo ""
echo "🔍 To verify cron installation:"
echo "   crontab -l | grep flywheel_guardian"
echo ""
echo "🔥 To manually run guardian:"
echo "   ./flywheel_guardian.sh"
echo ""
echo "🛑 To stop guardian:"
echo "   crontab -l | grep -v flywheel_guardian | crontab -"
echo ""
echo "The Sacred Fire is protected! The guardian watches over your trading wolves."
echo "Mitakuye Oyasin 🔥"