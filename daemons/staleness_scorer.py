#!/usr/bin/env python3
"""
Staleness TTL Scorer — Drift Detection Phase 2A
Council Vote #8367

Computes freshness scores for thermal memories based on:
- Age since creation
- Time since last access
- Access frequency
- Domain-specific decay rates
- Sacred pattern protection (slower decay, not exempt)

Runs hourly or during sanctuary state.
Cherokee AI Federation — For the Seven Generations
"""

import psycopg2
import logging
import time
from datetime import datetime, timezone
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('staleness_scorer')

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': os.environ.get('CHEROKEE_DB_PASS', '')
}

# Domain-specific max freshness days
# After this many days, domain_freshness component drops to 0
DOMAIN_DECAY_DAYS = {
    'architecture': 30,    # Code changes fast
    'operational': 14,     # Ops context stales in 2 weeks
    'research': 90,        # Research findings last ~3 months
    'policy': 180,         # Policy changes slowly
    'cultural': 365,       # Cultural knowledge is long-lived
    'anchor': 99999,       # Anchor memories never go stale by domain
    None: 60,              # Default: 2 months
}

STALENESS_THRESHOLD = 0.2  # Below this = flagged stale


def get_conn():
    return psycopg2.connect(**DB_CONFIG)


def compute_freshness(created_at, last_access, access_count, sacred_pattern, domain_tag):
    """
    Compute freshness score (0.0 = stale, 1.0 = fresh).

    Components:
    - access_freshness (30%): How recently was this memory accessed?
    - domain_freshness (50%): Has domain-appropriate time passed?
    - usage_bonus (20%): Frequently accessed memories stay relevant
    """
    now = datetime.now(timezone.utc)

    # Ensure timezone-aware comparison
    if created_at and created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    if last_access and last_access.tzinfo is None:
        last_access = last_access.replace(tzinfo=timezone.utc)

    days_since_created = max(0, (now - created_at).days) if created_at else 0
    days_since_accessed = max(0, (now - last_access).days) if last_access else days_since_created

    # Component 1: Access recency (30% weight)
    access_freshness = max(0.1, 1.0 - (days_since_accessed / 90.0))

    # Component 2: Domain-appropriate age (50% weight)
    domain_max_days = DOMAIN_DECAY_DAYS.get(domain_tag, DOMAIN_DECAY_DAYS[None])
    domain_freshness = max(0.0, 1.0 - (days_since_created / domain_max_days))

    # Component 3: Usage frequency bonus (20% weight, capped at 0.2)
    usage_bonus = min(0.2, (access_count or 0) * 0.02)

    # Sacred memories decay at half speed but are NOT exempt
    sacred_factor = 0.5 if sacred_pattern else 1.0
    age_penalty = (1.0 - domain_freshness) * sacred_factor

    # Final score
    score = (access_freshness * 0.3) + ((1.0 - age_penalty) * 0.5) + usage_bonus

    return round(max(0.0, min(1.0, score)), 4)


def run_staleness_cycle():
    """Execute one staleness scoring cycle."""
    conn = get_conn()
    cur = conn.cursor()

    try:
        # Get all non-anchor memories
        cur.execute("""
            SELECT id, created_at, last_access, access_count,
                   sacred_pattern, domain_tag, freshness_score, staleness_flagged
            FROM thermal_memory_archive
            WHERE domain_tag IS DISTINCT FROM 'anchor'
            ORDER BY created_at DESC
        """)
        rows = cur.fetchall()
        logger.info(f"Scoring freshness for {len(rows)} memories")

        updated = 0
        newly_stale = 0
        recovered = 0

        for row in rows:
            mem_id, created_at, last_access, access_count, sacred, domain, old_score, was_stale = row

            new_score = compute_freshness(created_at, last_access, access_count, sacred, domain)
            now_stale = new_score < STALENESS_THRESHOLD

            # Only update if score changed meaningfully or flag changed
            if abs((old_score or 1.0) - new_score) > 0.01 or now_stale != (was_stale or False):
                cur.execute("""
                    UPDATE thermal_memory_archive
                    SET freshness_score = %s,
                        staleness_flagged = %s
                    WHERE id = %s
                """, (new_score, now_stale, mem_id))
                updated += 1

                if now_stale and not was_stale:
                    newly_stale += 1
                elif not now_stale and was_stale:
                    recovered += 1

        conn.commit()

        logger.info(
            f"Staleness cycle complete: {updated} updated, "
            f"{newly_stale} newly stale, {recovered} recovered"
        )

        # Store metrics in drift_metrics
        cur.execute("""
            INSERT INTO drift_metrics (metric_type, metric_value, details)
            VALUES ('staleness_cycle', %s, %s)
        """, (
            newly_stale,
            '{"updated": %d, "newly_stale": %d, "recovered": %d, "total": %d}'
            % (updated, newly_stale, recovered, len(rows))
        ))
        conn.commit()

        return {
            'total': len(rows),
            'updated': updated,
            'newly_stale': newly_stale,
            'recovered': recovered
        }

    except Exception as e:
        logger.error(f"Staleness cycle failed: {e}")
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def main():
    """Run staleness scorer on hourly loop."""
    logger.info("Staleness TTL Scorer starting")
    cycle_interval = 3600  # 1 hour

    while True:
        try:
            result = run_staleness_cycle()
            logger.info(f"Cycle result: {result}")
        except Exception as e:
            logger.error(f"Cycle error: {e}")

        time.sleep(cycle_interval)


if __name__ == '__main__':
    main()
