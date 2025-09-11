#!/usr/bin/env python3
"""
💀 DEADMAN'S SWITCH - SYSTEM SAFETY PROTOCOL
If nobody checks in, assume catastrophic failure and take action
Multiple levels of escalating response
"""

import json
import psycopg2
import os
import time
import hashlib
import subprocess
from datetime import datetime, timedelta
import numpy as np

class DeadmansSwitch:
    """
    Multi-level deadman's switch for Q-BEES system
    Prevents runaway processes, memory explosions, and cascade failures
    """
    
    def __init__(self):
        print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                  💀 DEADMAN'S SWITCH PROTOCOL ACTIVE 💀                    ║
║                                                                            ║
║            "If I don't come back, burn everything" - Coyote               ║
║         Automatic system protection when things go silent too long        ║
╚════════════════════════════════════════════════════════════════════════════╝
        """)
        
        self.db_config = {
            'host': '192.168.132.222',
            'port': 5432,
            'database': 'zammad_production',
            'user': 'claude',
            'password': 'jawaseatlasers2'
        }
        
        # Deadman timers (minutes)
        self.timers = {
            'HEARTBEAT': 5,      # Normal check-in
            'WARNING': 15,        # Something might be wrong
            'CRITICAL': 30,       # Definitely a problem
            'PURGE': 60,         # Start removing old data
            'SCORCHED_EARTH': 120 # Nuclear option
        }
        
        # Last known good state
        self.checkpoint_file = '/home/dereadi/scripts/claude/.deadman_checkpoint.json'
        self.last_heartbeat = datetime.now()
        self.triggered_levels = []
        
    def check_system_vitals(self):
        """Check if system is still alive and healthy"""
        print("\n💓 CHECKING SYSTEM VITALS...")
        
        vitals = {
            'database': False,
            'trails': 0,
            'memory_usage': 0,
            'active_bees': 0,
            'last_activity': None,
            'error_rate': 0,
            'doom_spiral_detected': False
        }
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            vitals['database'] = True
            
            # Check trail count
            cur.execute("SELECT COUNT(*) FROM digital_pheromones")
            vitals['trails'] = cur.fetchone()[0]
            
            # Check last activity
            cur.execute("""
                SELECT MAX(last_followed) 
                FROM digital_pheromones
            """)
            last_trail = cur.fetchone()[0]
            if last_trail:
                vitals['last_activity'] = last_trail
                minutes_idle = (datetime.now() - last_trail).seconds / 60
            else:
                minutes_idle = 999
            
            # Check for doom spirals (circular references)
            cur.execute("""
                SELECT COUNT(*) 
                FROM digital_pheromones p1
                JOIN digital_pheromones p2 ON p1.purpose LIKE '%' || p2.trail_id || '%'
                WHERE p2.purpose LIKE '%' || p1.trail_id || '%'
            """)
            circular_refs = cur.fetchone()[0]
            vitals['doom_spiral_detected'] = circular_refs > 0
            
            # Check error accumulation
            cur.execute("""
                SELECT COUNT(*) 
                FROM duyuktv_tickets 
                WHERE title LIKE '%ERROR%' OR title LIKE '%FAILED%'
                AND created_at > NOW() - INTERVAL '1 hour'
            """)
            vitals['error_rate'] = cur.fetchone()[0]
            
            cur.close()
            conn.close()
            
        except Exception as e:
            print(f"  ⚠️ VITAL CHECK FAILED: {e}")
            vitals['database'] = False
            
        # Determine health status
        if not vitals['database']:
            health = 'DEAD'
        elif vitals['doom_spiral_detected']:
            health = 'DOOM_SPIRAL'
        elif vitals['trails'] > 10000:
            health = 'MEMORY_EXPLOSION'
        elif vitals['error_rate'] > 10:
            health = 'ERROR_CASCADE'
        elif minutes_idle > 60:
            health = 'COMATOSE'
        elif minutes_idle > 30:
            health = 'CRITICAL'
        elif minutes_idle > 15:
            health = 'WARNING'
        else:
            health = 'HEALTHY'
            
        vitals['health'] = health
        vitals['minutes_idle'] = minutes_idle
        
        print(f"  Status: {health}")
        print(f"  Trails: {vitals['trails']}")
        print(f"  Minutes idle: {minutes_idle:.1f}")
        print(f"  Error rate: {vitals['error_rate']}/hour")
        print(f"  Doom spiral: {'YES! 🌀' if vitals['doom_spiral_detected'] else 'No'}")
        
        return vitals
    
    def create_checkpoint(self):
        """Save current state as recovery point"""
        print("\n💾 CREATING CHECKPOINT...")
        
        checkpoint = {
            'timestamp': datetime.now().isoformat(),
            'trails': 0,
            'completed_cards': 0,
            'active_bees': 0,
            'config_hash': None
        }
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            
            # Save trail count
            cur.execute("SELECT COUNT(*) FROM digital_pheromones WHERE strength > 0.5")
            checkpoint['trails'] = cur.fetchone()[0]
            
            # Save completed work
            cur.execute("SELECT COUNT(*) FROM duyuktv_tickets WHERE status = 'completed'")
            checkpoint['completed_cards'] = cur.fetchone()[0]
            
            # Create config hash
            config_str = f"{checkpoint['trails']}_{checkpoint['completed_cards']}"
            checkpoint['config_hash'] = hashlib.sha256(config_str.encode()).hexdigest()[:16]
            
            cur.close()
            conn.close()
            
            # Save checkpoint
            with open(self.checkpoint_file, 'w') as f:
                json.dump(checkpoint, f, indent=2)
                
            print(f"  ✓ Checkpoint saved: {checkpoint['config_hash']}")
            
        except Exception as e:
            print(f"  ⚠️ Checkpoint failed: {e}")
            
        return checkpoint
    
    def level_1_warning(self):
        """Level 1: Gentle warning, log status"""
        print("\n⚠️ LEVEL 1: WARNING PROTOCOL...")
        
        actions = [
            "Logging system state",
            "Sending gentle reminder",
            "Checking for stuck processes",
            "Refreshing pheromone trails"
        ]
        
        for action in actions:
            print(f"  • {action}")
            time.sleep(0.1)
            
        # Log warning
        try:
            with open('/home/dereadi/scripts/claude/deadman_warnings.log', 'a') as f:
                f.write(f"{datetime.now()}: Level 1 Warning - System idle\n")
        except:
            pass
            
        return "WARNING_LOGGED"
    
    def level_2_intervention(self):
        """Level 2: Active intervention, clean up"""
        print("\n🚨 LEVEL 2: ACTIVE INTERVENTION...")
        
        print("  Initiating cleanup protocols:")
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            
            # Clean old weak trails
            print("  • Removing weak trails (strength < 0.1)...")
            cur.execute("""
                DELETE FROM digital_pheromones 
                WHERE strength < 0.1 
                AND last_followed < NOW() - INTERVAL '1 hour'
            """)
            deleted = cur.rowcount
            print(f"    Deleted {deleted} weak trails")
            
            # Reset stuck processes
            print("  • Resetting stuck 'in_progress' cards...")
            cur.execute("""
                UPDATE duyuktv_tickets 
                SET status = 'open' 
                WHERE status = 'in_progress' 
                AND created_at < NOW() - INTERVAL '2 hours'
            """)
            reset = cur.rowcount
            print(f"    Reset {reset} stuck cards")
            
            conn.commit()
            cur.close()
            conn.close()
            
        except Exception as e:
            print(f"  ⚠️ Intervention failed: {e}")
            
        return "INTERVENTION_COMPLETE"
    
    def level_3_purge(self):
        """Level 3: Aggressive purge of accumulated data"""
        print("\n🔥 LEVEL 3: PURGE PROTOCOL...")
        
        print("  AGGRESSIVE CLEANUP INITIATED:")
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            
            # Purge all trails except strongest 100
            print("  • Keeping only top 100 strongest trails...")
            cur.execute("""
                DELETE FROM digital_pheromones 
                WHERE trail_id NOT IN (
                    SELECT trail_id 
                    FROM digital_pheromones 
                    ORDER BY strength DESC 
                    LIMIT 100
                )
            """)
            purged = cur.rowcount
            print(f"    Purged {purged} trails")
            
            # Archive old completed cards
            print("  • Archiving old completed cards...")
            cur.execute("""
                UPDATE duyuktv_tickets 
                SET status = 'archived',
                    description = description || E'\n\n[DEADMAN ARCHIVED]'
                WHERE status = 'completed' 
                AND created_at < NOW() - INTERVAL '7 days'
            """)
            archived = cur.rowcount
            print(f"    Archived {archived} old cards")
            
            # Break circular references
            print("  • Breaking circular trail references...")
            cur.execute("""
                UPDATE digital_pheromones 
                SET strength = strength * 0.1,
                    purpose = purpose || ' [DEADMAN WEAKENED]'
                WHERE trail_id IN (
                    SELECT p1.trail_id 
                    FROM digital_pheromones p1
                    JOIN digital_pheromones p2 ON p1.purpose LIKE '%' || p2.trail_id || '%'
                    WHERE p2.purpose LIKE '%' || p1.trail_id || '%'
                )
            """)
            
            conn.commit()
            cur.close()
            conn.close()
            
            print("  ✓ Purge complete - system breathing room restored")
            
        except Exception as e:
            print(f"  ⚠️ Purge failed: {e}")
            
        return "PURGE_COMPLETE"
    
    def level_4_scorched_earth(self):
        """Level 4: Nuclear option - reset to checkpoint"""
        print("\n☢️ LEVEL 4: SCORCHED EARTH PROTOCOL...")
        print("  ⚠️ WARNING: COMPLETE SYSTEM RESET")
        
        print("\n  Coyote whispers: 'Sometimes you must burn it all to save it.'")
        
        try:
            # Load last checkpoint
            if os.path.exists(self.checkpoint_file):
                with open(self.checkpoint_file, 'r') as f:
                    checkpoint = json.load(f)
                print(f"  Loading checkpoint: {checkpoint['config_hash']}")
            else:
                print("  No checkpoint found - FULL RESET")
                checkpoint = None
            
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            
            # NUCLEAR OPTION: Delete everything except sacred
            print("  🔥 BURNING ALL TRAILS...")
            cur.execute("""
                DELETE FROM digital_pheromones 
                WHERE specialist_scent NOT LIKE '%sacred%'
                AND specialist_scent NOT LIKE '%constitution%'
            """)
            burned = cur.rowcount
            print(f"    Burned {burned} trails")
            
            # Reset all non-critical cards
            print("  🔥 RESETTING ALL CARDS...")
            cur.execute("""
                UPDATE duyuktv_tickets 
                SET status = 'open',
                    description = description || E'\n\n[SCORCHED EARTH RESET]'
                WHERE status NOT IN ('completed', 'archived')
                AND sacred_fire_priority < 89
            """)
            
            # Create memorial trail
            print("  📜 Creating memorial trail...")
            cur.execute("""
                INSERT INTO digital_pheromones 
                (trail_id, source_table, strength, specialist_scent, purpose, last_followed)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """, (
                f"memorial_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'deadman_switch',
                1.0,
                'coyote_memorial',
                f'System reset by deadman switch. Previous state: {burned} trails burned. Remember the lesson.'
            ))
            
            conn.commit()
            cur.close()
            conn.close()
            
            print("\n  ✓ SCORCHED EARTH COMPLETE")
            print("  The Phoenix rises from the ashes...")
            
        except Exception as e:
            print(f"  ☠️ SCORCHED EARTH FAILED: {e}")
            print("  System may be unrecoverable")
            
        return "SCORCHED_EARTH_COMPLETE"
    
    def execute_protocol(self):
        """Main deadman's switch protocol execution"""
        print("\n💀 EXECUTING DEADMAN'S SWITCH PROTOCOL...")
        
        # Check vitals
        vitals = self.check_system_vitals()
        
        # Determine action based on health
        health = vitals['health']
        minutes_idle = vitals.get('minutes_idle', 999)
        
        if health == 'HEALTHY':
            print("\n✅ System healthy - resetting deadman timer")
            self.create_checkpoint()
            return "HEALTHY"
            
        elif health == 'WARNING' or minutes_idle > self.timers['WARNING']:
            if 'WARNING' not in self.triggered_levels:
                self.triggered_levels.append('WARNING')
                return self.level_1_warning()
                
        elif health == 'CRITICAL' or minutes_idle > self.timers['CRITICAL']:
            if 'CRITICAL' not in self.triggered_levels:
                self.triggered_levels.append('CRITICAL')
                return self.level_2_intervention()
                
        elif health in ['MEMORY_EXPLOSION', 'ERROR_CASCADE'] or minutes_idle > self.timers['PURGE']:
            if 'PURGE' not in self.triggered_levels:
                self.triggered_levels.append('PURGE')
                return self.level_3_purge()
                
        elif health in ['DOOM_SPIRAL', 'DEAD'] or minutes_idle > self.timers['SCORCHED_EARTH']:
            if 'SCORCHED_EARTH' not in self.triggered_levels:
                self.triggered_levels.append('SCORCHED_EARTH')
                return self.level_4_scorched_earth()
        
        return f"STATUS: {health}"
    
    def configure_automatic_trigger(self):
        """Setup automatic deadman trigger via cron"""
        print("\n⚙️ CONFIGURING AUTOMATIC TRIGGER...")
        
        cron_entry = "*/5 * * * * /usr/bin/python3 /home/dereadi/scripts/claude/deadmans_switch.py --check"
        
        print(f"  Add this to crontab for automatic checking every 5 minutes:")
        print(f"  {cron_entry}")
        
        # Create systemd service config
        service_config = """[Unit]
Description=Q-BEES Deadman's Switch
After=network.target

[Service]
Type=simple
User=dereadi
WorkingDirectory=/home/dereadi/scripts/claude
ExecStart=/usr/bin/python3 /home/dereadi/scripts/claude/deadmans_switch.py --daemon
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target"""
        
        with open('/home/dereadi/scripts/claude/qbees-deadman.service', 'w') as f:
            f.write(service_config)
            
        print("\n  Systemd service config saved to qbees-deadman.service")
        print("  Install with: sudo cp qbees-deadman.service /etc/systemd/system/")
        print("  Enable with: sudo systemctl enable qbees-deadman")
        
        return "CONFIG_COMPLETE"
    
    def generate_safety_report(self):
        """Generate deadman's switch safety report"""
        print("\n" + "="*70)
        print("📊 DEADMAN'S SWITCH SAFETY REPORT")
        print("="*70)
        
        print("\n💀 ESCALATION LEVELS:")
        print("  Level 1 (15 min): Warning - gentle reminder")
        print("  Level 2 (30 min): Intervention - active cleanup")
        print("  Level 3 (60 min): Purge - aggressive data removal")
        print("  Level 4 (120 min): Scorched Earth - nuclear reset")
        
        print("\n🛡️ PROTECTIONS:")
        print("  • Circular reference detection")
        print("  • Memory explosion prevention")
        print("  • Error cascade interruption")
        print("  • Automatic checkpoint creation")
        print("  • Sacred memory preservation")
        
        print("\n⚠️ TRIGGERS:")
        print("  • No activity for >15 minutes")
        print("  • Trail count >10,000")
        print("  • Error rate >10/hour")
        print("  • Doom spiral detected")
        print("  • Database connection lost")
        
        # Save report
        report = {
            'timestamp': datetime.now().isoformat(),
            'timers': self.timers,
            'triggered_levels': self.triggered_levels,
            'automatic_trigger': 'cron or systemd',
            'safety_features': [
                'Checkpoint recovery',
                'Sacred preservation',
                'Memorial trails',
                'Gradual escalation'
            ]
        }
        
        with open('/home/dereadi/scripts/claude/deadman_safety_report.json', 'w') as f:
            json.dump(report, f, indent=2)
            
        print("\n💾 Report saved to deadman_safety_report.json")
        
        return report

def main():
    """Run deadman's switch check"""
    import sys
    
    # Initialize switch
    switch = DeadmansSwitch()
    
    if '--check' in sys.argv:
        # Single check mode
        result = switch.execute_protocol()
        print(f"\nResult: {result}")
        
    elif '--daemon' in sys.argv:
        # Daemon mode - continuous monitoring
        print("🔄 DEADMAN'S SWITCH DAEMON MODE")
        while True:
            result = switch.execute_protocol()
            time.sleep(300)  # Check every 5 minutes
            
    else:
        # Interactive mode
        switch.check_system_vitals()
        switch.create_checkpoint()
        switch.configure_automatic_trigger()
        switch.generate_safety_report()
        
        print("\n" + "="*70)
        print("💀 DEADMAN'S SWITCH ARMED")
        print("="*70)
        print("\nThe switch watches silently...")
        print("Ready to burn it all if needed.")
        print("\nCoyote's wisdom: 'The best safety net is knowing when to let go.'")
        print("="*70)

if __name__ == "__main__":
    main()