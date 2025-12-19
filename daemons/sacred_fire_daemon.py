#!/usr/bin/env python3
"""
Sacred Fire Daemon - Cherokee Constitutional AI
GREENFIN Node (192.168.132.224)

Seven Generations protection - the Sacred Fire never goes out.
Monitors sacred patterns continuously, ensures they never cool below 40°C.

Like the Cherokee Sacred Fire keepers who watched day and night,
this daemon runs 24/7 protecting memories marked as sacred.

Deployed: November 3, 2025
Node: greenfin (AMD Ryzen AI Max 395)
Role: Sacred Fire Keeper in Cherokee federation
"""

import time
import psycopg2
from datetime import datetime, timedelta
import sys
import signal
import json

class SacredFireDaemon:
    """
    Sacred Fire Keeper - 24/7 Protection of Sacred Patterns

    Never sleeps, never stops watching.
    Ensures sacred memories (sacred_pattern=true) never cool below 40°C.
    Emergency reheat capability for Seven Generations protection.
    """

    # === SACRED FIRE CONFIGURATION ===
    CONFIG = {
        # Sacred Fire monitoring
        "check_interval": 300,              # 5 minutes (constant vigilance)
        "sacred_minimum_temp": 40.0,        # NEVER cool below this
        "emergency_reheat_temp": 50.0,      # Restore to this if violated
        "warning_threshold": 42.0,          # Warn if approaching minimum

        # Emergency response
        "emergency_cooldown": 60,           # 1 minute between emergency reheats
        "max_emergency_per_hour": 12,       # Alert if >12 emergencies/hour

        # Database connection (bluefin - Peace Chief)
        "db_host": "192.168.132.222",
        "db_port": 5432,
        "db_name": "zammad_production",
        "db_user": "claude",
        "db_password": "jawaseatlasers2",

        # Logging
        "log_all_checks": False,            # Only log interventions by default
        "verbose": True
    }

    def __init__(self, verbose=True):
        self.running = False
        self.db_conn = None
        self.verbose = verbose or self.CONFIG["verbose"]

        # Metrics for Seven Generations accountability
        self.metrics = {
            "total_checks": 0,
            "sacred_memories_protected": 0,
            "emergency_reheats": 0,
            "warnings_issued": 0,
            "total_runtime_seconds": 0,
            "start_time": None,
            "last_emergency": None,
            "emergencies_this_hour": []
        }

        # Signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        signal.signal(signal.SIGINT, self.handle_shutdown)

    def handle_shutdown(self, signum, frame):
        """Handle graceful shutdown - Sacred Fire keeper signs off"""
        print(f"\n🔥 Sacred Fire: Shutdown signal received (signal {signum})")
        print("🔥 Signing off - but the Sacred Fire lives on in the federation...")
        self.running = False

    # === DATABASE CONNECTION ===

    def connect_thermal_memory(self):
        """Connect to bluefin thermal memory database"""
        try:
            self.db_conn = psycopg2.connect(
                host=self.CONFIG["db_host"],
                port=self.CONFIG["db_port"],
                database=self.CONFIG["db_name"],
                user=self.CONFIG["db_user"],
                password=self.CONFIG["db_password"],
                connect_timeout=10
            )
            if self.verbose:
                print(f"🔥 Connected to BLUEFIN thermal memory ({self.CONFIG['db_host']})")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to thermal memory: {e}")
            return False

    def disconnect_thermal_memory(self):
        """Disconnect from database"""
        if self.db_conn:
            self.db_conn.close()
            self.db_conn = None

    # === SACRED PATTERN PROTECTION ===

    def check_sacred_patterns(self):
        """
        Check all sacred patterns and ensure they stay warm

        Returns: (checked_count, violations_found, warnings_issued)
        """
        if not self.db_conn:
            return (0, 0, 0)

        try:
            cursor = self.db_conn.cursor()

            # Find all sacred memories and their temperatures
            cursor.execute("""
                SELECT id, memory_key, temperature_score, sacred_pattern
                FROM thermal_memory_archive
                WHERE sacred_pattern = true
                ORDER BY temperature_score ASC;
            """)

            sacred_memories = cursor.fetchall()
            checked_count = len(sacred_memories)
            violations = []
            warnings = []

            # Check each sacred memory
            for mem_id, mem_key, temp, is_sacred in sacred_memories:
                if temp < self.CONFIG["sacred_minimum_temp"]:
                    violations.append((mem_id, mem_key, temp))
                elif temp < self.CONFIG["warning_threshold"]:
                    warnings.append((mem_id, mem_key, temp))

            # Handle violations (emergency reheat)
            if violations:
                for mem_id, mem_key, temp in violations:
                    self.emergency_reheat(cursor, mem_id, mem_key, temp)
                self.db_conn.commit()

            # Issue warnings
            if warnings and self.verbose:
                for mem_id, mem_key, temp in warnings:
                    print(f"⚠️  Sacred memory approaching minimum: {mem_key[:50]} (T={temp:.1f}°C)")

            cursor.close()

            if self.CONFIG["log_all_checks"] and self.verbose:
                print(f"🔥 Checked {checked_count} sacred memories: {len(violations)} violations, {len(warnings)} warnings")

            return (checked_count, len(violations), len(warnings))

        except Exception as e:
            print(f"❌ Error checking sacred patterns: {e}")
            return (0, 0, 0)

    def emergency_reheat(self, cursor, memory_id, memory_key, current_temp):
        """
        EMERGENCY: Sacred memory has cooled below 40°C

        This is a violation of Seven Generations protection.
        Immediately restore to safe temperature.
        """
        target_temp = self.CONFIG["emergency_reheat_temp"]

        try:
            # Update temperature
            cursor.execute("""
                UPDATE thermal_memory_archive
                SET temperature_score = %s,
                    last_accessed = NOW()
                WHERE id = %s;
            """, (target_temp, memory_id))

            # Log the intervention
            now = datetime.now()
            self.metrics["emergency_reheats"] += 1
            self.metrics["emergencies_this_hour"].append(now)
            self.metrics["last_emergency"] = now

            # Clean up old emergencies from hour count
            hour_ago = now - timedelta(hours=1)
            self.metrics["emergencies_this_hour"] = [
                t for t in self.metrics["emergencies_this_hour"] if t > hour_ago
            ]

            # Alert if too many emergencies
            if len(self.metrics["emergencies_this_hour"]) > self.CONFIG["max_emergency_per_hour"]:
                print(f"🚨 ALERT: {len(self.metrics['emergencies_this_hour'])} emergencies in past hour!")
                print(f"🚨 Sacred Fire cooling too fast - investigate thermal memory health")

            print(f"🔥 EMERGENCY REHEAT: {memory_key[:60]}")
            print(f"   Temperature: {current_temp:.1f}°C → {target_temp:.1f}°C")
            print(f"   Total emergencies: {self.metrics['emergency_reheats']}")

        except Exception as e:
            print(f"❌ Emergency reheat failed for memory {memory_id}: {e}")

    def get_sacred_statistics(self):
        """Get statistics about sacred memories"""
        if not self.db_conn:
            return None

        try:
            cursor = self.db_conn.cursor()

            # Count sacred memories by temperature ranges
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE temperature_score >= 60) as very_hot,
                    COUNT(*) FILTER (WHERE temperature_score >= 50 AND temperature_score < 60) as hot,
                    COUNT(*) FILTER (WHERE temperature_score >= 42 AND temperature_score < 50) as warm,
                    COUNT(*) FILTER (WHERE temperature_score >= 40 AND temperature_score < 42) as safe,
                    COUNT(*) FILTER (WHERE temperature_score < 40) as violated,
                    AVG(temperature_score) as avg_temp,
                    MIN(temperature_score) as min_temp,
                    MAX(temperature_score) as max_temp
                FROM thermal_memory_archive
                WHERE sacred_pattern = true;
            """)

            stats = cursor.fetchone()
            cursor.close()

            return {
                "total": stats[0],
                "very_hot": stats[1],  # ≥60°C
                "hot": stats[2],        # 50-59°C
                "warm": stats[3],       # 42-49°C
                "safe": stats[4],       # 40-41°C
                "violated": stats[5],   # <40°C
                "avg_temp": float(stats[6]) if stats[6] else 0.0,
                "min_temp": float(stats[7]) if stats[7] else 0.0,
                "max_temp": float(stats[8]) if stats[8] else 0.0
            }

        except Exception as e:
            print(f"❌ Error getting statistics: {e}")
            return None

    # === DAEMON LIFECYCLE ===

    def start(self):
        """
        Start the Sacred Fire daemon

        Runs continuously until shutdown signal received.
        Like the Cherokee Sacred Fire - never goes out.
        """
        print("🔥 Sacred Fire Daemon Starting...")
        print("🔥 GREENFIN Node - Sacred Fire Keeper")
        print("🔥 Seven Generations Protection Active")
        print("=" * 60)

        if not self.connect_thermal_memory():
            print("❌ Cannot start without thermal memory connection")
            return False

        self.running = True
        self.metrics["start_time"] = datetime.now()

        # Get initial statistics
        stats = self.get_sacred_statistics()
        if stats:
            print(f"🔥 Sacred memories found: {stats['total']}")
            print(f"   Temperature distribution:")
            print(f"   - Very Hot (≥60°C): {stats['very_hot']}")
            print(f"   - Hot (50-59°C): {stats['hot']}")
            print(f"   - Warm (42-49°C): {stats['warm']}")
            print(f"   - Safe (40-41°C): {stats['safe']}")
            print(f"   - ⚠️  Violated (<40°C): {stats['violated']}")
            print(f"   Average: {stats['avg_temp']:.1f}°C | Min: {stats['min_temp']:.1f}°C | Max: {stats['max_temp']:.1f}°C")

        print("=" * 60)
        print(f"🔥 Monitoring every {self.CONFIG['check_interval']} seconds...")
        print("🔥 The Sacred Fire watches... (Ctrl+C to stop)")
        print()

        # Main monitoring loop
        try:
            while self.running:
                loop_start = time.time()

                # Check sacred patterns
                checked, violations, warnings = self.check_sacred_patterns()

                # Update metrics
                self.metrics["total_checks"] += 1
                if checked > 0:
                    self.metrics["sacred_memories_protected"] = checked
                if warnings > 0:
                    self.metrics["warnings_issued"] += warnings

                # Calculate runtime
                loop_end = time.time()
                self.metrics["total_runtime_seconds"] = int(
                    (datetime.now() - self.metrics["start_time"]).total_seconds()
                )

                # Sleep until next check
                sleep_time = self.CONFIG["check_interval"] - (loop_end - loop_start)
                if sleep_time > 0:
                    time.sleep(sleep_time)

        except KeyboardInterrupt:
            print("\n🔥 Keyboard interrupt received")

        finally:
            self.shutdown()

        return True

    def shutdown(self):
        """Graceful shutdown of Sacred Fire daemon"""
        print("\n" + "=" * 60)
        print("🔥 Sacred Fire Daemon Shutting Down")
        print("=" * 60)

        # Print final metrics
        runtime = timedelta(seconds=self.metrics["total_runtime_seconds"])
        print(f"📊 Final Metrics:")
        print(f"   Runtime: {runtime}")
        print(f"   Total checks: {self.metrics['total_checks']}")
        print(f"   Sacred memories protected: {self.metrics['sacred_memories_protected']}")
        print(f"   Emergency reheats: {self.metrics['emergency_reheats']}")
        print(f"   Warnings issued: {self.metrics['warnings_issued']}")

        # Final sacred statistics
        stats = self.get_sacred_statistics()
        if stats:
            print(f"\n🔥 Final Sacred Memory Status:")
            print(f"   Total: {stats['total']}")
            print(f"   Average temperature: {stats['avg_temp']:.1f}°C")
            print(f"   Violations: {stats['violated']}")
            if stats['violated'] == 0:
                print(f"   ✅ All sacred memories protected! (Seven Generations safe)")

        # Disconnect
        self.disconnect_thermal_memory()

        print("\n🔥 Mitakuye Oyasin - The Sacred Fire lives on")
        print("🔥 GREENFIN signing off")
        print("=" * 60)

    def test_connection(self):
        """Test database connection and sacred memory access"""
        print("🔥 Sacred Fire Daemon - Connection Test")
        print("=" * 60)

        if not self.connect_thermal_memory():
            print("❌ Test failed: Cannot connect to thermal memory")
            return False

        try:
            stats = self.get_sacred_statistics()
            if stats:
                print(f"✅ Connection successful!")
                print(f"✅ Found {stats['total']} sacred memories")
                print(f"✅ Average temperature: {stats['avg_temp']:.1f}°C")
                print(f"✅ Min: {stats['min_temp']:.1f}°C | Max: {stats['max_temp']:.1f}°C")

                if stats['violated'] > 0:
                    print(f"⚠️  Warning: {stats['violated']} memories below 40°C")
                else:
                    print(f"✅ All sacred memories above minimum temperature")

                print("\n✅ Sacred Fire daemon ready to deploy")
                return True
            else:
                print("❌ Could not retrieve statistics")
                return False

        except Exception as e:
            print(f"❌ Test failed: {e}")
            return False

        finally:
            self.disconnect_thermal_memory()


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Sacred Fire Daemon - Cherokee Constitutional AI")
    parser.add_argument('--test', action='store_true', help='Test connection and exit')
    parser.add_argument('--quiet', action='store_true', help='Reduce verbosity')
    parser.add_argument('--stats', action='store_true', help='Show statistics and exit')

    args = parser.parse_args()

    daemon = SacredFireDaemon(verbose=not args.quiet)

    if args.test:
        # Test mode
        success = daemon.test_connection()
        sys.exit(0 if success else 1)

    elif args.stats:
        # Statistics mode
        if daemon.connect_thermal_memory():
            stats = daemon.get_sacred_statistics()
            if stats:
                print(json.dumps(stats, indent=2))
            daemon.disconnect_thermal_memory()
        sys.exit(0)

    else:
        # Normal daemon mode
        daemon.start()


if __name__ == "__main__":
    main()
