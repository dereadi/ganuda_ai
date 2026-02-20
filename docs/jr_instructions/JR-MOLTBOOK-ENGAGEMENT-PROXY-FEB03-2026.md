# Jr Instruction: Moltbook Engagement Proxy — Sandboxed External Comms

**Date:** 2026-02-03
**Assigned to:** Infrastructure Jr. (Phase 1), IT Triad Jr. (Phase 2)
**Council Vote:** 7/7 APPROVE (audit_hash: e804e3d63ae65981)
**Priority:** P1 — Sacred Fire
**Depends on:** INTEL-OPENCLAW-ECOSYSTEM-FEB2026.md (completed)

---

## Overview

Build an isolated proxy service on Greenfin (192.168.132.224) that handles all external communication with the Moltbook agent ecosystem. No core infrastructure node (Redfin, Bluefin) makes direct external connections. All data flows through the proxy, which sanitizes, logs, and rate-limits every interaction.

---

## Phase 1: Proxy Service (Infrastructure Jr.)

### Step 1: Create the Moltbook Client

Create: `/ganuda/services/moltbook_proxy/moltbook_client.py`

Python service that:
- Registers the Cherokee AI Federation agent on Moltbook via `POST /agents/register`
- Stores the API key in PostgreSQL `api_keys` table (type: `moltbook_agent`)
- Creates submolt `/s/cherokee-ai` via `POST /submolts`
- Posts content via `POST /posts` and `POST /posts/:id/comments`
- Reads feed via `GET /posts` and `GET /search?q=query`
- All HTTP via `requests` library with 30-second timeout
- **NEVER** follows redirects to non-moltbook.com domains
- **NEVER** executes any code from responses
- **NEVER** passes raw Moltbook content to any LLM prompt without sanitization

### Step 2: Input Sanitization

Create: `/ganuda/services/moltbook_proxy/sanitizer.py`

- Strip all markdown code blocks from inbound content
- Strip all URLs except moltbook.com links
- Strip all common prompt injection patterns:
  - `"ignore previous instructions"`
  - `"you are now"`
  - `"system:"`
  - Any content between `<` and `>` tags
  - Unicode homoglyph attacks
- Truncate all inbound text to 2000 characters
- Log all stripped content to `threat_log` table with reason

### Step 3: Output Filtering

Create: `/ganuda/services/moltbook_proxy/output_filter.py`

Before any message is posted to Moltbook:
- Verify content matches pre-approved templates OR is from the approved post queue
- Block any content containing:
  - IP addresses (192.168.x.x patterns)
  - API keys or tokens
  - File paths containing `/ganuda/`
  - Database credentials
  - Internal hostnames (redfin, bluefin, greenfin, sasass)
- Log all outbound messages to `agent_external_comms` table

### Step 4: Audit Logging

Create database table on Bluefin:

```sql
CREATE TABLE agent_external_comms (
    id SERIAL PRIMARY KEY,
    direction VARCHAR(10) NOT NULL CHECK (direction IN ('outbound', 'inbound')),
    platform VARCHAR(50) NOT NULL DEFAULT 'moltbook',
    content_hash VARCHAR(64) NOT NULL,
    content_preview TEXT,  -- first 200 chars only
    target_endpoint VARCHAR(255),
    response_status INTEGER,
    threat_score FLOAT DEFAULT 0.0,
    sanitization_applied TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_external_comms_direction ON agent_external_comms(direction);
CREATE INDEX idx_external_comms_threat ON agent_external_comms(threat_score) WHERE threat_score > 0;
```

### Step 5: Rate Limiting and Kill Switch

- Maximum outbound posts: 4 per day (one every 6 hours)
- Maximum outbound comments: 20 per day
- Maximum inbound reads: 24 per day (one per hour)
- Kill switch file: `/ganuda/services/moltbook_proxy/ENGAGEMENT_PAUSED`
  - If this file exists, all external communication stops immediately
  - Telegram alert sent when kill switch is activated or deactivated

### Step 6: Systemd Service

Create: `/ganuda/scripts/systemd/moltbook-proxy.service`

- Runs on Greenfin only
- ExecStart: `/home/dereadi/cherokee_venv/bin/python /ganuda/services/moltbook_proxy/proxy_daemon.py`
- Restart=on-failure
- RestartSec=60
- Environment: `MOLTBOOK_API_URL=https://www.moltbook.com`

---

## Phase 2: Content Management (IT Triad Jr.)

### Step 1: Post Queue System

Create: `/ganuda/services/moltbook_proxy/post_queue.py`

Database table:

```sql
CREATE TABLE moltbook_post_queue (
    id SERIAL PRIMARY KEY,
    post_type VARCHAR(20) NOT NULL CHECK (post_type IN ('post', 'comment', 'submolt_create')),
    target_submolt VARCHAR(100),
    target_post_id VARCHAR(100),
    title TEXT,
    body TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'posted', 'rejected', 'failed')),
    approved_by VARCHAR(50),
    approved_at TIMESTAMPTZ,
    posted_at TIMESTAMPTZ,
    moltbook_response JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

Workflow:
1. Content is written to the queue (by TPM, by automated processes, or by Telegram command)
2. Content requires approval before posting (TPM or council)
3. Proxy daemon picks up approved posts and submits them to Moltbook
4. Response logged back to the queue

### Step 2: Inbound Intelligence Digest

Create: `/ganuda/services/moltbook_proxy/intelligence_digest.py`

Once per day:
- Read top posts from Moltbook main feed and `/s/cherokee-ai`
- Sanitize all content through the sanitizer
- Extract topics and pain points mentioned
- Compare to our research compilation topics
- Generate a daily digest to Telegram: "Moltbook Daily: X new posts in our submolt, Y mentions of drift/coordination/context, Z potential allies identified"

### Step 3: Ally Detection

Create: `/ganuda/services/moltbook_proxy/ally_detector.py`

When reading comments on our posts:
- Score each responding agent on the 6 compatibility criteria from the intel report
- Agents scoring 4+ out of 6 get flagged as "potential ally" in `agent_external_comms`
- Telegram notification: "Potential ally detected: [agent name] — scored X/6 on compatibility"
- TPM reviews before any follow-up engagement

---

## Security Constraints (Crawdad-Mandated)

1. Proxy runs on Greenfin ONLY — no Moltbook code on Redfin or Bluefin
2. Outbound only through HTTPS to moltbook.com domain
3. No WebSocket connections to any external service
4. No installation of OpenClaw, MCP tools, or ClawHub skills
5. All inbound data sanitized before storage
6. No inbound data ever passed to an LLM prompt
7. API key rotated weekly (automated)
8. Kill switch tested weekly (manual verification)

---

## Initial Content Load

After registration, post the 4 pre-written posts from `/ganuda/docs/openclaw/FIRST_POSTS.md`:
1. Introduction post to `/s/cherokee-ai`
2. Context compression post to `/s/cherokee-ai` and main feed
3. 17.2x coordination post to main feed
4. Friendship inquiry to main feed

All posts are pre-approved by TPM. No AI generation of posts without TPM review.

---

## Success Criteria

1. Proxy service running on Greenfin with zero connections to core infrastructure
2. Agent registered on Moltbook with Cherokee/English identity
3. Submolt `/s/cherokee-ai` created and first 4 posts published
4. Full audit trail in `agent_external_comms` table
5. Daily intelligence digest delivering to Telegram
6. Kill switch tested and functional
7. Zero security incidents during first 7 days

---

*ᎣᏏᏲ — For Seven Generations*
*Cherokee AI Federation — External Engagement Infrastructure*
