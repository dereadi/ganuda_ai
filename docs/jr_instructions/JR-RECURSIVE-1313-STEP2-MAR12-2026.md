# [RECURSIVE] Peace Chief Curiosity Engine — Stub Pipeline and Capacitor - Step 2

**Parent Task**: #1313
**Auto-decomposed**: 2026-03-12T16:49:39.418135
**Original Step Title**: Create the Curiosity Engine Library

---

### Step 2: Create the Curiosity Engine Library

**File:** `/ganuda/lib/curiosity_engine.py`

```python
"""
Curiosity Engine — Peace Chief stub-filling pipeline.

When partner shares content (LinkedIn posts, articles, podcasts, emails),
this library extracts stubs (named entities, concepts), routes them,
buffers them through the Flux Capacitor, and queues research.

Design principle: The Capacitor. Partner bursts. The organism does NOT
burst with him. It buffers, evaluates, smooths, and releases work at
a sustainable rate.

DC references: DC-9 (waste heat), DC-10 (reflex), DC-11 (macro polymorphism)
"""

import hashlib
import json
import logging
import re
from datetime import datetime, timezone, timedelta
from typing import Optional

import psycopg2
import psycopg2.extras

# Try importing SubAgentDispatch — fall back to regex-only mode if unavailable
try:
    from lib.sub_agent_dispatch import SubAgentDispatch, SubAgentError
    HAS_SUB_AGENT = True
except ImportError:
    HAS_SUB_AGENT = False
    SubAgentError = Exception

logger = logging.getLogger("curiosity_engine")

DB_CONFIG = {
    "host": "192.168.132.222",
    "port": 5432,
    "dbname": "zammad_production",
    "user": "claude",
    "password": "os.environ.get("CHEROKEE_DB_PASS", "")",
}

# ---------------------------------------------------------------------------
# Database setup
# ---------------------------------------------------------------------------

MIGRATION_SQL = """
CREATE TABLE IF NOT EXISTS curiosity_stubs (
    id SERIAL PRIMARY KEY,
    source_content_hash VARCHAR(64),
    stub_type VARCHAR(50),
    name VARCHAR(255),
    context TEXT,
    depth VARCHAR(20),
    domain VARCHAR(20),
    action VARCHAR(20),
    council_owner VARCHAR(50),
    priority INTEGER,
    status VARCHAR(20) DEFAULT 'pending',
    filled_by VARCHAR(100),
    filled_content TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    filled_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_curiosity_stubs_status ON curiosity_stubs(status);
CREATE INDEX IF NOT EXISTS idx_curiosity_stubs_hash ON curiosity_stubs(source_content_hash);
CREATE INDEX IF NOT EXISTS idx_curiosity_stubs_created ON curiosity_stubs(created_at);
"""


def _get_conn():
    return psycopg2.connect(**DB_CONFIG)


def setup_database():
    """Run the migration to create curiosity_stubs table."""
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(MIGRATION_SQL)
        conn.commit()
        logger.info("curiosity_stubs table ready")
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Stub extraction
# ---------------------------------------------------------------------------

EXTRACT_SYSTEM_PROMPT = """Extract all named entities and concepts from the following content.
Return a JSON array of objects:
{
  "type": "person|company|organization|regulation|concept|event|technology",
  "name": "exact name as mentioned",
  "context": "one sentence — what was said about them or why they were mentioned",
  "stub_depth": "shallow|medium|deep"
}

shallow = just a name drop, probably not worth researching
medium = mentioned with some context, worth a quick lookup
deep = central to the content, worth full research

Be thorough. Every proper noun. Every company. Every law or act mentioned.
Every person who commented or was quoted. Every technology named.
Return ONLY the JSON array, no markdown fences."""

ROUTE_SYSTEM_PROMPT = """Given this stub extracted from content the Chief shared, classify it.
Return JSON with these fields:
- domain: war_chief (technical/infrastructure) OR peace_chief (business/legal/diplomacy/culture)
- action: research (need to learn more) | monitor (bookmark, check later) | connect (potential relationship) | build (engineering need identified)
- council_owner: one of deer|crane|otter|spider|eagle_eye|crawdad|gecko|raven|coyote
- priority: 1 (critical) to 4 (low)

Return ONLY the JSON object, no markdown fences."""


def extract_stubs_local(content: str) -> list[dict]:
    """Use local model via SubAgentDispatch to extract named entities.
    Falls back to regex if the model is unavailable."""
    if not HAS_SUB_AGENT:
        return extract_stubs_regex(content)

    dispatch = SubAgentDispatch()
    try:
        raw = dispatch.fallback_chain(
            "redfin-fast", "sasass-general", "sasass-fast",
            EXTRACT_SYSTEM_PROMPT, content, max_tokens=2048, temperature=0.2,
        )
        # Strip markdown fences if model wraps them anyway
        raw = raw.strip()
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)
        stubs = json.loads(raw)
        if isinstance(stubs, list):
            return stubs
        logger.warning("Model returned non-list, falling back to regex")
        return extract_stubs_regex(content)
    except (SubAgentError, json.JSONDecodeError, Exception) as exc:
        logger.warning("Local model extraction failed (%s), falling back to regex", exc)
        return extract_stubs_regex(content)


def extract_stubs_regex(content: str) -> list[dict]:
    """Regex/heuristic fallback for stub extraction."""
    stubs = []
    seen_names = set()

    # Capitalized multi-word proper nouns (2-5 words)
    for m in re.finditer(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,4})\b', content):
        name = m.group(1)
        if name in seen_names:
            continue
        seen_names.add(name)
        # Determine depth by frequency
        count = content.count(name)
        depth = "deep" if count >= 3 else "medium" if count >= 2 else "shallow"
        # Extract surrounding sentence for context
        ctx = _extract_context(content, m.start())
        stubs.append({
            "type": "person",
            "name": name,
            "context": ctx,
            "stub_depth": depth,
        })

    # "CEO of X", "founder of X", "CTO of X" patterns
    for m in re.finditer(
        r'\b(?:CEO|CTO|COO|CFO|founder|co-founder|president|director)\s+(?:of|at)\s+([A-Z][A-Za-z0-9&\' ]{2,40})',
        content, re.IGNORECASE
    ):
        name = m.group(1).strip().rstrip(".,;:")
        if name not in seen_names:
            seen_names.add(name)
            stubs.append({
                "type": "company",
                "name": name,
                "context": _extract_context(content, m.start()),
                "stub_depth": "medium",
            })

    # Regulation / act / law patterns
    for m in re.finditer(r'\b([A-Z][A-Za-z0-9 ]{2,40}(?:Act|Law|Regulation|Rule|Standard|Protocol))\b', content):
        name = m.group(1).strip()
        if name not in seen_names:
            seen_names.add(name)
            stubs.append({
                "type": "regulation",
                "name": name,
                "context": _extract_context(content, m.start()),
                "stub_depth": "medium",
            })

    # Single capitalized words that look like company/product names (all-caps 3+ letters)
    for m in re.finditer(r'\b([A-Z]{3,12})\b', content):
        name = m.group(1)
        # Skip common acronyms that aren't entities
        if name in {"THE", "AND", "FOR", "BUT", "NOT", "ARE", "WAS", "HAS", "HAD",
                     "CEO", "CTO", "COO", "CFO", "LLC", "INC", "USA", "API", "SQL",
                     "HTTP", "JSON", "HTML", "CSS"}:
            continue
        if name not in seen_names:
            seen_names.add(name)
            stubs.append({
                "type": "organization",
                "name": name,
                "context": _extract_context(content, m.start()),
                "stub_depth": "shallow",
            })

    return stubs


def _extract_context(content: str, pos: int, window: int = 120) -> str:
    """Extract a sentence-ish window around a position."""
    start = max(0, pos - window)
    end = min(len(content), pos + window)
    snippet = content[start:end].strip()
    # Try to snap to sentence boundaries
    first_period = snippet.find(". ")
    if first_period > 0 and first_period < len(snippet) // 3:
        snippet = snippet[first_period + 2:]
    last_period = snippet.rfind(". ")
    if last_period > len(snippet) * 2 // 3:
        snippet = snippet[:last_period + 1]
    return snippet


# ---------------------------------------------------------------------------
# Stub routing
# ---------------------------------------------------------------------------

# Heuristic routing keywords
_DOMAIN_KEYWORDS = {
    "war_chief": {"code", "server", "deploy", "api", "database", "gpu", "model",
                  "infrastructure", "node", "vram", "latency", "benchmark", "rust",
                  "python", "linux", "docker", "kubernetes", "vllm", "mlx"},
    "peace_chief": {"business", "market", "legal", "patent", "compliance", "sales",
                    "customer", "partner", "investor", "revenue", "pricing", "brand",
                    "culture", "community", "linkedin", "podcast", "article"},
}

_COUNCIL_KEYWORDS = {
    "deer": {"market", "business", "revenue", "pricing", "sales", "linkedin", "brand"},
    "crane": {"governance", "diplomacy", "protocol", "standard", "iso", "compliance", "external"},
    "otter": {"legal", "patent", "regulation", "law", "act", "soc2", "gdpr", "hipaa"},
    "spider": {"code", "infrastructure", "deploy", "api", "database", "server", "node"},
    "eagle_eye": {"monitor", "observe", "drift", "anomaly", "alert", "telemetry"},
    "crawdad": {"pii", "credential", "secret", "privacy", "scrub", "security"},
    "gecko": {"memory", "thermal", "knowledge", "archive", "context"},
    "raven": {"tech debt", "regression", "test", "quality", "review"},
    "coyote": {"risk", "concern", "dissent", "caution", "safety", "question"},
}


def route_stub(stub: dict, content: str) -> dict:
    """Classify stub by domain, action, council_owner, priority.
    Tries local model first, falls back to heuristic."""
    if HAS_SUB_AGENT:
        try:
            return _route_stub_model(stub, content)
        except Exception as exc:
            logger.warning("Model routing failed (%s), using heuristic", exc)

    return _route_stub_heuristic(stub, content)


def _route_stub_model(stub: dict, content: str) -> dict:
    """Use local model to route a stub."""
    dispatch = SubAgentDispatch()
    user_msg = f"Stub: {stub['name']} (type: {stub['type']})\nContext: {stub.get('context', '')}\nFrom content: {content[:500]}"
    raw = dispatch.fallback_chain(
        "redfin-fast", "sasass-fast", "sasass-general",
        ROUTE_SYSTEM_PROMPT, user_msg, max_tokens=256, temperature=0.1,
    )
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    result = json.loads(raw)
    # Validate expected fields
    for field in ("domain", "action", "council_owner", "priority"):
        if field not in result:
            raise ValueError(f"Missing field: {field}")
    return result


def _route_stub_heuristic(stub: dict, content: str) -> dict:
    """Heuristic routing based on keywords."""
    combined = f"{stub.get('name', '')} {stub.get('context', '')} {stub.get('type', '')}".lower()

    # Domain
    war_score = sum(1 for kw in _DOMAIN_KEYWORDS["war_chief"] if kw in combined)
    peace_score = sum(1 for kw in _DOMAIN_KEYWORDS["peace_chief"] if kw in combined)
    domain = "war_chief" if war_score > peace_score else "peace_chief"

    # Action
    stub_type = stub.get("type", "").lower()
    if stub_type in ("person", "company", "organization"):
        action = "connect" if stub.get("stub_depth") == "deep" else "research"
    elif stub_type in ("regulation", "concept"):
        action = "research"
    elif stub_type in ("technology",):
        action = "build" if domain == "war_chief" else "research"
    else:
        action = "monitor"

    # Council owner
    council_owner = "deer"  # default to Deer (peace chief lead)
    best_score = 0
    for council, keywords in _COUNCIL_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in combined)
        if score > best_score:
            best_score = score
            council_owner = council

    # Priority based on depth
    depth = stub.get("stub_depth", "shallow")
    if depth == "deep":
        priority = 1
    elif depth == "medium":
        priority = 2
    else:
        priority = 4

    return {
        "domain": domain,
        "action": action,
        "council_owner": council_owner,
        "priority": priority,
    }


# ---------------------------------------------------------------------------
# Flux Capacitor
# ---------------------------------------------------------------------------

class StubCapacitor:
    """The Flux Capacitor. Buffer partner bursts. Evaluate. Smooth.

    Converts partner's AC signal (jagged bursts) into smooth DC current
    (steady work). The organism runs at its own pace regardless of
    partner's frequency.
    """

    MAX_STUBS_PER_HOUR = 5
    COOLING_PERIOD_MINUTES = 30

    def buffer(self, stubs: list[dict], content_hash: str):
        """Store stubs with status='buffered' in curiosity_stubs.
        Deduplicates against existing buffered stubs for the same content."""
        conn = _get_conn()
        try:
            with conn.cursor() as cur:
                for stub in stubs:
                    # Check for duplicate name + same content hash
                    cur.execute(
                        "SELECT id FROM curiosity_stubs WHERE source_content_hash = %s AND name = %s",
                        (content_hash, stub.get("name", "")),
                    )
                    if cur.fetchone():
                        continue

                    routing = stub.get("_routing", {})
                    cur.execute(
                        """INSERT INTO curiosity_stubs
                           (source_content_hash, stub_type, name, context, depth,
                            domain, action, council_owner, priority, status)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'buffered')""",
                        (
                            content_hash,
                            stub.get("type", "unknown"),
                            stub.get("name", ""),
                            stub.get("context", ""),
                            stub.get("stub_depth", "shallow"),
                            routing.get("domain", "peace_chief"),
                            routing.get("action", "research"),
                            routing.get("council_owner", "deer"),
                            routing.get("priority", 3),
                        ),
                    )
            conn.commit()
            logger.info("Buffered %d stubs for content %s", len(stubs), content_hash[:12])
        finally:
            conn.close()

    def evaluate(self) -> list[dict]:
        """After cooling period, score buffered stubs.
        Promotes stubs that have cooled long enough. Drops low-quality ones.
        Returns list of promoted stubs."""
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=self.COOLING_PERIOD_MINUTES)
        conn = _get_conn()
        promoted = []
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """SELECT * FROM curiosity_stubs
                       WHERE status = 'buffered' AND created_at <= %s
                       ORDER BY priority ASC, created_at ASC""",
                    (cutoff,),
                )
                cooled = cur.fetchall()

                for stub in cooled:
                    actionable = _score_actionable(stub)
                    novelty = _score_novelty(stub, cur)

                    if actionable < 0.3 and novelty < 0.3:
                        # Drop — not worth the compute
                        cur.execute(
                            "UPDATE curiosity_stubs SET status = 'dismissed' WHERE id = %s",
                            (stub["id"],),
                        )
                        logger.debug("Dismissed stub %s (%s): actionable=%.2f novelty=%.2f",
                                     stub["id"], stub["name"], actionable, novelty)
                    else:
                        # Determine target status based on depth
                        if stub["depth"] == "shallow":
                            new_status = "dismissed"
                        elif stub["depth"] == "deep":
                            new_status = "queued_for_research"
                        else:
                            new_status = "pending"

                        cur.execute(
                            "UPDATE curiosity_stubs SET status = %s WHERE id = %s",
                            (new_status, stub["id"]),
                        )
                        if new_status != "dismissed":
                            promoted.append(dict(stub))

            conn.commit()
            logger.info("Evaluated %d cooled stubs, promoted %d", len(cooled), len(promoted))
        finally:
            conn.close()

        return promoted

    def smooth(self) -> list[dict]:
        """Release stubs at a sustainable rate.
        Returns stubs ready for dispatch, limited by MAX_STUBS_PER_HOUR."""
        conn = _get_conn()
        released = []
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Check how many were dispatched in the last hour
                one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
                cur.execute(
                    """SELECT COUNT(*) as cnt FROM curiosity_stubs
                       WHERE status = 'researching'
                       AND created_at >= %s""",
                    (one_hour_ago,),
                )
                dispatched_recently = cur.fetchone()["cnt"]
                remaining_budget = max(0, self.MAX_STUBS_PER_HOUR - dispatched_recently)

                if remaining_budget == 0:
                    logger.info("Hourly stub budget exhausted (%d dispatched)", dispatched_recently)
                    return []

                # Get queued stubs ordered by priority
                cur.execute(
                    """SELECT * FROM curiosity_stubs
                       WHERE status = 'queued_for_research'
                       ORDER BY priority ASC, created_at ASC
                       LIMIT %s""",
                    (remaining_budget,),
                )
                ready = cur.fetchall()

                for stub in ready:
                    cur.execute(
                        "UPDATE curiosity_stubs SET status = 'researching' WHERE id = %s",
                        (stub["id"],),
                    )
                    released.append(dict(stub))

            conn.commit()
            logger.info("Released %d stubs for research (budget remaining: %d)",
                        len(released), remaining_budget - len(released))
        finally:
            conn.close()

        return released

    def merge_burst(self, new_stubs: list[dict]):
        """Deduplicate stubs from rapid successive shares.
        Merges new stubs against recently buffered ones by name similarity."""
        conn = _get_conn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                recent_window = datetime.now(timezone.utc) - timedelta(minutes=15)
                cur.execute(
                    """SELECT id, name, context FROM curiosity_stubs
                       WHERE status = 'buffered' AND created_at >= %s""",
                    (recent_window,),
                )
                existing = {row["name"].lower(): row for row in cur.fetchall()}

                merged_count = 0
                for stub in new_stubs:
                    key = stub.get("name", "").lower()
                    if key in existing:
                        # Merge context — append new context to existing
                        existing_row = existing[key]
                        combined_context = f"{existing_row['context']} | {stub.get('context', '')}"
                        cur.execute(
                            "UPDATE curiosity_stubs SET context = %s WHERE id = %s",
                            (combined_context[:2000], existing_row["id"]),
                        )
                        merged_count += 1

            conn.commit()
            if merged_count:
                logger.info("Merged %d duplicate stubs from burst", merged_count)
            return merged_count
        finally:
            conn.close()


def _score_actionable(stub: dict) -> float:
    """Score how actionable a stub is (0.0-1.0)."""
    score = 0.5  # baseline

    depth = stub.get("depth", "shallow")
    if depth == "deep":
        score += 0.3
    elif depth == "medium":
        score += 0.1
    else:
        score -= 0.2

    action = stub.get("action", "monitor")
    if action == "research":
        score += 0.1
    elif action == "connect":
        score += 0.15
    elif action == "build":
        score += 0.2

    priority = stub.get("priority", 3)
    if priority <= 1:
        score += 0.15
    elif priority == 2:
        score += 0.05

    return max(0.0, min(1.0, score))


def _score_novelty(stub: dict, cursor) -> float:
    """Score how novel a stub is (0.0-1.0) by checking for prior occurrences."""
    name = stub.get("name", "")
    if not name:
        return 0.0

    # Check if we've seen this name before (any status)
    cursor.execute(
        """SELECT COUNT(*) as cnt FROM curiosity_stubs
           WHERE name = %s AND id != %s""",
        (name, stub["id"]),
    )
    prior_count = cursor.fetchone()["cnt"]

    if prior_count == 0:
        return 0.9  # totally new
    elif prior_count == 1:
        return 0.5  # seen once before
    elif prior_count <= 3:
        return 0.2  # recurring
    else:
        return 0.05  # well known, low novelty


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def ingest_sensory_input(content: str, source: str = "unknown") -> dict:
    """Main entry point. Partner shared something. Start curiosity pipeline.

    Args:
        content: The raw text (LinkedIn post, article, transcript, etc.)
        source: Where it came from (linkedin, telegram, email, podcast, etc.)

    Returns:
        dict with keys: content_hash, stubs_extracted, stubs_buffered,
        breakdown, top_stubs, report
    """
    # Ensure table exists
    setup_database()

    # 1. Hash content for dedup
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

    # Check if we already processed this content
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM curiosity_stubs WHERE source_content_hash = %s",
                (content_hash,),
            )
            if cur.fetchone()[0] > 0:
                logger.info("Content %s already processed, skipping", content_hash[:12])
                return {
                    "content_hash": content_hash,
                    "stubs_extracted": 0,
                    "stubs_buffered": 0,
                    "duplicate": True,
                    "report": f"Content already processed (hash: {content_hash[:12]})",
                }
    finally:
        conn.close()

    # 2. Extract stubs
    raw_stubs = extract_stubs_local(content)
    logger.info("Extracted %d raw stubs from %s content", len(raw_stubs), source)

    # 3. Route each stub (skip shallow — DC-9 waste heat)
    for stub in raw_stubs:
        depth = stub.get("stub_depth", "shallow")
        if depth in ("medium", "deep"):
            routing = route_stub(stub, content)
        else:
            routing = {
                "domain": "peace_chief",
                "action": "monitor",
                "council_owner": "deer",
                "priority": 4,
            }
        stub["_routing"] = routing

    # 4. Buffer through capacitor
    capacitor = StubCapacitor()
    capacitor.merge_burst(raw_stubs)
    capacitor.buffer(raw_stubs, content_hash)

    # 5. Build breakdown
    depth_counts = {"deep": 0, "medium": 0, "shallow": 0}
    domain_counts = {"peace_chief": 0, "war_chief": 0}
    for stub in raw_stubs:
        d = stub.get("stub_depth", "shallow")
        depth_counts[d] = depth_counts.get(d, 0) + 1
        dm = stub.get("_routing", {}).get("domain", "peace_chief")
        domain_counts[dm] = domain_counts.get(dm, 0) + 1

    # Top stubs by priority (deep/medium only)
    actionable = [s for s in raw_stubs if s.get("stub_depth") in ("deep", "medium")]
    actionable.sort(key=lambda s: s.get("_routing", {}).get("priority", 4))
    top_stubs = actionable[:3]

    # 6. Generate report
    report = generate_report(raw_stubs, source, depth_counts, domain_counts, top_stubs)

    return {
        "content_hash": content_hash,
        "stubs_extracted": len(raw_stubs),
        "stubs_buffered": len(raw_stubs),
        "duplicate": False,
        "breakdown": {
            "depths": depth_counts,
            "domains": domain_counts,
        },
        "top_stubs": [{"name": s["name"], "type": s["type"], "depth": s["stub_depth"]} for s in top_stubs],
        "report": report,
    }


def generate_report(stubs: list[dict], source: str,
                    depth_counts: Optional[dict] = None,
                    domain_counts: Optional[dict] = None,
                    top_stubs: Optional[list[dict]] = None) -> str:
    """Generate intake report string."""
    if depth_counts is None:
        depth_counts = {"deep": 0, "medium": 0, "shallow": 0}
        for s in stubs:
            d = s.get("stub_depth", "shallow")
            depth_counts[d] = depth_counts.get(d, 0) + 1

    if domain_counts is None:
        domain_counts = {"peace_chief": 0, "war_chief": 0}
        for s in stubs:
            dm = s.get("_routing", {}).get("domain", "peace_chief")
            domain_counts[dm] = domain_counts.get(dm, 0) + 1

    if top_stubs is None:
        actionable = [s for s in stubs if s.get("stub_depth") in ("deep", "medium")]
        actionable.sort(key=lambda s: s.get("_routing", {}).get("priority", 4))
        top_stubs = actionable[:3]

    total = len(stubs)
    queued = depth_counts.get("deep", 0) + depth_counts.get("medium", 0)

    lines = [
        f"Curiosity Engine processed {source} content.",
        f"Extracted: {total} stubs ({depth_counts.get('deep', 0)} deep, "
        f"{depth_counts.get('medium', 0)} medium, {depth_counts.get('shallow', 0)} shallow)",
        f"Queued: {queued} for research",
        f"Routed: {domain_counts.get('peace_chief', 0)} to Peace Chief, "
        f"{domain_counts.get('war_chief', 0)} to War Chief",
    ]

    if top_stubs:
        lines.append("Top stubs:")
        for i, s in enumerate(top_stubs, 1):
            name = s.get("name", "unknown")
            stype = s.get("type", "?")
            depth = s.get("stub_depth", "?")
            lines.append(f"  {i}. {name} ({stype}, {depth})")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Convenience: run capacitor evaluation cycle
# ---------------------------------------------------------------------------

def run_capacitor_cycle() -> dict:
    """Run a full capacitor cycle: evaluate cooled stubs, then smooth release.
    Intended to be called periodically (e.g., every 30 minutes by a timer)."""
    setup_database()
    capacitor = StubCapacitor()

    promoted = capacitor.evaluate()
    released = capacitor.smooth()

    return {
        "promoted": len(promoted),
        "released": len(released),
        "released_stubs": [{"id": s["id"], "name": s["name"]} for s in released],
    }


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")

    if len(sys.argv) > 1 and sys.argv[1] == "--setup":
        setup_database()
        print("Database setup complete.")
    elif len(sys.argv) > 1 and sys.argv[1] == "--cycle":
        result = run_capacitor_cycle()
        print(f"Capacitor cycle: promoted={result['promoted']}, released={result['released']}")
    else:
        # Demo with stdin
        content = sys.stdin.read() if not sys.stdin.isatty() else "No content provided. Pass via stdin."
        source = sys.argv[1] if len(sys.argv) > 1 else "cli"
        result = ingest_sensory_input(content, source)
        print(result["report"])
```
