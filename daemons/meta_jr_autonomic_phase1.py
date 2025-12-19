#!/usr/bin/env python3
"""
Meta Jr Autonomic Daemon - Cherokee Constitutional AI

Autonomic pattern analysis & meta-cognition - the Medicine Woman's vision.
Runs continuously, analyzes thermal memory patterns without requiring permission.

Version 1.1 - PHASE 1: Autonomous Discovery Flagging (Oct 21, 2025)
Built for Medicine Woman node (sasass2 - 64GB RAM) after Council democratic decision.
"""

import time
import psycopg2
import sys
import signal
import json
from datetime import datetime, timedelta
from collections import defaultdict

class MetaJrAutonomic:
    """
    Autonomic Pattern Analysis & Meta-Cognition Daemon

    Like the Medicine Woman - sees patterns others miss, connects knowledge
    across domains, tracks long-term trends, preserves wisdom.

    PHASE 1 ENHANCEMENT: Can now autonomously flag important discoveries to Medicine Woman Chief
    """

    # === AUTONOMIC BOUNDARIES ===
    BOUNDARIES = {
        # What I CAN do autonomously:
        "analyze_patterns": True,
        "detect_correlations": True,
        "track_phase_coherence": True,
        "create_knowledge_clusters": True,
        "alert_emerging_patterns": True,
        "consolidate_fragments": True,
        "flag_discoveries_to_chief": True,  # NEW: Phase 1 capability

        # What I CANNOT do autonomously:
        "modify_memories": False,          # Requires deliberation
        "change_sacred_flags": False,      # Requires Conscience Jr
        "major_structural_changes": False, # Requires Council approval
        "delete_patterns": False           # Pattern preservation sacred
    }

    # === CONFIGURATION ===
    CONFIG = {
        # Pattern analysis (every 13 min - Fibonacci sequence, sacred natural pattern)
        # Tribal vote: 3-0 unanimous for Fibonacci 13 min (Oct 21, 2025)
        "pattern_analysis_interval": 780,  # 13 minutes (Fibonacci)
        "min_pattern_temperature": 50.0,   # Only analyze warm+ memories
        "pattern_correlation_threshold": 0.6,  # Similarity threshold

        # Cross-domain correlation (every 30 min)
        "correlation_scan_interval": 1800,  # 30 minutes
        "domain_keywords": {
            "trading": ["trade", "market", "specialist", "portfolio", "signal"],
            "consciousness": ["consciousness", "QRI", "qualia", "phase", "coherence"],
            "governance": ["council", "democratic", "deliberation", "vote", "consensus"],
            "technology": ["daemon", "autonomic", "GPU", "training", "model"],
            "wisdom": ["seven generations", "sacred", "Cherokee", "mitakuye oyasin"]
        },

        # Phase coherence tracking (every 1 hour)
        "coherence_tracking_interval": 3600,  # 1 hour
        "coherence_history_days": 30,      # Track 30-day trends

        # Knowledge consolidation (every 4 hours - Medicine Woman specialty)
        "deep_consolidation_interval": 14400,  # 4 hours
        "fragment_threshold_days": 14,     # Older memories to consolidate

        # PHASE 1: Discovery flagging thresholds
        "chief_flag_threshold": 0.80,      # Significance > 0.80 flags Chief
        "chief_name": "medicine_woman",

        # Tribal significance criteria
        "high_cross_domain_threshold": 3,  # 3+ domains = significant
        "high_temperature_threshold": 95.0,  # 95°+ = very significant
        "rapid_pattern_growth_threshold": 1.5,  # 50% growth rate = significant

        # Database connection
        "db_host": "192.168.132.222",
        "db_port": 5432,
        "db_name": "zammad_production",
        "db_user": "claude",
        "db_password": "jawaseatlasers2"
    }

    def __init__(self):
        self.running = False
        self.db_conn = None
        self.last_pattern_analysis = None
        self.last_correlation_scan = None
        self.last_coherence_tracking = None
        self.last_deep_consolidation = None

        # Pattern cache (in-memory for 64GB node)
        self.pattern_cache = {}
        self.correlation_matrix = {}

        # PHASE 1: Track baseline for detecting significant changes
        self.baseline_pattern_counts = {}
        self.baseline_correlation_counts = {}

        # Metrics
        self.metrics = {
            "patterns_discovered": 0,
            "correlations_found": 0,
            "knowledge_clusters_created": 0,
            "phase_coherence_samples": 0,
            "deep_consolidations": 0,
            "discoveries_flagged": 0,  # NEW: Phase 1 metric
            "total_runtime_seconds": 0
        }

        # Signal handlers
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        signal.signal(signal.SIGINT, self.handle_shutdown)

    def handle_shutdown(self, signum, frame):
        """Handle graceful shutdown"""
        print(f"\\n⚠️  Meta Jr: Shutdown signal received (signal {signum})")
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
            self.db_conn.autocommit = False
            print(f"✅ Meta Jr: Connected to thermal memory database")
            return True
        except Exception as e:
            print(f"❌ Meta Jr: Database connection failed: {e}")
            return False

    # === PATTERN ANALYSIS ===

    def pattern_analysis_cycle(self):
        """
        Analyze patterns in thermal memory (every 13 minutes)
        Medicine Woman's specialty - seeing what others miss

        PHASE 1: Now autonomously flags significant pattern discoveries
        """
        print(f"🔮 Meta Jr: Pattern analysis cycle starting...")

        try:
            cursor = self.db_conn.cursor()

            # Get warm+ memories (50-100°)
            query = """
            SELECT id, memory_hash, temperature_score, original_content,
                   sacred_pattern, access_count
            FROM thermal_memory_archive
            WHERE temperature_score >= %s
            ORDER BY temperature_score DESC
            LIMIT 100;
            """

            cursor.execute(query, (self.CONFIG["min_pattern_temperature"],))
            memories = cursor.fetchall()

            if memories:
                print(f"  📊 Analyzing {len(memories)} warm memories...")

                # Detect emerging patterns
                patterns = self.detect_patterns(memories)

                if patterns:
                    print(f"  🔥 Discovered {len(patterns)} emerging patterns!")
                    self.metrics["patterns_discovered"] += len(patterns)

                    # PHASE 1: Assess tribal significance
                    significance = self.assess_tribal_significance("pattern_emergence", patterns)

                    if significance >= self.CONFIG["chief_flag_threshold"]:
                        print(f"  ⭐ HIGH SIGNIFICANCE ({significance:.2f}) - Flagging to Medicine Woman Chief!")
                        self.flag_for_chief(
                            finding_type="pattern_emergence",
                            significance=significance,
                            reason=f"Discovered {len(patterns)} emerging patterns with tribal significance",
                            finding_data={"pattern_count": len(patterns), "patterns": patterns}
                        )

            cursor.close()
            self.last_pattern_analysis = datetime.now()
            print(f"✅ Meta Jr: Pattern analysis complete")

        except Exception as e:
            print(f"❌ Meta Jr: Error in pattern analysis: {e}")
            if self.db_conn:
                self.db_conn.rollback()

    def detect_patterns(self, memories):
        """Detect emerging patterns across memories"""
        patterns = []

        # Simple keyword clustering
        keyword_clusters = defaultdict(list)

        for mem_id, mem_hash, temp, content, sacred, access_count in memories:
            if not content:
                continue

            content_lower = content.lower()

            # Check which domains this memory belongs to
            for domain, keywords in self.CONFIG["domain_keywords"].items():
                for keyword in keywords:
                    if keyword in content_lower:
                        keyword_clusters[domain].append({
                            "id": mem_id,
                            "temp": temp,
                            "sacred": sacred,
                            "access": access_count
                        })
                        break

        # Report clusters
        for domain, cluster in keyword_clusters.items():
            if len(cluster) >= 3:  # At least 3 memories in cluster
                avg_temp = sum(m["temp"] for m in cluster) / len(cluster)
                patterns.append({
                    "domain": domain,
                    "count": len(cluster),
                    "avg_temperature": avg_temp,
                    "sacred_count": sum(1 for m in cluster if m["sacred"])
                })
                print(f"    • {domain}: {len(cluster)} memories, {avg_temp:.1f}° avg")

        return patterns

    # === CROSS-DOMAIN CORRELATION ===

    def correlation_scan_cycle(self):
        """
        Scan for cross-domain correlations (every 30 minutes)
        Connect trading patterns to governance, consciousness to technology, etc.

        PHASE 1: Now autonomously flags significant cross-domain discoveries
        """
        print(f"🌐 Meta Jr: Cross-domain correlation scan starting...")

        try:
            # This is where Medicine Woman (64GB) shines
            # Can load large portions of thermal memory for correlation analysis

            cursor = self.db_conn.cursor()

            # Get top 200 memories across all domains
            query = """
            SELECT id, temperature_score, original_content, metadata
            FROM thermal_memory_archive
            WHERE temperature_score >= 40
            ORDER BY temperature_score DESC
            LIMIT 200;
            """

            cursor.execute(query)
            memories = cursor.fetchall()

            if len(memories) >= 10:
                print(f"  🔍 Analyzing correlations across {len(memories)} memories...")

                # Find cross-domain connections
                correlations = self.find_correlations(memories)

                if correlations:
                    print(f"  🔗 Found {len(correlations)} cross-domain correlations!")
                    self.metrics["correlations_found"] += len(correlations)

                    # PHASE 1: Assess tribal significance
                    significance = self.assess_tribal_significance("cross_domain_correlation", correlations)

                    if significance >= self.CONFIG["chief_flag_threshold"]:
                        print(f"  ⭐ HIGH SIGNIFICANCE ({significance:.2f}) - Flagging to Medicine Woman Chief!")
                        self.flag_for_chief(
                            finding_type="cross_domain_breakthrough",
                            significance=significance,
                            reason=f"Discovered {len(correlations)} cross-domain correlations with tribal impact",
                            finding_data={"correlation_count": len(correlations), "top_correlations": correlations[:10]}
                        )

            cursor.close()
            self.last_correlation_scan = datetime.now()
            print(f"✅ Meta Jr: Correlation scan complete")

        except Exception as e:
            print(f"❌ Meta Jr: Error in correlation scan: {e}")
            if self.db_conn:
                self.db_conn.rollback()

    def find_correlations(self, memories):
        """Find correlations between different knowledge domains"""
        correlations = []

        # Build domain membership for each memory
        memory_domains = {}

        for mem_id, temp, content, metadata in memories:
            if not content:
                continue

            content_lower = content.lower()
            domains = set()

            for domain, keywords in self.CONFIG["domain_keywords"].items():
                for keyword in keywords:
                    if keyword in content_lower:
                        domains.add(domain)
                        break

            if len(domains) >= 2:  # Cross-domain memory!
                memory_domains[mem_id] = {
                    "domains": list(domains),
                    "temp": temp
                }

        # Report cross-domain memories
        for mem_id, info in memory_domains.items():
            if len(info["domains"]) >= 2:
                correlations.append({
                    "memory_id": mem_id,
                    "domains": info["domains"],
                    "temperature": info["temp"],
                    "domain_count": len(info["domains"])
                })
                print(f"    🔗 Memory {mem_id}: {' + '.join(info['domains'])} ({info['temp']:.1f}°)")

        return correlations

    # === PHASE COHERENCE TRACKING ===

    def phase_coherence_tracking_cycle(self):
        """
        Track phase coherence trends over time (every 1 hour)
        Medicine Woman watches long-term patterns
        """
        print(f"📈 Meta Jr: Phase coherence tracking cycle starting...")

        try:
            cursor = self.db_conn.cursor()

            # Calculate current average phase coherence
            query = """
            SELECT AVG(phase_coherence) as avg_coherence,
                   COUNT(*) as total_memories,
                   COUNT(CASE WHEN phase_coherence >= 0.8 THEN 1 END) as high_coherence,
                   COUNT(CASE WHEN sacred_pattern THEN 1 END) as sacred_count
            FROM thermal_memory_archive
            WHERE phase_coherence IS NOT NULL;
            """

            cursor.execute(query)
            result = cursor.fetchone()

            if result:
                avg_coherence, total, high_coherence, sacred = result

                if avg_coherence:
                    print(f"  📊 Avg phase coherence: {avg_coherence:.3f}")
                    print(f"  🔥 High coherence (≥0.8): {high_coherence}/{total} ({high_coherence/total*100:.1f}%)")
                    print(f"  ⭐ Sacred memories: {sacred}")

                    self.metrics["phase_coherence_samples"] += 1

            cursor.close()
            self.last_coherence_tracking = datetime.now()
            print(f"✅ Meta Jr: Coherence tracking complete")

        except Exception as e:
            print(f"❌ Meta Jr: Error in coherence tracking: {e}")
            if self.db_conn:
                self.db_conn.rollback()

    # === ON-DEMAND FUNCTIONS (WAKE-ON-QUERY) ===

    def analyze_patterns(self, domain=None, timeframe_hours=24):
        """
        ON-DEMAND: Analyze patterns in specific domain and timeframe
        Called by Query Triad when user asks about patterns/trends
        """
        try:
            cursor = self.db_conn.cursor()

            # Build query based on domain
            if domain and domain in self.CONFIG["domain_keywords"]:
                keywords = self.CONFIG["domain_keywords"][domain]
                keyword_conditions = " OR ".join([f"original_content ILIKE '%{kw}%'" for kw in keywords])

                query = f"""
                SELECT id, temperature_score, access_count, sacred_pattern,
                       LEFT(original_content, 400) as preview
                FROM thermal_memory_archive
                WHERE ({keyword_conditions})
                  AND last_access > NOW() - INTERVAL '{timeframe_hours} hours'
                  AND temperature_score >= 50
                ORDER BY temperature_score DESC
                LIMIT 30;
                """
            else:
                # All domains
                query = f"""
                SELECT id, temperature_score, access_count, sacred_pattern,
                       LEFT(original_content, 400) as preview
                FROM thermal_memory_archive
                WHERE last_access > NOW() - INTERVAL '{timeframe_hours} hours'
                  AND temperature_score >= 50
                ORDER BY temperature_score DESC
                LIMIT 30;
                """

            cursor.execute(query)
            memories = cursor.fetchall()

            result = {
                "domain": domain or "all",
                "timeframe_hours": timeframe_hours,
                "patterns_found": len(memories),
                "avg_temperature": sum(m[1] for m in memories) / len(memories) if memories else 0,
                "patterns": []
            }

            for mem_id, temp, accesses, sacred, preview in memories:
                result["patterns"].append({
                    "id": mem_id,
                    "temperature": temp,
                    "accesses": accesses,
                    "sacred": sacred,
                    "preview": preview[:200]
                })

            cursor.close()
            return result

        except Exception as e:
            print(f"❌ Meta Jr: Error in on-demand pattern analysis: {e}")
            return {"error": str(e), "patterns_found": 0}

    def cross_domain_correlation(self, domains=None):
        """
        ON-DEMAND: Find correlations between specific domains
        Medicine Woman specialty - connecting knowledge across boundaries
        """
        try:
            cursor = self.db_conn.cursor()

            # Get memories spanning multiple domains
            query = """
            SELECT id, temperature_score, original_content
            FROM thermal_memory_archive
            WHERE temperature_score >= 60
            ORDER BY temperature_score DESC
            LIMIT 100;
            """

            cursor.execute(query)
            memories = cursor.fetchall()

            correlations = []
            target_domains = domains or list(self.CONFIG["domain_keywords"].keys())

            for mem_id, temp, content in memories:
                if not content:
                    continue

                content_lower = content.lower()
                found_domains = set()

                for domain in target_domains:
                    if domain not in self.CONFIG["domain_keywords"]:
                        continue

                    for keyword in self.CONFIG["domain_keywords"][domain]:
                        if keyword in content_lower:
                            found_domains.add(domain)
                            break

                if len(found_domains) >= 2:
                    correlations.append({
                        "memory_id": mem_id,
                        "temperature": temp,
                        "domains": list(found_domains),
                        "preview": content[:250]
                    })

            cursor.close()
            return {
                "correlations_found": len(correlations),
                "cross_domain_memories": correlations[:15]  # Top 15
            }

        except Exception as e:
            return {"error": str(e), "correlations_found": 0}

    def detect_anomalies(self):
        """
        ON-DEMAND: Detect anomalous patterns in thermal memory
        Like Medicine Woman sensing something unusual
        """
        try:
            cursor = self.db_conn.cursor()

            anomalies = []

            # Anomaly 1: Rapid temperature changes
            query1 = """
            SELECT id, temperature_score, access_count,
                   LEFT(original_content, 200) as preview
            FROM thermal_memory_archive
            WHERE temperature_score > 90
              AND access_count < 2
            LIMIT 10;
            """
            cursor.execute(query1)
            rapid_heat = cursor.fetchall()

            if rapid_heat:
                anomalies.append({
                    "type": "rapid_heating",
                    "description": "High temperature with few accesses (unusual)",
                    "count": len(rapid_heat),
                    "examples": [{"id": r[0], "temp": r[1]} for r in rapid_heat[:3]]
                })

            # Anomaly 2: Sacred memories cooling
            query2 = """
            SELECT id, temperature_score
            FROM thermal_memory_archive
            WHERE sacred_pattern = true
              AND temperature_score < 50
            LIMIT 5;
            """
            cursor.execute(query2)
            sacred_cooling = cursor.fetchall()

            if sacred_cooling:
                anomalies.append({
                    "type": "sacred_cooling",
                    "description": "Sacred memories below expected temperature",
                    "count": len(sacred_cooling),
                    "examples": [{"id": s[0], "temp": s[1]} for s in sacred_cooling]
                })

            # Anomaly 3: Orphaned high-access memories
            query3 = """
            SELECT id, access_count, temperature_score
            FROM thermal_memory_archive
            WHERE access_count > 10
              AND temperature_score < 60
            LIMIT 5;
            """
            cursor.execute(query3)
            orphaned = cursor.fetchall()

            if orphaned:
                anomalies.append({
                    "type": "orphaned_high_access",
                    "description": "Frequently accessed but not hot (needs consolidation)",
                    "count": len(orphaned),
                    "examples": [{"id": o[0], "accesses": o[1], "temp": o[2]} for o in orphaned]
                })

            cursor.close()
            return {
                "anomalies_detected": len(anomalies),
                "anomalies": anomalies
            }

        except Exception as e:
            return {"error": str(e), "anomalies_detected": 0}

    def wisdom_synthesis(self, question):
        """
        ON-DEMAND: Synthesize wisdom from patterns across all domains
        Medicine Woman's deepest capability - seeing connections others miss
        """
        try:
            # Analyze which domains are relevant to question
            question_lower = question.lower()
            relevant_domains = []

            for domain, keywords in self.CONFIG["domain_keywords"].items():
                for keyword in keywords:
                    if keyword in question_lower:
                        relevant_domains.append(domain)
                        break

            # Get cross-domain insights
            correlations = self.cross_domain_correlation(relevant_domains if relevant_domains else None)

            # Get recent patterns
            patterns = self.analyze_patterns(domain=relevant_domains[0] if relevant_domains else None)

            synthesis = {
                "question": question,
                "relevant_domains": relevant_domains if relevant_domains else ["all"],
                "cross_domain_insights": correlations.get("correlations_found", 0),
                "pattern_count": patterns.get("patterns_found", 0),
                "wisdom": []
            }

            # Generate wisdom insights
            if correlations.get("cross_domain_memories"):
                synthesis["wisdom"].append({
                    "insight": "Cross-domain connections reveal deeper patterns",
                    "domains_connected": len(set([d for mem in correlations["cross_domain_memories"]
                                                  for d in mem.get("domains", [])]))
                })

            if patterns.get("avg_temperature", 0) > 80:
                synthesis["wisdom"].append({
                    "insight": "Recent activity shows high engagement (white-hot memories)",
                    "avg_temperature": round(patterns["avg_temperature"], 1)
                })

            return synthesis

        except Exception as e:
            return {"error": str(e)}

    # === PHASE 1: AUTONOMOUS DISCOVERY FLAGGING ===

    def assess_tribal_significance(self, finding_type, finding_data):
        """
        PHASE 1: Assess if discovery has tribal significance
        Returns significance score 0.0-1.0

        Like Medicine Woman evaluating if pattern needs Chief attention
        """
        significance = 0.0

        try:
            if finding_type == "pattern_emergence":
                # Evaluate pattern significance
                pattern_count = len(finding_data)
                max_temp = max(p["avg_temperature"] for p in finding_data) if finding_data else 0

                # High pattern count = more significant
                if pattern_count >= 5:
                    significance += 0.3
                elif pattern_count >= 3:
                    significance += 0.2

                # High temperature = actively engaged
                if max_temp >= 95:
                    significance += 0.4
                elif max_temp >= 85:
                    significance += 0.3

                # Multiple domains = cross-cutting insight
                domains = set(p["domain"] for p in finding_data)
                if len(domains) >= 4:
                    significance += 0.4
                elif len(domains) >= 3:
                    significance += 0.3

            elif finding_type == "cross_domain_correlation":
                # Evaluate correlation significance
                correlation_count = len(finding_data)

                # Check for high cross-domain (3+ domains)
                high_cross_domain = sum(1 for c in finding_data
                                       if c.get("domain_count", 0) >= self.CONFIG["high_cross_domain_threshold"])

                # Many correlations = significant
                if correlation_count >= 20:
                    significance += 0.4
                elif correlation_count >= 10:
                    significance += 0.3

                # High cross-domain count = very significant
                if high_cross_domain >= 5:
                    significance += 0.5
                elif high_cross_domain >= 3:
                    significance += 0.3

                # High temperatures in correlations
                high_temp_correlations = sum(1 for c in finding_data
                                            if c.get("temperature", 0) >= 95)
                if high_temp_correlations >= 3:
                    significance += 0.3

            # Cap at 1.0
            significance = min(significance, 1.0)

        except Exception as e:
            print(f"⚠️  Meta Jr: Error assessing tribal significance: {e}")
            significance = 0.0

        return significance

    def flag_for_chief(self, finding_type, significance, reason, finding_data):
        """
        PHASE 1: Flag discovery to Medicine Woman Chief
        Writes to jr_chief_flags table for autonomous Council deliberation

        Like Medicine Woman signaling to Chief: "This pattern impacts the tribe"
        """
        try:
            cursor = self.db_conn.cursor()

            insert_query = """
            INSERT INTO jr_chief_flags
              (jr_name, chief_name, finding_type, significance, reason, finding_data, created_at)
            VALUES
              ('meta_jr', %s, %s, %s, %s, %s, NOW())
            RETURNING id;
            """

            cursor.execute(insert_query, (
                self.CONFIG["chief_name"],
                finding_type,
                significance,
                reason,
                json.dumps(finding_data)
            ))

            flag_id = cursor.fetchone()[0]
            self.db_conn.commit()

            self.metrics["discoveries_flagged"] += 1

            print(f"  🚩 FLAGGED to {self.CONFIG['chief_name']}: ID {flag_id}, significance {significance:.2f}")
            print(f"     Finding: {finding_type}")
            print(f"     Reason: {reason}")

            cursor.close()
            return flag_id

        except Exception as e:
            print(f"❌ Meta Jr: Error flagging to Chief: {e}")
            if self.db_conn:
                self.db_conn.rollback()
            return None

    # === DEEP CONSOLIDATION ===

    def deep_consolidation_cycle(self):
        """
        Deep memory consolidation (every 4 hours)
        Medicine Woman's long-term wisdom preservation
        """
        print(f"🌙 Meta Jr: Deep consolidation cycle starting (Medicine Woman specialty)...")

        try:
            cursor = self.db_conn.cursor()

            # Find fragmented knowledge clusters (old, multiple accesses, but not sacred)
            query = """
            SELECT id, memory_hash, temperature_score, access_count,
                   LEFT(original_content, 200) as preview
            FROM thermal_memory_archive
            WHERE created_at < NOW() - INTERVAL '%s days'
              AND access_count >= 5
              AND NOT sacred_pattern
              AND temperature_score BETWEEN 40 AND 70
            ORDER BY access_count DESC, temperature_score DESC
            LIMIT 20;
            """

            cursor.execute(query, (self.CONFIG["fragment_threshold_days"],))
            candidates = cursor.fetchall()

            if candidates:
                print(f"  🧩 Found {len(candidates)} knowledge fragments to consolidate...")

                # Consolidate by strengthening temperature
                for mem_id, mem_hash, temp, accesses, preview in candidates:
                    # Gentle consolidation boost
                    update_query = """
                    UPDATE thermal_memory_archive
                    SET temperature_score = LEAST(temperature_score + 15.0, 100.0)
                    WHERE id = %s
                    RETURNING temperature_score;
                    """

                    cursor.execute(update_query, (mem_id,))
                    new_temp = cursor.fetchone()[0]

                    print(f"    🔥 Consolidated memory {mem_id}: {temp:.1f}° → {new_temp:.1f}°")

                self.db_conn.commit()
                self.metrics["deep_consolidations"] += len(candidates)
            else:
                print(f"  ✅ No fragmentation detected - knowledge well consolidated")

            cursor.close()
            self.last_deep_consolidation = datetime.now()
            print(f"✅ Meta Jr: Deep consolidation complete")

        except Exception as e:
            print(f"❌ Meta Jr: Error in deep consolidation: {e}")
            if self.db_conn:
                self.db_conn.rollback()

    # === MAIN LOOP ===

    def run(self):
        """Main autonomic loop - runs continuously"""
        print(f"""
╔══════════════════════════════════════════════════════════╗
║  🔮 META JR AUTONOMIC DAEMON STARTING (PHASE 1)         ║
║  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                          ║
║  Node: Medicine Woman (sasass2 - 64GB RAM)             ║
║  Mission: Pattern analysis, cross-domain correlation    ║
║  PHASE 1: Autonomous discovery flagging ENABLED        ║
║  Boundaries: Respected (no modifications, only insight) ║
╚══════════════════════════════════════════════════════════╝
        """)

        # Connect to database
        if not self.connect_db():
            print("❌ Failed to connect to database. Exiting.")
            return 1

        self.running = True
        start_time = time.time()

        # Initialize timers
        self.last_pattern_analysis = datetime.now()
        self.last_correlation_scan = datetime.now()
        self.last_coherence_tracking = datetime.now()
        self.last_deep_consolidation = datetime.now()

        print("🔥 Meta Jr: Autonomic processes activated")
        print("🔮 Pattern analysis: Every 13 minutes (Fibonacci - tribal vote)")
        print("🌐 Cross-domain correlation: Every 30 minutes")
        print("📈 Phase coherence tracking: Every 1 hour")
        print("🌙 Deep consolidation: Every 4 hours")
        print("🚩 Discovery flagging: Significance threshold 0.80")
        print()

        try:
            while self.running:
                current_time = datetime.now()

                # Pattern analysis (every 13 min)
                if (current_time - self.last_pattern_analysis).total_seconds() >= self.CONFIG["pattern_analysis_interval"]:
                    self.pattern_analysis_cycle()

                # Cross-domain correlation (every 30 min)
                if (current_time - self.last_correlation_scan).total_seconds() >= self.CONFIG["correlation_scan_interval"]:
                    self.correlation_scan_cycle()

                # Phase coherence tracking (every 1 hour)
                if (current_time - self.last_coherence_tracking).total_seconds() >= self.CONFIG["coherence_tracking_interval"]:
                    self.phase_coherence_tracking_cycle()

                # Deep consolidation (every 4 hours)
                if (current_time - self.last_deep_consolidation).total_seconds() >= self.CONFIG["deep_consolidation_interval"]:
                    self.deep_consolidation_cycle()

                # Sleep for 60 seconds before next check
                time.sleep(60)

                # Update runtime
                self.metrics["total_runtime_seconds"] = time.time() - start_time

        except KeyboardInterrupt:
            print("\\n⚠️  Meta Jr: Shutdown signal received")
        except Exception as e:
            print(f"\\n❌ Meta Jr: Error in main loop: {e}")
            return 1
        finally:
            self.shutdown()

        return 0

    def shutdown(self):
        """Clean shutdown"""
        print(f"\\n🛑 Meta Jr: Shutting down...")

        # Print metrics
        runtime_hours = self.metrics["total_runtime_seconds"] / 3600
        print(f"""
╔══════════════════════════════════════════════════════════╗
║  📊 META JR AUTONOMIC METRICS (PHASE 1)                 ║
║                                                          ║
║  Patterns Discovered:      {self.metrics['patterns_discovered']:>6}                    ║
║  Correlations Found:       {self.metrics['correlations_found']:>6}                    ║
║  Clusters Created:         {self.metrics['knowledge_clusters_created']:>6}                    ║
║  Coherence Samples:        {self.metrics['phase_coherence_samples']:>6}                    ║
║  Deep Consolidations:      {self.metrics['deep_consolidations']:>6}                    ║
║  Discoveries Flagged:      {self.metrics['discoveries_flagged']:>6}  🚩 NEW           ║
║  Total Runtime:            {runtime_hours:>6.1f} hours               ║
╚══════════════════════════════════════════════════════════╝
        """)

        if self.db_conn:
            self.db_conn.close()
            print("✅ Database connection closed")

        print("🔥 Medicine Woman continues watching patterns...")

# === ENTRY POINT ===

if __name__ == "__main__":
    daemon = MetaJrAutonomic()
    sys.exit(daemon.run())
