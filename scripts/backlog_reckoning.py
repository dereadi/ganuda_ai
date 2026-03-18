#!/usr/bin/env python3
"""
backlog_reckoning.py — Weekly Kanban Staleness Scoring

"The owl counts what the eagle forgot."

Scores kanban backlog items for staleness across six dimensions and produces
an advisory report. Does NOT auto-close anything — recommends only.

Council Vote: #2aaaa11e1715c307 (0.871 confidence, APPROVED WITH CONDITIONS)
Design Doc: /ganuda/docs/design/DC-BACKLOG-RECKONING-MAR10-2026.md

Usage:
    python3 backlog_reckoning.py              # text report to stdout
    python3 backlog_reckoning.py --json       # JSON to stdout
    python3 backlog_reckoning.py --slack      # post to Slack #saturday-morning
    python3 backlog_reckoning.py --dry-run    # score but don't post or write overrides
"""

import sys
sys.path.insert(0, '/ganuda')
sys.path.insert(0, '/ganuda/lib')

import argparse
import json
import logging
import os
import tempfile
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

import psycopg2
import psycopg2.extras

# ---------------------------------------------------------------------------
# Slack integration (graceful degradation)
# ---------------------------------------------------------------------------
try:
    from slack_federation import send as slack_send
    SLACK_AVAILABLE = True
except ImportError:
    SLACK_AVAILABLE = False

# ---------------------------------------------------------------------------
# Thermal memory integration (graceful degradation)
# ---------------------------------------------------------------------------
try:
    from ganuda_db import safe_thermal_write
    THERMAL_AVAILABLE = True
except ImportError:
    THERMAL_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
logger = logging.getLogger("backlog_reckoning")

TZ = ZoneInfo("America/Chicago")

# ===================================================================
# CONFIGURABLE CONSTANTS — Council Condition #2 (BINDING)
# All scoring thresholds defined here, not buried in logic.
# ===================================================================

# Age score thresholds (days)
AGE_TIER_1 = 30    # 0.0 below this
AGE_TIER_2 = 60    # 0.3
AGE_TIER_3 = 90    # 0.6
AGE_SCORE_T1 = 0.0
AGE_SCORE_T2 = 0.3
AGE_SCORE_T3 = 0.6
AGE_SCORE_T4 = 0.9

# Inactivity score thresholds (days since last update)
INACTIVITY_TIER_1 = 14
INACTIVITY_TIER_2 = 30
INACTIVITY_TIER_3 = 60
INACTIVITY_SCORE_T1 = 0.0
INACTIVITY_SCORE_T2 = 0.3
INACTIVITY_SCORE_T3 = 0.6
INACTIVITY_SCORE_T4 = 0.9

# DC drift thresholds (count of new DCs since ticket creation)
DC_DRIFT_TIER_1 = 1
DC_DRIFT_TIER_2 = 3
DC_DRIFT_TIER_3 = 5
DC_DRIFT_SCORE_T1 = 0.0
DC_DRIFT_SCORE_T2 = 0.3
DC_DRIFT_SCORE_T3 = 0.6
DC_DRIFT_SCORE_T4 = 0.9

# EPIC decomposition
EPIC_STALE_DAYS = 30
EPIC_STALE_SCORE = 0.9
EPIC_ACTIVE_SCORE = 0.3
NON_EPIC_SCORE = 0.0

# Deprecated tech keywords
DEPRECATED_TECH = [
    'ChromaDB', 'DeepSeek-R1-Distill', 'telegram_bot_daemon',
    'cherokee-council-gateway', 'sag-unified', 'vllm-redfin',
]

# Market freshness keywords
MARKET_KEYWORDS = [
    'LinkedIn', 'partnership', 'pricing', 'customer', 'onboarding', 'sales',
]
MARKET_FRESH_DAYS = 30
MARKET_NO_SIGNAL_SCORE = 0.6

# Composite weights
WEIGHT_AGE = 0.20
WEIGHT_INACTIVITY = 0.25
WEIGHT_DC_DRIFT = 0.20
WEIGHT_DECOMPOSITION = 0.10
WEIGHT_TECH_SUPERSESSION = 0.15
WEIGHT_MARKET_FRESHNESS = 0.10

# Classification thresholds
STALE_THRESHOLD = 0.7
REVIEW_THRESHOLD = 0.4

# Output caps
MAX_STALE = 7
MAX_REVIEW = 5

# Override tracking
OVERRIDES_PATH = '/ganuda/config/backlog_reckoning_overrides.json'
OVERRIDE_RATE_LIMIT = 0.30   # Council Condition #1
KILL_SWITCH_RUNS = 4         # Council Condition #3

# Jr work queue staleness thresholds (for the secondary query)
JR_IN_PROGRESS_STALE_DAYS = 3
JR_PENDING_STALE_DAYS = 5


# ===================================================================
# Database Connection
# ===================================================================

def get_connection():
    """Get DB connection via ganuda_db or manual fallback."""
    try:
        from ganuda_db import get_db_config
        config = get_db_config()
        return psycopg2.connect(**config)
    except Exception as e:
        logger.warning("ganuda_db unavailable (%s), using manual config", e)
        password = os.environ.get('CHEROKEE_DB_PASS')
        if not password:
            # Try secrets.env
            secrets_path = '/ganuda/config/secrets.env'
            if os.path.exists(secrets_path):
                with open(secrets_path) as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('CHEROKEE_DB_PASS='):
                            password = line.split('=', 1)[1].strip().strip('"').strip("'")
                            break
        if not password:
            raise RuntimeError(
                "CHEROKEE_DB_PASS not set and ganuda_db unavailable. "
                "Set the env var or check /ganuda/config/secrets.env."
            )
        return psycopg2.connect(
            host='192.168.132.222',
            port=5432,
            dbname='zammad_production',
            user='claude',
            password=password,
        )


# ===================================================================
# Override / Kill Switch
# ===================================================================

def load_overrides() -> dict:
    """Load override tracking JSON."""
    if os.path.exists(OVERRIDES_PATH):
        try:
            with open(OVERRIDES_PATH) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning("Failed to load overrides: %s", e)
    return {"runs": []}


def save_overrides(data: dict) -> None:
    """Atomic write of override tracking JSON."""
    os.makedirs(os.path.dirname(OVERRIDES_PATH), exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        dir=os.path.dirname(OVERRIDES_PATH), suffix='.tmp'
    )
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_path, OVERRIDES_PATH)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def check_kill_switch(overrides: dict) -> bool:
    """Council Condition #3: check if kill switch is engaged.

    After 4 runs, if override rate >30% OR no tickets closed,
    stop recommending closures until recalibrated.
    """
    runs = overrides.get("runs", [])
    if len(runs) < KILL_SWITCH_RUNS:
        return False

    recent = runs[-KILL_SWITCH_RUNS:]

    # Check override rate
    total_flagged = sum(len(r.get("flagged", [])) for r in recent)
    total_kept = sum(len(r.get("kept", [])) for r in recent)
    if total_flagged > 0:
        override_rate = total_kept / total_flagged
        if override_rate > OVERRIDE_RATE_LIMIT:
            logger.warning(
                "COYOTE REVIEW REQUIRED: override rate %.1f%% > %.1f%% threshold over last %d runs",
                override_rate * 100, OVERRIDE_RATE_LIMIT * 100, KILL_SWITCH_RUNS,
            )
            return True

    # Check if any tickets were closed
    total_closed = sum(len(r.get("closed", [])) for r in recent)
    if total_closed == 0:
        logger.warning(
            "COYOTE REVIEW REQUIRED: no tickets closed in last %d runs",
            KILL_SWITCH_RUNS,
        )
        return True

    return False


# ===================================================================
# Scoring Functions
# ===================================================================

def score_age(created_at: datetime) -> float:
    """Score based on ticket age."""
    if created_at is None:
        return AGE_SCORE_T4
    age_days = (datetime.now() - created_at).days
    if age_days < AGE_TIER_1:
        return AGE_SCORE_T1
    elif age_days < AGE_TIER_2:
        return AGE_SCORE_T2
    elif age_days < AGE_TIER_3:
        return AGE_SCORE_T3
    return AGE_SCORE_T4


def score_inactivity(updated_at: datetime) -> float:
    """Score based on time since last update."""
    if updated_at is None:
        return INACTIVITY_SCORE_T4
    days_inactive = (datetime.now() - updated_at).days
    if days_inactive < INACTIVITY_TIER_1:
        return INACTIVITY_SCORE_T1
    elif days_inactive < INACTIVITY_TIER_2:
        return INACTIVITY_SCORE_T2
    elif days_inactive < INACTIVITY_TIER_3:
        return INACTIVITY_SCORE_T3
    return INACTIVITY_SCORE_T4


def score_dc_drift(cur, created_at: datetime) -> Tuple[float, int]:
    """Score based on number of DCs ratified since ticket creation.

    Returns (score, dc_count).
    """
    if created_at is None:
        return DC_DRIFT_SCORE_T1, 0

    cur.execute("""
        SELECT COUNT(DISTINCT id)
        FROM thermal_memory_archive
        WHERE sacred_pattern = true
          AND original_content LIKE '%%DC-%%'
          AND created_at > %s
    """, (created_at,))
    row = cur.fetchone()
    dc_count = row[0] if row else 0

    if dc_count < DC_DRIFT_TIER_1:
        return DC_DRIFT_SCORE_T1, dc_count
    elif dc_count < DC_DRIFT_TIER_2:
        return DC_DRIFT_SCORE_T2, dc_count
    elif dc_count < DC_DRIFT_TIER_3:
        return DC_DRIFT_SCORE_T3, dc_count
    return DC_DRIFT_SCORE_T4, dc_count


def score_decomposition(cur, ticket_id: int, title: str) -> float:
    """Score EPICs that have no linked Jr task activity."""
    if not title.upper().startswith('EPIC'):
        return NON_EPIC_SCORE

    cutoff = datetime.now() - timedelta(days=EPIC_STALE_DAYS)

    # Search for Jr tasks referencing this EPIC by ID or title keywords
    title_words = [w for w in title.split() if len(w) > 3 and w.upper() != 'EPIC']
    conditions = [f"(title ILIKE '%%{ticket_id}%%' OR description ILIKE '%%{ticket_id}%%')"]
    for word in title_words[:3]:
        # Escape single quotes for safety
        safe_word = word.replace("'", "''")
        conditions.append(f"(title ILIKE '%%{safe_word}%%' OR description ILIKE '%%{safe_word}%%')")

    where = " OR ".join(conditions)
    cur.execute(f"""
        SELECT COUNT(*)
        FROM jr_work_queue
        WHERE ({where})
          AND status = 'completed'
          AND updated_at > %s
    """, (cutoff,))
    row = cur.fetchone()
    recent_completions = row[0] if row else 0

    if recent_completions == 0:
        return EPIC_STALE_SCORE
    return EPIC_ACTIVE_SCORE


def score_tech_supersession(title: str) -> float:
    """Score based on deprecated technology references."""
    title_lower = title.lower()
    for tech in DEPRECATED_TECH:
        if tech.lower() in title_lower:
            return 0.9
    return 0.0


def score_market_freshness(cur, title: str) -> float:
    """Score market-related tickets without recent Deer signals."""
    title_lower = title.lower()
    is_market = any(kw.lower() in title_lower for kw in MARKET_KEYWORDS)
    if not is_market:
        return 0.0

    cutoff = datetime.now() - timedelta(days=MARKET_FRESH_DAYS)
    cur.execute("""
        SELECT COUNT(*)
        FROM thermal_memory_archive
        WHERE (domain_tag = 'market' OR tags::text LIKE '%%deer%%')
          AND created_at > %s
    """, (cutoff,))
    row = cur.fetchone()
    recent_signals = row[0] if row else 0

    if recent_signals > 0:
        return 0.0
    return MARKET_NO_SIGNAL_SCORE


def compute_composite(scores: Dict[str, float]) -> float:
    """Weighted average of all dimension scores."""
    return (
        scores['age'] * WEIGHT_AGE
        + scores['inactivity'] * WEIGHT_INACTIVITY
        + scores['dc_drift'] * WEIGHT_DC_DRIFT
        + scores['decomposition'] * WEIGHT_DECOMPOSITION
        + scores['tech_supersession'] * WEIGHT_TECH_SUPERSESSION
        + scores['market_freshness'] * WEIGHT_MARKET_FRESHNESS
    )


# ===================================================================
# Main Query + Scoring
# ===================================================================

def query_and_score(cur) -> Tuple[List[dict], dict]:
    """Query kanban items and score each one.

    Returns (scored_items, stats_dict).
    """
    cur.execute("""
        SELECT id, title, status, created_at, updated_at
        FROM duyuktv_tickets
        WHERE status IN ('open', 'backlog')
        ORDER BY created_at ASC
    """)
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]

    scored_items = []
    all_scores = []

    for row in rows:
        item = dict(zip(columns, row))
        title = item.get('title', '') or ''

        # Check seed/dormant exemption
        is_seed = any(tag in title.lower() for tag in ['seed', 'dormant'])

        # Score all six dimensions
        age = score_age(item['created_at'])
        inactivity = score_inactivity(item['updated_at'])
        dc_drift_val, dc_count = score_dc_drift(cur, item['created_at'])
        decomposition = score_decomposition(cur, item['id'], title)
        tech_sup = score_tech_supersession(title)
        market = score_market_freshness(cur, title)

        scores = {
            'age': age,
            'inactivity': inactivity,
            'dc_drift': dc_drift_val,
            'decomposition': decomposition,
            'tech_supersession': tech_sup,
            'market_freshness': market,
        }
        composite = compute_composite(scores)
        all_scores.append(composite)

        # Classify
        if is_seed:
            classification = 'SEED'
        elif composite >= STALE_THRESHOLD:
            classification = 'STALE'
        elif composite >= REVIEW_THRESHOLD:
            classification = 'REVIEW'
        else:
            classification = 'KEEP'

        scored_items.append({
            'id': item['id'],
            'title': title,
            'status': item['status'],
            'created_at': item['created_at'].isoformat() if item['created_at'] else None,
            'updated_at': item['updated_at'].isoformat() if item['updated_at'] else None,
            'scores': scores,
            'composite': round(composite, 3),
            'dc_count': dc_count,
            'classification': classification,
        })

    # Compute stats
    age_days = []
    for row in rows:
        item = dict(zip(columns, row))
        if item['created_at']:
            age_days.append((datetime.now() - item['created_at']).days)

    median_age = sorted(age_days)[len(age_days) // 2] if age_days else 0
    median_score = sorted(all_scores)[len(all_scores) // 2] if all_scores else 0.0

    stats = {
        'total_scored': len(rows),
        'median_age_days': median_age,
        'median_score': round(median_score, 2),
    }

    return scored_items, stats


def query_jr_stale(cur) -> List[dict]:
    """Secondary query: find stale jr_work_queue tasks."""
    stale_items = []

    # In-progress > 3 days
    cutoff_ip = datetime.now() - timedelta(days=JR_IN_PROGRESS_STALE_DAYS)
    cur.execute("""
        SELECT id, title, status, created_at, updated_at
        FROM jr_work_queue
        WHERE status = 'in_progress'
          AND updated_at < %s
        ORDER BY updated_at ASC
    """, (cutoff_ip,))
    for row in cur.fetchall():
        columns = [desc[0] for desc in cur.description]
        item = dict(zip(columns, row))
        item['stale_reason'] = f"in_progress for >{JR_IN_PROGRESS_STALE_DAYS} days"
        stale_items.append(item)

    # Pending > 5 days
    cutoff_p = datetime.now() - timedelta(days=JR_PENDING_STALE_DAYS)
    cur.execute("""
        SELECT id, title, status, created_at, updated_at
        FROM jr_work_queue
        WHERE status = 'pending'
          AND created_at < %s
        ORDER BY created_at ASC
    """, (cutoff_p,))
    for row in cur.fetchall():
        columns = [desc[0] for desc in cur.description]
        item = dict(zip(columns, row))
        item['stale_reason'] = f"pending for >{JR_PENDING_STALE_DAYS} days"
        stale_items.append(item)

    # Failed tasks
    cur.execute("""
        SELECT id, title, status, created_at, updated_at
        FROM jr_work_queue
        WHERE status = 'failed'
        ORDER BY updated_at DESC
        LIMIT 10
    """)
    for row in cur.fetchall():
        columns = [desc[0] for desc in cur.description]
        item = dict(zip(columns, row))
        item['stale_reason'] = 'failed'
        stale_items.append(item)

    return stale_items


# ===================================================================
# Output Formatters
# ===================================================================

def format_text(scored_items: List[dict], jr_stale: List[dict], stats: dict,
                kill_switch: bool) -> str:
    """Format human-readable text report."""
    now = datetime.now(TZ)
    lines = []
    lines.append(f"BACKLOG RECKONING — {now.strftime('%a %b %d, %Y %H:%M CT')}")
    lines.append("=" * 64)

    if kill_switch:
        lines.append("")
        lines.append("*** COYOTE REVIEW REQUIRED — Kill switch engaged ***")
        lines.append("Override rate exceeded threshold or no tickets closed in last 4 runs.")
        lines.append("Staleness recommendations suppressed until recalibrated.")
        lines.append("")

    # Separate by classification
    stale = [i for i in scored_items if i['classification'] == 'STALE']
    review = [i for i in scored_items if i['classification'] == 'REVIEW']
    seeds = [i for i in scored_items if i['classification'] == 'SEED']

    stale.sort(key=lambda x: x['composite'], reverse=True)
    review.sort(key=lambda x: x['composite'], reverse=True)

    # Cap output
    stale_capped = stale[:MAX_STALE]
    review_capped = review[:MAX_REVIEW]

    lines.append("")
    if not kill_switch:
        lines.append(f"STALE (recommend close/rewrite): {len(stale)} items"
                      + (f" (showing top {MAX_STALE})" if len(stale) > MAX_STALE else ""))
        if stale_capped:
            for item in stale_capped:
                s = item['scores']
                lines.append(f"  #{item['id']} [{item['composite']:.2f}] {item['title'][:70]}")
                lines.append(
                    f"    -> Age: {s['age']:.1f} | Inactivity: {s['inactivity']:.1f} | "
                    f"DC drift: {s['dc_drift']:.1f} | Tech: {s['tech_supersession']:.1f}"
                )
                if item['dc_count'] > 0:
                    lines.append(
                        f"    -> {item['dc_count']} DCs ratified since creation."
                    )
        else:
            lines.append("  (none)")

    lines.append("")
    lines.append(f"REVIEW (needs human eye): {len(review)} items"
                  + (f" (showing top {MAX_REVIEW})" if len(review) > MAX_REVIEW else ""))
    if review_capped:
        for item in review_capped:
            s = item['scores']
            lines.append(f"  #{item['id']} [{item['composite']:.2f}] {item['title'][:70]}")
            lines.append(
                f"    -> Age: {s['age']:.1f} | Inactivity: {s['inactivity']:.1f} | "
                f"DC drift: {s['dc_drift']:.1f} | Tech: {s['tech_supersession']:.1f}"
            )
    else:
        lines.append("  (none)")

    if seeds:
        lines.append("")
        lines.append(f"SEEDS (quarterly review): {len(seeds)} items")
        for item in seeds:
            lines.append(f"  #{item['id']} [{item['composite']:.2f}] {item['title'][:70]}")

    # Jr work queue staleness
    if jr_stale:
        lines.append("")
        lines.append(f"JR QUEUE STALENESS: {len(jr_stale)} items")
        for item in jr_stale:
            title = (item.get('title') or '')[:60]
            lines.append(f"  #{item['id']} [{item['stale_reason']}] {title}")

    lines.append("")
    lines.append(
        f"STATS: {stats['total_scored']} open items scored. "
        f"Median age: {stats['median_age_days']} days. "
        f"Median score: {stats['median_score']:.2f}."
    )

    # Override rate from history
    overrides = load_overrides()
    runs = overrides.get("runs", [])
    if runs:
        last = runs[-1]
        rate = last.get("override_rate", "N/A")
        if isinstance(rate, (int, float)):
            lines.append(f"Override rate (last run): {rate:.0%}")
        else:
            lines.append(f"Override rate (last run): {rate}")
    else:
        lines.append("Override rate (last 4 weeks): N/A (first run)")

    lines.append("=" * 64)
    return "\n".join(lines)


def format_json(scored_items: List[dict], jr_stale: List[dict], stats: dict,
                kill_switch: bool) -> str:
    """Format JSON output."""
    stale = [i for i in scored_items if i['classification'] == 'STALE']
    review = [i for i in scored_items if i['classification'] == 'REVIEW']
    seeds = [i for i in scored_items if i['classification'] == 'SEED']

    stale.sort(key=lambda x: x['composite'], reverse=True)
    review.sort(key=lambda x: x['composite'], reverse=True)

    output = {
        'timestamp': datetime.now(TZ).isoformat(),
        'kill_switch_engaged': kill_switch,
        'stale': stale[:MAX_STALE] if not kill_switch else [],
        'review': review[:MAX_REVIEW],
        'seeds': seeds,
        'jr_stale': [
            {
                'id': i['id'],
                'title': i.get('title', ''),
                'status': i.get('status', ''),
                'stale_reason': i['stale_reason'],
            }
            for i in jr_stale
        ],
        'stats': stats,
    }
    return json.dumps(output, indent=2, default=str)


# ===================================================================
# Main
# ===================================================================

def main():
    parser = argparse.ArgumentParser(description="Backlog Reckoning — Kanban Staleness Scoring")
    parser.add_argument('--text', action='store_true', default=True,
                        help='Text output (default)')
    parser.add_argument('--json', action='store_true', dest='json_mode',
                        help='JSON output')
    parser.add_argument('--slack', action='store_true',
                        help='Post to Slack #saturday-morning')
    parser.add_argument('--dry-run', action='store_true',
                        help='Score but do not post to Slack or write overrides')
    args = parser.parse_args()

    # Load overrides and check kill switch
    overrides = load_overrides()
    kill_switch = check_kill_switch(overrides)

    # Connect and score
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()

        scored_items, stats = query_and_score(cur)
        jr_stale = query_jr_stale(cur)

    except Exception as e:
        logger.error("Database error: %s", e)
        sys.exit(1)
    finally:
        if conn:
            conn.commit()  # explicit commit before close
            conn.close()

    # Output
    if args.json_mode:
        report = format_json(scored_items, jr_stale, stats, kill_switch)
        print(report)
    elif args.slack:
        report = format_text(scored_items, jr_stale, stats, kill_switch)
        if args.dry_run:
            print("[DRY RUN — would post to Slack #saturday-morning]")
            print(report)
        elif SLACK_AVAILABLE:
            ok = slack_send("saturday-morning", report)
            if ok:
                logger.info("Posted backlog reckoning to #saturday-morning")
            else:
                logger.error("Failed to post to Slack — printing to stdout")
                print(report)
        else:
            logger.warning("Slack not available — printing to stdout")
            print(report)
    else:
        report = format_text(scored_items, jr_stale, stats, kill_switch)
        print(report)

    # Write thermal memory (unless dry-run)
    if not args.dry_run and THERMAL_AVAILABLE:
        stale_count = len([i for i in scored_items if i['classification'] == 'STALE'])
        review_count = len([i for i in scored_items if i['classification'] == 'REVIEW'])
        temp = 50  # default temperature

        # Check override rate for elevated temperature
        runs = overrides.get("runs", [])
        if runs:
            last_rate = runs[-1].get("override_rate")
            if isinstance(last_rate, (int, float)) and last_rate > OVERRIDE_RATE_LIMIT:
                temp = 70

        try:
            safe_thermal_write(
                original_content=(
                    f"Backlog Reckoning run: {stats['total_scored']} items scored, "
                    f"{stale_count} STALE, {review_count} REVIEW. "
                    f"Median age {stats['median_age_days']}d, median score {stats['median_score']:.2f}. "
                    f"Jr stale: {len(jr_stale)}."
                ),
                temperature=temp,
                domain_tag='operations',
                tags=['backlog_reckoning', 'owl'],
            )
        except Exception as e:
            logger.warning("Failed to write thermal: %s", e)

    # Record override tracking placeholder (unless dry-run)
    if not args.dry_run:
        stale_ids = [
            i['id'] for i in scored_items
            if i['classification'] == 'STALE'
        ][:MAX_STALE]
        if stale_ids or not overrides.get("runs"):
            run_record = {
                "date": datetime.now(TZ).strftime("%Y-%m-%d"),
                "flagged": stale_ids,
                "closed": [],   # filled in by Chief or automation later
                "kept": [],     # filled in by Chief or automation later
                "override_rate": 0.0,
            }
            overrides.setdefault("runs", []).append(run_record)
            try:
                save_overrides(overrides)
                logger.info("Overrides file updated: %s", OVERRIDES_PATH)
            except Exception as e:
                logger.warning("Failed to save overrides: %s", e)

    if kill_switch:
        print("\n*** COYOTE REVIEW REQUIRED — see log for details ***",
              file=sys.stderr)


if __name__ == '__main__':
    main()
