#!/usr/bin/env python3
"""
🎖️ SPECIALIST ARMY CONTROLLER
Unified command center for all specialists
"""

import subprocess
import time
import os
import signal
import json
from datetime import datetime

print("🎖️ SPECIALIST ARMY CONTROLLER")
print("=" * 60)

class SpecialistArmy:
    def __init__(self):
        self.specialists = {
            'mean_reversion': {
                'script': 'mean_reversion_specialist_v2.py',
                'process': None,
                'symbol': '🎯'
            },
            'trend': {
                'script': 'trend_specialist_v2.py', 
                'process': None,
                'symbol': '📈'
            },
            'volatility': {
                'script': 'volatility_specialist_v2.py',
                'process': None,
                'symbol': '⚡'
            },
            'breakout': {
                'script': 'breakout_specialist_v2.py',
                'process': None,
                'symbol': '🚀'
            }
        }
        self.running = False
        
    def start_specialist(self, name):
        """Start a single specialist"""
        spec = self.specialists[name]
        if spec['process'] is None or spec['process'].poll() is not None:
            try:
                spec['process'] = subprocess.Popen(
                    ['python3', spec['script']],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd='/home/dereadi/scripts/claude'
                )
                print(f"{spec['symbol']} {name.upper()} specialist deployed")
                return True
            except Exception as e:
                print(f"❌ Failed to start {name}: {e}")
                return False
        else:
            print(f"⚠️ {name} already running")
            return False
            
    def stop_specialist(self, name):
        """Stop a single specialist"""
        spec = self.specialists[name]
        if spec['process'] and spec['process'].poll() is None:
            spec['process'].terminate()
            time.sleep(1)
            if spec['process'].poll() is None:
                spec['process'].kill()
            spec['process'] = None
            print(f"⛔ {name.upper()} specialist terminated")
            
    def start_all(self):
        """Deploy the entire army"""
        print("\n🚀 DEPLOYING SPECIALIST ARMY...")
        self.running = True
        
        # Start specialists with delays to prevent race conditions
        for name in self.specialists:
            self.start_specialist(name)
            time.sleep(2)  # Stagger launches
            
        print("✅ All specialists deployed")
        
    def stop_all(self):
        """Recall the entire army"""
        print("\n⛔ RECALLING SPECIALIST ARMY...")
        self.running = False
        
        for name in self.specialists:
            self.stop_specialist(name)
            
        # Also kill any zombies
        subprocess.run(['pkill', '-f', 'specialist'], capture_output=True)
        print("✅ All specialists terminated")
        
    def status(self):
        """Check army status"""
        print("\n📊 SPECIALIST ARMY STATUS:")
        print("-" * 40)
        
        active = 0
        for name, spec in self.specialists.items():
            if spec['process'] and spec['process'].poll() is None:
                print(f"{spec['symbol']} {name}: ✅ ACTIVE")
                active += 1
            else:
                print(f"{spec['symbol']} {name}: ⭕ INACTIVE")
                
        print(f"\nActive specialists: {active}/{len(self.specialists)}")
        return active
        
    def monitor(self):
        """Monitor and restart crashed specialists"""
        print("\n👁️ MONITORING MODE ACTIVATED")
        print("Press Ctrl+C to stop")
        
        try:
            while self.running:
                # Check each specialist
                for name in self.specialists:
                    spec = self.specialists[name]
                    if spec['process'] is None or spec['process'].poll() is not None:
                        print(f"\n⚠️ {name} crashed, restarting...")
                        self.start_specialist(name)
                        
                # Show status every 5 minutes
                time.sleep(300)
                self.status()
                
        except KeyboardInterrupt:
            print("\n\n🛑 Shutdown signal received")
            self.stop_all()

# Main execution
if __name__ == "__main__":
    army = SpecialistArmy()
    
    print("\n🎖️ SPECIALIST ARMY COMMAND CENTER")
    print("Commands:")
    print("  1. START - Deploy all specialists")
    print("  2. STOP  - Terminate all specialists")
    print("  3. STATUS - Check army status")
    print("  4. MONITOR - Auto-restart mode")
    print("  5. EXIT - Quit controller")
    print()
    
    while True:
        command = input("Command> ").strip().upper()
        
        if command == "START" or command == "1":
            army.start_all()
        elif command == "STOP" or command == "2":
            army.stop_all()
        elif command == "STATUS" or command == "3":
            army.status()
        elif command == "MONITOR" or command == "4":
            army.monitor()
        elif command == "EXIT" or command == "5":
            if army.running:
                army.stop_all()
            print("👋 Controller shutting down")
            break
        else:
            print("❌ Unknown command")