#!/usr/bin/env python3
"""
Seed Skill Library — Insert hand-crafted seed skills into skill_library.

Part of SkillRL Epic (Council vote #b91e297a508525c3).
JR-SKILLRL-08: Solves Raven's cold start problem by populating the library
with 12 verified, generic, reusable patterns from day one.

All skills are inserted with status='active' and council_vote_id='seed_library'.
Each skill passes sanitize_skill before insertion — no infrastructure leaks.
"""

import json
import logging
import os
import sys

import psycopg2

# Add project root to path for lib imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib.skill_descriptor import SkillDescriptor
from lib.skill_extractor import sanitize_skill

logger = logging.getLogger("seed_skill_library")

DB_CONFIG = {
    "host": "192.168.132.222",
    "port": 5432,
    "dbname": "zammad_production",
    "user": "claude",
    "password": os.environ.get("CHEROKEE_DB_PASS", ""),
}


def build_seed_skills() -> list[SkillDescriptor]:
    """Build 12 hand-crafted seed skills covering the federation's most common patterns."""
    return [
        # ── db_operations ──
        SkillDescriptor(
            name="Add column to existing table with migration",
            intent=(
                "Schema evolution must be additive and reversible. Adding a column with a "
                "DEFAULT value avoids breaking existing queries, and wrapping in a transaction "
                "ensures atomicity — either the migration completes fully or rolls back clean."
            ),
            method=(
                "1. Write an ALTER TABLE ADD COLUMN statement with appropriate type and DEFAULT. "
                "2. Wrap in BEGIN/COMMIT transaction block. "
                "3. Add a rollback script (ALTER TABLE DROP COLUMN IF EXISTS). "
                "4. Verify with SELECT column_name FROM information_schema.columns. "
                "5. Update any ORM models or data classes that reference the table."
            ),
            difficulty=3,
            tool_hints=["psql", "psycopg2", "information_schema"],
            domain="code",
        ),
        SkillDescriptor(
            name="Create database index for slow query",
            intent=(
                "Indexes trade write overhead for read speed. Adding a targeted index on "
                "columns used in WHERE, JOIN, or ORDER BY clauses can reduce query time by "
                "orders of magnitude without changing application code."
            ),
            method=(
                "1. Identify slow query via EXPLAIN ANALYZE. "
                "2. Check existing indexes on the table (pg_indexes or \\di). "
                "3. Create index with CREATE INDEX CONCURRENTLY to avoid table locks. "
                "4. Re-run EXPLAIN ANALYZE to confirm improvement. "
                "5. Document the index purpose in a migration comment."
            ),
            difficulty=4,
            tool_hints=["psql", "EXPLAIN ANALYZE", "CREATE INDEX CONCURRENTLY"],
            domain="code",
        ),
        # ── api_integration ──
        SkillDescriptor(
            name="Create FastAPI endpoint with health check",
            intent=(
                "Every new API endpoint needs a health check so monitoring can verify it is "
                "alive independently. Separating the health route from business logic ensures "
                "the service can be probed without side effects."
            ),
            method=(
                "1. Define the business endpoint with proper request/response models (Pydantic). "
                "2. Add a /health GET endpoint returning {'status': 'ok', 'service': '<name>'}. "
                "3. Include error handling with appropriate HTTP status codes. "
                "4. Add request validation and input sanitization. "
                "5. Write a smoke test that hits both the health and business endpoints."
            ),
            difficulty=4,
            tool_hints=["fastapi", "pydantic", "uvicorn", "httpx"],
            domain="code",
        ),
        # ── frontend ──
        SkillDescriptor(
            name="Fix CSS layout with scoped DOM queries",
            intent=(
                "CSS fixes must be scoped to avoid cascading side effects. Using scoped "
                "selectors (class-based or data attributes) ensures the fix applies only to "
                "the target component without breaking other layouts."
            ),
            method=(
                "1. Identify the broken layout element via browser dev tools. "
                "2. Add a scoped CSS class or data attribute to the target element. "
                "3. Write the fix using the scoped selector (avoid tag-only selectors). "
                "4. Test at multiple viewport widths (mobile, tablet, desktop). "
                "5. Verify no sibling or parent elements are affected by the change."
            ),
            difficulty=4,
            tool_hints=["css", "browser_devtools", "responsive_testing"],
            domain="code",
        ),
        # ── ops_deployment ──
        SkillDescriptor(
            name="Create systemd service with timer",
            intent=(
                "Recurring tasks need a service unit for execution and a timer unit for "
                "scheduling. Separating the two means the service can be triggered manually "
                "or on schedule, and systemd handles logging, restart, and dependency ordering."
            ),
            method=(
                "1. Create the .service unit with Type=oneshot, ExecStart, User, and WorkingDirectory. "
                "2. Create the .timer unit with OnCalendar or OnBootSec schedule. "
                "3. Set Persistent=true on the timer so missed runs fire on next boot. "
                "4. Enable and start the timer (systemctl enable --now <name>.timer). "
                "5. Verify with systemctl list-timers and journalctl -u <name>.service."
            ),
            difficulty=5,
            tool_hints=["systemctl", "journalctl", "systemd_unit_files"],
            domain="ops",
        ),
        SkillDescriptor(
            name="Deploy configuration with rollback capability",
            intent=(
                "Configuration changes are the most common cause of outages. Every config "
                "deployment must preserve the previous version so a rollback is one command "
                "away. Copy-before-write is cheaper than debugging a broken config at 2 AM."
            ),
            method=(
                "1. Back up the current config file with a timestamped copy. "
                "2. Validate the new config syntax before deployment (lint, dry-run, or parse check). "
                "3. Deploy the new config to the target location. "
                "4. Reload or restart the affected service. "
                "5. Verify the service is healthy. If unhealthy, restore backup and reload."
            ),
            difficulty=4,
            tool_hints=["cp", "systemctl", "config_validation"],
            domain="ops",
        ),
        # ── testing ──
        SkillDescriptor(
            name="Write integration test for API endpoint",
            intent=(
                "Integration tests verify that the API contract holds end-to-end, catching "
                "issues that unit tests miss (serialization, middleware, auth). Testing the "
                "actual HTTP layer ensures the endpoint works as a consumer would use it."
            ),
            method=(
                "1. Set up a test client (TestClient for FastAPI, or httpx). "
                "2. Write a test for the happy path with expected status code and response shape. "
                "3. Write tests for error cases (bad input, missing auth, not found). "
                "4. Assert on response status codes AND response body content. "
                "5. Clean up any test data created during the test."
            ),
            difficulty=4,
            tool_hints=["pytest", "httpx", "TestClient", "fixtures"],
            domain="code",
        ),
        # ── security ──
        SkillDescriptor(
            name="Run credential scan on source file",
            intent=(
                "Credentials in source code are the most common security vulnerability. "
                "Pattern-based scanning catches hardcoded passwords, API keys, and private "
                "keys before they reach version control or production."
            ),
            method=(
                "1. Define patterns to scan for: passwords, API keys, private keys, connection strings. "
                "2. Run regex scan against target files for each pattern. "
                "3. Flag any matches with file path, line number, and pattern name. "
                "4. For each match, determine if it is a true positive or false positive. "
                "5. Replace true positives with environment variable references."
            ),
            difficulty=3,
            tool_hints=["regex", "grep", "env_vars", "secrets_management"],
            domain="code",
        ),
        # ── monitoring ──
        SkillDescriptor(
            name="Add health check to monitoring system",
            intent=(
                "A service without a health check is invisible to operations. Health checks "
                "must be lightweight (no side effects), fast (sub-second), and return a "
                "machine-parseable status so automated alerting can act on failures."
            ),
            method=(
                "1. Identify the service's critical dependency (DB, upstream API, filesystem). "
                "2. Write a health check that probes each dependency with a timeout. "
                "3. Return structured status: {'healthy': bool, 'checks': {dep: status}}. "
                "4. Register the health check endpoint in the monitoring configuration. "
                "5. Set up an alert rule that fires when the health check fails N times consecutively."
            ),
            difficulty=3,
            tool_hints=["health_endpoint", "monitoring_config", "alerting"],
            domain="ops",
        ),
        # ── config ──
        SkillDescriptor(
            name="Add config section with kill switch",
            intent=(
                "New features should launch behind a kill switch so they can be disabled "
                "without a code deployment. A config-driven kill switch reduces blast radius — "
                "flip one value and the feature is off, no rollback needed."
            ),
            method=(
                "1. Add a new section to the config file with 'enabled: true/false' as the kill switch. "
                "2. Add any feature-specific parameters with sensible defaults. "
                "3. Load the config at startup and check the enabled flag before feature execution. "
                "4. Log when the feature is disabled so operators know the kill switch is active. "
                "5. Document the config section and its parameters in the config schema."
            ),
            difficulty=3,
            tool_hints=["yaml", "config_loader", "feature_flags"],
            domain="code",
        ),
        # ── refactoring ──
        SkillDescriptor(
            name="Extract shared logic into base class",
            intent=(
                "When two or more classes share identical logic, extracting it into a base class "
                "eliminates duplication and creates a single point of change. The key insight is "
                "identifying WHICH logic is truly shared vs. accidentally similar."
            ),
            method=(
                "1. Identify the duplicated methods/attributes across classes. "
                "2. Determine which parts are truly shared vs. coincidentally similar. "
                "3. Create a base class with the shared logic as methods. "
                "4. Have the original classes inherit from the base and remove duplicated code. "
                "5. Run all existing tests to verify behavior is unchanged (no regressions)."
            ),
            difficulty=5,
            tool_hints=["inheritance", "abc", "pytest", "refactoring"],
            domain="code",
        ),
        # ── governance ──
        SkillDescriptor(
            name="Submit proposal to council with concerns",
            intent=(
                "Governance proposals that anticipate objections get approved faster and with "
                "higher confidence. Pre-loading concerns into the proposal shows the council "
                "that risks were considered, converting potential dissent into built-in safeguards."
            ),
            method=(
                "1. Draft the proposal with a clear problem statement and proposed solution. "
                "2. Identify at least 2 potential concerns or risks. "
                "3. For each concern, propose a mitigation or condition. "
                "4. Submit to the council vote mechanism with the concerns embedded. "
                "5. If approved with conditions, create follow-up tasks for each condition."
            ),
            difficulty=6,
            tool_hints=["council_vote", "proposal_format", "condition_tracking"],
            domain="general",
        ),
    ]


def insert_seed_skill(skill: SkillDescriptor, conn) -> bool:
    """Insert a single seed skill into the skill_library table.

    Returns True if inserted, False if skipped (duplicate or error).
    """
    row = skill.to_db_row()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO skill_library (
                skill_id, name, intent, method, difficulty,
                tool_hints, domain, is_compound, parent_skills,
                council_vote_id, provenance_hash, source_task_id,
                status, content_hash
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s::text[], %s, %s, %s::varchar(64)[],
                %s, %s, %s,
                %s, %s
            )
            ON CONFLICT (skill_id) DO NOTHING
            """,
            (
                row["skill_id"],
                row["name"],
                row["intent"],
                row["method"],
                row["difficulty"],
                json.loads(row["tool_hints"]),   # PostgreSQL array
                row["domain"],
                row["is_compound"],
                json.loads(row["parent_skills"]),  # PostgreSQL array
                "seed_library",                  # council_vote_id
                row["content_hash"],             # provenance_hash = content_hash for seeds
                row["source_task_id"],
                "active",                        # status
                row["content_hash"],
            ),
        )
        inserted = cur.rowcount > 0
        conn.commit()
        if inserted:
            logger.info("Inserted seed skill: %s (id=%s)", skill.name, skill.skill_id)
        else:
            logger.info("Skipped duplicate seed skill: %s (id=%s)", skill.name, skill.skill_id)
        return inserted
    except Exception as exc:
        conn.rollback()
        logger.error("Failed to insert seed skill '%s': %s", skill.name, exc)
        return False
    finally:
        cur.close()


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # Build seed skills
    raw_skills = build_seed_skills()
    logger.info("Built %d seed skills", len(raw_skills))

    # Sanitize each skill — reject any with infrastructure leaks
    sanitized_skills = []
    for skill in raw_skills:
        result = sanitize_skill(skill)
        if result is None:
            logger.error("REJECTED skill '%s' — failed sanitize_skill", skill.name)
            sys.exit(1)
        sanitized_skills.append(result)

    logger.info("All %d skills passed sanitize_skill", len(sanitized_skills))

    # Verify content hashes are valid
    for skill in sanitized_skills:
        assert len(skill.content_hash) == 64, f"Invalid content_hash for {skill.name}"

    # Connect to DB and insert
    try:
        conn = psycopg2.connect(**DB_CONFIG)
    except Exception as exc:
        logger.error("DB connection failed: %s", exc)
        logger.info("Skills validated successfully but not inserted (no DB connection).")
        # Print summary for verification
        domains = set()
        for s in sanitized_skills:
            domains.add(s.domain)
            print(f"  [{s.domain}] {s.name} (difficulty={s.difficulty}, id={s.skill_id})")
        print(f"\nDomains covered: {sorted(domains)}")
        print(f"Total skills: {len(sanitized_skills)}")
        return

    try:
        inserted = 0
        for skill in sanitized_skills:
            if insert_seed_skill(skill, conn):
                inserted += 1

        logger.info("Seed complete: %d/%d skills inserted", inserted, len(sanitized_skills))

        # Verify
        cur = conn.cursor()
        cur.execute(
            "SELECT skill_id, name, domain, difficulty, status "
            "FROM skill_library WHERE council_vote_id = 'seed_library' "
            "ORDER BY domain, difficulty"
        )
        rows = cur.fetchall()
        logger.info("Verification: %d seed skills in skill_library", len(rows))
        for row in rows:
            logger.info("  %s | %s | %s | d=%d | %s", row[0], row[2], row[1], row[3], row[4])
        cur.close()
    finally:
        conn.commit()  # explicit commit before close
        conn.close()


if __name__ == "__main__":
    main()
