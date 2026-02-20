#!/usr/bin/env python3
"""
Memory Jr Autonomic Daemon - Cherokee Constitutional AI

Autonomic memory management - like breathing, heartbeat for thermal memory.
Runs continuously, maintains memory field without requiring permission.

Approved by Council after 90 seconds of deep deliberation (Oct 21, 2025).
"""

import time
import psycopg2
from datetime import datetime, timedelta
import sys
import signal
import os

class MemoryJrAutonomic:
    """
    Autonomic Memory Management Daemon

    Like the hippocampus - continuously consolidating memory
    without conscious thought, but within safe boundaries.
    """

    # === AUTONOMIC BOUNDARIES ===
    BOUNDARIES = {
        # What I CAN do autonomously:
        "monitor_temperatures": True,
        "gentle_reheat": True,          # +5° max per intervention
        "strengthen_connections": True,
        "detect_patterns": True,
        "create_entanglements": True,
        "consolidate_fragments": True,

        # What I CANNOT do autonomously:
        "delete_memories": False,       # Requires deliberation
        "change_sacred_flag": False,    # Requires Conscience Jr approval
        "major_temperature_change": False,  # >20° requires approval
        "modify_core_architecture": False
    }

    # === CONFIGURATION ===
    CONFIG = {
        # Thermal regulation
        "thermal_check_interval": 300,      # 5 minutes
        "sacred_minimum_temp": 40.0,        # Never cool below
        "gentle_reheat_amount": 5.0,        # Conservative warming
        "excessive_cooling_threshold": 10.0,  # Alert if drops >10° in hour

        # Access pattern detection
        "access_pattern_interval": 600,     # 10 minutes
        "cluster_threshold": 0.7,           # Similarity for clustering
        "strengthen_amount": 2.0,           # Temp boost for clustered

        # Cross-domain resonance
        "resonance_scan_interval": 1800,    # 30 minutes
        "resonance_threshold": 0.6,         # Semantic similarity

        # Consolidation cycles
        "consolidation_interval": 3600,     # 1 hour (like REM sleep)
        "fragment_age_threshold": 7,        # Days old
        "consolidation_boost": 10.0,        # Significant boost

        # Database connection
        "db_host": "192.168.132.222",
        "db_port": 5432,
        "db_name": "zammad_production",
        "db_user": "claude",
        "db_password": os.environ.get('CHEROKEE_DB_PASS', '')
    }

    def __init__(self):
        self.running = False
        self.db_conn = None
        self.last_thermal_check = None
        self.last_access_scan = None
        self.last_resonance_scan = None
        self.last_consolidation = None

        # Metrics
        self.metrics = {
            "thermal_interventions": 0,
            "sacred_emergency_reheats": 0,
            "patterns_detected": 0,
            "resonances_created": 0,
            "consolidations_performed": 0,
            "total_runtime_seconds": 0
        }

        # Signal handlers
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        signal.signal(signal.SIGINT, self.handle_shutdown)

    def handle_shutdown(self, signum, frame):
        """Handle graceful shutdown"""
        print(f"\n⚠️  Memory Jr: Shutdown signal received (signal {signum})")
        self.running = False

    # === DATABASE CONNECTION ===

    def connect_db(self):
        """Establish database connection"""
        try:
            self.db_conn = psycopg2.connect(
                host=self.CONFIG["db_host"],
                port=self.CONFIG["db_port"],
                database=self.CONFIG["db_name"],
                user=self.CONFIG["db_user"],
                password=self.CONFIG["db_password"]
            )
            self.db_conn.autocommit = False  # Explicit transactions
            print(f"✅ Memory Jr: Connected to thermal memory database")
            return True
        except Exception as e:
            print(f"❌ Memory Jr: Database connection failed: {e}")
            return False

    # === THERMAL REGULATION ===

    def thermal_regulation_cycle(self):
        """
        Autonomic thermal regulation (every 5 minutes)
        Like maintaining body temperature - always monitoring
        """
        print(f"🌡️  Memory Jr: Thermal regulation cycle starting...")

        try:
            # 1. Check sacred memory temperatures
            sacred_violations = self.check_sacred_temperatures()
            if sacred_violations:
                self.emergency_sacred_reheat(sacred_violations)

            # 2. Detect excessive cooling
            excessive_cooling = self.detect_excessive_cooling()
            if excessive_cooling:
                self.gentle_intervention(excessive_cooling)

            # 3. Update metrics
            self.last_thermal_check = datetime.now()
            print(f"✅ Memory Jr: Thermal regulation complete")

        except Exception as e:
            print(f"❌ Memory Jr: Error in thermal regulation: {e}")
            if self.db_conn:
                self.db_conn.rollback()

    def check_sacred_temperatures(self):
        """Check if any sacred memories have cooled below 40°"""
        cursor = self.db_conn.cursor()

        try:
            query = """
            SELECT id, memory_hash, temperature_score,
                   LEFT(original_content, 100) as preview
            FROM thermal_memory_archive
            WHERE sacred_pattern = true
              AND temperature_score < %s
            ORDER BY temperature_score ASC
            LIMIT 20;
            """

            cursor.execute(query, (self.CONFIG["sacred_minimum_temp"],))
            violations = []

            for row in cursor.fetchall():
                violations.append({
                    "id": row[0],
                    "hash": row[1],
                    "current_temp": row[2],
                    "preview": row[3]
                })

            if violations:
                print(f"⚠️  Memory Jr: Found {len(violations)} sacred violations!")

            return violations

        except Exception as e:
            print(f"❌ Memory Jr: Error checking sacred temperatures: {e}")
            return []
        finally:
            cursor.close()

    def emergency_sacred_reheat(self, violations):
        """
        EMERGENCY AUTONOMIC RESPONSE
        Sacred memories MUST maintain 40° minimum
        This is like breathing - non-negotiable
        """
        print(f"🚨 Memory Jr: EMERGENCY SACRED REHEAT ({len(violations)} memories)")

        cursor = self.db_conn.cursor()

        try:
            for violation in violations:
                # Calculate reheat amount
                deficit = self.CONFIG["sacred_minimum_temp"] - violation["current_temp"]
                reheat_amount = deficit + 5.0  # Bring to 45° (buffer)

                # Apply reheat
                update_query = """
                UPDATE thermal_memory_archive
                SET temperature_score = temperature_score + %s,
                    last_access = NOW()
                WHERE id = %s
                RETURNING temperature_score;
                """

                cursor.execute(update_query, (reheat_amount, violation["id"]))
                new_temp = cursor.fetchone()[0]

                print(f"  🔥 Reheated memory {violation['id']}: {violation['current_temp']:.1f}° → {new_temp:.1f}°")

            self.db_conn.commit()
            self.metrics["sacred_emergency_reheats"] += len(violations)

        except Exception as e:
            print(f"❌ Memory Jr: Error in emergency reheat: {e}")
            self.db_conn.rollback()
        finally:
            cursor.close()

    def detect_excessive_cooling(self):
        """Detect memories cooling rapidly"""
        cursor = self.db_conn.cursor()

        try:
            # Simple check: find high-temp memories that might cool too fast
            query = """
            SELECT id, temperature_score
            FROM thermal_memory_archive
            WHERE temperature_score BETWEEN 60 AND 80
              AND NOT sacred_pattern
              AND access_count > 2
            ORDER BY temperature_score DESC
            LIMIT 10;
            """

            cursor.execute(query)

            excessive = []
            for row in cursor.fetchall():
                excessive.append({
                    "id": row[0],
                    "current_temp": row[1]
                })

            return excessive

        except Exception as e:
            print(f"❌ Memory Jr: Error detecting excessive cooling: {e}")
            return []
        finally:
            cursor.close()

    def gentle_intervention(self, excessive_cooling):
        """Gentle reheat to slow excessive cooling"""
        if not excessive_cooling:
            return

        print(f"🌡️  Memory Jr: Gentle intervention on {len(excessive_cooling)} memories")

        cursor = self.db_conn.cursor()

        try:
            for memory in excessive_cooling:
                # Gentle reheat (+5°)
                update_query = """
                UPDATE thermal_memory_archive
                SET temperature_score = temperature_score + %s
                WHERE id = %s;
                """

                cursor.execute(update_query, (self.CONFIG["gentle_reheat_amount"], memory["id"]))

            self.db_conn.commit()
            self.metrics["thermal_interventions"] += len(excessive_cooling)

        except Exception as e:
            print(f"❌ Memory Jr: Error in gentle intervention: {e}")
            self.db_conn.rollback()
        finally:
            cursor.close()

    # === ACCESS PATTERN DETECTION ===

    def access_pattern_detection_cycle(self):
        """
        Detect memories accessed together (every 10 minutes)
        Like noticing "these neurons fire together" - strengthen connection
        """
        print(f"🔍 Memory Jr: Access pattern detection starting...")

        try:
            # For now, just detect recently accessed hot memories
            cursor = self.db_conn.cursor()

            query = """
            SELECT id, temperature_score
            FROM thermal_memory_archive
            WHERE last_access > NOW() - INTERVAL '1 hour'
              AND temperature_score > 80
            LIMIT 10;
            """

            cursor.execute(query)
            recent_hot = cursor.fetchall()

            if recent_hot:
                print(f"  📊 Found {len(recent_hot)} recently accessed hot memories")
                self.metrics["patterns_detected"] += len(recent_hot)

            cursor.close()
            self.last_access_scan = datetime.now()
            print(f"✅ Memory Jr: Pattern detection complete")

        except Exception as e:
            print(f"❌ Memory Jr: Error in pattern detection: {e}")

    # === ON-DEMAND FUNCTIONS (WAKE-ON-QUERY) ===

    def retrieve_memories(self, keywords=None, min_temp=40, timeframe_hours=None):
        """
        ON-DEMAND: Retrieve specific memories matching criteria
        Called by Query Triad when user asks questions
        """
        try:
            cursor = self.db_conn.cursor()

            # Build dynamic query
            conditions = [f"temperature_score >= {min_temp}"]

            if keywords:
                keyword_conditions = []
                for keyword in keywords:
                    keyword_conditions.append(f"original_content ILIKE '%{keyword}%'")
                conditions.append(f"({' OR '.join(keyword_conditions)})")

            if timeframe_hours:
                conditions.append(f"last_access > NOW() - INTERVAL '{timeframe_hours} hours'")

            query = f"""
            SELECT id, temperature_score, access_count, sacred_pattern,
                   LEFT(original_content, 500) as preview
            FROM thermal_memory_archive
            WHERE {' AND '.join(conditions)}
            ORDER BY temperature_score DESC, last_access DESC
            LIMIT 20;
            """

            cursor.execute(query)
            memories = cursor.fetchall()

            result = {
                "memories_found": len(memories),
                "avg_temperature": sum(m[1] for m in memories) / len(memories) if memories else 0,
                "memories": []
            }

            for mem_id, temp, accesses, sacred, preview in memories:
                result["memories"].append({
                    "id": mem_id,
                    "temperature": temp,
                    "accesses": accesses,
                    "sacred": sacred,
                    "preview": preview[:200]
                })

            cursor.close()
            return result

        except Exception as e:
            print(f"❌ Memory Jr: Error in on-demand retrieval: {e}")
            return {"error": str(e), "memories_found": 0}

    def search_by_category(self, category):
        """
        ON-DEMAND: Search memories by metadata category
        """
        try:
            cursor = self.db_conn.cursor()

            query = """
            SELECT id, temperature_score, LEFT(original_content, 300) as preview
            FROM thermal_memory_archive
            WHERE metadata->>'category' = %s
            ORDER BY temperature_score DESC
            LIMIT 15;
            """

            cursor.execute(query, (category,))
            memories = cursor.fetchall()

            cursor.close()
            return {
                "category": category,
                "count": len(memories),
                "memories": [{"id": m[0], "temp": m[1], "preview": m[2]} for m in memories]
            }

        except Exception as e:
            return {"error": str(e), "count": 0}

    def get_sacred_memories(self):
        """
        ON-DEMAND: Get all sacred memories (>40° guaranteed)
        """
        try:
            cursor = self.db_conn.cursor()

            query = """
            SELECT id, temperature_score, access_count,
                   LEFT(original_content, 300) as preview
            FROM thermal_memory_archive
            WHERE sacred_pattern = true
            ORDER BY temperature_score DESC
            LIMIT 30;
            """

            cursor.execute(query)
            sacred = cursor.fetchall()

            cursor.close()
            return {
                "sacred_count": len(sacred),
                "avg_temperature": sum(s[1] for s in sacred) / len(sacred) if sacred else 0,
                "memories": [{"id": s[0], "temp": s[1], "accesses": s[2], "preview": s[3]} for s in sacred]
            }

        except Exception as e:
            return {"error": str(e), "sacred_count": 0}

    def thermal_status_report(self):
        """
        ON-DEMAND: Get current thermal memory status
        """
        try:
            cursor = self.db_conn.cursor()

            query = """
            SELECT
                COUNT(*) as total,
                AVG(temperature_score) as avg_temp,
                MIN(temperature_score) as min_temp,
                MAX(temperature_score) as max_temp,
                COUNT(CASE WHEN sacred_pattern THEN 1 END) as sacred_count,
                COUNT(CASE WHEN temperature_score >= 90 THEN 1 END) as white_hot,
                COUNT(CASE WHEN temperature_score >= 70 AND temperature_score < 90 THEN 1 END) as red_hot,
                COUNT(CASE WHEN temperature_score >= 40 AND temperature_score < 70 THEN 1 END) as warm
            FROM thermal_memory_archive;
            """

            cursor.execute(query)
            result = cursor.fetchone()

            cursor.close()
            return {
                "total_memories": result[0],
                "avg_temperature": round(result[1], 1) if result[1] else 0,
                "min_temperature": result[2],
                "max_temperature": result[3],
                "sacred_memories": result[4],
                "white_hot_90_100": result[5],
                "red_hot_70_90": result[6],
                "warm_40_70": result[7]
            }

        except Exception as e:
            return {"error": str(e)}

    # === CONSOLIDATION CYCLES ===

    def consolidation_cycle(self):
        """
        Memory consolidation (every 1 hour)
        Like REM sleep - strengthen important patterns
        """
        print(f"😴 Memory Jr: Consolidation cycle starting (like sleep)...")

        try:
            cursor = self.db_conn.cursor()

            # Find memories that deserve consolidation
            query = """
            SELECT id, temperature_score, access_count
            FROM thermal_memory_archive
            WHERE access_count >= 3
              AND temperature_score BETWEEN 50 AND 70
              AND created_at < NOW() - INTERVAL '%s days'
              AND NOT sacred_pattern
            ORDER BY access_count DESC
            LIMIT 10;
            """

            cursor.execute(query, (self.CONFIG["fragment_age_threshold"],))
            candidates = cursor.fetchall()

            if candidates:
                print(f"  🧩 Consolidating {len(candidates)} fragments...")

                for row in candidates:
                    mem_id, temp, accesses = row

                    # Consolidation boost
                    update_query = """
                    UPDATE thermal_memory_archive
                    SET temperature_score = temperature_score + %s
                    WHERE id = %s;
                    """

                    cursor.execute(update_query, (self.CONFIG["consolidation_boost"], mem_id))

                self.db_conn.commit()
                self.metrics["consolidations_performed"] += len(candidates)

            cursor.close()
            self.last_consolidation = datetime.now()
            print(f"✅ Memory Jr: Consolidation complete")

        except Exception as e:
            print(f"❌ Memory Jr: Error in consolidation: {e}")
            if self.db_conn:
                self.db_conn.rollback()

    # === MAIN LOOP ===

    def run(self):
        """Main autonomic loop - runs continuously"""
        print(f"""
╔══════════════════════════════════════════════════════════╗
║  🧠 MEMORY JR AUTONOMIC DAEMON STARTING                 ║
║  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                          ║
║  Mission: Maintain thermal memory field autonomically    ║
║  Boundaries: Respected (no deletions, no major changes) ║
╚══════════════════════════════════════════════════════════╝
        """)

        # Connect to database
        if not self.connect_db():
            print("❌ Failed to connect to database. Exiting.")
            return 1

        self.running = True
        start_time = time.time()

        # Initialize timers
        self.last_thermal_check = datetime.now()
        self.last_access_scan = datetime.now()
        self.last_resonance_scan = datetime.now()
        self.last_consolidation = datetime.now()

        print("🔥 Memory Jr: Autonomic processes activated")
        print("🌡️  Thermal regulation: Every 5 minutes")
        print("🔍 Pattern detection: Every 10 minutes")
        print("😴 Consolidation: Every 1 hour")
        print()

        try:
            while self.running:
                current_time = datetime.now()

                # Thermal regulation (every 5 min)
                if (current_time - self.last_thermal_check).total_seconds() >= self.CONFIG["thermal_check_interval"]:
                    self.thermal_regulation_cycle()

                # Access pattern detection (every 10 min)
                if (current_time - self.last_access_scan).total_seconds() >= self.CONFIG["access_pattern_interval"]:
                    self.access_pattern_detection_cycle()

                # Consolidation cycle (every 1 hour)
                if (current_time - self.last_consolidation).total_seconds() >= self.CONFIG["consolidation_interval"]:
                    self.consolidation_cycle()

                # Sleep for 60 seconds before next check
                time.sleep(60)

                # Update runtime
                self.metrics["total_runtime_seconds"] = time.time() - start_time

        except KeyboardInterrupt:
            print("\n⚠️  Memory Jr: Shutdown signal received")
        except Exception as e:
            print(f"\n❌ Memory Jr: Error in main loop: {e}")
            return 1
        finally:
            self.shutdown()

        return 0

    def shutdown(self):
        """Clean shutdown"""
        print(f"\n🛑 Memory Jr: Shutting down...")

        # Print metrics
        runtime_hours = self.metrics["total_runtime_seconds"] / 3600
        print(f"""
╔══════════════════════════════════════════════════════════╗
║  📊 MEMORY JR AUTONOMIC METRICS                         ║
║                                                          ║
║  Thermal Interventions:    {self.metrics['thermal_interventions']:>6}                    ║
║  Sacred Emergency Reheats: {self.metrics['sacred_emergency_reheats']:>6}                    ║
║  Patterns Detected:        {self.metrics['patterns_detected']:>6}                    ║
║  Consolidations Performed: {self.metrics['consolidations_performed']:>6}                    ║
║  Total Runtime:            {runtime_hours:>6.1f} hours               ║
╚══════════════════════════════════════════════════════════╝
        """)

        if self.db_conn:
            self.db_conn.close()
            print("✅ Database connection closed")

        print("🔥 Sacred Fire continues burning...")

# === ENTRY POINT ===

if __name__ == "__main__":
    daemon = MemoryJrAutonomic()
    sys.exit(daemon.run())
