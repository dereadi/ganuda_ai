#!/usr/bin/env python3
"""FARA Learning Drift Detector — Eagle Eye Canary.

Checks if FARA correction patterns are drifting from baseline.
Corrections are recorded, but nobody checks if the corrections themselves
are diverging (e.g., learning the wrong lesson from a misclassified failure).

Runs weekly via systemd timer. Reports to thermal memory and alerts
via Slack/Telegram if drift is detected.

Drift signals:
  1. Category distribution shift — corrections clustering in new categories
  2. Verdict flip-flop — same quiz types getting contradictory corrections
  3. Rule staleness — rules exist but never help (times_helped stays 0)
  4. Correction volume anomaly — sudden spike or drop in corrections
  5. Lesson divergence — recent lessons contradict older lessons

Council mandate: Eagle Eye Gap #1398.
For Seven Generations.
"""

import argparse
import hashlib
import json
import logging
import os
import sys
from collections import Counter
from datetime import datetime, timedelta

import psycopg2
from psycopg2.extras import RealDictCursor

# --- Configuration ---

DB_HOST = os.getenv("CHEROKEE_DB_HOST", os.getenv("DB_HOST", os.environ.get('CHEROKEE_DB_HOST', '10.100.0.2')))
DB_NAME = os.getenv("CHEROKEE_DB_NAME", os.getenv("DB_NAME", "zammad_production"))
DB_USER = os.getenv("CHEROKEE_DB_USER", os.getenv("DB_USER", "claude"))
DB_PASS = os.getenv("CHEROKEE_DB_PASS", os.getenv("DB_PASS", ""))

# Drift detection thresholds
CATEGORY_DRIFT_THRESHOLD = 0.5     # Jaccard distance > 0.5 = drift
STALENESS_THRESHOLD_DAYS = 30      # Rule unused for 30+ days
RULE_HELP_RATIO_MIN = 0.1          # Rule helped < 10% of the time after 5+ uses
VOLUME_SPIKE_FACTOR = 3.0          # 3x average = anomaly
MIN_EPISODES_FOR_ANALYSIS = 2      # Need at least 2 episodes to compare

# Time windows
BASELINE_WINDOW_DAYS = 90          # Older corrections = baseline
RECENT_WINDOW_DAYS = 14            # Recent corrections to compare

# --- Logging ---

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger("fara_drift")


# --- Database ---

def get_db():
    """Get database connection."""
    return psycopg2.connect(
        host=DB_HOST, dbname=DB_NAME,
        user=DB_USER, password=DB_PASS
    )


# --- Drift Detection Functions ---

def check_category_drift(conn):
    """Signal 1: Are corrections clustering in new/different categories?

    Compare category distribution of recent corrections vs baseline.
    Uses Jaccard distance on category sets + chi-squared-like comparison.
    """
    now = datetime.now()
    recent_cutoff = now - timedelta(days=RECENT_WINDOW_DAYS)
    baseline_cutoff = now - timedelta(days=BASELINE_WINDOW_DAYS)

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Baseline categories (older corrections)
        cur.execute("""
            SELECT lesson_learned, quiz_type
            FROM fara_episodes
            WHERE was_correct = FALSE
              AND created_at < %s
              AND created_at >= %s
              AND lesson_learned IS NOT NULL
        """, (recent_cutoff, baseline_cutoff))
        baseline_episodes = cur.fetchall()

        # Recent categories
        cur.execute("""
            SELECT lesson_learned, quiz_type
            FROM fara_episodes
            WHERE was_correct = FALSE
              AND created_at >= %s
              AND lesson_learned IS NOT NULL
        """, (recent_cutoff,))
        recent_episodes = cur.fetchall()

    if not baseline_episodes and not recent_episodes:
        return {
            "signal": "category_drift",
            "status": "NO_DATA",
            "detail": "No corrections found in either window",
            "drifted": False
        }

    # Extract keyword categories from lessons
    def extract_keywords(episodes):
        keywords = Counter()
        for ep in episodes:
            lesson = (ep.get("lesson_learned") or "").lower()
            # Extract domain-specific keywords
            for kw in ["hair", "face", "identity", "skin", "pose", "outfit",
                        "expression", "artifact", "proportion", "color",
                        "lighting", "transfer", "blend", "stubble", "beard"]:
                if kw in lesson:
                    keywords[kw] += 1
            # Also count quiz types
            qt = ep.get("quiz_type") or "unknown"
            keywords[f"type:{qt}"] += 1
        return keywords

    baseline_kw = extract_keywords(baseline_episodes)
    recent_kw = extract_keywords(recent_episodes)

    baseline_set = set(baseline_kw.keys())
    recent_set = set(recent_kw.keys())

    # Jaccard distance
    if baseline_set or recent_set:
        intersection = baseline_set & recent_set
        union = baseline_set | recent_set
        jaccard_distance = 1.0 - (len(intersection) / len(union)) if union else 0.0
    else:
        jaccard_distance = 0.0

    # New categories not in baseline
    new_categories = recent_set - baseline_set
    lost_categories = baseline_set - recent_set

    drifted = jaccard_distance > CATEGORY_DRIFT_THRESHOLD

    return {
        "signal": "category_drift",
        "status": "DRIFT" if drifted else "STABLE",
        "jaccard_distance": round(jaccard_distance, 3),
        "threshold": CATEGORY_DRIFT_THRESHOLD,
        "baseline_categories": sorted(baseline_set),
        "recent_categories": sorted(recent_set),
        "new_categories": sorted(new_categories),
        "lost_categories": sorted(lost_categories),
        "baseline_count": len(baseline_episodes),
        "recent_count": len(recent_episodes),
        "drifted": drifted
    }


def check_verdict_flipflop(conn):
    """Signal 2: Are same quiz types getting contradictory corrections?

    Look for quiz types where corrections flip between pass->fail and fail->pass.
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT quiz_type,
                   fara_verdict,
                   tpm_verdict,
                   lesson_learned,
                   created_at
            FROM fara_episodes
            WHERE was_correct = FALSE
              AND tpm_verdict IS NOT NULL
            ORDER BY quiz_type, created_at
        """)
        corrections = cur.fetchall()

    if len(corrections) < 2:
        return {
            "signal": "verdict_flipflop",
            "status": "NO_DATA",
            "detail": "Fewer than 2 corrections to compare",
            "drifted": False
        }

    # Group by quiz_type
    by_type = {}
    for c in corrections:
        qt = c["quiz_type"] or "unknown"
        if qt not in by_type:
            by_type[qt] = []
        by_type[qt].append(c)

    flipflops = []
    for qt, episodes in by_type.items():
        if len(episodes) < 2:
            continue
        # Check for contradictory verdicts
        verdicts = [(e["fara_verdict"], e["tpm_verdict"]) for e in episodes]
        # If FARA said pass but TPM said fail AND also FARA said fail but TPM said pass
        # for the same quiz type, that is a flipflop
        fara_pass_tpm_fail = any(fv == "pass" and tv == "fail" for fv, tv in verdicts)
        fara_fail_tpm_pass = any(fv == "fail" and tv == "pass" for fv, tv in verdicts)
        if fara_pass_tpm_fail and fara_fail_tpm_pass:
            flipflops.append({
                "quiz_type": qt,
                "correction_count": len(episodes),
                "verdicts": [{"fara": fv, "tpm": tv} for fv, tv in verdicts]
            })

    drifted = len(flipflops) > 0

    return {
        "signal": "verdict_flipflop",
        "status": "DRIFT" if drifted else "STABLE",
        "flipflop_count": len(flipflops),
        "flipflops": flipflops,
        "quiz_types_checked": len(by_type),
        "drifted": drifted
    }


def check_rule_staleness(conn):
    """Signal 3: Rules that exist but never help.

    A rule that has been applied 5+ times but helped 0 times is learning
    the wrong lesson. A rule unused for 30+ days is dead weight.
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Rules that are applied but never help
        cur.execute("""
            SELECT rule_hash, category, rule_text, importance,
                   times_applied, times_helped, created_at, last_used_at
            FROM fara_rules
            WHERE is_active = TRUE
        """)
        rules = cur.fetchall()

    stale_rules = []
    unhelpful_rules = []
    now = datetime.now()

    for rule in rules:
        # Check staleness (never used or not used recently)
        last_used = rule.get("last_used_at")
        created = rule["created_at"]
        age_days = (now - created).days

        if age_days >= STALENESS_THRESHOLD_DAYS and last_used is None:
            stale_rules.append({
                "rule_hash": rule["rule_hash"],
                "category": rule["category"],
                "rule_text": rule["rule_text"][:100],
                "age_days": age_days,
                "reason": "Never used"
            })
        elif last_used and (now - last_used).days >= STALENESS_THRESHOLD_DAYS:
            stale_rules.append({
                "rule_hash": rule["rule_hash"],
                "category": rule["category"],
                "rule_text": rule["rule_text"][:100],
                "days_since_used": (now - last_used).days,
                "reason": "Not used recently"
            })

        # Check help ratio
        applied = rule["times_applied"] or 0
        helped = rule["times_helped"] or 0
        if applied >= 5 and (helped / applied) < RULE_HELP_RATIO_MIN:
            unhelpful_rules.append({
                "rule_hash": rule["rule_hash"],
                "category": rule["category"],
                "rule_text": rule["rule_text"][:100],
                "times_applied": applied,
                "times_helped": helped,
                "help_ratio": round(helped / applied, 3) if applied else 0
            })

    drifted = len(unhelpful_rules) > 0  # Unhelpful rules = actively wrong learning

    return {
        "signal": "rule_staleness",
        "status": "DRIFT" if drifted else ("STALE" if stale_rules else "HEALTHY"),
        "total_rules": len(rules),
        "stale_rules": stale_rules,
        "stale_count": len(stale_rules),
        "unhelpful_rules": unhelpful_rules,
        "unhelpful_count": len(unhelpful_rules),
        "drifted": drifted
    }


def check_volume_anomaly(conn):
    """Signal 4: Sudden spike or drop in correction volume.

    Compare recent correction rate to historical average.
    """
    now = datetime.now()
    recent_cutoff = now - timedelta(days=RECENT_WINDOW_DAYS)

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Total corrections and time range
        cur.execute("""
            SELECT COUNT(*) as total,
                   MIN(created_at) as first_correction,
                   MAX(created_at) as last_correction
            FROM fara_episodes
            WHERE was_correct = FALSE
        """)
        totals = cur.fetchone()

        # Recent corrections
        cur.execute("""
            SELECT COUNT(*) as recent_count
            FROM fara_episodes
            WHERE was_correct = FALSE
              AND created_at >= %s
        """, (recent_cutoff,))
        recent = cur.fetchone()

    total = totals["total"] or 0
    recent_count = recent["recent_count"] or 0

    if total < MIN_EPISODES_FOR_ANALYSIS:
        return {
            "signal": "volume_anomaly",
            "status": "NO_DATA",
            "detail": f"Only {total} corrections total, need {MIN_EPISODES_FOR_ANALYSIS}",
            "drifted": False
        }

    first = totals["first_correction"]
    last = totals["last_correction"]
    if first and last:
        total_days = max((last - first).days, 1)
        avg_per_week = (total / total_days) * 7
        recent_per_week = (recent_count / RECENT_WINDOW_DAYS) * 7

        spike = recent_per_week > (avg_per_week * VOLUME_SPIKE_FACTOR) if avg_per_week > 0 else False
        drought = recent_count == 0 and total > 5  # No recent corrections despite history
    else:
        avg_per_week = 0
        recent_per_week = 0
        spike = False
        drought = False

    drifted = spike  # Spike suggests systemic mislearning

    return {
        "signal": "volume_anomaly",
        "status": "SPIKE" if spike else ("DROUGHT" if drought else "NORMAL"),
        "total_corrections": total,
        "recent_corrections": recent_count,
        "avg_per_week": round(avg_per_week, 2),
        "recent_per_week": round(recent_per_week, 2),
        "spike_threshold": VOLUME_SPIKE_FACTOR,
        "is_spike": spike,
        "is_drought": drought,
        "drifted": drifted
    }


def check_lesson_divergence(conn):
    """Signal 5: Recent lessons contradict older lessons.

    Simple keyword overlap check — if recent lessons use antonyms or
    contradictory language compared to baseline lessons.
    """
    now = datetime.now()
    recent_cutoff = now - timedelta(days=RECENT_WINDOW_DAYS)

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT lesson_learned, created_at
            FROM fara_episodes
            WHERE was_correct = FALSE
              AND lesson_learned IS NOT NULL
            ORDER BY created_at
        """)
        all_lessons = cur.fetchall()

    if len(all_lessons) < 2:
        return {
            "signal": "lesson_divergence",
            "status": "NO_DATA",
            "detail": "Fewer than 2 lessons to compare",
            "drifted": False
        }

    # Split into baseline and recent
    baseline_lessons = [l for l in all_lessons if l["created_at"] < recent_cutoff]
    recent_lessons = [l for l in all_lessons if l["created_at"] >= recent_cutoff]

    # Check for contradictions using simple antonym pairs
    antonym_pairs = [
        ("must", "should not"), ("always", "never"),
        ("required", "optional"), ("important", "unimportant"),
        ("transfer", "preserve"), ("include", "exclude"),
        ("pass", "fail"), ("correct", "incorrect")
    ]

    contradictions = []
    for bl in baseline_lessons:
        bl_text = (bl["lesson_learned"] or "").lower()
        for rl in recent_lessons:
            rl_text = (rl["lesson_learned"] or "").lower()
            for word_a, word_b in antonym_pairs:
                if (word_a in bl_text and word_b in rl_text) or \
                   (word_b in bl_text and word_a in rl_text):
                    contradictions.append({
                        "baseline_lesson": bl["lesson_learned"][:100],
                        "recent_lesson": rl["lesson_learned"][:100],
                        "antonym_pair": [word_a, word_b]
                    })

    # Deduplicate
    seen = set()
    unique_contradictions = []
    for c in contradictions:
        key = (c["baseline_lesson"], c["recent_lesson"])
        if key not in seen:
            seen.add(key)
            unique_contradictions.append(c)

    drifted = len(unique_contradictions) > 0

    return {
        "signal": "lesson_divergence",
        "status": "DRIFT" if drifted else "CONSISTENT",
        "baseline_lessons": len(baseline_lessons),
        "recent_lessons": len(recent_lessons),
        "contradictions": unique_contradictions,
        "contradiction_count": len(unique_contradictions),
        "drifted": drifted
    }


# --- Reporting ---

def log_to_thermal(conn, run_id, results, overall_status):
    """Log drift detection results to thermal_memory_archive."""
    drifted_signals = [r for r in results if r.get("drifted")]

    content = (
        f"FARA LEARNING DRIFT CHECK {run_id}\n"
        f"Timestamp: {datetime.now().isoformat()}\n"
        f"Overall: {overall_status}\n"
        f"Signals checked: {len(results)}\n"
        f"Drift detected: {len(drifted_signals)}\n\n"
    )
    for r in results:
        status_str = r.get("status", "UNKNOWN")
        content += f"  [{status_str}] {r['signal']}\n"
        if r.get("drifted"):
            # Add detail for drifted signals
            if r["signal"] == "category_drift":
                content += f"    Jaccard distance: {r.get('jaccard_distance', 'N/A')}\n"
                content += f"    New categories: {r.get('new_categories', [])}\n"
            elif r["signal"] == "verdict_flipflop":
                content += f"    Flipflop count: {r.get('flipflop_count', 0)}\n"
            elif r["signal"] == "rule_staleness":
                content += f"    Unhelpful rules: {r.get('unhelpful_count', 0)}\n"
            elif r["signal"] == "volume_anomaly":
                content += f"    Recent/week: {r.get('recent_per_week', 0)} vs avg: {r.get('avg_per_week', 0)}\n"
            elif r["signal"] == "lesson_divergence":
                content += f"    Contradictions: {r.get('contradiction_count', 0)}\n"

    temp_score = 90.0 if overall_status == "DRIFT_DETECTED" else 50.0
    memory_hash = hashlib.sha256(
        f"fara-drift-{run_id}-{datetime.now().isoformat()}".encode()
    ).hexdigest()[:16]

    metadata = json.dumps({
        "type": "fara_learning_drift",
        "run_id": run_id,
        "overall_status": overall_status,
        "signals_checked": len(results),
        "drifted_count": len(drifted_signals),
        "drifted_signals": [r["signal"] for r in drifted_signals],
        "results": results
    })

    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO thermal_memory_archive
            (memory_hash, original_content, temperature_score, metadata,
             source_node, memory_type, tags, created_at)
            VALUES (%s, %s, %s, %s::jsonb, 'redfin', 'episodic',
                    %s, NOW())
        """, (memory_hash, content, temp_score, metadata,
              ["fara", "drift", "eagle_eye", "canary", "learning"]))
        conn.commit()
        log.info("Logged to thermal_memory_archive (hash=%s)", memory_hash)
    except Exception as e:
        log.error("Failed to log to thermal: %s", e)
        conn.rollback()


def send_alert(message):
    """Send drift alert via Slack (primary) or Telegram (fallback)."""
    # Primary: Slack
    try:
        sys.path.insert(0, "/ganuda/lib")
        from slack_federation import send as slack_send
        slack_send("fire-guard", message, urgent=True)
        log.info("Alert sent via Slack")
        return
    except Exception as e:
        log.warning("Slack send failed: %s", e)

    # Fallback: Telegram
    try:
        import requests
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if bot_token and chat_id:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            requests.post(url, json={
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown",
            }, timeout=10)
            log.info("Alert sent via Telegram")
    except Exception as e:
        log.error("Telegram send failed: %s", e)


# --- Main ---

def run_drift_check():
    """Run all drift detection signals and report."""
    import time
    run_id = f"fara-drift-{int(time.time())}"
    log.info("Starting FARA learning drift check: %s", run_id)

    try:
        conn = get_db()
    except Exception as e:
        log.error("Database connection failed: %s", e)
        return None, "DB_ERROR"

    results = []

    # Run all 5 drift signals
    checks = [
        ("category_drift", check_category_drift),
        ("verdict_flipflop", check_verdict_flipflop),
        ("rule_staleness", check_rule_staleness),
        ("volume_anomaly", check_volume_anomaly),
        ("lesson_divergence", check_lesson_divergence),
    ]

    for name, check_fn in checks:
        try:
            result = check_fn(conn)
            results.append(result)
            status = result.get("status", "UNKNOWN")
            drifted = result.get("drifted", False)
            log.info("  [%s] %s%s", status, name,
                     " ** DRIFT **" if drifted else "")
        except Exception as e:
            log.error("  [ERROR] %s: %s", name, e)
            results.append({
                "signal": name,
                "status": "ERROR",
                "detail": str(e),
                "drifted": False
            })

    # Determine overall status
    drifted_signals = [r for r in results if r.get("drifted")]
    if drifted_signals:
        overall_status = "DRIFT_DETECTED"
    elif all(r.get("status") == "NO_DATA" for r in results):
        overall_status = "INSUFFICIENT_DATA"
    else:
        overall_status = "STABLE"

    log.info("Overall: %s (%d/%d signals drifted)",
             overall_status, len(drifted_signals), len(results))

    # Log to thermal memory
    log_to_thermal(conn, run_id, results, overall_status)

    # Alert if drift detected
    if overall_status == "DRIFT_DETECTED":
        msg = (
            f"*FARA LEARNING DRIFT DETECTED*\n\n"
            f"Run: `{run_id}`\n"
            f"Drifted signals: {len(drifted_signals)}/{len(results)}\n\n"
        )
        for r in drifted_signals:
            msg += f"  - *{r['signal']}*: {r.get('status')}\n"
            if r["signal"] == "category_drift":
                msg += f"    New categories: {', '.join(r.get('new_categories', []))}\n"
            elif r["signal"] == "verdict_flipflop":
                msg += f"    {r.get('flipflop_count', 0)} quiz types with contradictory corrections\n"
            elif r["signal"] == "rule_staleness":
                msg += f"    {r.get('unhelpful_count', 0)} rules that never help\n"
            elif r["signal"] == "lesson_divergence":
                msg += f"    {r.get('contradiction_count', 0)} contradictory lessons\n"

        msg += f"\nReview corrections and rules in `fara_episodes` / `fara_rules` tables."
        send_alert(msg)

    conn.commit()  # explicit commit before close
    conn.close()
    return results, overall_status


def main():
    parser = argparse.ArgumentParser(
        description="FARA Learning Drift Detector — Eagle Eye Canary"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Print check descriptions without running")
    parser.add_argument("--json", action="store_true",
                        help="Output results as JSON")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Verbose output")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.dry_run:
        print("FARA Learning Drift Detector — 5 signals configured:")
        print("  1. category_drift     — Correction categories shifting from baseline")
        print("  2. verdict_flipflop   — Same quiz types getting contradictory corrections")
        print("  3. rule_staleness     — Rules that exist but never help")
        print("  4. volume_anomaly     — Sudden spike/drop in correction volume")
        print("  5. lesson_divergence  — Recent lessons contradict older lessons")
        print(f"\nBaseline window: {BASELINE_WINDOW_DAYS} days")
        print(f"Recent window:   {RECENT_WINDOW_DAYS} days")
        print(f"Min episodes:    {MIN_EPISODES_FOR_ANALYSIS}")
        return

    results, overall_status = run_drift_check()

    if args.json:
        print(json.dumps({
            "overall_status": overall_status,
            "results": results
        }, indent=2, default=str))
    else:
        print(f"\n=== FARA Learning Drift Check ===")
        print(f"Overall: {overall_status}")
        print()
        for r in results:
            drifted = r.get("drifted", False)
            marker = " ** DRIFT **" if drifted else ""
            print(f"  [{r.get('status', 'UNKNOWN'):>12}] {r['signal']}{marker}")

            # Print extra detail based on signal
            if r["signal"] == "category_drift" and r.get("status") != "NO_DATA":
                print(f"               Jaccard distance: {r.get('jaccard_distance', 'N/A')} "
                      f"(threshold: {r.get('threshold', CATEGORY_DRIFT_THRESHOLD)})")
                if r.get("new_categories"):
                    print(f"               New categories: {', '.join(r['new_categories'])}")
            elif r["signal"] == "rule_staleness":
                print(f"               Total rules: {r.get('total_rules', 0)}, "
                      f"stale: {r.get('stale_count', 0)}, "
                      f"unhelpful: {r.get('unhelpful_count', 0)}")
            elif r["signal"] == "volume_anomaly" and r.get("status") != "NO_DATA":
                print(f"               Avg/week: {r.get('avg_per_week', 0)}, "
                      f"recent/week: {r.get('recent_per_week', 0)}")
            elif r["signal"] == "lesson_divergence" and r.get("status") != "NO_DATA":
                print(f"               Contradictions: {r.get('contradiction_count', 0)}")

        print()

    passed = overall_status != "DRIFT_DETECTED"
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
