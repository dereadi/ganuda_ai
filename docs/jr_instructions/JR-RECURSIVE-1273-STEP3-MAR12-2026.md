# [RECURSIVE] Chain Protocol: Web Service Rings + YouTube First Ring - Step 3

**Parent Task**: #1273
**Auto-decomposed**: 2026-03-12T18:03:53.181988
**Original Step Title**: Ring Registration

---

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
