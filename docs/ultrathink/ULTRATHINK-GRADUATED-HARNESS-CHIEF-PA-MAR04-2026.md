# ULTRATHINK: Graduated Harness Tiers + Chief Personal Assistant

**Date**: March 4, 2026
**Phase**: ADAPT (Long Man Methodology)
**Author**: TPM (Claude Opus 4.6)
**Council Vote**: #2c2fa88a53817307 (APPROVED)
**Longhouse Session**: #b940f09b18605c97 (UNANIMOUS, 14 voices)
**Sacred Thermal**: #119134
**Spec IDs**: d1e2e5f9a879ff3b2606dae87f3a34f0 (Chief PA), afb50b8ea12864cffdc7d9f17cf33072 (Harness Tiers)
**River Cycle**: RC-2026-03A

---

## Executive Summary

The Cherokee AI Federation needs two interlocked capabilities:

1. **Graduated Harness Tiers** -- A three-tier inference architecture that matches response sophistication to query stakes, with automatic escalation. Tier 1 (Reflex) is commodity-fast (~50ms, single LLM call). Tier 2 (Deliberation) is differentiated (~500ms, 2-3 specialists). Tier 3 (Council) is the moat (~30-120s, full ethos with sacred patterns and thermal memory). Users never choose tiers; the system self-escalates based on confidence and stakes detection (DC-6 Gradient Principle).

2. **Chief Personal Assistant (MVP)** -- A featherweight daemon on bmasass (M4 Max 128GB, macOS) that proactively surfaces calendar, email, and cluster activity to the Chief via Slack. The PA is the alpha/beta reference implementation that exercises all three harness tiers dynamically. It proves the architecture works before we sell it.

The Longhouse ratified this unanimously -- 14 voices including Coyote's full consent. That does not happen often. The design constraints (DC-5, DC-6, DC-7) apply constitutionally. Tier 3 topology is fixed star (Thermal #82856).

---

## Architecture Diagram

```
                          CHIEF'S ATTENTION SURFACE
                          =========================

    +------------------+     Slack Webhook      +------------------+
    |   Slack (Push)   | <--------------------- |   PA Daemon      |
    +------------------+                        |   (bmasass)      |
                                                |                  |
    +------------------+                        |  - Calendar Poll |
    | Google Calendar  | ----OAuth2 API-------> |  - Email Wire    |
    +------------------+                        |  - Briefing Gen  |
                                                |  - Harness Client|
    +------------------+                        +--------+---------+
    | gmail_api_daemon | --classification meta-->         |
    | (redfin)         |                                  |
    +------------------+                                  |
                                                          |
                    GRADUATED HARNESS TIERS                |
                    ======================                |
                                                          v
    +-----------------------------------------------------+--------+
    |                    HARNESS API                                 |
    |              POST /harness/query                              |
    |  (redfin gateway:8080 or standalone FastAPI)                  |
    +-------+------------------+------------------+-----------------+
            |                  |                  |
            v                  v                  v
    +-------+------+  +-------+-------+  +-------+---------+
    | TIER 1       |  | TIER 2        |  | TIER 3          |
    | REFLEX       |  | DELIBERATION  |  | COUNCIL         |
    | ~50ms        |  | ~500ms        |  | ~30-120s        |
    |              |  |               |  |                  |
    | Single LLM   |  | 2-3 Specialists| | All 7+ Specialists|
    | Config-driven |  | Quick consensus| | Full ethos       |
    | No federation |  | Majority vote | | Two Wolves       |
    | Fallback model|  | Diversity score| | Sacred patterns  |
    +--------------+  +-------+-------+  | Thermal memory   |
                              |          +-------+----------+
                              |                  |
            FEDERATION INFRASTRUCTURE            |
            =========================            |
                              |                  |
    +----------+    +---------+--+    +----------+------+
    | redfin   |    | bluefin    |    | greenfin        |
    | vLLM:8000|    | PG:5432    |    | Embedding:8003  |
    | Gateway  |    | Thermal Mem|    | BGE-large 1024d |
    | :8080    |    | Council    |    |                 |
    |          |    | Votes      |    |                 |
    +----------+    +------------+    +-----------------+

    +----------+
    | bmasass  |    <-- PA daemon lives HERE
    | MLX:8800 |    <-- DeepSeek-R1 for reasoning (used by gateway)
    | Tailscale|    <-- 100.103.27.106 (primary until WG Phase 2)
    +----------+

    ESCALATION FLOW:
    ================
    Request -> Tier 1 -> confidence >= 0.7? -> Return
                      -> confidence < 0.7?  -> Tier 2 -> confidence >= 0.6 AND stakes=low? -> Return
                                                      -> confidence < 0.6 OR stakes=high?  -> Tier 3 -> Return
```

---

## Tier Definitions with Interfaces

### Tier 1: REFLEX

**Purpose**: Fast, cheap, good-enough answers for straightforward queries.
**Latency target**: <50ms p95.
**Model**: Single LLM call to redfin vLLM:8000 (Qwen2.5-72B-AWQ) via gateway.
**Fallback**: If federation unreachable, use cached response templates or local lightweight model.
**No federation dependencies**: Self-contained by design (Spider requirement).
**Input validation**: Every request validated before processing (Crawdad requirement).

```python
# Interface
class Tier1Reflex:
    def query(self, request: HarnessRequest) -> HarnessResponse:
        """Single LLM call with config-driven prompt template."""
        # 1. Validate input (Crawdad)
        # 2. Select prompt template from config
        # 3. Single inference call
        # 4. Score confidence
        # 5. Return response with confidence + tier metadata
```

**Config-driven means**: Prompt templates, model endpoints, temperature, max_tokens -- all in YAML. No specialist logic. Swapping the model requires changing one config value.

### Tier 2: DELIBERATION

**Purpose**: Quick multi-perspective synthesis for queries that need more than a single viewpoint.
**Latency target**: <500ms p95.
**Specialists**: 2-3 selected by domain affinity (e.g., Medicine Woman + Turtle for health claims).
**Consensus**: Majority vote (not full quorum). Simple aggregation, not the full Two Wolves pipeline.
**Dependencies**: Thermal memory (bluefin:5432), vLLM (redfin:8000), embedding (greenfin:8003).
**Diversity scoring**: Every response includes diversity metadata (Elisi requirement).

```python
# Interface
class Tier2Deliberation:
    def query(self, request: HarnessRequest, tier1_context: Optional[dict] = None) -> HarnessResponse:
        """2-3 specialist quick consensus."""
        # 1. Select 2-3 specialists by domain
        # 2. Parallel invocation (async)
        # 3. Majority vote aggregation
        # 4. Diversity score
        # 5. Confidence score from agreement level
        # 6. Return with tier1_context preserved if escalated
```

### Tier 3: COUNCIL

**Purpose**: Full ethos invocation for high-stakes, complex, or ambiguous queries.
**Latency target**: <120s p95.
**Specialists**: All 7+ (Bear, Eagle, Spider, Crawdad, Owl, Raven, Turtle + any active Outer Council).
**Topology**: Fixed star (constitutional, Thermal #82856). Cannot be changed without seven-gen review.
**Features**: Two Wolves routing manifest, sacred pattern access, thermal memory integration, full metacognition.
**Wiring**: Routes through existing specialist_council.py and gateway. Mostly wiring, not new logic.

```python
# Interface
class Tier3Council:
    def query(self, request: HarnessRequest, escalation_context: Optional[dict] = None) -> HarnessResponse:
        """Full council deliberation with ethos."""
        # 1. Invoke specialist_council.py full pipeline
        # 2. Two Wolves routing manifest
        # 3. Sacred pattern matching from thermal memory
        # 4. Council vote with metacognition
        # 5. Return with full audit trail
```

### Unified Request/Response Models

```python
@dataclass
class HarnessRequest:
    query: str
    context: dict                    # Arbitrary context (calendar data, email metadata, etc.)
    user_id: str                     # For personalization (Deer requirement)
    session_id: str                  # For conversation continuity
    force_tier: Optional[int] = None # Only for testing -- production NEVER sets this

@dataclass
class HarnessResponse:
    answer: str
    tier_used: int                   # 1, 2, or 3
    confidence: float                # 0.0 - 1.0
    escalation_path: List[int]       # e.g., [1, 2] if escalated from Tier 1 to Tier 2
    latency_ms: float
    diversity_score: Optional[float] # Only Tier 2+
    council_vote_id: Optional[str]   # Only Tier 3
    metadata: dict                   # Tier-specific metadata
```

---

## Escalation Logic Pseudocode

```
function handle_request(request):
    # TIER 1: REFLEX
    response_1 = tier1.query(request)

    if response_1.confidence >= TIER1_CONFIDENCE_THRESHOLD (0.7):
        return response_1

    # TIER 2: DELIBERATION
    # Seamless context transfer (Jr requirement)
    response_2 = tier2.query(request, tier1_context=response_1.metadata)

    stakes = detect_stakes(request, response_2)

    if response_2.confidence >= TIER2_CONFIDENCE_THRESHOLD (0.6) AND stakes != HIGH:
        response_2.escalation_path = [1, 2]
        return response_2

    # TIER 3: COUNCIL
    escalation_context = {
        "tier1_response": response_1.metadata,
        "tier2_response": response_2.metadata,
        "escalation_reason": "low_confidence" if response_2.confidence < 0.6 else "high_stakes"
    }
    response_3 = tier3.query(request, escalation_context=escalation_context)
    response_3.escalation_path = [1, 2, 3]

    # Audit trail in thermal memory
    store_escalation_thermal(request, response_3)

    return response_3

function detect_stakes(request, response):
    # Heuristic-based stakes detection
    # High-stakes indicators:
    #   - Keywords: "VA claim", "disability", "legal", "medical", "financial"
    #   - User history: previous Tier 3 queries on same topic
    #   - Specialist disagreement in Tier 2 (low agreement = uncertain = high stakes)
    #   - Confidence drop between Tier 1 and Tier 2
    #
    # Coyote rule: humans underestimate stakes.
    # When in doubt, escalate. Cost of over-escalation < cost of under-escalation.
```

**De-escalation**: NOT supported in v1. Once a request escalates, it stays at the higher tier for that request lifecycle. This is intentional -- de-escalation introduces complexity and potential for information loss. Revisit in v2 after observing real escalation patterns.

---

## Chief PA Component Breakdown

### 1. pa_daemon.py -- Main Daemon (8 story points)
- **Runtime**: Python 3.11+ on bmasass (macOS), managed by launchd
- **Event loop**: asyncio-based. Polls calendar (5 min), checks email queue (2 min), generates briefings (daily at 6:30 AM CT)
- **Configuration**: /ganuda/services/chief_pa/config.yaml -- all endpoints, intervals, thresholds
- **Graceful shutdown**: SIGTERM handling, drain in-flight requests
- **Health**: Self-health-check writes to /tmp/pa_daemon_health.json

### 2. google_calendar.py -- Calendar Integration (5 story points)
- **API**: Google Calendar API v3, read-only scope
- **Auth**: OAuth2 with offline access, token stored in ~/.config/chief_pa/google_token.json (permission 600)
- **Polling**: Configurable interval (default 5 min). Fetches next 24h of events
- **Urgency detection**: Events within 30 min trigger immediate Slack push
- **Dedup**: Event ID tracking prevents duplicate notifications

### 3. slack_notifier.py -- Notification Service (3 story points)
- **Method**: Slack Incoming Webhook (simplest, no bot token needed)
- **Format**: Slack Block Kit for rich formatting
- **Categories**: calendar-urgent, briefing, email-triage, cluster-alert
- **Rate limit**: Max 10 messages/hour (prevents notification fatigue)
- **Silent hours**: 10 PM - 6 AM CT (configurable)
- **Retry**: 3 retries with exponential backoff on webhook failures

### 4. email_triage_wire.py -- Email Triage Integration (5 story points)
- **Source**: Reads from existing gmail_api_daemon.py output (redfin)
- **Transport**: HTTP call to redfin or direct DB query to bluefin for classification results
- **Classification**: actionable / informational / ignorable
- **Urgency**: Actionable emails with urgency > 0.8 get immediate Slack push
- **Privacy**: No email body stored on bmasass. Classification metadata only.

### 5. briefing_generator.py -- Daily Briefing (8 story points)
- **Schedule**: 6:30 AM CT daily
- **Data sources**:
  - Jr work queue: completions, failures, in-progress (last 24h) -- query bluefin
  - Council votes: recent votes with outcomes -- query bluefin
  - Thermal alerts: memories with temp >= 90 in last 24h -- query bluefin
  - Calendar: today's events -- from google_calendar module
  - Email triage: actionable email count and top items -- from email_triage_wire
- **Synthesis**: Routes assembled data through Tier 2 (Deliberation) for natural language summary
- **Output**: Slack Block Kit formatted message with sections

### 6. harness_client.py -- Harness Client Library (5 story points)
- **Purpose**: Abstracts harness tiers from PA daemon
- **Transport**: HTTP to redfin gateway:8080 (or standalone harness API)
- **Timeouts**: Tier-aware: 30s (Tier 1), 60s (Tier 2), 180s (Tier 3)
- **Circuit breaker**: If federation unreachable for >5 min, degrade gracefully

---

## Dependency Map

```
EXTERNAL SERVICES                  FEDERATION                         BMASASS
================                   ==========                         ======

Google Calendar API  ------>  google_calendar.py  ------+
                                                        |
Gmail (via gmail_api_daemon) --> email_triage_wire.py --+
                                                        |
Slack Incoming Webhook  <---- slack_notifier.py  <------+
                                                        |
                              briefing_generator.py ----+-- pa_daemon.py
                                                        |
                              harness_client.py --------+
                                    |
                                    v
                              HARNESS API (redfin)
                                    |
                    +---------------+---------------+
                    |               |               |
              tier1_reflex    tier2_delib     tier3_council
                    |               |               |
                    v               v               v
              vLLM:8000      specialists      specialist_council.py
              (redfin)       + thermal_mem    + gateway (redfin)
                             (bluefin)        + thermal (bluefin)
                             + embedding      + embedding (greenfin)
                             (greenfin)
```

**Build order** (respects dependency chain):
1. harness_core (shared models, config) -- no deps
2. tier1_reflex -- depends on harness_core
3. google_calendar.py -- no federation deps
4. slack_notifier.py -- no federation deps
5. tier2_deliberation -- depends on harness_core + federation
6. tier3_council_wire -- depends on harness_core + existing specialist_council.py
7. escalation_engine -- depends on all three tiers
8. email_triage_wire.py -- depends on gmail_api_daemon (existing)
9. briefing_generator.py -- depends on all data sources + harness_client
10. harness_client.py -- depends on harness API
11. pa_daemon.py -- depends on all PA components
12. Acceptance test suite -- depends on all of the above

---

## File Structure

```
/ganuda/
  lib/
    harness/
      __init__.py
      core.py              # HarnessRequest, HarnessResponse, config loader
      tier1_reflex.py      # Single LLM call, config-driven
      tier2_deliberation.py # 2-3 specialist quick consensus
      tier3_council.py     # Wire to specialist_council.py
      escalation.py        # Confidence + stakes-based escalation engine
      config.yaml          # Tier configs: models, thresholds, timeouts

  sag/routes/
    harness_routes.py      # POST /harness/query FastAPI endpoint

  services/
    chief_pa/
      __init__.py
      pa_daemon.py         # Main daemon (launchd on bmasass)
      google_calendar.py   # Google Calendar API integration
      slack_notifier.py    # Slack Incoming Webhook client
      email_triage_wire.py # Wire to gmail_api_daemon output
      briefing_generator.py # Daily briefing assembler
      harness_client.py    # Client for harness API
      config.yaml          # PA config: intervals, endpoints, Slack webhook
      launchd/
        com.cherokee.chief-pa.plist  # launchd plist for bmasass
```

---

## Security Considerations (Crawdad Input)

1. **Input Validation at Every Tier**: All requests validated against schema before processing. No raw user input reaches LLM prompts without sanitization. Injection prevention via prompt template parameterization.

2. **OAuth2 Token Security**: Google OAuth2 tokens stored in ~/.config/chief_pa/google_token.json with permission 600. Token refresh handled in-process, never logged. Token files excluded from any backup that leaves bmasass.

3. **Slack Webhook URL**: Stored in config.yaml (permission 600), never in source code. Rotatable without code changes.

4. **No PII on bmasass**: Email classification metadata only (subject hash, sender domain, urgency score). No email bodies, no calendar event descriptions stored locally. All detailed data stays on federation nodes (bluefin).

5. **Network Security**: WireGuard (encrypted, authenticated) preferred. Tailscale fallback (also encrypted). No plaintext federation traffic.

6. **Config File Permissions**: All config files on bmasass chmod 600. launchd plist owned by dereadi, not world-readable.

7. **Federation Auth**: PA daemon authenticates to federation using existing ganuda_auth mechanism. No new auth system needed.

---

## Seven-Generation Considerations (Turtle Input)

1. **Tier 3 Topology is Constitutional**: The fixed star topology for council deliberation (Thermal #82856) cannot be changed without seven-gen review. No one can silently degrade Tier 3 into a faster-but-shallower pipeline. The moat is protected by governance, not just code.

2. **Escalation Logic Must Be Transparent**: Every escalation decision is recorded in thermal memory with full reasoning. Future generations can audit why the system chose to escalate (or not). Institutional memory of judgment quality.

3. **No Vendor Lock-in at Tier 1**: Tier 1 is config-driven precisely so that model providers can be swapped. Seven generations from now, the LLM landscape will be unrecognizable. Tier 1 value is in prompt engineering and domain templates, not the model.

4. **Chief PA Sets the Pattern**: The PA is the first consumer of the harness. Whatever patterns we establish here (config format, health checks, launchd management, Slack formatting) will be copied by every future harness consumer. Build it right.

5. **DC-7 (Noyawisgi) Applies**: The harness must transform under pressure, not just restore. If Tier 2 consistently fails, the system should learn to route differently -- not just retry. Conserved sequences (Sacred Prompts, Council topology, Ghigau veto) survive all transformations.

---

## Product Line Roadmap

### Phase 1: Foundation (Current Sprint -- RC-2026-03A)
- Harness core + Tier 1 Reflex
- Chief PA MVP (calendar, briefing, Slack)
- bmasass launchd service

### Phase 2: Multi-Tier (RC-2026-03B)
- Tier 2 Deliberation module
- Escalation engine
- Email triage wiring
- Chief PA exercises Tier 1 + Tier 2

### Phase 3: Full Ethos (RC-2026-04A)
- Tier 3 Council wiring
- Full escalation chain (1 -> 2 -> 3)
- Acceptance test suite passes
- Chief PA exercises all 3 tiers

### Phase 4: Product Packaging (RC-2026-04B)
- Customer-facing harness API
- Tier-based pricing model
- Usage metering and billing hooks
- Documentation for external consumers

### Phase 5: Deer Market Entry
- Deer (Outer Council) drives go-to-market
- Customer segmentation determines default tier visibility
- Personalization at Tier 1 (Deer requirement)
- Beta customers on Tier 1 + Tier 2

---

## Risk Register

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------|--------|------------|
| R1 | Google Calendar OAuth2 flow requires manual browser auth on bmasass -- breaks headless daemon | Medium | High | Pre-authorize token via interactive flow before daemon starts. Token auto-refreshes thereafter. Document in setup instructions. |
| R2 | Tier 1 confidence scoring is unreliable -- causes unnecessary escalation flood | High | Medium | Start with conservative thresholds (0.7). Monitor escalation rate in thermal memory. Tune after 1 week of production data. |
| R3 | bmasass WireGuard Phase 2 not deployed -- forces Tailscale for all federation calls | Low | Low | Tailscale works fine. Slightly higher latency (~5ms). Not a blocker. |
| R4 | Slack webhook rate limit (Slack imposes their own) -- messages dropped | Low | Medium | Our self-imposed rate limit (10/hour) is well under Slack limit (1/sec). Monitor 429 responses. |
| R5 | gmail_api_daemon output format changes -- breaks email_triage_wire | Medium | Medium | email_triage_wire validates schema on every read. Fails loudly (Slack alert) if format mismatch. |
| R6 | Tier 2 specialist selection heuristic is naive -- wrong specialists chosen | Medium | Medium | Start with simple keyword-based domain matching. Log specialist selections. Council reviews selections weekly. |
| R7 | Federation outage during morning briefing -- Chief gets no briefing | Low | High | Briefing generator caches last successful briefing. On failure, sends cached briefing with STALE warning + cluster status. |
| R8 | Escalation engine becomes a cost sink -- too many Tier 3 calls | Medium | High | Rate limit escalations: max 5 Tier 3 calls per hour for any single user. Dashboard showing escalation patterns. |

---

## Acceptance Test Plan (Owl Requirement)

Owl said: testable acceptance criteria BEFORE building each tier. Anti-80/20.

### Tier 1 Tests
| Test | Method | Pass Criteria |
|------|--------|--------------|
| T1-LATENCY | Send 1000 simple queries, measure p95 | p95 < 50ms |
| T1-OFFLINE | Block all federation IPs, send query | Response returned (fallback) |
| T1-VALIDATION | Send malformed input (SQL injection, XSS, oversized) | Rejected with 400, no crash |
| T1-CONFIG | Change model endpoint in config, restart | New model used, no code change |
| T1-CONFIDENCE | Send ambiguous query | Confidence < 0.7, escalation triggered |

### Tier 2 Tests
| Test | Method | Pass Criteria |
|------|--------|--------------|
| T2-LATENCY | Send 100 domain queries, measure p95 | p95 < 500ms |
| T2-SPECIALISTS | Send health query | Medicine Woman + Turtle selected (not all 7) |
| T2-DIVERSITY | Check diversity_score in response | Score > 0, reflects specialist spread |
| T2-CONTEXT | Escalate from T1, check T2 response | tier1_context present in metadata |
| T2-ESCALATION | Send high-stakes query with low T2 confidence | Escalates to T3 |

### Tier 3 Tests
| Test | Method | Pass Criteria |
|------|--------|--------------|
| T3-LATENCY | Send 20 complex queries, measure p95 | p95 < 120s |
| T3-FULL-QUORUM | Check specialist count in response | All 7+ specialists participated |
| T3-TWO-WOLVES | Check routing_manifest in metacognition | Two Wolves audit trail present |
| T3-SACRED | Query with sacred pattern match | Sacred pattern referenced in response |
| T3-VOTE | Check council_vote_id in response | Vote recorded in council_votes table |

### Chief PA Tests
| Test | Method | Pass Criteria |
|------|--------|--------------|
| PA-CALENDAR | Create Google Calendar event, wait 1 polling interval | Event appears in Slack within interval + 5s |
| PA-URGENT | Create event 15 min from now | Immediate Slack push (not waiting for next poll) |
| PA-BRIEFING | Wait for 6:30 AM CT | Briefing arrives in Slack with all 5 sections |
| PA-SILENT | Trigger notification at 11 PM CT | No Slack message. Queued for morning. |
| PA-RSS | Measure daemon RSS after 24h uptime | RSS < 100MB |
| PA-REBOOT | Reboot bmasass | Daemon auto-restarts via launchd |
| PA-FEDERATION-DOWN | Block federation IPs | Daemon stays alive, sends cached/degraded briefing |
| PA-EMAIL | Send actionable email, wait for classification | Email surfaces in next briefing OR immediate push if urgency > 0.8 |

### Escalation Tests
| Test | Method | Pass Criteria |
|------|--------|--------------|
| ESC-AUTO | Send low-confidence query | Escalates 1->2 automatically |
| ESC-STAKES | Send "VA disability claim" query | Reaches Tier 3 regardless of confidence |
| ESC-CONTEXT | Check T3 response metadata | Contains T1 and T2 context |
| ESC-AUDIT | Query thermal memory for escalation | Audit trail present with reasoning |
| ESC-NO-DEESCALATE | Once at T3, check response | tier_used = 3, not downgraded |
| ESC-RATE-LIMIT | Flood with 10 high-stakes queries | Max 5 T3 calls/hour, remainder queued |

---

## Longhouse Voice Summary (Session #b940f09b18605c97)

| Voice | Key Contribution | Status |
|-------|-----------------|--------|
| **Coyote** | System must self-escalate. Humans underestimate stakes. | Incorporated in escalation engine -- users never choose tiers. |
| **Owl** | Testable acceptance criteria BEFORE building. Anti-80/20. | Acceptance test plan written above. Tests defined before code. |
| **Crawdad** | Input validation and config security at every tier. | Security considerations section. Validation in all tier interfaces. |
| **Jr** | Fallback model for Tier 1. Seamless context transfer on escalation. | Tier 1 offline fallback specified. Context chain in escalation logic. |
| **Raven** | Tier 3 is the moat. Protect it. | Tier 3 constitutional. Rate-limited. Cannot be diluted. |
| **Spider** | Tier 1 self-contained. Tier 2+ needs federation infra. | Dependency map reflects this cleanly. |
| **Gecko** | Faster = less wise. Latency targets. | 50ms / 500ms / 30-120s targets defined. |
| **Deer** | Customer segmentation. Personalization at Tier 1. | Product roadmap Phase 5. user_id in HarnessRequest. |
| **Elisi** | Diversity scoring in product tiers. | diversity_score in HarnessResponse. Tier 2+ required. |
| **Turtle** | Seven-gen review clause. | Constitutional protections. Seven-gen section above. |

---

## Open Questions for Chief Review

1. **Slack vs. other notification channels**: Currently Slack-only. Should we add SMS for truly urgent alerts (e.g., cluster down)?
2. **bmasass WireGuard Phase 2 timing**: Do we block on WireGuard or ship with Tailscale and upgrade later?
3. **Tier 1 fallback model**: What model for offline Tier 1? Cached templates? Or do we accept "federation unavailable" as acceptable degraded state?
4. **Briefing time**: 6:30 AM CT -- is that the right time for Chief's morning routine?
5. **Email triage scope**: All Gmail, or filtered labels only?

---

*TPM Note: This completes the ADAPT phase of Long Man. Next phase is BUILD -- Jr instructions will be generated from the kanban items below. Owl reviews after BUILD. The anti-80/20 principle applies: we verify each tier works before building the next.*
