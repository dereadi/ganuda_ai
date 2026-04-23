"""Shared helpers for TPM Claude Code hooks.

Injects context from BOTH dimensions of Ganuda memory:
  - Thermal (significance axis): pgvector + temperature scoring on bluefin
  - Crawdad (temporal axis): filesystem mtime-reverse walk

Both dimensions are required per `project_crawdad_thermal_architecture_nov2025`.
"""

import datetime
import json
import os
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path

EMBEDDING_SERVICE_URL = os.environ.get(
    "GANUDA_EMBEDDING_URL",
    "http://192.168.132.224:8003",
)

# Crawdad roots — walked mtime-reverse on each invocation
CRAWDAD_ROOTS = [
    "/ganuda/docs/kb",
    "/ganuda/docs/jr_instructions",
    "/ganuda/docs/longhouse",
    "/ganuda/docs",
    "/home/dereadi/.claude/projects/-ganuda/memory",
]

LOG_DIR = "/ganuda/logs/tpm_hooks"

# Stopwords — unhelpful for keyword extraction
_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "if", "then", "else", "for", "to",
    "of", "in", "on", "at", "by", "with", "from", "is", "are", "was", "were",
    "be", "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "should", "could", "may", "might", "must", "shall", "can", "this",
    "that", "these", "those", "i", "you", "he", "she", "it", "we", "they",
    "me", "us", "them", "my", "your", "his", "her", "its", "our", "their",
    "let", "lets", "like", "just", "so", "about", "what", "how", "why",
    "when", "where", "which", "who", "whom", "whose", "some", "any",
}


def extract_keywords(text, limit=6):
    """Extract simple keyword tokens for filesystem matching.

    Not semantic — just tokens worth grep-testing against filenames and
    first few KB of file content.
    """
    if not text:
        return []
    # Tokens: 3+ alphanum characters, preserve case-bearing words
    tokens = re.findall(r"\b[A-Za-z][A-Za-z0-9_-]{2,}\b", text)
    seen = []
    seen_lower = set()
    for t in tokens:
        t_low = t.lower()
        if t_low in _STOPWORDS:
            continue
        if t_low in seen_lower:
            continue
        seen.append(t)
        seen_lower.add(t_low)
        if len(seen) >= limit:
            break
    return seen


def search_thermal(query, limit=3, threshold=0.5, timeout=5):
    """Semantic search via embedding service (/v1/search).

    Returns list of {id, similarity, content, metadata} dicts.
    Empty list on any failure — hooks must NEVER block the user turn.
    """
    if not query:
        return []
    try:
        payload = json.dumps({
            "query": query[:500],
            "limit": limit,
            "threshold": threshold,
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{EMBEDDING_SERVICE_URL}/v1/search",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8")) or []
    except (urllib.error.URLError, OSError, json.JSONDecodeError) as exc:
        print(f"TPM hook: thermal search failed ({exc})", file=sys.stderr)
        return []


def crawdad_walk(keywords, hours=168, limit=3, roots=None, content_bytes=2048):
    """Filesystem mtime-reverse walk (the crawdad move).

    Returns list of dicts: {path, mtime_age_h, snippet, score}.
    Score = number of keyword hits in filename + content preview.
    """
    roots = roots or CRAWDAD_ROOTS
    now = datetime.datetime.now().timestamp()
    cutoff = now - (hours * 3600)

    # Lowercased keywords for matching
    kw_low = [k.lower() for k in (keywords or []) if len(k) >= 3]

    candidates = []
    for root in roots:
        root_path = Path(root)
        if not root_path.exists():
            continue
        try:
            for p in root_path.rglob("*"):
                if not p.is_file():
                    continue
                try:
                    mt = p.stat().st_mtime
                except OSError:
                    continue
                if mt < cutoff:
                    continue
                # Read small preview for keyword scoring + snippet
                try:
                    with open(p, "rb") as f:
                        raw = f.read(content_bytes)
                    preview = raw.decode("utf-8", errors="ignore")
                except OSError:
                    preview = ""
                name_low = p.name.lower()
                preview_low = preview.lower()
                score = 0
                for k in kw_low:
                    if k in name_low:
                        score += 2  # filename hit weighted higher
                    if k in preview_low:
                        score += 1
                # When no keywords, score=0 → take most-recent regardless
                candidates.append({
                    "path": str(p),
                    "mtime": mt,
                    "mtime_age_h": round((now - mt) / 3600, 1),
                    "preview": preview[:240].replace("\n", " "),
                    "score": score,
                })
        except (OSError, PermissionError):
            continue

    # Rank: keyword-hits DESC, then mtime DESC (most recent first)
    candidates.sort(key=lambda c: (-c["score"], -c["mtime"]))
    # If we have keywords, require at least score>0. If no keywords (SessionStart
    # has no specific query), fall back to most-recent regardless of score.
    if kw_low:
        filtered = [c for c in candidates if c["score"] > 0]
        return filtered[:limit]
    return candidates[:limit]


def format_thermal_line(i, m):
    """Single-line compact representation of a thermal hit."""
    sim = m.get("similarity", 0.0)
    content = (m.get("content") or "").replace("\n", " ")
    meta = m.get("metadata") or {}
    temp = meta.get("temperature_score") or meta.get("temperature") or ""
    sacred = " SACRED" if meta.get("sacred_pattern") else ""
    tag = f" temp={temp}" if temp != "" else ""
    return f"  {i}. [thermal|{sim:.2f}{tag}{sacred}] {content[:240]}"


def format_crawdad_line(i, c):
    """Single-line compact representation of a crawdad hit."""
    age = c.get("mtime_age_h", 0)
    age_label = f"{age}h" if age < 48 else f"{round(age/24, 1)}d"
    path = c.get("path", "")
    # Trim path to last 2 segments for readability
    short_path = "/".join(path.rsplit("/", 3)[-3:])
    preview = (c.get("preview") or "").strip()[:180]
    return f"  {i}. [crawdad|age={age_label}|score={c.get('score',0)}] {short_path} — {preview}"


def log_invocation(hook_name, data):
    """Append a telemetry row. Failures swallowed — never break the turn."""
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        path = os.path.join(LOG_DIR, f"{hook_name}.log")
        with open(path, "a", encoding="utf-8") as f:
            row = {
                "ts": datetime.datetime.now().isoformat(timespec="seconds"),
                **data,
            }
            f.write(json.dumps(row) + "\n")
    except OSError:
        pass


_otel_counter = None
_otel_hist_chars = None


def emit_otel(hook_name, injected_chars, thermal_hits, crawdad_hits, latency_ms):
    """Best-effort OTel emission. Silently no-op if opentelemetry unavailable.

    Eagle Eye's observability ask (Apr 22 2026 Council) — baked in from day one.
    """
    global _otel_counter, _otel_hist_chars
    try:
        if _otel_counter is None:
            from opentelemetry import metrics
            meter = metrics.get_meter("ganuda.tpm_hooks")
            _otel_counter = meter.create_counter(
                "ganuda.tpm_hooks.invocations",
                description="TPM hook fires per event type",
            )
            _otel_hist_chars = meter.create_histogram(
                "ganuda.tpm_hooks.injected_chars",
                description="Chars injected by TPM hooks per fire",
                unit="chars",
            )
        attrs = {
            "hook_name": hook_name,
            "thermal_hits": int(thermal_hits),
            "crawdad_hits": int(crawdad_hits),
        }
        _otel_counter.add(1, attributes=attrs)
        _otel_hist_chars.record(int(injected_chars or 0), attributes=attrs)
    except Exception:
        pass
