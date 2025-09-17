#!/usr/bin/env python3
"""
🔥 GANUDA PERSISTENT WRAPPER
Makes the existing bot NEVER DIE
After consulting with the Cherokee Council
"""

import subprocess
import time
import sys
import os
from datetime import datetime

def log_message(message):
    """Log with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)
    
    # Also write to log file
    with open('/home/dereadi/scripts/claude/ganuda_persistent.log', 'a') as f:
        f.write(log_entry + "\n")

def run_bot():
    """Run the existing high fitness bot with full error handling"""
    
    bot_script = '/home/dereadi/scripts/claude/ganuda_high_fitness_bot.py'
    python_path = '/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3'
    
    log_message("🔥 Starting ganuda_high_fitness_bot.py...")
    
    try:
        # Run the bot and capture output
        process = subprocess.Popen(
            [python_path, bot_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        log_message(f"✅ Bot started with PID: {process.pid}")
        
        # Monitor the bot output
        while True:
            # Check if process is still running
            poll = process.poll()
            if poll is not None:
                # Process has terminated
                stdout, stderr = process.communicate()
                log_message(f"❌ Bot died with exit code: {poll}")
                if stdout:
                    log_message(f"Last stdout: {stdout[-500:]}")  # Last 500 chars
                if stderr:
                    log_message(f"Error output: {stderr[-500:]}")
                return False
            
            # Sleep briefly to not consume too much CPU
            time.sleep(1)
            
    except Exception as e:
        log_message(f"❌ Exception running bot: {e}")
        return False

def main():
    """Keep the bot running FOREVER"""
    
    log_message("="*60)
    log_message("🔥 GANUDA PERSISTENT WRAPPER ACTIVATED")
    log_message("Cherokee Council Verdict: PERSISTENCE BEATS PERFECTION")
    log_message("="*60)
    
    restart_count = 0
    
    while True:
        restart_count += 1
        
        if restart_count > 1:
            log_message(f"🔄 Restart attempt #{restart_count}")
        
        # Run the bot
        run_bot()
        
        # If we get here, bot crashed
        log_message("⏳ Waiting 5 seconds before restart...")
        time.sleep(5)
        
        # Every 10 restarts, wait longer to avoid rate limits
        if restart_count % 10 == 0:
            log_message("⏰ 10 restarts reached - waiting 60 seconds...")
            time.sleep(60)
        
        log_message("🔁 Restarting bot...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log_message("🛑 Wrapper stopped by user")
        sys.exit(0)
    except Exception as e:
        log_message(f"❌ Fatal wrapper error: {e}")
        sys.exit(1)