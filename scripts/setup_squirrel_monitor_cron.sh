#!/bin/bash
# Add to crontab - run every Sunday at 8 PM
(crontab -l 2>/dev/null; echo "0 20 * * 0 /home/dereadi/cherokee_venv/bin/python3 /ganuda/scripts/flying_squirrel_monitor.py >> /tmp/squirrel_monitor.log 2>&1") | crontab -
echo "Cron job added: Weekly Flying Squirrel analysis at Sunday 8 PM"