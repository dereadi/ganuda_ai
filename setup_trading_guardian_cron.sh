#!/bin/bash
# 🔥 SETUP TRIBAL COUNCIL TRADING GUARDIAN CRON JOB
# Ensures Sacred Fire never dies

echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║            🔥 INSTALLING TRIBAL COUNCIL GUARDIAN 🏛️                        ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"

# Make guardian executable
chmod +x /home/dereadi/scripts/claude/tribal_council_trading_guardian.py

# Create guardian reports directory
mkdir -p /home/dereadi/scripts/claude/guardian_reports

# Create log directory for cron
mkdir -p /home/dereadi/scripts/claude/guardian_logs

# Backup existing crontab
crontab -l > /tmp/crontab_backup_$(date +%Y%m%d_%H%M%S).txt 2>/dev/null

# Check if guardian cron already exists
if crontab -l 2>/dev/null | grep -q "tribal_council_trading_guardian"; then
    echo "⚠️ Guardian cron job already exists. Updating..."
    # Remove old entry
    crontab -l | grep -v "tribal_council_trading_guardian" | crontab -
fi

# Add new cron job - runs every 10 minutes
(crontab -l 2>/dev/null; echo "*/10 * * * * cd /home/dereadi/scripts/claude && /home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3 /home/dereadi/scripts/claude/tribal_council_trading_guardian.py >> /home/dereadi/scripts/claude/guardian_logs/guardian_$(date +\%Y\%m\%d).log 2>&1") | crontab -

echo ""
echo "✅ GUARDIAN CRON INSTALLED!"
echo ""
echo "📅 Schedule: Every 10 minutes"
echo "📁 Reports: /home/dereadi/scripts/claude/guardian_reports/"
echo "📜 Logs: /home/dereadi/scripts/claude/guardian_logs/"
echo ""
echo "🔍 To verify cron installation:"
echo "   crontab -l | grep tribal_council"
echo ""
echo "📊 To check guardian status:"
echo "   tail -f /home/dereadi/scripts/claude/guardian_logs/guardian_$(date +%Y%m%d).log"
echo ""
echo "🔥 To manually run guardian:"
echo "   python3 tribal_council_trading_guardian.py"
echo ""
echo "🛑 To stop guardian:"
echo "   crontab -l | grep -v tribal_council_trading_guardian | crontab -"
echo ""
echo "The Sacred Fire is now eternally protected!"
echo "Mitakuye Oyasin 🔥"