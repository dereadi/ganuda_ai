#!/usr/bin/env python3
"""Fire Guard periodic backlog review — LMC-16 Step 3.

Walks duyuktv_tickets backlog every 24h (configurable to 72h), classifies each
entry via lib.fire_guard_backlog_reviewer, posts a ONE Slack summary to
#fire-guard for Partner ratification. Manual-only-close discipline (Eagle Eye +
Coyote convergence): NO auto-close, only surface.

Authorizing Council vote: 08c642a0fd176a92 (DELIBERATE phase, Diversity 0.358 HEALTHY).
ADAPT plan: /ganuda/docs/lm_workflow_proceduralization_adapt_plan.md

Usage:
  fire_guard_backlog_review.py [--limit N] [--dry-run] [--no-slack]

Cron-schedule via systemd-user-timer (per same pattern as federation-pg-backup.timer).
"""
import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import List

import psycopg2
import psycopg2.extras

# Path setup
sys.path.insert(0, os.environ.get("GANUDA_ROOT", "/ganuda"))

from lib.fire_guard_backlog_reviewer import (  # noqa: E402
    classify_ticket,
    is_classifier_healthy,
    _get_conn,
    COUNCIL_AUDIT_HASH,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("fire_guard_backlog_review")


# ---------------------------------------------------------------------------
# Backlog selection (read-only on duyuktv_tickets per Spider mitigation)
# ---------------------------------------------------------------------------

def fetch_backlog_candidates(limit: int = 50) -> List[dict]:
    """Fetch oldest backlog tickets that have NOT been classified in past 24h."""
    with _get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT t.id, t.title, t.description, t.priority,
                       EXTRACT(DAY FROM (NOW() - t.updated_at))::int AS days_stale
                FROM duyuktv_tickets t
                WHERE t.status = 'backlog'
                  AND NOT EXISTS (
                    SELECT 1 FROM classification_audit_log cal
                     WHERE cal.ticket_id = t.id
                       AND cal.classified_at > NOW() - INTERVAL '24 hours'
                  )
                ORDER BY t.updated_at ASC
                LIMIT %s
            """, (limit,))
            return list(cur.fetchall())


# ---------------------------------------------------------------------------
# Slack posting (best-effort; failure does not abort the classification run)
# ---------------------------------------------------------------------------

def format_slack_summary(classifications: List[dict]) -> str:
    """One Slack message with table of classifications awaiting Partner ratification."""
    if not classifications:
        return ":herb: Fire Guard backlog review — no new candidates this cycle."

    by_class: dict = {}
    for c in classifications:
        by_class.setdefault(c["classification"], []).append(c)

    lines = [
        f":file_folder: *Fire Guard backlog review* — {len(classifications)} classified",
        f"_Council audit_ `{COUNCIL_AUDIT_HASH}` _(LMC-16)_",
        "",
    ]

    class_emoji = {
        "still_relevant": ":seedling:",
        "needs_decomposition": ":scissors:",
        "close_as_stale": ":wastebasket:",
    }
    for klass in ("close_as_stale", "needs_decomposition", "still_relevant"):
        items = by_class.get(klass, [])
        if not items:
            continue
        lines.append(f"{class_emoji.get(klass, '')} *{klass}* ({len(items)}):")
        for it in items[:10]:  # cap per-class display
            lines.append(f"  • #{it['ticket_id']} ({it['days_stale']}d) — _{it.get('rationale','')[:120]}_")
        if len(items) > 10:
            lines.append(f"  _...and {len(items) - 10} more_")
        lines.append("")

    lines.append("_Reply with: `keep #N`, `close #N`, `decompose #N`, or `reject #N` to ratify._")
    return "\n".join(lines)


def post_to_slack(message: str) -> bool:
    """Best-effort Slack post. Failure is logged, not raised."""
    webhook = os.environ.get("FIRE_GUARD_SLACK_WEBHOOK")
    if not webhook:
        log.warning("FIRE_GUARD_SLACK_WEBHOOK not set; skipping Slack post")
        log.info("Would have posted:\n%s", message)
        return False
    try:
        import requests
        r = requests.post(webhook, json={"text": message}, timeout=10)
        r.raise_for_status()
        log.info("Slack post ok")
        return True
    except Exception as e:
        log.error(f"Slack post failed (best-effort): {e}")
        return False


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def run(limit: int = 50, dry_run: bool = False, post_slack: bool = True) -> dict:
    """Execute one backlog review cycle.

    Returns a summary dict suitable for downstream logging / Dawn Mist.
    """
    log.info("Fire Guard backlog review starting (limit=%d, dry_run=%s)", limit, dry_run)

    # Eagle Eye health gate: halt classifier if rejection-rate exceeds threshold
    health = is_classifier_healthy()
    if not health["healthy"]:
        log.error(
            "Classifier unhealthy: rejection_rate=%.3f >= threshold=%.3f over %d days. HALTING.",
            health["rate"], health["threshold"], health["window_days"]
        )
        if post_slack:
            post_to_slack(
                f":rotating_light: Fire Guard backlog reviewer HALTED. "
                f"Rejection rate {health['rate']:.1%} exceeds threshold {health['threshold']:.0%} "
                f"over {health['window_days']}-day window. Partner intervention required."
            )
        return {"halted": True, "health": health}

    candidates = fetch_backlog_candidates(limit)
    log.info("Fetched %d candidates", len(candidates))

    classifications = []
    for c in candidates:
        try:
            result = classify_ticket(
                ticket_id=c["id"],
                title=c["title"],
                description=c["description"] or "",
                days_stale=c["days_stale"],
                dry_run=dry_run,
            )
            classifications.append({
                "ticket_id": c["id"],
                "days_stale": c["days_stale"],
                **result,
            })
        except Exception as e:
            log.error("Classification failed for ticket #%d: %s", c["id"], e)

    log.info("Classified %d/%d tickets", len(classifications), len(candidates))

    if post_slack:
        post_to_slack(format_slack_summary(classifications))

    return {
        "halted": False,
        "fetched": len(candidates),
        "classified": len(classifications),
        "by_class": {
            k: sum(1 for c in classifications if c.get("classification") == k)
            for k in ("still_relevant", "needs_decomposition", "close_as_stale")
        },
        "dry_run": dry_run,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def main():
    parser = argparse.ArgumentParser(description="Fire Guard backlog review (LMC-16)")
    parser.add_argument("--limit", type=int, default=50, help="Max tickets per cycle")
    parser.add_argument("--dry-run", action="store_true", help="Classify without persisting")
    parser.add_argument("--no-slack", action="store_true", help="Suppress Slack post (logs instead)")
    args = parser.parse_args()

    summary = run(limit=args.limit, dry_run=args.dry_run, post_slack=not args.no_slack)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
