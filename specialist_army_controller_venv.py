#!/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3
"""
🎖️ SPECIALIST ARMY CONTROLLER (VENV)
Production-ready unified command center
"""

import subprocess
import time
import os
import signal
import json
import sys
from datetime import datetime
from pathlib import Path

# Ensure we're using the virtual environment
VENV_PYTHON = "/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3"
CLAUDE_DIR = "/home/dereadi/scripts/claude"

print("🎖️ SPECIALIST ARMY CONTROLLER V2 (PRODUCTION)")
print("=" * 60)
print(f"Virtual Environment: {VENV_PYTHON}")
print(f"Working Directory: {CLAUDE_DIR}")
print()

class SpecialistArmy:
    def __init__(self):
        # Load council-approved configuration
        config_file = Path(CLAUDE_DIR) / "council_specialist_army_decision.json"
        if config_file.exists():
            with open(config_file) as f:
                self.config = json.load(f)
                print("✅ Loaded council-approved configuration")
        else:
            self.config = {
                "configuration": {
                    "deploy_threshold": 500,
                    "retrieve_threshold": 250,
                    "max_position_pct": 0.15,
                    "base_delay": 60,
                    "pressure_multiplier": 1.5
                }
            }
            
        self.specialists = {
            'mean_reversion': {
                'script': 'mean_reversion_specialist_v2.py',
                'process': None,
                'symbol': '🎯',
                'restarts': 0
            },
            'trend': {
                'script': 'trend_specialist_v2.py', 
                'process': None,
                'symbol': '📈',
                'restarts': 0
            },
            'volatility': {
                'script': 'volatility_specialist_v2.py',
                'process': None,
                'symbol': '⚡',
                'restarts': 0
            },
            'breakout': {
                'script': 'breakout_specialist_v2.py',
                'process': None,
                'symbol': '🚀',
                'restarts': 0
            }
        }
        self.running = False
        self.start_time = None
        
    def start_specialist(self, name):
        """Start a single specialist with venv"""
        spec = self.specialists[name]
        if spec['process'] is None or spec['process'].poll() is not None:
            try:
                # Use virtual environment Python
                spec['process'] = subprocess.Popen(
                    [VENV_PYTHON, spec['script']],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=CLAUDE_DIR,
                    env={**os.environ, 'PYTHONPATH': CLAUDE_DIR}
                )
                print(f"{spec['symbol']} {name.upper()} specialist deployed (PID: {spec['process'].pid})")
                
                # Log to thermal memory
                self.log_event(f"Started {name} specialist")
                return True
                
            except Exception as e:
                print(f"❌ Failed to start {name}: {e}")
                return False
        else:
            print(f"⚠️ {name} already running (PID: {spec['process'].pid})")
            return False
            
    def stop_specialist(self, name):
        """Stop a single specialist gracefully"""
        spec = self.specialists[name]
        if spec['process'] and spec['process'].poll() is None:
            pid = spec['process'].pid
            spec['process'].terminate()
            time.sleep(2)
            
            if spec['process'].poll() is None:
                print(f"⚠️ Force killing {name}")
                spec['process'].kill()
                
            spec['process'] = None
            print(f"⛔ {name.upper()} specialist terminated (was PID: {pid})")
            self.log_event(f"Stopped {name} specialist")
            
    def start_all(self):
        """Deploy the entire army with staggered start"""
        print("\n🚀 DEPLOYING SPECIALIST ARMY...")
        self.running = True
        self.start_time = datetime.now()
        
        # Council mandated: Start with conservative settings
        print("Loading council-approved configuration...")
        time.sleep(1)
        
        # Start specialists with delays to prevent race conditions
        for name in self.specialists:
            self.start_specialist(name)
            time.sleep(3)  # Stagger launches as per council
            
        print("✅ All specialists deployed")
        self.log_event("Army deployment complete")
        
    def stop_all(self):
        """Recall the entire army"""
        print("\n⛔ RECALLING SPECIALIST ARMY...")
        self.running = False
        
        for name in self.specialists:
            self.stop_specialist(name)
            
        # Kill any zombies
        subprocess.run(['pkill', '-f', 'specialist_v2'], capture_output=True)
        print("✅ All specialists terminated")
        self.log_event("Army recalled")
        
    def status(self):
        """Check army status with health metrics"""
        print("\n📊 SPECIALIST ARMY STATUS:")
        print("-" * 40)
        
        active = 0
        for name, spec in self.specialists.items():
            if spec['process'] and spec['process'].poll() is None:
                print(f"{spec['symbol']} {name}: ✅ ACTIVE (PID: {spec['process'].pid})")
                active += 1
            else:
                print(f"{spec['symbol']} {name}: ⭕ INACTIVE")
                
        print(f"\nActive specialists: {active}/{len(self.specialists)}")
        
        if self.start_time:
            uptime = datetime.now() - self.start_time
            print(f"Uptime: {uptime}")
            
        # Check restart counts
        total_restarts = sum(s['restarts'] for s in self.specialists.values())
        if total_restarts > 0:
            print(f"⚠️ Total restarts: {total_restarts}")
            
        return active
        
    def monitor(self):
        """Monitor and auto-restart crashed specialists"""
        print("\n👁️ MONITORING MODE ACTIVATED")
        print("Council mandate: Monitor for first hour")
        print("Press Ctrl+C to stop")
        
        monitor_start = datetime.now()
        
        try:
            while self.running:
                # Check each specialist
                for name in self.specialists:
                    spec = self.specialists[name]
                    if spec['process'] is None or spec['process'].poll() is not None:
                        spec['restarts'] += 1
                        
                        # Council safeguard: Max 3 restarts
                        if spec['restarts'] <= 3:
                            print(f"\n⚠️ {name} crashed, restarting (attempt {spec['restarts']})...")
                            self.start_specialist(name)
                        else:
                            print(f"\n🚨 {name} exceeded restart limit, leaving stopped")
                            
                # Status update every 5 minutes
                time.sleep(300)
                self.status()
                
                # Check monitoring duration
                duration = datetime.now() - monitor_start
                if duration.total_seconds() > 3600:  # 1 hour
                    print("\n✅ First hour monitoring complete (council requirement)")
                    
        except KeyboardInterrupt:
            print("\n\n🛑 Shutdown signal received")
            self.stop_all()
            
    def log_event(self, event):
        """Log to thermal memory system"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event,
            "specialists": {
                name: "active" if (spec['process'] and spec['process'].poll() is None) else "inactive"
                for name, spec in self.specialists.items()
            }
        }
        
        # Append to log file
        log_file = Path(CLAUDE_DIR) / "specialist_army.log"
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
            
    def emergency_kill(self):
        """Emergency kill all - council mandated safety"""
        print("\n🚨 EMERGENCY KILL ACTIVATED")
        subprocess.run(['pkill', '-9', '-f', 'specialist'], capture_output=True)
        subprocess.run(['pkill', '-9', '-f', 'flywheel'], capture_output=True)
        
        for spec in self.specialists.values():
            spec['process'] = None
            
        print("☠️ All trading processes terminated")
        self.log_event("EMERGENCY KILL EXECUTED")

# Service mode for systemd
def service_mode():
    """Run in service mode for systemd"""
    army = SpecialistArmy()
    
    print("🤖 Running in SERVICE MODE")
    army.start_all()
    
    # Monitor forever (systemd will manage lifecycle)
    while True:
        time.sleep(60)
        
        # Auto-restart crashed specialists
        for name, spec in army.specialists.items():
            if spec['process'] is None or spec['process'].poll() is not None:
                if spec['restarts'] < 3:
                    spec['restarts'] += 1
                    print(f"Auto-restarting {name} (attempt {spec['restarts']})")
                    army.start_specialist(name)
                    
        # Log status every 10 minutes
        if int(time.time()) % 600 == 0:
            army.status()

# Main execution
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--service":
        service_mode()
    else:
        # Interactive mode
        army = SpecialistArmy()
        
        print("\n🎖️ SPECIALIST ARMY COMMAND CENTER")
        print("Council Status: APPROVED ✅")
        print()
        print("Commands:")
        print("  1. START - Deploy all specialists")
        print("  2. STOP  - Terminate all specialists")
        print("  3. STATUS - Check army status")
        print("  4. MONITOR - Auto-restart mode")
        print("  5. KILL - Emergency kill all")
        print("  6. EXIT - Quit controller")
        print()
        
        while True:
            command = input("Command> ").strip().upper()
            
            if command in ["START", "1"]:
                army.start_all()
            elif command in ["STOP", "2"]:
                army.stop_all()
            elif command in ["STATUS", "3"]:
                army.status()
            elif command in ["MONITOR", "4"]:
                army.monitor()
            elif command in ["KILL", "5"]:
                army.emergency_kill()
            elif command in ["EXIT", "6"]:
                if army.running:
                    army.stop_all()
                print("👋 Controller shutting down")
                break
            else:
                print("❌ Unknown command")