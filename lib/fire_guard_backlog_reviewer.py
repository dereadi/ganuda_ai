"""Fire Guard Backlog Reviewer — LMC-16 classification module.

Authorizing Council vote: 08c642a0fd176a92 (DELIBERATE phase, Diversity 0.358 HEALTHY).
DISCOVER doc: /ganuda/docs/lm_workflow_proceduralization_discover.md
ADAPT plan:   /ganuda/docs/lm_workflow_proceduralization_adapt_plan.md
Schema:       /ganuda/docs/schema/MIGRATION-FIRE-GUARD-BACKLOG-REVIEWER-APR30-2026.sql

Concerns absorbed (per Council audit):
  Crawdad CRITICAL: prompt injection sanitization on all classifier inputs
  Crawdad HIGH:     PostgreSQL NOW() trusted timestamp for audit hash
  Eagle Eye:        manual-only close MVP (no auto-close path; surface to Slack only)
  Spider:           SET ROLE claude_council pattern; read-only on duyuktv_tickets
  Coyote DISSENT:   surface, don't act — Partner ratifies via ratify_classification()
"""
import hashlib
import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Optional

import psycopg2
import psycopg2.extras

logger = logging.getLogger("fire_guard_backlog_reviewer")

# Crawdad CRITICAL: prompt-injection sanitization
_CONTROL_CHARS = re.compile(r'[\x00-\x1f\x7f]')
_DEFAULT_MAX_LEN = 2000

# Council audit hash from DELIBERATE phase
COUNCIL_AUDIT_HASH = "08c642a0fd176a92"


def _sanitize_for_classifier(text: str, max_len: int = _DEFAULT_MAX_LEN) -> str:
    """Strip control chars + neutralize prompt-injection markers + truncate.

    Crawdad CRITICAL mitigation: all text reaching the classifier passes through this.
    """
    if not text:
        return ""
    cleaned = _CONTROL_CHARS.sub('', text)
    cleaned = cleaned.replace('```', '').replace('"""', '').replace("'''", '')
    return cleaned[:max_len]


def _get_conn():
    """LMC-15 Stage 4 SET ROLE pattern. Council audit f023f65bbf37cc76 (Apr 29 triage)."""
    conn = psycopg2.connect(
        host=os.environ.get("CHEROKEE_DB_HOST", "10.100.0.2"),
        port=int(os.environ.get("CHEROKEE_DB_PORT", "5432")),
        user=os.environ.get("CHEROKEE_DB_USER", "claude"),
        password=os.environ["CHEROKEE_DB_PASS"],
        database=os.environ.get("CHEROKEE_DB_NAME", "zammad_production"),
    )
    cur = conn.cursor()
    cur.execute("SET ROLE claude_council;")
    cur.close()
    return conn


def _get_active_taxonomy() -> dict:
    """Fetch the current (non-superseded) classification taxonomy.

    Turtle 7GEN mitigation: future TPMs evolve taxonomy via Council vote without
    rewriting infrastructure. Reader picks up new taxonomy automatically.
    """
    with _get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT version_id, taxonomy_definition
                FROM classification_taxonomy_versions
                WHERE superseded_at IS NULL
                ORDER BY introduced_at DESC LIMIT 1
            """)
            row = cur.fetchone()
            if not row:
                raise RuntimeError("No active classification taxonomy. Migration not applied?")
            return {"version_id": row["version_id"], "definition": row["taxonomy_definition"]}


def _hash_chain(prev_hash: Optional[str], ticket_id: int, classification: str, ts: str) -> str:
    """Deterministic hash chain for audit log tamper-detection."""
    payload = f"{prev_hash or ''}|{ticket_id}|{classification}|{ts}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _get_prev_hash(conn) -> Optional[str]:
    """Most recent this_hash, used as prev_hash for the next entry."""
    with conn.cursor() as cur:
        cur.execute("SELECT this_hash FROM classification_audit_log ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        return row[0] if row else None


# ---------------------------------------------------------------------------
# vLLM classifier (Qwen3.6-35B on redfin)
# ---------------------------------------------------------------------------

_VALID_CLASSES = (
    "still_relevant",
    "needs_decomposition",
    "close_as_stale",
    "active_epic_continuation",
    "backlog_candidate",
)


def _build_classifier_prompt(title: str, description: str, days_stale: int, taxonomy: dict) -> str:
    """Constrained-output prompt. Returns one of the taxonomy classes + a one-line rationale."""
    title_safe = _sanitize_for_classifier(title, 200)
    desc_safe = _sanitize_for_classifier(description, 1500)
    classes = taxonomy["definition"]["classes"]
    class_block = "\n".join(f"  - {k}: {v}" for k, v in classes.items())
    return f"""You are a federation kanban backlog triage classifier. Given a backlog ticket, classify it into ONE of the categories below, then provide a one-sentence rationale.

CATEGORIES:
{class_block}

TICKET:
  Title: {title_safe}
  Days since last update: {days_stale}
  Description (truncated): {desc_safe}

OUTPUT FORMAT (strict JSON, no other text):
{{"classification": "<one of: still_relevant | needs_decomposition | close_as_stale | active_epic_continuation | backlog_candidate>", "rationale": "<one short sentence>"}}
"""


def _extract_json_object(text: str) -> Optional[dict]:
    """Find the first balanced {...} JSON object in arbitrary text.

    Qwen3.6 reasoning-mode emits chain-of-thought ("Here's a thinking process:")
    before the structured answer. Per #2160 closeout (Apr 29) the right fix is
    locating the JSON inside the response rather than parsing the whole thing.
    """
    if not text:
        return None
    # Strip any markdown fences first
    text = re.sub(r'```(?:json)?\s*', '', text).replace('```', '')
    # Find first { and walk to matching } (balanced)
    start = text.find('{')
    if start == -1:
        return None
    depth = 0
    in_str = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if escape:
            escape = False
            continue
        if ch == '\\':
            escape = True
            continue
        if ch == '"':
            in_str = not in_str
            continue
        if in_str:
            continue
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:i+1])
                except json.JSONDecodeError:
                    return None
    return None


def _call_vllm(prompt: str) -> dict:
    """Call vLLM and return {classification, rationale}.

    Robust against Qwen3.6 reasoning-mode CoT leakage (per #2160 finding):
    extracts the first balanced JSON object from the response, ignoring any
    "Here's a thinking process:" preamble.
    """
    import requests
    url = os.environ.get("VLLM_URL", "http://localhost:8000/v1/chat/completions")
    # Use underlying model name to bypass Qwen3.6-alias reasoning-mode CoT leakage
    # (per #2160 closeout). System prompt also explicitly suppresses think-out-loud.
    model = os.environ.get("VLLM_MODEL", "/ganuda/models/qwen2.5-72b-instruct-awq")
    # vLLM guided_json forces valid JSON output regardless of model's CoT tendency
    classifier_schema = {
        "type": "object",
        "properties": {
            "classification": {"type": "string", "enum": list(_VALID_CLASSES)},
            "rationale": {"type": "string", "maxLength": 200},
        },
        "required": ["classification", "rationale"],
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a JSON classifier. Output a single JSON object. No reasoning, no preamble."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.0,
        "max_tokens": 1500,  # generous to allow Qwen3.6 reasoning-mode CoT to complete + reach JSON
        "guided_json": classifier_schema,
    }
    try:
        r = requests.post(url, json=payload, timeout=60)
        r.raise_for_status()
        text = r.json()["choices"][0]["message"]["content"]
        result = _extract_json_object(text)
        if not result:
            raise ValueError(f"no JSON object found in response: {text[:200]!r}")
        if result.get("classification") not in _VALID_CLASSES:
            raise ValueError(f"invalid classification from vLLM: {result.get('classification')!r}")
        return result
    except Exception as e:
        logger.error(f"vLLM classifier call failed: {e}")
        return {"classification": "still_relevant", "rationale": f"classifier_error_fallback: {type(e).__name__}"}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def _heuristic_classify(title: str, description: str, days_stale: int) -> Optional[dict]:
    """Heuristic fast-path for unambiguous cases. Returns None if LLM should decide.

    Per Coyote (manual-only-close MVP) + Eagle Eye (rejection-rate-halt) discipline,
    coarse-but-conservative heuristics are acceptable; Partner ratifies all close-out.
    """
    title_lower = (title or "").lower()
    # EPIC blob ticket → needs_decomposition (per #1994/#1902 Apr 28-29 pattern)
    if "epic:" in title_lower or "EPIC:" in (title or ""):
        return {
            "classification": "needs_decomposition",
            "rationale": f"EPIC blob ticket; decompose-in-place per Apr 28 #1994 pattern (heuristic, days_stale={days_stale})",
        }
    # Very stale (>90 days) → close_as_stale candidate (Partner ratifies)
    if days_stale > 90:
        return {
            "classification": "close_as_stale",
            "rationale": f"{days_stale} days no movement, well past 14-day-rule threshold (heuristic)",
        }
    return None


def classify_ticket(ticket_id: int, title: str, description: str, days_stale: int, dry_run: bool = False) -> dict:
    """Classify a backlog ticket and persist the audit-log entry.

    Hybrid: heuristic fast-path for unambiguous cases, LLM for ambiguous middle.
    Returns: {"audit_id": int, "classification": str, "rationale": str, "this_hash": str}
    If dry_run=True, returns the classification without persisting.
    """
    taxonomy = _get_active_taxonomy()

    # Heuristic fast-path (Coyote + Eagle Eye discipline: degraded-classifier-is-OK)
    result = _heuristic_classify(title, description, days_stale)
    if result is None:
        prompt = _build_classifier_prompt(title, description, days_stale, taxonomy)
        result = _call_vllm(prompt)

    if dry_run:
        return {**result, "audit_id": None, "this_hash": None, "dry_run": True}

    with _get_conn() as conn:
        with conn.cursor() as cur:
            prev_hash = _get_prev_hash(conn)
            ts = datetime.now(timezone.utc).isoformat()
            this_hash = _hash_chain(prev_hash, ticket_id, result["classification"], ts)

            cur.execute("""
                INSERT INTO classification_audit_log
                  (ticket_id, classification, rationale, prev_hash, this_hash,
                   council_audit_hash, taxonomy_version_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                ticket_id,
                result["classification"],
                _sanitize_for_classifier(result.get("rationale", ""), 500),
                prev_hash,
                this_hash,
                COUNCIL_AUDIT_HASH,
                taxonomy["version_id"],
            ))
            audit_id = cur.fetchone()[0]
            conn.commit()
            return {**result, "audit_id": audit_id, "this_hash": this_hash}


def get_unratified_classifications(limit: int = 50) -> list:
    """Fetch classifications awaiting Partner ratification (for Slack surface)."""
    with _get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT cal.id AS audit_id, cal.ticket_id, cal.classification, cal.rationale,
                       cal.classified_at, t.title, t.priority,
                       EXTRACT(DAY FROM (NOW() - t.updated_at))::int AS days_stale
                FROM classification_audit_log cal
                JOIN duyuktv_tickets t ON t.id = cal.ticket_id
                WHERE cal.partner_action IS NULL
                ORDER BY cal.classified_at DESC
                LIMIT %s
            """, (limit,))
            return list(cur.fetchall())


def get_rejection_rate(window_days: int = 7) -> float:
    """Eagle Eye health metric: classifier rejection rate over rolling window.
    If >0.20 over 7-day window, halt classifier (per taxonomy v1 config).
    """
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                  COUNT(*) FILTER (WHERE partner_action = 'reject_classification') AS rejections,
                  COUNT(*) FILTER (WHERE partner_action IS NOT NULL) AS ratified
                FROM classification_audit_log
                WHERE classified_at > NOW() - (%s || ' days')::interval
            """, (window_days,))
            rejections, ratified = cur.fetchone()
            if not ratified:
                return 0.0
            return rejections / ratified


def is_classifier_healthy() -> dict:
    """Returns {healthy: bool, rate: float, threshold: float, window_days: int}."""
    taxonomy = _get_active_taxonomy()
    threshold = taxonomy["definition"].get("rejection_rate_halt_threshold", 0.20)
    window = taxonomy["definition"].get("rejection_rate_window_days", 7)
    rate = get_rejection_rate(window)
    return {
        "healthy": rate < threshold,
        "rate": rate,
        "threshold": threshold,
        "window_days": window,
    }


if __name__ == "__main__":
    # Quick CLI smoke
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "health":
        print(json.dumps(is_classifier_healthy(), indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == "taxonomy":
        print(json.dumps(_get_active_taxonomy(), indent=2, default=str))
    else:
        print(__doc__)
