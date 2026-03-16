#!/usr/bin/env python3
"""
Skill Drift Audit — Eagle Eye's weekly check-up on the SkillRL library.

Runs weekly via systemd timer (Wed 05:00). Checks:
1. Content Integrity — SHA256 hash verification for all active skills
2. NEVER_SEND Re-scan — catches patterns added after skill creation
3. DC Violation Scan — flags sovereignty, security, build-to-last, waste-heat violations
4. Cold Skill Pruning — retires skills unused for 30+ days (Coyote condition)
5. Proficiency Report — identifies weakest categories for dawn mist briefing

Part of SkillRL Epic (Council vote #b91e297a508525c3).
"""

import hashlib
import json
import logging
import os
import re
import sys
from datetime import datetime

import psycopg2
import psycopg2.extras

# ── DB config (same pattern as fire_guard.py) ──
DB_HOST = os.environ.get("CHEROKEE_DB_HOST", "192.168.132.222")
DB_NAME = os.environ.get("CHEROKEE_DB_NAME", "zammad_production")
DB_USER = os.environ.get("CHEROKEE_DB_USER", "claude")
DB_PASS = os.environ.get("CHEROKEE_DB_PASS", "")

logger = logging.getLogger("skill_drift_audit")

# ── NEVER_SEND patterns (mirrored from skill_extractor.py + domain_tokenizer.py) ──
NEVER_SEND_PATTERNS = [
    r"CHEROKEE_DB_PASS",
    r"secrets\.env",
    r"\.pem\b",
    r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----",
    r"password\s*=\s*\S+",
    # Node names
    r"\bredfin\b",
    r"\bbluefin\b",
    r"\bgreenfin\b",
    r"\bowlfin\b",
    r"\beaglefin\b",
    r"\bsilverfin\b",
    r"\bbmasass\b",
    r"\bsasass2?\b",
    r"\bthunderduck\b",
    # LAN IPs
    r"\b192\.168\.\d{1,3}\.\d{1,3}\b",
    # WireGuard IPs
    r"\b10\.100\.0\.\d{1,3}\b",
    # Tailscale IPs
    r"\b100\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
    # Internal paths
    r"/ganuda/[\w/.\-]+",
]

# ── DC Violation patterns (flag only, don't quarantine) ──
DC_VIOLATION_PATTERNS = {
    "sovereignty": [
        r"migrate\s+to\s+aws",
        r"\bcloud\b",
        r"\bsaas\b",
    ],
    "security": [
        r"chmod\s+777",
        r"disable\s+firewall",
    ],
    "build_to_last": [
        r"move\s+fast\s+and\s+break\s+things",
        r"rewrite\s+from\s+scratch",
    ],
    "waste_heat": [
        r"scale\s+up",
        r"bigger\s+model",
        r"brute\s+force",
    ],
}


def compute_content_hash(intent: str, method: str, tool_hints) -> str:
    """Recompute SHA256 content_hash matching SkillDescriptor.content_hash property."""
    if isinstance(tool_hints, str):
        try:
            tool_hints = json.loads(tool_hints)
        except (json.JSONDecodeError, TypeError):
            tool_hints = []
    if tool_hints is None:
        tool_hints = []
    raw = intent + "||" + method + "||" + "|".join(sorted(tool_hints))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def check_never_send(text: str) -> list:
    """Check text against NEVER_SEND patterns. Returns list of matched patterns."""
    violations = []
    for pattern in NEVER_SEND_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            violations.append(pattern)
    return violations


def check_dc_violations(text: str) -> list:
    """Check text against DC violation patterns. Returns list of (category, pattern) tuples."""
    violations = []
    for category, patterns in DC_VIOLATION_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                violations.append((category, pattern))
    return violations


def run_audit(conn) -> dict:
    """
    Run the full drift audit against the skill_library table.

    Args:
        conn: A psycopg2 connection object.

    Returns:
        dict: Audit report matching the expected JSON schema.
    """
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    now = datetime.now(tz=None)  # local time, consistent with other scripts

    # Fetch all active skills
    cur.execute("""
        SELECT skill_id, name, intent, method, tool_hints, domain,
               content_hash, total_uses, successful_uses, total_reward,
               last_used, created_at, status
        FROM skill_library
        WHERE status = 'active'
    """)
    active_skills = cur.fetchall()

    integrity_checked = 0
    integrity_failures = 0
    never_send_violations = 0
    dc_violations_flagged = 0
    cold_skills_retired = 0
    quarantined_ids = []

    # ── 1. Content Integrity ──
    for skill in active_skills:
        integrity_checked += 1
        computed = compute_content_hash(
            skill["intent"], skill["method"], skill["tool_hints"]
        )
        if computed != skill["content_hash"]:
            integrity_failures += 1
            logger.critical(
                "INTEGRITY FAILURE: skill %s (%s) hash mismatch. "
                "Stored=%s Computed=%s. Auto-quarantining.",
                skill["skill_id"], skill["name"],
                skill["content_hash"], computed,
            )
            cur.execute(
                "UPDATE skill_library SET status = 'quarantine' WHERE skill_id = %s",
                (skill["skill_id"],),
            )
            conn.commit()
            quarantined_ids.append(skill["skill_id"])

    # ── 2. NEVER_SEND Re-scan ──
    for skill in active_skills:
        if skill["skill_id"] in quarantined_ids:
            continue  # already quarantined by integrity check
        for field_name in ("intent", "method"):
            violations = check_never_send(skill.get(field_name, ""))
            if violations:
                never_send_violations += 1
                logger.critical(
                    "NEVER_SEND violation in skill %s (%s) field '%s': %s. Auto-quarantining.",
                    skill["skill_id"], skill["name"], field_name, violations,
                )
                cur.execute(
                    "UPDATE skill_library SET status = 'quarantine' WHERE skill_id = %s",
                    (skill["skill_id"],),
                )
                conn.commit()
                quarantined_ids.append(skill["skill_id"])
                break  # don't double-count

    # ── 3. DC Violation Scan (flag only) ──
    for skill in active_skills:
        if skill["skill_id"] in quarantined_ids:
            continue
        method_text = skill.get("method", "")
        intent_text = skill.get("intent", "")
        combined = intent_text + " " + method_text
        violations = check_dc_violations(combined)
        if violations:
            dc_violations_flagged += 1
            logger.warning(
                "DC VIOLATION flagged in skill %s (%s): %s",
                skill["skill_id"], skill["name"],
                [(cat, pat) for cat, pat in violations],
            )

    # ── 4. Cold Skill Pruning ──
    cur.execute("""
        UPDATE skill_library
        SET status = 'retired', retire_reason = 'cold_30d'
        WHERE status = 'active'
          AND last_used IS NULL
          AND created_at < NOW() - INTERVAL '30 days'
        RETURNING skill_id, name
    """)
    cold_retired = cur.fetchall()
    conn.commit()
    cold_skills_retired = len(cold_retired)
    for skill in cold_retired:
        logger.info(
            "COLD PRUNED: skill %s (%s) — never used, created > 30 days ago.",
            skill["skill_id"], skill["name"],
        )

    # ── 5. Proficiency Report ──
    cur.execute("""
        SELECT domain, category, proficiency_score
        FROM skill_proficiency
        ORDER BY proficiency_score ASC
        LIMIT 10
    """)
    weakest_rows = cur.fetchall()
    weakest_categories = [
        {"domain": r["domain"], "category": r["category"], "proficiency": float(r["proficiency_score"])}
        for r in weakest_rows
    ]

    # Count current statuses for report
    cur.execute("""
        SELECT status, COUNT(*) as cnt
        FROM skill_library
        GROUP BY status
    """)
    status_counts = {r["status"]: r["cnt"] for r in cur.fetchall()}
    cur.close()

    report = {
        "timestamp": now.strftime("%Y-%m-%dT%H:%M:%S"),
        "integrity_checked": integrity_checked,
        "integrity_failures": integrity_failures,
        "never_send_violations": never_send_violations,
        "dc_violations_flagged": dc_violations_flagged,
        "cold_skills_retired": cold_skills_retired,
        "active_skills": status_counts.get("active", 0),
        "candidate_skills": status_counts.get("candidate", 0),
        "quarantined_skills": status_counts.get("quarantine", 0),
        "weakest_categories": weakest_categories,
    }

    logger.info("Drift audit complete: %s", json.dumps(report, indent=2))
    return report


def main():
    """Entry point for standalone execution."""
    global DB_PASS

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # Load secrets if DB_PASS not set
    if not DB_PASS:
        try:
            with open("/ganuda/config/secrets.env") as f:
                for line in f:
                    m = re.match(r"^(\w+)=(.+)$", line.strip())
                    if m:
                        os.environ[m.group(1)] = m.group(2)
            DB_PASS = os.environ.get("CHEROKEE_DB_PASS", "")
        except FileNotFoundError:
            pass

    if not DB_PASS:
        logger.error("No DB password found. Set CHEROKEE_DB_PASS or populate config/secrets.env.")
        sys.exit(1)

    conn = psycopg2.connect(
        host=DB_HOST, port=5432, dbname=DB_NAME,
        user=DB_USER, password=DB_PASS, connect_timeout=10,
    )

    try:
        report = run_audit(conn)
        print(json.dumps(report, indent=2))
    finally:
        conn.close()


if __name__ == "__main__":
    main()
