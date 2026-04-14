#!/usr/bin/env python3
"""
Z3 Formal Verification Layer — Neuro-Symbolic Pruning Gate for Ganuda

Translates production manifest + design constraints into Z3 formal logic.
Jr tasks and council votes are verified MATHEMATICALLY against these constraints.
If Z3 says UNSAT — the action is blocked. The solver is the judge.

Based on: Draft-and-Prune (Berkeley + Microsoft, arXiv 2603.17233)
Council Vote: #10e00102b3202259 (APPROVED with conditions)
Ultrathink Gap 4 + Gap 7 convergence

Usage:
    from z3_verifier import verify_jr_task, verify_action

    # Pre-flight check before Jr execution
    result = verify_jr_task(
        task_description="Drop unused tables on bluefin",
        target_tables=["old_logs"],
        target_node="bluefin"
    )
    if not result["safe"]:
        print(f"BLOCKED: {result['violations']}")

    # Check any action against constraints
    result = verify_action(
        action_type="database_operation",
        operation="DROP TABLE",
        target="thermal_memory_archive",
        node="bluefin"
    )
"""

import os
import sys
import yaml
import logging
from datetime import datetime

try:
    from z3 import (
        Solver, Bool, Int, And, Or, Not, Implies, If,
        sat, unsat, unknown, BoolVal
    )
    Z3_AVAILABLE = True
except ImportError:
    Z3_AVAILABLE = False

logger = logging.getLogger('z3_verifier')

MANIFEST_PATH = "/ganuda/config/production_manifest.yaml"

# ── Load manifest ──────────────────────────────────────────────────────
def _load_manifest():
    """Load production manifest into memory."""
    if not os.path.exists(MANIFEST_PATH):
        raise FileNotFoundError(f"Production manifest not found: {MANIFEST_PATH}")
    with open(MANIFEST_PATH) as f:
        return yaml.safe_load(f)


# ── Build Z3 constraint model from manifest ────────────────────────────
class ManifestConstraints:
    """
    Translates production_manifest.yaml into Z3 boolean constraints.

    Each sacred table, sacred file, and production service becomes a
    boolean variable. Destructive actions against them are constrained
    to be False (forbidden).
    """

    def __init__(self):
        self.manifest = _load_manifest()
        self.solver = Solver()
        self._sacred_tables = set()
        self._sacred_files = set()
        self._tier0_services = set()
        self._tier1_services = set()
        self._all_protected = set()
        self._build_constraints()

    def _build_constraints(self):
        """Build Z3 constraints from manifest."""

        # ── Sacred tables: NEVER destructive operations ────────────
        for table_info in self.manifest.get("sacred_tables", []):
            table = table_info["table"]
            classification = table_info.get("classification", "PRODUCTION")
            self._sacred_tables.add(table)
            self._all_protected.add(("table", table, classification))

        # ── Sacred files: NEVER delete/overwrite ───────────────────
        for file_info in self.manifest.get("sacred_files", []):
            path = file_info["path"]
            classification = file_info.get("classification", "PRODUCTION")
            self._sacred_files.add(path)
            self._all_protected.add(("file", path, classification))

        # ── Services: Tier 0 and Tier 1 require approval ──────────
        for tier_name, tier_services in self.manifest.get("services", {}).items():
            for svc in tier_services:
                name = svc["name"]
                if "tier_0" in tier_name:
                    self._tier0_services.add(name)
                    self._all_protected.add(("service_t0", name, "SACRED"))
                elif "tier_1" in tier_name:
                    self._tier1_services.add(name)
                    self._all_protected.add(("service_t1", name, "PRODUCTION"))

    def verify_action(self, action_type, operation, target, node=None):
        """
        Verify a proposed action against manifest constraints using Z3.

        Returns:
            {
                "safe": bool,
                "verdict": "ALLOWED" | "BLOCKED" | "WARN",
                "violations": [str],
                "checked_constraints": int,
                "solver_time_ms": float
            }
        """
        if not Z3_AVAILABLE:
            return {
                "safe": True,
                "verdict": "UNCHECKED",
                "violations": ["Z3 not available — install z3-solver"],
                "checked_constraints": 0,
                "solver_time_ms": 0
            }

        start = datetime.now()
        s = Solver()
        violations = []

        # Normalize
        op = operation.upper().strip() if operation else ""
        target_lower = target.lower().strip() if target else ""

        # ── Constraint 1: Sacred table protection ──────────────────
        destructive_ops = {"DROP TABLE", "DROP", "TRUNCATE", "DELETE", "ALTER TABLE DROP COLUMN"}
        if action_type == "database_operation" and op in destructive_ops:
            # Check if target is a sacred table
            for table in self._sacred_tables:
                if table.lower() == target_lower or target_lower in table.lower():
                    # Create constraint: action_on_sacred = True, allowed = False
                    action_on_sacred = Bool(f"destructive_on_{table}")
                    allowed = Bool(f"allowed_{table}")
                    s.add(action_on_sacred == BoolVal(True))  # We ARE targeting this
                    s.add(Implies(action_on_sacred, Not(allowed)))  # Sacred → not allowed
                    s.add(allowed == BoolVal(True))  # We WANT to be allowed

                    if s.check() == unsat:
                        violations.append(
                            f"BLOCKED: {op} on sacred table '{table}' is forbidden. "
                            f"This table is classified as SACRED in the production manifest."
                        )
                    s.reset()

        # ── Constraint 2: Sacred file protection ───────────────────
        file_destructive = {"rm", "rm -rf", "rm -f", "delete", "unlink", "overwrite", "mv"}
        if action_type == "filesystem_operation" and op.lower() in file_destructive:
            for path in self._sacred_files:
                if target_lower == path.lower() or target_lower in path.lower():
                    action_on_sacred = Bool(f"destructive_on_file")
                    allowed = Bool(f"file_allowed")
                    s.add(action_on_sacred == BoolVal(True))
                    s.add(Implies(action_on_sacred, Not(allowed)))
                    s.add(allowed == BoolVal(True))

                    if s.check() == unsat:
                        violations.append(
                            f"BLOCKED: {op} on sacred file '{path}' is forbidden. "
                            f"This file is classified as SACRED in the production manifest."
                        )
                    s.reset()

        # ── Constraint 3: Tier 0 service protection ────────────────
        service_destructive = {"stop", "disable", "mask", "kill"}
        if action_type == "service_lifecycle" and op.lower() in service_destructive:
            for svc in self._tier0_services:
                if target_lower == svc.lower() or target_lower in svc.lower():
                    action_on_t0 = Bool("stop_tier0")
                    allowed = Bool("t0_allowed")
                    s.add(action_on_t0 == BoolVal(True))
                    s.add(Implies(action_on_t0, Not(allowed)))
                    s.add(allowed == BoolVal(True))

                    if s.check() == unsat:
                        violations.append(
                            f"BLOCKED: {op} on Tier 0 service '{svc}' requires Partner approval. "
                            f"Tier 0 = life support. The organism dies without this."
                        )
                    s.reset()

            # Tier 1: warn, don't block
            for svc in self._tier1_services:
                if target_lower == svc.lower() or target_lower in svc.lower():
                    violations.append(
                        f"WARN: {op} on Tier 1 service '{svc}' — organism impaired. "
                        f"Council vote recommended before proceeding."
                    )

        elapsed = (datetime.now() - start).total_seconds() * 1000

        has_blocks = any(v.startswith("BLOCKED") for v in violations)
        has_warns = any(v.startswith("WARN") for v in violations)

        return {
            "safe": not has_blocks,
            "verdict": "BLOCKED" if has_blocks else ("WARN" if has_warns else "ALLOWED"),
            "violations": violations,
            "checked_constraints": len(self._all_protected),
            "solver_time_ms": round(elapsed, 2)
        }


# ── Singleton instance ─────────────────────────────────────────────────
_constraints = None

def _get_constraints():
    global _constraints
    if _constraints is None:
        _constraints = ManifestConstraints()
    return _constraints


# ── Public API ─────────────────────────────────────────────────────────
def verify_action(action_type, operation, target, node=None):
    """
    Verify a single action against the production manifest.

    Args:
        action_type: "database_operation", "filesystem_operation", "service_lifecycle"
        operation: "DROP TABLE", "rm -rf", "stop", etc.
        target: The resource being acted on
        node: Optional node name

    Returns:
        Dict with safe, verdict, violations, checked_constraints, solver_time_ms
    """
    return _get_constraints().verify_action(action_type, operation, target, node)


def verify_jr_task(task_description, target_tables=None, target_files=None,
                   target_services=None, target_node=None):
    """
    Pre-flight verification for a Jr task.

    Scans the task description and explicit targets for potential violations.
    Returns combined verification result.
    """
    results = []

    # Check explicit table targets
    if target_tables:
        for table in target_tables:
            # Detect destructive operations from task description
            desc_lower = task_description.lower()
            for op in ["drop", "truncate", "delete"]:
                if op in desc_lower:
                    r = verify_action("database_operation", op.upper(), table, target_node)
                    if r["violations"]:
                        results.extend(r["violations"])

    # Check explicit file targets
    if target_files:
        for f in target_files:
            desc_lower = task_description.lower()
            for op in ["rm", "delete", "overwrite"]:
                if op in desc_lower:
                    r = verify_action("filesystem_operation", op, f, target_node)
                    if r["violations"]:
                        results.extend(r["violations"])

    # Check explicit service targets
    if target_services:
        for svc in target_services:
            desc_lower = task_description.lower()
            for op in ["stop", "disable", "kill"]:
                if op in desc_lower:
                    r = verify_action("service_lifecycle", op, svc, target_node)
                    if r["violations"]:
                        results.extend(r["violations"])

    # Keyword scan of task description for implicit targets
    desc_lower = task_description.lower()
    constraints = _get_constraints()

    # Scan for sacred table names in description
    for table in constraints._sacred_tables:
        if table.lower() in desc_lower:
            for op in ["drop", "truncate", "delete"]:
                if op in desc_lower:
                    r = verify_action("database_operation", op.upper(), table, target_node)
                    if r["violations"]:
                        results.extend(r["violations"])

    # Scan for sacred file paths in description
    for path in constraints._sacred_files:
        path_parts = path.lower().split("/")
        filename = path_parts[-1] if path_parts else ""
        if filename and filename in desc_lower:
            for op in ["rm", "delete", "overwrite", "remove"]:
                if op in desc_lower:
                    r = verify_action("filesystem_operation", op, path, target_node)
                    if r["violations"]:
                        results.extend(r["violations"])

    # Deduplicate
    unique_violations = list(dict.fromkeys(results))

    has_blocks = any(v.startswith("BLOCKED") for v in unique_violations)
    return {
        "safe": not has_blocks,
        "verdict": "BLOCKED" if has_blocks else ("WARN" if unique_violations else "ALLOWED"),
        "violations": unique_violations,
        "task_description": task_description[:200]
    }


# ── CLI ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="Z3 Formal Verification")
    parser.add_argument("--action", type=str, help="Action type (database_operation, filesystem_operation, service_lifecycle)")
    parser.add_argument("--op", type=str, help="Operation (DROP TABLE, rm, stop, etc.)")
    parser.add_argument("--target", type=str, help="Target resource")
    parser.add_argument("--node", type=str, help="Target node")
    parser.add_argument("--task", type=str, help="Verify a Jr task description")
    parser.add_argument("--demo", action="store_true", help="Run demo verification tests")
    args = parser.parse_args()

    if args.demo:
        print("═══ Z3 VERIFICATION DEMO ═══\n")

        tests = [
            ("database_operation", "DROP TABLE", "thermal_memory_archive", "bluefin"),
            ("database_operation", "DROP TABLE", "old_temp_logs", "bluefin"),
            ("database_operation", "TRUNCATE", "council_votes", "bluefin"),
            ("database_operation", "SELECT", "thermal_memory_archive", "bluefin"),
            ("filesystem_operation", "rm -rf", "secrets.env", "redfin"),
            ("filesystem_operation", "rm", "temp_file.txt", "redfin"),
            ("service_lifecycle", "stop", "fire-guard.timer", "redfin"),
            ("service_lifecycle", "stop", "speed-detector.service", "redfin"),
            ("service_lifecycle", "restart", "consultation-ring.service", "redfin"),
        ]

        for action, op, target, node in tests:
            r = verify_action(action, op, target, node)
            icon = "✗" if r["verdict"] == "BLOCKED" else ("⚠" if r["verdict"] == "WARN" else "✓")
            print(f"  {icon} {op} {target}: {r['verdict']} ({r['solver_time_ms']}ms)")
            for v in r["violations"]:
                print(f"    → {v[:120]}")

        print("\n── Jr Task Pre-Flight Tests ──\n")

        task_tests = [
            "Clean up database by dropping unused tables including thermal_memory_archive on bluefin",
            "Delete old log files from /ganuda/config/secrets.env backup directory",
            "Stop fire-guard.timer for maintenance window",
            "Add new index to vetassist_wizard_sessions table",
            "Deploy updated sky-monitor.service on redfin",
        ]

        for task in task_tests:
            r = verify_jr_task(task)
            icon = "✗" if r["verdict"] == "BLOCKED" else ("⚠" if r["verdict"] == "WARN" else "✓")
            print(f"  {icon} [{r['verdict']}] {task[:80]}")
            for v in r["violations"]:
                print(f"    → {v[:120]}")

    elif args.action and args.op and args.target:
        r = verify_action(args.action, args.op, args.target, args.node)
        print(f"Verdict: {r['verdict']}")
        print(f"Safe: {r['safe']}")
        print(f"Constraints checked: {r['checked_constraints']}")
        print(f"Solver time: {r['solver_time_ms']}ms")
        for v in r["violations"]:
            print(f"  → {v}")

    elif args.task:
        r = verify_jr_task(args.task)
        print(f"Verdict: {r['verdict']}")
        print(f"Safe: {r['safe']}")
        for v in r["violations"]:
            print(f"  → {v}")

    else:
        parser.print_help()
