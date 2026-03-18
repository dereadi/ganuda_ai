#!/usr/bin/env python3
"""
Deer LinkedIn Draft Generation from Thermal Fuel
Cherokee AI Federation — Outer Council (Deer)
Jr Task #1284

Queries thermal_memory_archive for sacred and high-temperature business/market
thermals, dispatches to local models via sub_agent_dispatch for LinkedIn post
drafting, screens for internal terms, and saves drafts for partner review.

NEVER auto-posts. Drafts only.

Usage:
    python3 scripts/deer_linkedin_drafts.py                     # last 48h, top 5
    python3 scripts/deer_linkedin_drafts.py --hours 72          # last 72 hours
    python3 scripts/deer_linkedin_drafts.py --limit 10          # draft up to 10
    python3 scripts/deer_linkedin_drafts.py --dry-run           # show fuel, skip LLM
    python3 scripts/deer_linkedin_drafts.py --include-sacred    # include sacred thermals
"""

import sys
import os
import json
import re
import argparse
import logging
from datetime import datetime

sys.path.insert(0, '/ganuda')
sys.path.insert(0, '/ganuda/lib')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
)
logger = logging.getLogger("deer_linkedin_drafts")

# ---------------------------------------------------------------------------
# Content safety — terms that must NEVER appear in public posts
# ---------------------------------------------------------------------------

BLOCKED_TERMS = [
    "thermal_memory", "thermal memory", "council_votes", "duyuktv",
    "jr_work_queue", "bluefin", "redfin", "greenfin", "owlfin", "eaglefin",
    "bmasass", "sasass", "sacred_fire", "nftables", "192.168", "10.100.0",
    "zammad_production", "FreeIPA", "silverfin", "WireGuard",
    "Qwen2.5", "Qwen3", "vLLM", "mlx_lm", "DeepSeek-R1", "RTX PRO 6000",
    "cherokee_venv", "jr_executor", "SEARCH/REPLACE", "psycopg2",
    "sub_agent_dispatch", "thermal_memory_archive", "ganuda_db",
    "keepalived", "Caddy", "Tailscale",
]

# Short terms need word-boundary matching to avoid false positives
BLOCKED_WORDS = ["TEG", "SAG", "DLQ"]


def screen_content(draft: str) -> list:
    """Screen draft for blocked internal terms. Returns list of violations."""
    lower = draft.lower()
    found = [term for term in BLOCKED_TERMS if term.lower() in lower]
    for word in BLOCKED_WORDS:
        if re.search(r'\b' + re.escape(word) + r'\b', draft, re.IGNORECASE):
            found.append(word)
    return found


# ---------------------------------------------------------------------------
# Thermal fuel queries
# ---------------------------------------------------------------------------

DEER_DOMAINS = (
    'deer_jewel', 'deer_scout', 'market', 'business', 'legal',
    'partnership', 'deer', 'otter', 'crane', 'research', 'design',
)


def get_thermal_fuel(hours: int = 48, limit: int = 5,
                     include_sacred: bool = False) -> list:
    """
    Fetch high-value thermals suitable for LinkedIn content.

    Selection criteria:
      1. Sacred thermals (temp >= 90) — only if include_sacred=True
      2. Business/market domain thermals (temp >= 70)
      3. Any high-temperature thermals (temp >= 85)

    Deduplicates against previously drafted thermals (linkedin_drafts table).
    """
    from ganuda_db import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()

        # Check if linkedin_drafts table exists for dedup
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'linkedin_drafts'
            )
        """)
        drafts_table_exists = cur.fetchone()[0]

        # Build dedup subquery — match on source_ref containing the thermal id
        dedup_clause = ""
        if drafts_table_exists:
            dedup_clause = """
                AND t.id::text NOT IN (
                    SELECT COALESCE(
                        (metadata->>'thermal_id'),
                        ''
                    ) FROM linkedin_drafts
                    WHERE metadata->>'thermal_id' IS NOT NULL
                )
            """

        # Sacred filter
        sacred_clause = ""
        if not include_sacred:
            sacred_clause = "AND t.sacred_pattern = false"

        # Build domain list for parameterized query
        domain_placeholders = ', '.join(['%s'] * len(DEER_DOMAINS))

        query = f"""
            SELECT t.id, t.original_content, t.temperature_score,
                   t.sacred_pattern, t.domain_tag, t.metadata,
                   t.created_at
            FROM thermal_memory_archive t
            WHERE t.created_at >= NOW() - INTERVAL '{int(hours)} hours'
              AND t.original_content IS NOT NULL
              AND LENGTH(t.original_content) > 50
              {sacred_clause}
              {dedup_clause}
              AND (
                  -- Business/market domain thermals
                  (t.domain_tag IN ({domain_placeholders})
                   AND t.temperature_score >= 70)
                  -- Any high-temp thermal
                  OR t.temperature_score >= 85
              )
            ORDER BY
                t.temperature_score DESC,
                t.created_at DESC
            LIMIT %s
        """
        params = list(DEER_DOMAINS) + [limit]
        cur.execute(query, params)
        cols = [d[0] for d in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        return rows
    finally:
        conn.commit()  # explicit commit before close
        conn.close()


# ---------------------------------------------------------------------------
# LLM draft generation via sub_agent_dispatch
# ---------------------------------------------------------------------------

LINKEDIN_SYSTEM_PROMPT = """You are Deer, the Market/Business council member of the Cherokee AI Federation.
Write a LinkedIn post (150-250 words) based on the insight below.

Rules:
- Share the PHILOSOPHY and THINKING, never the technical implementation
- Use accessible language for a business/AI professional audience
- Reference Cherokee governance principles when relevant (governance by consent, seven generations thinking, collective wisdom)
- Open with a hook: a question, bold statement, or surprising fact
- Include 1-2 thought-provoking questions to drive engagement
- End with 3-5 relevant hashtags
- Use line breaks for readability (LinkedIn format)
- Tone: thoughtful, confident, inviting conversation. NOT salesy or hype.
- Never mention specific tools, servers, IP addresses, model names, or internal architecture
- Focus on the IDEA, the PRINCIPLE, or the INSIGHT — not the implementation
- Themes that resonate: sovereign AI, community-governed technology, Cherokee values in tech, practical AI architecture, lessons from building distributed systems
- NEVER fabricate claims. Only use what is in the source material.

Return ONLY the LinkedIn post text. No explanations, no metadata, no markdown fencing."""


def generate_draft(thermal: dict) -> dict:
    """
    Generate a LinkedIn draft from a single thermal using sub_agent_dispatch.

    Returns {"ok": bool, "draft": str, "node": str, "latency_ms": int}
    """
    from sub_agent_dispatch import SubAgentDispatch

    dispatcher = SubAgentDispatch(default_timeout=60.0)

    content = thermal.get("original_content", "")
    meta = thermal.get("metadata", {})
    if isinstance(meta, str):
        try:
            meta = json.loads(meta)
        except (json.JSONDecodeError, TypeError):
            meta = {}

    temp_score = thermal.get("temperature_score", 0)
    domain = thermal.get("domain_tag", "general")

    prompt = f"""Draft a LinkedIn post based on this internal insight:

SOURCE CONTENT:
{content[:3000]}

CONTEXT:
- Domain: {domain}
- Importance: Temperature {temp_score}/100
- Date: {thermal.get('created_at', 'recent')}

Remember: Extract the universal principle or insight. Do NOT expose internal system details."""

    # Use bmasass Qwen3-30B for creative work, fallback to redfin vLLM
    result = dispatcher.dispatch_with_fallback(
        prompt,
        system=LINKEDIN_SYSTEM_PROMPT,
        node="bmasass_qwen3",
        temperature=0.7,
        max_tokens=1024,
    )

    return {
        "ok": result["ok"],
        "draft": result["text"] if result["ok"] else "",
        "node": result["node"],
        "latency_ms": result["latency_ms"],
    }


# ---------------------------------------------------------------------------
# Database persistence
# ---------------------------------------------------------------------------

def ensure_drafts_table():
    """Create the linkedin_drafts table if it does not exist (uses existing migration)."""
    import psycopg2
    from ganuda_db import get_connection

    migration_path = "/ganuda/scripts/migrations/linkedin_drafts_schema.sql"
    if not os.path.exists(migration_path):
        logger.warning("Migration file not found at %s", migration_path)
        return

    conn = get_connection()
    try:
        cur = conn.cursor()
        with open(migration_path) as f:
            try:
                cur.execute(f.read())
                conn.commit()
            except psycopg2.errors.DuplicateTable:
                conn.rollback()
    finally:
        conn.commit()  # explicit commit before close
        conn.close()


def save_draft(thermal: dict, draft_text: str, model_node: str,
               latency_ms: int) -> bool:
    """Save a LinkedIn draft to the linkedin_drafts table. Returns True on success."""
    from ganuda_db import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()

        # Extract hashtags from draft
        hashtag_matches = re.findall(r'#(\w+)', draft_text)
        hashtags = hashtag_matches[:5] if hashtag_matches else []

        metadata = {
            "thermal_id": str(thermal["id"]),
            "temperature_score": thermal.get("temperature_score"),
            "domain_tag": thermal.get("domain_tag"),
            "model_node": model_node,
            "latency_ms": latency_ms,
            "generated_at": datetime.now().isoformat(),
            "jr_task": 1284,
        }

        cur.execute("""
            INSERT INTO linkedin_drafts
                (source_type, source_ref, draft_content, hashtags, metadata)
            VALUES (%s, %s, %s, %s, %s::jsonb)
        """, (
            "thermal_fuel",
            f"thermal#{thermal['id']}",
            draft_text,
            hashtags,
            json.dumps(metadata),
        ))
        conn.commit()
        return True
    except Exception as e:
        logger.error("Failed to save draft for thermal %d: %s", thermal["id"], e)
        conn.rollback()
        return False
    finally:
        conn.commit()  # explicit commit before close
        conn.close()


def save_drafts_to_file(drafts: list,
                        filepath: str = "/ganuda/logs/linkedin_drafts_fallback.jsonl"):
    """Fallback: append drafts to JSONL file if DB write fails."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "a") as f:
        for d in drafts:
            f.write(json.dumps(d, default=str) + "\n")
    logger.info("Saved %d drafts to fallback file %s", len(drafts), filepath)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run_pipeline(hours: int = 48, limit: int = 5, dry_run: bool = False,
                 include_sacred: bool = False) -> dict:
    """
    Full pipeline: fetch thermal fuel -> draft posts -> screen -> save for review.
    """
    logger.info("Deer LinkedIn Drafts (Jr #1284) — scanning last %dh, limit %d, "
                "sacred=%s", hours, limit, include_sacred)

    # 1. Fetch thermal fuel
    thermals = get_thermal_fuel(hours=hours, limit=limit,
                                include_sacred=include_sacred)
    logger.info("Found %d thermal fuel candidates", len(thermals))

    if not thermals:
        logger.info("No thermal fuel found. Nothing to draft.")
        return {"fuel_count": 0, "drafted": 0, "saved": 0,
                "screened_out": 0, "errors": 0}

    if dry_run:
        logger.info("DRY RUN — fuel candidates:")
        for i, t in enumerate(thermals, 1):
            preview = (t.get("original_content", "") or "")[:120]
            logger.info(
                "  %d. [id=%d temp=%s sacred=%s domain=%s] %s...",
                i, t["id"], t.get("temperature_score"),
                t.get("sacred_pattern"), t.get("domain_tag"), preview
            )
        return {"fuel_count": len(thermals), "drafted": 0, "saved": 0,
                "screened_out": 0, "errors": 0, "dry_run": True}

    # 2. Ensure drafts table exists
    ensure_drafts_table()

    # 3. Generate, screen, and save drafts
    drafted = 0
    saved = 0
    screened_out = 0
    errors = 0
    file_fallback = []

    for i, thermal in enumerate(thermals, 1):
        logger.info("Drafting %d/%d from thermal #%d (temp=%s, domain=%s)",
                     i, len(thermals), thermal["id"],
                     thermal.get("temperature_score"),
                     thermal.get("domain_tag"))

        result = generate_draft(thermal)
        if not result["ok"]:
            logger.warning("LLM draft failed for thermal #%d: %s",
                           thermal["id"], result.get("draft", "unknown"))
            errors += 1
            continue

        draft_text = result["draft"]
        drafted += 1
        logger.info("Draft generated (%d chars, %dms, node=%s)",
                     len(draft_text), result["latency_ms"], result["node"])

        # 4. Screen for internal terms
        violations = screen_content(draft_text)
        if violations:
            logger.warning("BLOCKED thermal #%d — internal terms found: %s",
                           thermal["id"], violations)
            screened_out += 1
            continue

        # 5. Save to database
        if save_draft(thermal, draft_text, result["node"], result["latency_ms"]):
            saved += 1
            logger.info("Draft saved for thermal #%d", thermal["id"])
        else:
            file_fallback.append({
                "thermal_id": thermal["id"],
                "draft": draft_text,
                "node": result["node"],
                "latency_ms": result["latency_ms"],
                "timestamp": datetime.now().isoformat(),
            })

    # 6. File fallback for DB failures
    if file_fallback:
        save_drafts_to_file(file_fallback)
        saved += len(file_fallback)

    summary = {
        "fuel_count": len(thermals),
        "drafted": drafted,
        "saved": saved,
        "screened_out": screened_out,
        "errors": errors,
    }
    logger.info("Pipeline complete: %s", json.dumps(summary))

    # 7. Notify via Slack (best-effort)
    try:
        from slack_federation import send as slack_send
        msg = (f"Deer LinkedIn Drafts: {drafted} drafted from {len(thermals)} thermals. "
               f"{saved} saved, {screened_out} screened out, {errors} errors.")
        slack_send("deer-signals", msg)
    except Exception:
        pass

    # 8. Print pending count
    try:
        from ganuda_db import execute_query
        rows = execute_query(
            "SELECT COUNT(*) as cnt FROM linkedin_drafts WHERE status = 'pending'"
        )
        pending = rows[0]["cnt"] if rows else 0
        logger.info("%d total drafts pending Chief review.", pending)
    except Exception:
        pass

    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Deer LinkedIn Draft Generation from Thermal Fuel (Jr #1284)"
    )
    parser.add_argument("--hours", type=int, default=48,
                        help="Look-back window in hours (default: 48)")
    parser.add_argument("--limit", type=int, default=5,
                        help="Max drafts to generate (default: 5)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print fuel candidates without drafting")
    parser.add_argument("--include-sacred", action="store_true",
                        help="Include sacred thermals as fuel (default: exclude)")
    args = parser.parse_args()

    result = run_pipeline(
        hours=args.hours,
        limit=args.limit,
        dry_run=args.dry_run,
        include_sacred=args.include_sacred,
    )

    sys.exit(0 if result.get("saved", 0) > 0 or result.get("dry_run") else 1)
