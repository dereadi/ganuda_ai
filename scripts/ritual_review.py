#!/usr/bin/env python3
"""
Ritual Reinforcement Engine — Cherokee AI Federation
Council Vote #8487 — The school year review for the cluster.

Schedule:
  - Weekly (Sunday 4:00 AM): Standard review + cultural digest
  - Monthly (new moon): Deep review + pattern challenge
  - Seasonal: Major review (manual trigger)
  - Annual (Green Corn): Full renewal (manual trigger)

Usage:
  python3 ritual_review.py --mode weekly
  python3 ritual_review.py --mode monthly
  python3 ritual_review.py --mode seasonal
  python3 ritual_review.py --mode green-corn
"""

import os
import sys
import json
import hashlib
import argparse
import logging
from datetime import datetime, timedelta

import psycopg2
from psycopg2.extras import RealDictCursor

# Load database credentials from environment or secrets file
SECRETS_FILE = "/ganuda/config/secrets.env"
DIGEST_OUTPUT = "/ganuda/docs/cultural_digest.md"
LOG_FILE = "/var/log/ganuda/ritual_review.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [RITUAL] %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ritual_review")


def load_secrets():
    """Load database credentials from secrets.env"""
    secrets = {}
    if os.path.exists(SECRETS_FILE):
        with open(SECRETS_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    secrets[key] = val
    return secrets


def get_db_connection():
    """Connect to zammad_production on bluefin"""
    secrets = load_secrets()
    return psycopg2.connect(
        host=secrets.get("CHEROKEE_DB_HOST", "192.168.132.222"),
        dbname=secrets.get("CHEROKEE_DB_NAME", "zammad_production"),
        user=secrets.get("CHEROKEE_DB_USER", "claude"),
        password=secrets.get("CHEROKEE_DB_PASS", ""),
        port=int(secrets.get("CHEROKEE_DB_PORT", "5432"))
    )


def gather_patterns(conn):
    """GATHER — Read all behavioral_pattern memories"""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT id, original_content, temperature_score, tags, metadata,
                   created_at, memory_type
            FROM thermal_memory_archive
            WHERE memory_type = 'behavioral_pattern'
            ORDER BY temperature_score DESC, created_at ASC
        """)
        return cur.fetchall()


def gather_sacred(conn):
    """Read sacred memories for Green Corn review"""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT id, original_content, temperature_score, tags, metadata,
                   created_at, memory_type
            FROM thermal_memory_archive
            WHERE memory_type = 'sacred'
               OR (metadata->>'sacred_fire')::boolean = true
            ORDER BY created_at ASC
        """)
        return cur.fetchall()


def check_recent_references(conn, pattern, days=30):
    """Check if a pattern has been referenced in recent episodic memories"""
    try:
        keywords = []
        # Extract key terms from the pattern content
        content = (pattern.get("original_content") or "").lower()
        for tag in (pattern.get("tags") or []):
            if isinstance(tag, str) and tag not in ("behavioral", "foundational", "emergent", "corrective", "taught", "auto-generated", "needs-review"):
                keywords.append(tag)

        if not keywords:
            # Try extracting words from content as fallback
            words = [w for w in content.split() if len(w) > 5 and w.isalpha()][:3]
            keywords = words

        # Safety: ensure we actually have usable keywords
        keywords = [k for k in keywords if k and isinstance(k, str) and len(k) > 2]
        if not keywords:
            return 0

        # Search for keyword mentions in recent episodic memories
        conditions = " OR ".join(["original_content ILIKE %s" for _ in keywords])
        params = [f"%{kw}%" for kw in keywords[:5]]

        with conn.cursor() as cur:
            cur.execute(f"""
                SELECT COUNT(*) FROM thermal_memory_archive
                WHERE memory_type = 'episodic'
                  AND created_at > NOW() - INTERVAL '{days} days'
                  AND ({conditions})
            """, params)
            return cur.fetchone()[0]
    except Exception as e:
        logger.warning(f"check_recent_references failed for pattern {pattern.get('id', '?')}: {e}")
        return 0


def review_pattern(conn, pattern, mode="weekly"):
    """REVIEW — Evaluate a single pattern for reinforcement or flagging"""
    metadata = pattern.get("metadata") or {}
    sacred_fire = metadata.get("sacred_fire", False)
    can_evolve = metadata.get("can_evolve", True)
    review_interval = metadata.get("review_interval_days", 7)
    last_validated = metadata.get("last_validated", "")
    observation_count = metadata.get("observation_count", 0)

    result = {
        "id": pattern["id"],
        "action": "reinforce",  # default
        "reason": "",
        "sacred_fire": sacred_fire,
        "current_temp": float(pattern["temperature_score"]),
        "new_temp": float(pattern["temperature_score"]),
    }

    # Sacred fire patterns: always reinforce, never flag
    if sacred_fire and mode != "green-corn":
        result["action"] = "reinforce"
        result["reason"] = "Sacred fire — always reinforced"
        result["new_temp"] = max(float(pattern["temperature_score"]), 0.95)
        return result

    # Check for recent references
    reference_count = check_recent_references(conn, pattern)

    if reference_count > 3:
        # Actively referenced — reinforce strongly
        result["action"] = "reinforce"
        result["reason"] = f"Actively referenced ({reference_count} recent mentions)"
        result["new_temp"] = min(float(pattern["temperature_score"]) + 0.05, 1.0)
    elif reference_count > 0:
        # Some references — mild reinforce
        result["action"] = "reinforce"
        result["reason"] = f"Referenced ({reference_count} mentions)"
        result["new_temp"] = min(float(pattern["temperature_score"]) + 0.02, 1.0)
    else:
        # No recent references
        if mode in ("monthly", "seasonal", "green-corn"):
            result["action"] = "flag"
            result["reason"] = "No recent references — flagged for human review"
            result["new_temp"] = float(pattern["temperature_score"])  # Don't decay yet
        else:
            # Weekly: just note it, don't flag yet
            result["action"] = "monitor"
            result["reason"] = "No recent references — monitoring"
            result["new_temp"] = float(pattern["temperature_score"])

    return result


def reinforce_patterns(conn, reviews):
    """REINFORCE — Update temperature scores for validated patterns"""
    reinforced = 0
    with conn.cursor() as cur:
        for review in reviews:
            if review["action"] == "reinforce" and review["new_temp"] != review["current_temp"]:
                cur.execute("""
                    UPDATE thermal_memory_archive
                    SET temperature_score = %s
                    WHERE id = %s
                """, (review["new_temp"], review["id"]))
                reinforced += 1
    conn.commit()
    logger.info(f"Reinforced {reinforced} patterns")
    return reinforced


def generate_digest(patterns, reviews, mode, failure_results=None, new_corrective=None):
    """DIGEST — Generate cultural digest document"""
    now = datetime.now()
    digest_lines = [
        f"# Cultural Digest — {now.strftime('%B %d, %Y')}",
        f"",
        f"**Mode:** {mode} review",
        f"**Generated:** {now.isoformat()}",
        f"**Patterns reviewed:** {len(patterns)}",
        f"",
        f"---",
        f"",
        f"## Active Behavioral Patterns",
        f"",
    ]

    # Group by pattern type
    foundational = []
    emergent = []
    corrective = []
    taught = []

    for pattern, review in zip(patterns, reviews):
        meta = pattern.get("metadata") or {}
        ptype = meta.get("pattern_type", "unknown")
        entry = {
            "content": pattern["original_content"][:300],
            "temp": float(pattern["temperature_score"]),
            "action": review["action"],
            "reason": review["reason"],
            "sacred_fire": meta.get("sacred_fire", False),
        }
        if ptype == "foundational" or entry["sacred_fire"]:
            foundational.append(entry)
        elif ptype == "emergent":
            emergent.append(entry)
        elif ptype == "corrective":
            corrective.append(entry)
        else:
            taught.append(entry)

    if foundational:
        digest_lines.append("### Sacred Fire (Foundational — Never Decay)")
        digest_lines.append("")
        for i, p in enumerate(foundational, 1):
            status = "REINFORCED" if p["action"] == "reinforce" else p["action"].upper()
            digest_lines.append(f"{i}. [{status}] {p['content'][:200]}...")
            digest_lines.append(f"   - Temperature: {p['temp']:.2f} | {p['reason']}")
            digest_lines.append("")

    if emergent:
        digest_lines.append("### Emergent Patterns (Arose Naturally)")
        digest_lines.append("")
        for i, p in enumerate(emergent, 1):
            status = "REINFORCED" if p["action"] == "reinforce" else p["action"].upper()
            digest_lines.append(f"{i}. [{status}] {p['content'][:200]}...")
            digest_lines.append(f"   - Temperature: {p['temp']:.2f} | {p['reason']}")
            digest_lines.append("")

    if corrective:
        digest_lines.append("### Corrective Patterns (Learned from Mistakes)")
        digest_lines.append("")
        for i, p in enumerate(corrective, 1):
            status = "REINFORCED" if p["action"] == "reinforce" else p["action"].upper()
            digest_lines.append(f"{i}. [{status}] {p['content'][:200]}...")
            digest_lines.append(f"   - Temperature: {p['temp']:.2f} | {p['reason']}")
            digest_lines.append("")

    if taught:
        digest_lines.append("### Taught Patterns (Explicitly Instructed)")
        digest_lines.append("")
        for i, p in enumerate(taught, 1):
            status = "REINFORCED" if p["action"] == "reinforce" else p["action"].upper()
            digest_lines.append(f"{i}. [{status}] {p['content'][:200]}...")
            digest_lines.append(f"   - Temperature: {p['temp']:.2f} | {p['reason']}")
            digest_lines.append("")

    # Failure processing summary (ERN dampening)
    if failure_results:
        dampened = [f for f in failure_results if f["status"] == "dampened"]
        new_types = [f for f in failure_results if f["status"] == "new_failure_type"]

        digest_lines.append("### Failure Processing (ERN Dampening)")
        digest_lines.append("")
        digest_lines.append(f"Failures reviewed: {len(failure_results)}")
        digest_lines.append(f"Known types (dampened): {len(dampened)}")
        digest_lines.append(f"New failure types: {len(new_types)}")
        digest_lines.append("")
        for f in dampened:
            digest_lines.append(f"- [DAMPENED] {f['title'][:100]} → matched pattern #{f['matched_pattern_id']}")
        for f in new_types:
            digest_lines.append(f"- [NEW] {f['title'][:100]} → corrective pattern auto-generated")
        digest_lines.append("")

    if new_corrective:
        digest_lines.append("### New Corrective Patterns (Auto-Generated — Needs Human Review)")
        digest_lines.append("")
        for nc in new_corrective:
            digest_lines.append(f"- Source: {nc['source'][:100]}")
            digest_lines.append(f"  Error: {nc['error'][:150]}")
        digest_lines.append("")

    # Flagged patterns (need human review)
    flagged = [r for r in reviews if r["action"] == "flag"]
    if flagged:
        digest_lines.append("### FLAGGED FOR HUMAN REVIEW")
        digest_lines.append("")
        for r in flagged:
            digest_lines.append(f"- Pattern ID {r['id']}: {r['reason']}")
        digest_lines.append("")

    digest_lines.append("---")
    digest_lines.append(f"*Generated by ritual_review.py ({mode} mode)*")
    digest_lines.append(f"*Neuroscience basis: Hobson et al. (2017) — Rituals decrease neural response to failure (PMC5452956)*")
    digest_lines.append(f"*Next review: see Cherokee ceremonial calendar*")

    return "\n".join(digest_lines)


def gather_recent_failures(conn, days=7):
    """Read recent failed Jr tasks and service incidents from work queue"""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT id, task_id, title, error_message, status, completed_at
            FROM jr_work_queue
            WHERE status IN ('failed', 'error')
              AND updated_at > NOW() - INTERVAL '%s days'
            ORDER BY updated_at DESC
        """, (days,))
        failed_tasks = cur.fetchall()

        # Also check for service-down episodic memories
        cur.execute("""
            SELECT id, original_content, created_at
            FROM thermal_memory_archive
            WHERE memory_type = 'episodic'
              AND created_at > NOW() - INTERVAL '%s days'
              AND (original_content ILIKE '%%ALERT%%'
                   OR original_content ILIKE '%%DOWN%%'
                   OR original_content ILIKE '%%ERROR%%'
                   OR original_content ILIKE '%%FAILED%%')
            ORDER BY created_at DESC
            LIMIT 20
        """, (days,))
        incidents = cur.fetchall()

        return failed_tasks, incidents


def process_failures(conn, failed_tasks, incidents, patterns):
    """
    PROCESS FAILURES — The ERN dampening step.

    Neuroscience basis: Hobson et al. (2017) showed rituals reduce the
    error-related negativity (ERN) from -4.87μV to -1.22μV. The ritual
    doesn't prevent errors — it changes how the system responds to them.

    For each failure:
      a. Has this failure TYPE been seen before? (match to corrective pattern)
      b. If yes: log that the pattern was activated (dampened response)
      c. If no: create a new corrective behavioral pattern (learn from it)
      d. Either way: the failure is PROCESSED, not just recorded
    """
    processed = []
    new_patterns = []

    # Extract existing corrective pattern keywords
    corrective_patterns = [
        p for p in patterns
        if (p.get("metadata") or {}).get("pattern_type") == "corrective"
    ]

    for task in failed_tasks:
        error = (task.get("error_message") or task.get("title") or "").lower()
        matched_pattern = None

        # Try to match against existing corrective patterns
        for cp in corrective_patterns:
            cp_content = cp["original_content"].lower()
            # Simple keyword overlap check
            cp_keywords = set(tag for tag in (cp.get("tags") or [])
                            if tag not in ("behavioral", "corrective"))
            error_words = set(error.split())
            if cp_keywords & error_words:
                matched_pattern = cp
                break

        if matched_pattern:
            processed.append({
                "task_id": task.get("task_id", "unknown"),
                "title": task.get("title", ""),
                "status": "dampened",
                "matched_pattern_id": matched_pattern["id"],
                "message": f"Known failure type — corrective pattern {matched_pattern['id']} applies"
            })
        else:
            processed.append({
                "task_id": task.get("task_id", "unknown"),
                "title": task.get("title", ""),
                "status": "new_failure_type",
                "matched_pattern_id": None,
                "message": "New failure type — candidate for new corrective pattern"
            })
            new_patterns.append({
                "source": task.get("title", ""),
                "error": (task.get("error_message") or "")[:500],
                "task_id": task.get("task_id", "")
            })

    # Create new corrective patterns for unmatched failures (if any)
    if new_patterns:
        with conn.cursor() as cur:
            for np in new_patterns[:3]:  # Limit to 3 new patterns per cycle
                content = (
                    f"BEHAVIORAL PATTERN — CORRECTIVE (auto-generated by ritual engine): "
                    f"Jr task '{np['source']}' failed with: {np['error'][:200]}. "
                    f"This failure type was not matched to any existing corrective pattern. "
                    f"Needs human review to determine root cause and proper corrective guidance."
                )
                cur.execute("""
                    INSERT INTO thermal_memory_archive
                        (original_content, temperature_score, tags, metadata,
                         source_node, memory_type, memory_hash, created_at)
                    VALUES (%s, 0.7, %s, %s, 'redfin', 'behavioral_pattern', %s, NOW())
                """, (
                    content,
                    ["behavioral", "corrective", "auto-generated", "needs-review"],
                    json.dumps({
                        "pattern_type": "corrective",
                        "first_observed": datetime.now().strftime("%Y-%m-%d"),
                        "observation_count": 1,
                        "auto_generated": True,
                        "source_task": np["task_id"],
                        "can_evolve": True,
                        "review_interval_days": 7
                    }),
                    hashlib.md5(
                        f"auto-corrective-{np['task_id']}-{datetime.now().isoformat()}".encode()
                    ).hexdigest()
                ))
        conn.commit()

    logger.info(f"PROCESS FAILURES: {len(failed_tasks)} tasks, {len(incidents)} incidents")
    logger.info(f"  Dampened (known type): {sum(1 for p in processed if p['status'] == 'dampened')}")
    logger.info(f"  New failure types: {sum(1 for p in processed if p['status'] == 'new_failure_type')}")
    logger.info(f"  New corrective patterns created: {min(len(new_patterns), 3)}")

    return processed, new_patterns


def run_ritual(mode="weekly"):
    """Main ritual cycle: GATHER → PROCESS FAILURES → REVIEW → REINFORCE → DIGEST → SEED"""
    logger.info(f"=== RITUAL REVIEW BEGIN ({mode} mode) ===")

    conn = get_db_connection()
    try:
        # GATHER
        logger.info("GATHER — Reading behavioral patterns")
        patterns = gather_patterns(conn)
        logger.info(f"Found {len(patterns)} behavioral patterns")

        if mode == "green-corn":
            sacred = gather_sacred(conn)
            logger.info(f"Green Corn: also reviewing {len(sacred)} sacred memories")

        # PROCESS FAILURES (ERN dampening — Hobson et al. 2017)
        days_lookback = {"weekly": 7, "monthly": 30, "seasonal": 90, "green-corn": 365}
        logger.info(f"PROCESS FAILURES — Reviewing last {days_lookback[mode]} days")
        failed_tasks, incidents = gather_recent_failures(conn, days_lookback[mode])
        failure_results, new_corrective = process_failures(conn, failed_tasks, incidents, patterns)

        # Re-gather patterns if new corrective ones were created
        if new_corrective:
            patterns = gather_patterns(conn)
            logger.info(f"Re-gathered patterns after creating {len(new_corrective)} new corrective patterns")

        # REVIEW
        logger.info("REVIEW — Evaluating each pattern")
        reviews = []
        for pattern in patterns:
            review = review_pattern(conn, pattern, mode)
            reviews.append(review)
            logger.info(f"  Pattern {review['id']}: {review['action']} — {review['reason']}")

        # REINFORCE
        logger.info("REINFORCE — Updating temperature scores")
        reinforced_count = reinforce_patterns(conn, reviews)

        # DIGEST
        logger.info("DIGEST — Generating cultural digest")
        digest_content = generate_digest(patterns, reviews, mode,
                                         failure_results=failure_results,
                                         new_corrective=new_corrective)

        # SEED — Write digest to file
        logger.info(f"SEED — Writing cultural digest to {DIGEST_OUTPUT}")
        os.makedirs(os.path.dirname(DIGEST_OUTPUT), exist_ok=True)
        with open(DIGEST_OUTPUT, "w") as f:
            f.write(digest_content)

        # Log ritual completion to thermal memory
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO thermal_memory_archive
                    (original_content, temperature_score, tags, metadata,
                     source_node, memory_type, memory_hash, created_at)
                VALUES (%s, %s, %s, %s, 'redfin', 'episodic', %s, NOW())
            """, (
                f"RITUAL REVIEW ({mode}): Reviewed {len(patterns)} behavioral patterns. "
                f"Reinforced {reinforced_count}. "
                f"Flagged {sum(1 for r in reviews if r['action'] == 'flag')}. "
                f"Digest written to {DIGEST_OUTPUT}.",
                0.7,
                ["ritual", "review", mode],
                json.dumps({
                    "mode": mode,
                    "patterns_reviewed": len(patterns),
                    "reinforced": reinforced_count,
                    "flagged": sum(1 for r in reviews if r["action"] == "flag"),
                    "timestamp": datetime.now().isoformat()
                }),
                hashlib.md5(
                    f"ritual-review-{mode}-{datetime.now().strftime('%Y%m%d%H%M')}".encode()
                ).hexdigest()
            ))
        conn.commit()

        # Summary
        actions = {}
        for r in reviews:
            actions[r["action"]] = actions.get(r["action"], 0) + 1

        logger.info(f"=== RITUAL REVIEW COMPLETE ===")
        logger.info(f"  Mode: {mode}")
        logger.info(f"  Patterns reviewed: {len(patterns)}")
        logger.info(f"  Actions: {actions}")
        logger.info(f"  Digest: {DIGEST_OUTPUT}")

        return {
            "mode": mode,
            "patterns_reviewed": len(patterns),
            "actions": actions,
            "digest_path": DIGEST_OUTPUT
        }

    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cherokee AI Federation Ritual Review")
    parser.add_argument("--mode", choices=["weekly", "monthly", "seasonal", "green-corn"],
                        default="weekly", help="Review mode")
    args = parser.parse_args()

    result = run_ritual(args.mode)
    print(json.dumps(result, indent=2))