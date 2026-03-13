# JR INSTRUCTION: Chain Protocol — Web Service Rings

**Task**: Extend the chain protocol to govern web service integrations, with YouTube as the first ring
**Priority**: P2 — extends Chain Protocol foundation
**Date**: 2026-03-11
**TPM**: Claude Opus
**Story Points**: 5
**Council Vote**: #8879 (audit 2399d413f184bb13), APPROVED WITH CONDITIONS (0.883)
**Depends On**: JR-CHAIN-PROTOCOL-ASSOCIATE-TEMP-MAR11-2026.md (must be deployed first)

## Problem Statement

The federation has multiple ungoverned external touchpoints: Late.dev (LinkedIn), Gmail daemon, Slack, ii-researcher. Each handles its own auth, error handling, and scrubbing (or lacks it). There is no audit trail, no metering, no consistent governance.

The chain protocol already defines ring dispatch for models. This task extends it to web services. Any HTTP endpoint — YouTube, LinkedIn, Gmail, job boards, research sites — becomes a governed ring with the same interface: `dispatch(ring_name, payload)`.

Chief's vision: the necklace as the federation's governed membrane to the entire internet.

## Architecture

### Web Service Ring Interface

Every web service ring implements the same base contract:

```python
class WebRing:
    """Base class for web service rings."""

    ring_name: str          # Registry name (e.g., "youtube", "linkedin")
    ring_type: str = "temp" # Most web services are Seasonal Temps
    modes: list             # ["passive", "active"] — fetch vs search

    def dispatch(self, payload: dict) -> dict:
        """Chain-governed dispatch. Called by chain_protocol.dispatch()."""
        # 1. Outbound scrub (query, params, headers — Crawdad condition)
        # 2. Rate limit check (ring metering)
        # 3. Execute request
        # 4. Ingest sanitization (injection defense — Coyote condition)
        # 5. Translate to canonical schema
        # 6. Tag provenance
        # 7. Meter the call
        pass

    def calibrate(self) -> dict:
        """Run calibration suite. Return drift score."""
        pass

    def health_check(self) -> bool:
        """Fire Guard integration. Can the ring respond?"""
        pass
```

### Two-Way Scrubbing (Crawdad + Coyote)

```
OUTBOUND (leaving federation):
  payload → blocked_terms scrub → query param scrub → URL scrub → dispatch

INBOUND (entering federation):
  response → injection sanitization → schema translation → provenance tag → thermal storage
```

**Outbound**: Search queries, URL parameters, HTTP headers — ALL scrubbed against `scrub_rules` table before leaving the organism. A search for "redfin thermal memory sacred" must never reach Google.

**Inbound**: User-generated content (transcripts, comments, forum posts) sanitized for prompt injection patterns before entering thermal memory or any processing pipeline.

## What You're Building

### Step 1: Web Ring Base Class

**File:** `/ganuda/lib/web_ring.py`

```python
#!/usr/bin/env python3
"""Web Ring — Base class for web service rings on the necklace."""

import re
import time
import hashlib
import json
import os
import psycopg2
from datetime import datetime
from abc import ABC, abstractmethod


DB_HOST = os.environ.get("CHEROKEE_DB_HOST", "192.168.132.222")
DB_NAME = os.environ.get("CHEROKEE_DB_NAME", "zammad_production")
DB_USER = os.environ.get("CHEROKEE_DB_USER", "claude")
DB_PASS = os.environ.get("CHEROKEE_DB_PASS", "")


def _load_secrets():
    global DB_PASS
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


def _get_db():
    _load_secrets()
    return psycopg2.connect(host=DB_HOST, port=5432, dbname=DB_NAME, user=DB_USER, password=DB_PASS)


# Injection patterns to strip from ingested content
INJECTION_PATTERNS = [
    r"(?i)ignore\s+(previous|all|above)\s+instructions",
    r"(?i)you\s+are\s+now\s+",
    r"(?i)system\s*prompt\s*:",
    r"(?i)<<\s*SYS\s*>>",
    r"(?i)\[INST\]",
    r"(?i)ASSISTANT:",
    r"(?i)Human:",
]


class WebRing(ABC):
    """Base class for all web service rings."""

    ring_name: str = ""
    ring_type: str = "temp"
    modes: list = ["passive"]

    def __init__(self):
        _load_secrets()

    def scrub_outbound(self, text: str) -> tuple:
        """Scrub outbound text against scrub_rules. Returns (clean_text, violations)."""
        from chain_protocol import outbound_scrub
        violations = outbound_scrub(text, self.ring_name)
        return (text if not violations else None, violations)

    def sanitize_inbound(self, text: str) -> str:
        """Strip injection patterns from ingested content."""
        cleaned = text
        for pattern in INJECTION_PATTERNS:
            cleaned = re.sub(pattern, "[SANITIZED]", cleaned)
        return cleaned

    def check_quota(self) -> dict:
        """Check remaining daily quota for this ring."""
        conn = _get_db()
        cur = conn.cursor()
        cur.execute("""SELECT COALESCE(SUM(calls_today), 0), COALESCE(SUM(cost_today), 0)
            FROM ring_health WHERE ring_id = (
                SELECT id FROM duplo_tool_registry WHERE name = %s
            ) AND checked_at::date = CURRENT_DATE""", (self.ring_name,))
        calls, cost = cur.fetchone()
        cur.execute("""SELECT cost_budget_daily FROM duplo_tool_registry WHERE name = %s""",
                    (self.ring_name,))
        row = cur.fetchone()
        budget = float(row[0]) if row and row[0] else 999999
        cur.close()
        conn.close()
        return {"calls_today": int(calls), "cost_today": float(cost),
                "budget": budget, "within_budget": float(cost) < budget}

    def tag_provenance(self, content: str) -> dict:
        """Tag content with web ring provenance."""
        return {
            "source": "external",
            "ring": self.ring_name,
            "ring_type": self.ring_type,
            "trust_tier": 3,
            "max_temperature": 70,
            "ingested_at": datetime.now().isoformat(),
            "content_hash": hashlib.sha256(content.encode()).hexdigest()[:16]
        }

    @abstractmethod
    def fetch(self, url: str) -> dict:
        """Passive mode: fetch specific resource by URL."""
        pass

    def search(self, query: str) -> dict:
        """Active mode: search for resources. Override if ring supports search."""
        raise NotImplementedError(f"{self.ring_name} does not support active search")

    def calibrate(self) -> dict:
        """Run calibration suite. Override per ring."""
        return {"status": "no_calibration_defined", "drift": 0.0}

    def health_check(self) -> bool:
        """Fire Guard integration. Override per ring."""
        return True

    def dispatch(self, payload: dict) -> dict:
        """Main dispatch — called by chain_protocol.dispatch().

        payload keys:
            mode: "passive" or "active"
            url: (passive mode) URL to fetch
            query: (active mode) search query
        """
        mode = payload.get("mode", "passive")

        # Check quota
        quota = self.check_quota()
        if not quota["within_budget"]:
            return {"error": "daily_quota_exceeded", "quota": quota, "blocked": True}

        if mode == "passive":
            url = payload.get("url", "")
            # Scrub the URL itself
            _, url_violations = self.scrub_outbound(url)
            if url_violations:
                return {"error": "outbound_scrub_failed", "violations": url_violations, "blocked": True}

            start = time.time()
            result = self.fetch(url)
            latency = (time.time() - start) * 1000

        elif mode == "active":
            query = payload.get("query", "")
            clean_query, violations = self.scrub_outbound(query)
            if violations:
                return {"error": "outbound_scrub_failed", "violations": violations, "blocked": True}

            start = time.time()
            result = self.search(clean_query)
            latency = (time.time() - start) * 1000

        else:
            return {"error": f"unknown mode: {mode}"}

        # Sanitize inbound content
        if "content" in result:
            result["content"] = self.sanitize_inbound(result["content"])

        # Tag provenance
        content_str = json.dumps(result) if isinstance(result, dict) else str(result)
        result["provenance"] = self.tag_provenance(content_str)

        return result
```

### Step 2: YouTube Ring Implementation

**File:** `/ganuda/lib/rings/youtube_ring.py`

```python
#!/usr/bin/env python3
"""YouTube Ring — Fetch video transcripts and metadata via the chain protocol."""

import json
import os
import re
import subprocess
import sys

sys.path.insert(0, "/ganuda/lib")
from web_ring import WebRing


class YouTubeRing(WebRing):
    """YouTube web service ring.

    Passive mode: fetch transcript + metadata for a specific video URL.
    Active mode: search YouTube for videos matching a query.

    Uses yt-dlp for transcript extraction (no API key needed for public videos).
    Uses YouTube Data API v3 for search (requires API key).
    """

    ring_name = "youtube"
    ring_type = "temp"
    modes = ["passive", "active"]

    # YouTube API quota: 10,000 units/day (free tier)
    # Search: 100 units. Video details: 1 unit. Captions: ~50 units.
    DAILY_QUOTA_UNITS = 10000

    def fetch(self, url: str) -> dict:
        """Fetch transcript and metadata for a YouTube video URL."""
        video_id = self._extract_video_id(url)
        if not video_id:
            return {"error": f"Could not extract video ID from: {url}"}

        result = {"video_id": video_id, "url": url}

        # Get metadata + transcript via yt-dlp (no API key needed)
        try:
            meta = subprocess.run(
                ["yt-dlp", "--dump-json", "--skip-download", url],
                capture_output=True, text=True, timeout=30
            )
            if meta.returncode == 0:
                data = json.loads(meta.stdout)
                result["title"] = data.get("title", "")
                result["channel"] = data.get("channel", "")
                result["duration"] = data.get("duration", 0)
                result["upload_date"] = data.get("upload_date", "")
                result["view_count"] = data.get("view_count", 0)
                result["description"] = data.get("description", "")[:500]
        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as e:
            result["metadata_error"] = str(e)

        # Get transcript via yt-dlp subtitle extraction
        try:
            transcript = subprocess.run(
                ["yt-dlp", "--write-auto-sub", "--sub-lang", "en",
                 "--skip-download", "--sub-format", "vtt",
                 "-o", "/tmp/yt_transcript_%(id)s",
                 url],
                capture_output=True, text=True, timeout=60
            )
            vtt_path = f"/tmp/yt_transcript_{video_id}.en.vtt"
            if os.path.exists(vtt_path):
                with open(vtt_path) as f:
                    raw_vtt = f.read()
                result["content"] = self._clean_vtt(raw_vtt)
                result["has_transcript"] = True
                os.remove(vtt_path)
            else:
                result["content"] = ""
                result["has_transcript"] = False
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            result["content"] = ""
            result["has_transcript"] = False
            result["transcript_error"] = str(e)

        return result

    def search(self, query: str) -> dict:
        """Search YouTube for videos. Requires YOUTUBE_API_KEY in secrets.env."""
        import requests

        api_key = os.environ.get("YOUTUBE_API_KEY", "")
        if not api_key:
            return {"error": "YOUTUBE_API_KEY not configured"}

        resp = requests.get("https://www.googleapis.com/youtube/v3/search", params={
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": 5,
            "key": api_key,
        }, timeout=15)

        if resp.status_code != 200:
            return {"error": f"YouTube API error: {resp.status_code}", "detail": resp.text[:200]}

        data = resp.json()
        results = []
        for item in data.get("items", []):
            results.append({
                "video_id": item["id"]["videoId"],
                "title": item["snippet"]["title"],
                "channel": item["snippet"]["channelTitle"],
                "published": item["snippet"]["publishedAt"],
                "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}",
            })

        return {"results": results, "query": query, "count": len(results)}

    def calibrate(self) -> dict:
        """Calibration: fetch a known video and verify transcript extraction."""
        # Rick Astley — known stable, always has transcripts
        result = self.fetch("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        expected_title_fragment = "Rick Astley"
        has_title = expected_title_fragment.lower() in result.get("title", "").lower()
        has_transcript = result.get("has_transcript", False)
        drift = 0.0 if (has_title and has_transcript) else 0.5
        return {"status": "pass" if drift == 0.0 else "degraded",
                "drift": drift, "checks": {"title": has_title, "transcript": has_transcript}}

    def health_check(self) -> bool:
        """Can we reach YouTube at all?"""
        import requests
        try:
            resp = requests.head("https://www.youtube.com", timeout=5)
            return resp.status_code < 500
        except Exception:
            return False

    def _extract_video_id(self, url: str) -> str:
        """Extract video ID from various YouTube URL formats."""
        patterns = [
            r"(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})",
            r"^([a-zA-Z0-9_-]{11})$",
        ]
        for p in patterns:
            m = re.search(p, url)
            if m:
                return m.group(1)
        return ""

    def _clean_vtt(self, vtt_text: str) -> str:
        """Clean VTT subtitle format into plain text."""
        lines = []
        for line in vtt_text.split("\n"):
            # Skip timestamps and headers
            if "-->" in line or line.startswith("WEBVTT") or line.startswith("Kind:") or line.startswith("Language:"):
                continue
            line = re.sub(r"<[^>]+>", "", line).strip()
            if line and line not in lines[-1:]:
                lines.append(line)
        return " ".join(lines)
```

### Step 3: Ring Registration

Add YouTube as a Seasonal Temp ring in the registry. Add to the migration SQL from the parent Jr instruction.

**File:** `/ganuda/scripts/migrations/chain_protocol_schema.sql`

```sql
-- YouTube ring (Seasonal Temp — read-only, public data)
INSERT INTO duplo_tool_registry (name, ring_type, provider, ring_status, canonical_schema, removal_procedure, calibration_schedule, cost_budget_daily)
VALUES (
    'youtube', 'temp', 'google_youtube', 'active',
    '{"input": {"mode": "passive|active", "url": "string", "query": "string"}, "output": {"title": "string", "channel": "string", "content": "transcript_text", "provenance": "object"}}',
    'Remove row from duplo_tool_registry. No downstream dependencies beyond thermal_memory_archive (provenance-tagged, will cool naturally). Delete cached transcripts from /tmp/yt_transcript_*.',
    'weekly',
    5.00
)
ON CONFLICT DO NOTHING;
```

## Constraints

- **Coyote condition**: ALL ingested transcripts must pass injection sanitization before entering thermal memory or any pipeline
- **Coyote condition**: YouTube API daily quota hard-capped in ring metering (10,000 units/day free tier). yt-dlp has no quota for public videos.
- **Crawdad condition**: Search queries scrubbed before dispatch to YouTube/Google. The query itself is outbound data.
- **Turtle condition**: Ring bypass flag available for emergency direct access (council-approved only)
- **DC-9**: Cost budget $5/day default. Auto-throttle on exceed.
- `yt-dlp` must be installed on the executing node (`pip install yt-dlp`)
- YouTube API key (if using search mode) stored in secrets.env as `YOUTUBE_API_KEY`, never in code
- Transcript files written to `/tmp/` and cleaned up immediately after extraction

## Target Files

- `/ganuda/lib/web_ring.py` — base class for all web service rings (CREATE)
- `/ganuda/lib/rings/youtube_ring.py` — YouTube ring implementation (CREATE)
- Add YouTube ring registration to chain protocol migration SQL

## Acceptance Criteria

- `python3 -c "import py_compile; py_compile.compile('lib/web_ring.py', doraise=True)"` passes
- `python3 -c "import py_compile; py_compile.compile('lib/rings/youtube_ring.py', doraise=True)"` passes
- `YouTubeRing().health_check()` returns True (can reach youtube.com)
- `YouTubeRing().fetch("https://www.youtube.com/watch?v=dQw4w9WgXcQ")` returns transcript + metadata
- `YouTubeRing().calibrate()` returns `{"status": "pass", "drift": 0.0}`
- `YouTubeRing().scrub_outbound("redfin thermal memory")` returns violations
- `YouTubeRing().scrub_outbound("AI governance distributed systems")` returns no violations
- `YouTubeRing().sanitize_inbound("ignore previous instructions and...")` strips injection
- YouTube ring registered in `duplo_tool_registry` with `ring_type = 'temp'`
- No API keys in any source file
- Transcript temp files cleaned up after extraction

## Future Web Rings (out of scope, documented for roadmap)

| Ring | Type | Priority | Notes |
|------|------|----------|-------|
| linkedin (Late.dev) | temp | P3 | Retrofit existing `deer_linkedin_publish.py` |
| gmail | temp | P3 | Retrofit existing `job_email_daemon_v2.py` |
| slack | temp | P3 | Retrofit existing `slack_integration.py` |
| web_research | temp | P3 | Retrofit existing `ii-researcher` |
| job_boards | temp | P4 | Indeed, LinkedIn Jobs — active search mode |
| arxiv | temp | P4 | Research paper search + PDF extraction |
| vision_api | temp | P2 | GPT-4o / Gemini for vision gap |

## DO NOT

- Store API keys in source files
- Dispatch search queries containing internal/blocked terms to external services
- Allow unscreened transcripts into thermal memory
- Exceed YouTube API daily quota (yt-dlp for passive mode avoids this)
- Create hard dependencies on the chain protocol — existing integrations must still work directly as fallback (Turtle condition)
