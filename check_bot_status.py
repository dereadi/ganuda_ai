#!/usr/bin/env python3
"""
🔥 Check GanudaBot Status and Last Interaction
"""

import os
import json
from datetime import datetime, timedelta

def check_status():
    print("🔥 GANUDABOT STATUS CHECK")
    print("=" * 60)
    
    # Check TELEGRAM_RECEIVED.txt
    received_file = '/home/dereadi/scripts/claude/TELEGRAM_RECEIVED.txt'
    if os.path.exists(received_file):
        stat = os.stat(received_file)
        last_modified = datetime.fromtimestamp(stat.st_mtime)
        time_since = datetime.now() - last_modified
        
        with open(received_file, 'r') as f:
            lines = f.readlines()
            last_message = lines[-1].strip() if lines else "No messages"
        
        print(f"📱 LAST MESSAGE RECEIVED:")
        print(f"   {last_message}")
        print(f"   Received: {last_modified.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Time since: {time_since}")
        print("")
        
        if time_since > timedelta(hours=1):
            print("⚠️  No messages in over 1 hour!")
            print("   Bot may not be receiving messages properly")
        elif time_since > timedelta(minutes=10):
            print("📊 No recent activity (>10 minutes)")
        else:
            print("✅ Recent activity detected!")
    
    # Check if processes are running
    print("\n🔄 PROCESS STATUS:")
    wrapper_running = os.system("ps aux | grep ganuda_persistent_wrapper.py | grep -v grep > /dev/null 2>&1") == 0
    bot_running = os.system("ps aux | grep ganuda_high_fitness_bot.py | grep -v grep > /dev/null 2>&1") == 0
    
    print(f"   Wrapper: {'✅ Running' if wrapper_running else '❌ Not running'}")
    print(f"   Bot: {'✅ Running' if bot_running else '❌ Not running'}")
    
    # Check persistent log
    print("\n📜 PERSISTENT LOG STATUS:")
    log_file = '/home/dereadi/scripts/claude/ganuda_persistent.log'
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            lines = f.readlines()
            if lines:
                last_log = lines[-1].strip()
                print(f"   Last log: {last_log}")
                
                # Check for errors
                error_count = sum(1 for line in lines if '❌' in line or 'Error' in line or 'error' in line)
                if error_count > 0:
                    print(f"   ⚠️  Found {error_count} error(s) in log")
    
    # Analysis
    print("\n🏛️ CHEROKEE COUNCIL ANALYSIS:")
    
    if time_since > timedelta(hours=24):
        print("🐿️ Flying Squirrel: 'The bot hasn't seen activity in over a day!'")
        print("🦀 Crawdad: 'Walking backward, this looks like attempt #1 again'")
        print("🐺 Coyote: 'Time to send a test message to wake it up!'")
    elif time_since > timedelta(hours=1):
        print("🐢 Turtle: 'Patience, but verify - send a test message'")
        print("🕷️ Spider: 'The web may need reconnection to Telegram'")
    else:
        print("✅ Bot appears to be ready for messages!")
        print("🦅 Eagle Eye: 'All systems operational from above'")
    
    print("\n" + "=" * 60)
    print("📱 TO TEST: Send 'you there?' to @ganudabot on Telegram")
    print("=" * 60)

if __name__ == "__main__":
    check_status()