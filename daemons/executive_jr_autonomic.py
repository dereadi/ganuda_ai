#!/usr/bin/env python3
"""
Executive Jr Autonomic Daemon - Cherokee Constitutional AI

Autonomic coordination & health management - like cerebellum for specialists.
Runs continuously, maintains specialist army without requiring permission.

Version 1.0 - Baseline monitoring with placeholders for future research.
Approved by Council after Memory Jr validation (Oct 21, 2025).
"""

import time
import subprocess
import sys
import signal
import requests
from datetime import datetime, timedelta

class ExecutiveJrAutonomic:
    """
    Autonomic Coordination & Health Management Daemon

    Like the cerebellum - coordinates specialist movement automatically
    without conscious thought, but within safe boundaries.
    """

    # === AUTONOMIC BOUNDARIES ===
    BOUNDARIES = {
        # What I CAN do autonomously:
        "monitor_specialists": True,
        "restart_crashed_specialists": True,  # Within limits
        "gentle_coordination_nudges": True,   # Future implementation
        "monitor_health_metrics": True,
        "alert_other_jrs": True,
        "check_council_gateway": True,

        # What I CANNOT do autonomously:
        "stop_specialists_intentionally": False,  # Requires deliberation
        "change_trading_strategies": False,       # Requires approval
        "modify_core_architecture": False,
        "override_user_configs": False,
        "major_resource_changes": False  # >50% shift requires approval
    }

    # === CONFIGURATION ===
    CONFIG = {
        # Specialist health monitoring
        "health_check_interval": 120,      # 2 minutes
        "specialist_processes": [
            "trend_specialist_v2.py",
            "volatility_specialist_v2.py",
            "breakout_specialist_v2.py",
            "mean_reversion_specialist_v3.py"
        ],
        "specialist_dir": "/home/dereadi/scripts/claude/",
        "python_venv": "/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3",
        "auto_restart_enabled": True,
        "max_restart_attempts": 3,
        "restart_cooldown_seconds": 60,

        # Phase coherence monitoring (FUTURE - placeholder)
        "coherence_check_interval": 300,   # 5 minutes
        "low_coherence_threshold": 0.4,
        "high_coherence_threshold": 0.95,
        "nudge_strength": 0.1,

        # Resource optimization (FUTURE - placeholder)
        "resource_check_interval": 600,    # 10 minutes
        "cache_efficiency_threshold": 0.7,
        "memory_limit_mb": 2000,

        # Council readiness
        "readiness_check_interval": 900,   # 15 minutes
        "council_jrs": ["memory", "executive", "meta", "integration", "conscience"],
        "gateway_url": "http://192.168.132.223:5003"
    }

    def __init__(self):
        self.running = False
        self.last_health_check = None
        self.last_coherence_check = None
        self.last_resource_check = None
        self.last_readiness_check = None

        # Restart tracking (prevent infinite restart loops)
        self.restart_attempts = {}  # {specialist_name: count}
        self.last_restart_time = {}  # {specialist_name: timestamp}

        # Metrics
        self.metrics = {
            "health_checks_performed": 0,
            "specialists_restarted": 0,
            "restart_failures": 0,
            "council_gateway_failures": 0,
            "total_runtime_seconds": 0
        }

        # Signal handlers
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        signal.signal(signal.SIGINT, self.handle_shutdown)

    def handle_shutdown(self, signum, frame):
        """Handle graceful shutdown"""
        print(f"\\n⚠️  Executive Jr: Shutdown signal received (signal {signum})")
        self.running = False

    # === SPECIALIST HEALTH MONITORING ===

    def specialist_health_check(self):
        """
        Check if all specialists are running
        Auto-restart crashed specialists (within boundaries)
        """
        print(f"🏥 Executive Jr: Health check starting...")

        running_specialists = []
        crashed_specialists = []

        for spec_name in self.CONFIG["specialist_processes"]:
            if self.is_process_running(spec_name):
                running_specialists.append(spec_name)
            else:
                crashed_specialists.append(spec_name)

        # Report status
        print(f"  ✅ Running: {len(running_specialists)}")
        for spec in running_specialists:
            print(f"     • {spec}")

        if crashed_specialists:
            print(f"  ⚠️  Crashed: {len(crashed_specialists)}")
            for spec in crashed_specialists:
                print(f"     • {spec}")

            # Auto-restart if enabled
            if self.CONFIG["auto_restart_enabled"]:
                self.auto_restart_specialists(crashed_specialists)
        else:
            print(f"  🎯 All specialists healthy!")

        self.metrics["health_checks_performed"] += 1
        self.last_health_check = datetime.now()
        print(f"✅ Executive Jr: Health check complete")

    def is_process_running(self, spec_name):
        """Check if specialist process is running"""
        try:
            result = subprocess.run(
                ['pgrep', '-f', spec_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0 and result.stdout.strip()
        except Exception as e:
            print(f"  ❌ Error checking {spec_name}: {e}")
            return False

    def auto_restart_specialists(self, crashed):
        """Auto-restart crashed specialists (with safety limits)"""
        print(f"🔄 Executive Jr: Auto-restart initiated...")

        for spec_name in crashed:
            # Check restart attempts
            attempts = self.restart_attempts.get(spec_name, 0)

            if attempts >= self.CONFIG["max_restart_attempts"]:
                print(f"  ⚠️  {spec_name}: Max restart attempts ({attempts}) reached - ALERTING")
                # TODO: Alert other JRs (Meta Jr, Conscience Jr)
                continue

            # Check cooldown
            last_restart = self.last_restart_time.get(spec_name)
            if last_restart:
                elapsed = (datetime.now() - last_restart).total_seconds()
                if elapsed < self.CONFIG["restart_cooldown_seconds"]:
                    print(f"  ⏳ {spec_name}: Cooldown active ({elapsed:.0f}s)")
                    continue

            # Attempt restart
            print(f"  🔄 Restarting {spec_name} (attempt {attempts + 1}/{self.CONFIG['max_restart_attempts']})")

            if self.restart_specialist(spec_name):
                self.restart_attempts[spec_name] = attempts + 1
                self.last_restart_time[spec_name] = datetime.now()
                self.metrics["specialists_restarted"] += 1
                print(f"  ✅ {spec_name}: Restart successful")
            else:
                self.metrics["restart_failures"] += 1
                print(f"  ❌ {spec_name}: Restart failed")

    def restart_specialist(self, spec_name):
        """Restart a crashed specialist"""
        try:
            script_path = f"{self.CONFIG['specialist_dir']}{spec_name}"
            python_path = self.CONFIG["python_venv"]

            # Start specialist in background
            subprocess.Popen(
                [python_path, script_path],
                cwd=self.CONFIG["specialist_dir"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True  # Detach from parent
            )

            # Wait briefly to verify startup
            time.sleep(2)
            return self.is_process_running(spec_name)

        except Exception as e:
            print(f"  ❌ Error restarting {spec_name}: {e}")
            return False

    # === ON-DEMAND FUNCTIONS (WAKE-ON-QUERY) ===

    def resource_status(self):
        """
        ON-DEMAND: Get current specialist resource status
        Called by Query Triad when user asks about system health
        """
        status = {
            "specialists": {},
            "total_running": 0,
            "total_crashed": 0
        }

        for spec_name in self.CONFIG["specialist_processes"]:
            is_running = self.is_process_running(spec_name)
            status["specialists"][spec_name] = {
                "running": is_running,
                "restart_attempts": self.restart_attempts.get(spec_name, 0),
                "last_restart": str(self.last_restart_time.get(spec_name, "Never"))
            }
            if is_running:
                status["total_running"] += 1
            else:
                status["total_crashed"] += 1

        return status

    def coordinate_action(self, chiefs=None, jrs=None, task=None):
        """
        ON-DEMAND: Coordinate specific action across chiefs/JRs
        For complex queries requiring multiple JR coordination
        """
        result = {
            "task": task or "unspecified",
            "chiefs_requested": chiefs or [],
            "jrs_requested": jrs or [],
            "coordination_plan": []
        }

        # Build coordination plan
        if "memory" in (jrs or []):
            result["coordination_plan"].append("Memory Jr: Retrieve relevant thermal memories")

        if "meta" in (jrs or []):
            result["coordination_plan"].append("Meta Jr: Analyze cross-domain patterns")

        if "executive" in (jrs or []):
            result["coordination_plan"].append("Executive Jr: Coordinate resource allocation")

        # Specialist health context
        resource_stat = self.resource_status()
        result["specialist_health"] = {
            "running": resource_stat["total_running"],
            "crashed": resource_stat["total_crashed"]
        }

        return result

    def plan_execution(self, task_description):
        """
        ON-DEMAND: Create execution plan for complex task
        Breaks down into phases with resource allocation
        """
        plan = {
            "task": task_description,
            "phases": [],
            "estimated_duration": "TBD",
            "resource_requirements": []
        }

        # Simple heuristic-based planning
        if "trading" in task_description.lower():
            plan["phases"] = [
                "1. Check specialist health (Executive Jr)",
                "2. Review recent patterns (Meta Jr)",
                "3. Execute coordinated trades (Specialists)"
            ]
            plan["resource_requirements"] = ["All 4 specialists running", "Thermal memory access"]

        elif "memory" in task_description.lower() or "remember" in task_description.lower():
            plan["phases"] = [
                "1. Query thermal memory (Memory Jr)",
                "2. Analyze patterns (Meta Jr)",
                "3. Synthesize response (Integration Jr)"
            ]
            plan["resource_requirements"] = ["Database connection", "Memory Jr active"]

        else:
            plan["phases"] = [
                "1. Analyze requirements",
                "2. Coordinate JRs",
                "3. Execute and monitor"
            ]

        return plan

    def health_check_all(self):
        """
        ON-DEMAND: Comprehensive health check across all systems
        Like immediate physical exam instead of waiting for scheduled checkup
        """
        health = {
            "timestamp": str(datetime.now()),
            "specialists": {},
            "council_gateway": None,
            "metrics": self.metrics.copy()
        }

        # Specialist health
        for spec_name in self.CONFIG["specialist_processes"]:
            health["specialists"][spec_name] = self.is_process_running(spec_name)

        # Council Gateway
        try:
            response = requests.get(self.CONFIG["gateway_url"], timeout=5)
            health["council_gateway"] = {
                "status": "responsive" if response.status_code == 200 else f"status_{response.status_code}",
                "status_code": response.status_code
            }
        except Exception as e:
            health["council_gateway"] = {"status": "unreachable", "error": str(e)}

        # Summary
        running_count = sum(1 for running in health["specialists"].values() if running)
        health["summary"] = {
            "specialists_healthy": f"{running_count}/{len(self.CONFIG['specialist_processes'])}",
            "all_systems_operational": running_count == len(self.CONFIG["specialist_processes"]) and
                                       health["council_gateway"]["status"] == "responsive"
        }

        return health

    # === PHASE COHERENCE MONITORING (PLACEHOLDER) ===

    def phase_coherence_check(self):
        """
        Measure correlation between specialist signals
        PLACEHOLDER - Requires research (see EXECUTIVE_JR_KNOWLEDGE_GAPS.md)
        """
        print(f"🔗 Executive Jr: Phase coherence check (PLACEHOLDER)")

        # TODO: Implement after researching:
        # 1. Where specialists write signals
        # 2. How to calculate correlation matrix
        # 3. What coherence thresholds mean

        print(f"  ⏳ Signal collection not yet implemented")
        print(f"  ⏳ Correlation matrix calculation pending")
        print(f"  ⏳ See /ganuda/EXECUTIVE_JR_KNOWLEDGE_GAPS.md")

        self.last_coherence_check = datetime.now()

    # === RESOURCE OPTIMIZATION (PLACEHOLDER) ===

    def resource_optimization_check(self):
        """
        Monitor and optimize specialist resource usage
        PLACEHOLDER - Requires research (see EXECUTIVE_JR_KNOWLEDGE_GAPS.md)
        """
        print(f"📊 Executive Jr: Resource optimization check (PLACEHOLDER)")

        # TODO: Implement after researching:
        # 1. Where is LRU cache located
        # 2. How to measure cache efficiency
        # 3. How to optimize memory usage

        print(f"  ⏳ Cache stats collection not yet implemented")
        print(f"  ⏳ Memory optimization pending")
        print(f"  ⏳ See /ganuda/EXECUTIVE_JR_KNOWLEDGE_GAPS.md")

        self.last_resource_check = datetime.now()

    # === COUNCIL READINESS CHECK ===

    def council_readiness_check(self):
        """
        Ensure all 5 Council JRs can respond
        Verify Council Gateway is healthy
        """
        print(f"🦅 Executive Jr: Council readiness check...")

        # Check Council Gateway
        try:
            response = requests.get(
                self.CONFIG["gateway_url"],
                timeout=5
            )
            if response.status_code == 200:
                print(f"  ✅ Council Gateway: RESPONSIVE")
            else:
                print(f"  ⚠️  Council Gateway: Status {response.status_code}")
                self.metrics["council_gateway_failures"] += 1
        except Exception as e:
            print(f"  ❌ Council Gateway: UNREACHABLE ({e})")
            self.metrics["council_gateway_failures"] += 1

        # Check if gateway process is running
        if self.is_process_running("cherokee_tribal_mind.py"):
            print(f"  ✅ Council Gateway process: RUNNING")
        else:
            print(f"  ⚠️  Council Gateway process: NOT RUNNING")

        self.last_readiness_check = datetime.now()
        print(f"✅ Executive Jr: Readiness check complete")

    # === MAIN LOOP ===

    def run(self):
        """Main autonomic loop - runs continuously"""
        print(f"""
╔══════════════════════════════════════════════════════════╗
║  🎯 EXECUTIVE JR AUTONOMIC DAEMON STARTING              ║
║  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                          ║
║  Mission: Maintain specialist army autonomically         ║
║  Version: 1.0 (baseline monitoring + placeholders)      ║
║  Boundaries: Respected (no unauthorized modifications)  ║
╚══════════════════════════════════════════════════════════╝
        """)

        self.running = True
        start_time = time.time()

        # Initialize timers
        self.last_health_check = datetime.now()
        self.last_coherence_check = datetime.now()
        self.last_resource_check = datetime.now()
        self.last_readiness_check = datetime.now()

        print("🔥 Executive Jr: Autonomic processes activated")
        print("🏥 Specialist health: Every 2 minutes")
        print("🔗 Phase coherence: Every 5 minutes (PLACEHOLDER)")
        print("📊 Resource optimization: Every 10 minutes (PLACEHOLDER)")
        print("🦅 Council readiness: Every 15 minutes")
        print()

        try:
            while self.running:
                current_time = datetime.now()

                # Specialist health check (every 2 min)
                if (current_time - self.last_health_check).total_seconds() >= self.CONFIG["health_check_interval"]:
                    self.specialist_health_check()

                # Phase coherence check (every 5 min) - PLACEHOLDER
                if (current_time - self.last_coherence_check).total_seconds() >= self.CONFIG["coherence_check_interval"]:
                    self.phase_coherence_check()

                # Resource optimization (every 10 min) - PLACEHOLDER
                if (current_time - self.last_resource_check).total_seconds() >= self.CONFIG["resource_check_interval"]:
                    self.resource_optimization_check()

                # Council readiness (every 15 min)
                if (current_time - self.last_readiness_check).total_seconds() >= self.CONFIG["readiness_check_interval"]:
                    self.council_readiness_check()

                # Sleep for 60 seconds before next check
                time.sleep(60)

                # Update runtime
                self.metrics["total_runtime_seconds"] = time.time() - start_time

        except KeyboardInterrupt:
            print("\\n⚠️  Executive Jr: Shutdown signal received")
        except Exception as e:
            print(f"\\n❌ Executive Jr: Error in main loop: {e}")
            return 1
        finally:
            self.shutdown()

        return 0

    def shutdown(self):
        """Clean shutdown"""
        print(f"\\n🛑 Executive Jr: Shutting down...")

        # Print metrics
        runtime_hours = self.metrics["total_runtime_seconds"] / 3600
        print(f"""
╔══════════════════════════════════════════════════════════╗
║  📊 EXECUTIVE JR AUTONOMIC METRICS                      ║
║                                                          ║
║  Health Checks Performed:  {self.metrics['health_checks_performed']:>6}                    ║
║  Specialists Restarted:    {self.metrics['specialists_restarted']:>6}                    ║
║  Restart Failures:         {self.metrics['restart_failures']:>6}                    ║
║  Council Gateway Failures: {self.metrics['council_gateway_failures']:>6}                    ║
║  Total Runtime:            {runtime_hours:>6.1f} hours               ║
╚══════════════════════════════════════════════════════════╝
        """)

        print("🔥 Specialist Army continues trading...")

# === ENTRY POINT ===

if __name__ == "__main__":
    daemon = ExecutiveJrAutonomic()
    sys.exit(daemon.run())
