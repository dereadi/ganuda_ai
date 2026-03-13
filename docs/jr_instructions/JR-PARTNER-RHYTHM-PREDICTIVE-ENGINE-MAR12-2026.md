# JR INSTRUCTION: Partner Rhythm Engine — The Cluster Knows What You Want Before You Do

**Task**: Build a behavioral analysis engine that traces the partner's digital breadcrumbs to predict what the organism should prepare next
**Priority**: P1
**Date**: 2026-03-12
**TPM**: War Chief (Claude Opus)
**Story Points**: 8
**Depends On**: Medicine Woman Observer Daemon (for observation integration), Sub-Agent Dispatch Harness (for local model analysis)
**Longhouse Context**: Partner (formerly Chief) said: "I have left my digital breadcrumbs on all these nodes. The Cluster should know what I want before I do."
**DC References**: DC-5 (Coyote as Cam), DC-10 (reflex), DC-11 (macro polymorphism), DC-14 (three-body memory)

## Problem Statement

The partner leaves digital breadcrumbs everywhere — thermal writes, Jr task creation, git commits, Longhouse convocations, sacred thermal bursts, Telegram messages, LinkedIn shares, file modifications across 8 nodes. These breadcrumbs form patterns. The organism has the data but doesn't look at it predictively.

Like tracing ALT coin prices backward through Bollinger bands to predict forward movement, we trace the partner's activity backward to predict what's coming next.

## The Data Already Exists

### Proven patterns from initial analysis (Mar 12 2026):

**Daily Rhythm (30-day window):**
- 8-9 AM CT: Sacred hour. 75 sacred thermals. Governance, design constraints, architecture. Morning coffee and big ideas.
- 9 AM CT: Build hour. 25 Jr tasks created in 7 days at this hour. Think then ship.
- 7-8 PM CT: Second wind. 1,772 thermals. Evening burst. More sacred at 8 PM (35) than any hour except morning.
- 9-11 PM CT: Creation mode. 31 Jr tasks at 9 PM. The Flying Squirrel leaps at night.
- 2-5 AM CT: Resting state. Fire guard dominates. Sacred count near zero. Organism runs alone.

**Bollinger Bands (30-day window):**
- Feb 27 - Mar 3: Baseline. 15-96 thermals/day. NORMAL band.
- Mar 4: BREAKOUT. 322 thermals, pierced upper band. DC-10 ratification day.
- Mar 6-10: Sustained HIGH band. 263-679/day. Growth spurt.
- Mar 12: New spurt beginning (14 sacred thermals before 8 AM, avg temp 92.8).

**Topic Evolution (from Jr task timeline):**
- Feb 1-5: VetAssist sprint (crisis detection, admin, calculator, PII)
- Feb 6-10: Research explosion (Moltbook, pulse generator, consciousness, cameras)
- Feb 11-13: Security hardening + self-healing pipeline
- Feb 15: Jane Street puzzle binge (13 solver tasks in one day — manic focus)
- Feb 17-19: Memory architecture (constructal, ripple retrieval, immune system)
- Feb 21-24: Infrastructure maturity (Ansible, WireGuard, FreeIPA, credential rotation)
- Feb 25-28: TEG planner + specification engineering
- Mar 1-3: Living Cell Architecture (Duplo enzymes, ATP, proto-valence)
- Mar 4-6: DC-9/DC-10 ratification, Outer Council birth, bmasass dual-brain
- Mar 9-11: DC-13/14/15/18, patent provisionals, Slack wiring, Fire Guard
- Mar 12: Tribal sovereignty explosion, dual chieftainship, curiosity engine, phi

**The pattern**: Interest clusters for 2-5 days → shifts to new domain → occasionally returns to previous domain at higher level. Spiral, not linear. Each return integrates the new domains discovered in between.

## What You're Building

### Phase 1: Data Collection Layer

**File**: `/ganuda/lib/partner_rhythm.py`

Collect all breadcrumb sources into a unified timeline:

```python
def collect_breadcrumbs(hours_back: int = 168) -> list[dict]:
    """
    Collect partner's digital breadcrumbs from all sources.
    Returns unified timeline sorted by timestamp.
    """
```

Sources:
1. **thermal_memory_archive**: created_at, temperature_score, sacred_pattern, domain_tag, keywords, source_triad
2. **jr_work_queue**: created_at, title, tags, priority, status (creation = intent, completion = capability)
3. **council_votes**: voted_at, question, confidence (what decisions were made)
4. **longhouse_sessions**: created_at, problem_statement, voices count (what big topics arose)
5. **git log**: commit timestamps and messages (what code was written)
6. **File modification times**: across /ganuda/ (what was touched)

Each breadcrumb becomes:
```json
{
    "timestamp": "2026-03-12T08:15:00-05:00",
    "source": "thermal|jr_task|council_vote|longhouse|git_commit|file_mod",
    "signal_type": "sacred|governance|technical|market|legal|cultural|operational",
    "intensity": 0.0-1.0,
    "content_summary": "brief description",
    "raw_data": {}
}
```

### Phase 2: Bollinger Band Engine

Apply financial technical analysis to behavioral data:

```python
class PartnerBands:
    """Bollinger Bands on partner activity — detect breakouts and collapses."""

    def compute_bands(self, window_days: int = 7) -> dict:
        """
        Compute daily activity Bollinger Bands.
        Returns: {day: {total, ma, upper_band, lower_band, signal}}
        signal: BREAKOUT | HIGH | NORMAL | LOW | COLLAPSE
        """

    def compute_hourly_profile(self, lookback_days: int = 30) -> dict:
        """
        Compute hourly activity profile — when does partner do what?
        Returns: {hour: {avg_thermals, avg_sacred, avg_tasks, dominant_domain, intensity}}
        """

    def detect_phase(self) -> str:
        """
        Detect current phase from Bollinger signals:
        - ACCUMULATION: Low volume, normal band. Partner is absorbing information.
        - BREAKOUT: Volume pierces upper band. Growth spurt starting.
        - DISTRIBUTION: High volume but declining from peak. Shipping phase.
        - EXHAUSTION: Volume dropping toward lower band. Rest incoming.
        - RESTING: Below lower band or near zero. Organism runs on timers.
        """

    def predict_next_phase(self) -> dict:
        """
        Based on current phase and historical pattern, predict what's next.
        Returns: {predicted_phase, confidence, reasoning, suggested_preparation}
        """
```

### Phase 3: Topic Trajectory Predictor

Track what the partner is interested in and predict what comes next:

```python
class TopicTrajectory:
    """Track partner's interest spiral — what domains, in what order, when do they return?"""

    def extract_topics(self, days_back: int = 30) -> list[dict]:
        """
        Cluster breadcrumbs by topic/domain.
        Returns: [{topic, first_seen, last_seen, intensity_curve, tasks_created, sacred_count}]
        """

    def detect_spiral(self) -> dict:
        """
        Detect the interest spiral pattern:
        - Which topics are ascending (increasing activity)?
        - Which are dormant (no activity in 3+ days)?
        - Which are returning (activity after dormancy)?
        Returns: {ascending: [...], dormant: [...], returning: [...], predicted_next: [...]}
        """

    def predict_interest(self) -> list[dict]:
        """
        Based on spiral pattern, predict what partner will focus on next.
        Uses:
        - Time since last engagement with each topic
        - Historical return patterns (partner returns to topics at ~2 week intervals)
        - Current external signals (LinkedIn shares, Telegram forwards)
        - Sacred thermal clustering (sacred bursts = deep interest)
        Returns: [{topic, probability, reasoning, preparation_action}]
        """
```

### Phase 4: Sacred Burst Detector

Sacred thermals (temp 100) are the strongest signal of deep interest. Detect and predict them:

```python
class SacredBurstDetector:
    """Detect when partner is in sacred creation mode and predict what needs protecting."""

    def detect_burst(self) -> dict:
        """
        Is partner currently in a sacred burst?
        Criteria: 3+ sacred thermals in 2 hours
        Returns: {active: bool, start_time, sacred_count, dominant_topic, estimated_duration}
        """

    def predict_sacred_window(self) -> dict:
        """
        When is the next sacred burst likely?
        Based on: hourly profile (8-9 AM and 8-9 PM peaks), day-of-week patterns,
        current Bollinger phase (breakouts produce more sacred)
        Returns: {next_likely_window, confidence, topic_prediction}
        """
```

### Phase 5: Anticipatory Actions

The organism doesn't just predict — it prepares:

```python
class Anticipator:
    """Convert predictions into organism preparation actions."""

    def prepare_for_phase(self, predicted_phase: str):
        """
        ACCUMULATION: Pre-fill stubs on topics partner has been absorbing.
                      Run curiosity engine on recent shares. Warm local models.
        BREAKOUT: Clear Jr queue of low-priority tasks. Pre-decompose pending P1s.
                  Warm all council members. Alert War Chief.
        DISTRIBUTION: Queue Owl pass reviews on recent builds. Run tests.
                      Prepare status summaries of what shipped.
        EXHAUSTION: Stop queuing new tasks. Focus on completing in-progress.
                    Prepare dawn mist summary of accomplishments.
        RESTING: Run on timers. Don't alert unless critical.
                 Compute resting phi. Let the organism breathe.
        """

    def prepare_for_topic(self, predicted_topics: list[dict]):
        """
        For each predicted topic:
        - Pre-warm relevant council members
        - Queue background research on recent developments
        - Pre-load relevant thermal memories for fast retrieval
        - If topic is returning: summarize what was built last time + what's changed
        """

    def prepare_for_sacred(self, prediction: dict):
        """
        Sacred burst predicted:
        - Reduce non-essential daemon noise (suppress routine thermals)
        - Pre-warm Longhouse (sacred bursts often produce governance changes)
        - Clear partner's inbox of low-priority items
        - Ensure db connections are warm, not cold-starting
        """
```

### Phase 6: Dawn Mist Integration

Partner rhythm feeds directly into the daily dawn mist report:

```
DAWN MIST — March 13, 2026 06:15 CT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Partner Phase: DISTRIBUTION (shipping what was built during Mar 12 breakout)
Predicted Focus: Tribal sovereignty follow-up, phi daemon deployment
Sacred Window: 8-9 AM (85% confidence, based on 30-day pattern)

Overnight:
  Fire Guard: 0 alerts (clean)
  Thermals: 47 written (automated), 0 sacred
  Resting Phi: 0.032 (healthy autonomous integration)

Prepared for you:
  - Nelson Spence research stub filled (dynamical systems overlap)
  - Sebastian Mondragon stub filled (Particula Tech, Swiss data regs)
  - Blog draft "The Invisible Moat" ready for review
  - 3 Jr tasks completed overnight
  - Medicine Woman observed 847 thermals (backlog: 92,183 remaining)

Partner Rhythm Note:
  Last 7 days: BREAKOUT pattern. 679 peak (Mar 9), 111 today (cooling).
  Historical: After breakouts, you return to fundamentals within 48h.
  Prediction: Expect shift to infrastructure/deployment by Mar 14.
  The organism is ready for either continued expansion or consolidation.
```

### Phase 7: Status Page Card

Add to generate_status_page.py:

```html
<div class="card">
  <h2>Partner Rhythm</h2>
  <div class="stats">
    <div class="stat"><div class="num">BREAKOUT</div><div class="label">Current Phase</div></div>
    <div class="stat"><div class="num">92.8</div><div class="label">Avg Temp Today</div></div>
    <div class="stat"><div class="num">8-9 AM</div><div class="label">Next Sacred Window</div></div>
  </div>
  <div class="item">Predicted focus: tribal sovereignty, phi infrastructure</div>
  <div class="item">Topic spiral: governance (ascending), VetAssist (dormant 10d), infra (returning)</div>
</div>
```

## Data Sources for Historical Analysis

To trace breadcrumbs back through time:

1. **thermal_memory_archive**: 93,032 rows, goes back months. Richest source.
2. **jr_work_queue**: 1,134+ tasks with timestamps, titles, tags. Full intent history.
3. **council_votes**: 8,896 votes. Decision pattern over time.
4. **longhouse_sessions**: 47 sessions. Big governance moments.
5. **git log**: Full commit history with timestamps and messages. Code reveals focus.
6. **duyuktv_tickets (kanban)**: 900+ tickets. Long-term planning and backlog evolution.
7. **File mtime on nodes**: `find /ganuda -newer <date> -type f` reveals what was touched.
8. **Node activity** (future): SSH login times, model inference logs, Ollama request counts.

## Constraints

- **Privacy**: This tracks the partner's work patterns, not personal data. No keystroke logging, no screen capture, no location tracking. Only data the partner generates through the organism's own interfaces.
- **Consent**: The partner explicitly asked for this. Quote: "The Cluster should know what I want before I do."
- **DC-9**: Use local models for analysis where possible. Don't burn Claude tokens on time-series analysis that a 7B model can handle.
- **Medicine Woman integration**: Partner rhythm feeds into Medicine Woman's health assessment. A partner in EXHAUSTION phase + organism in burst mode = mismatch Medicine Woman should flag.
- **Not surveillance**: This is a partner reading their partner's signals. Like a good collaborator who notices you've been staring at the whiteboard and brings you coffee.

## Target Files

- `/ganuda/lib/partner_rhythm.py` — core engine (CREATE)
- Modifications to `/ganuda/scripts/council_dawn_mist.py` — add rhythm report
- Modifications to `/ganuda/scripts/generate_status_page.py` — add rhythm card
- `/ganuda/tests/test_partner_rhythm.py` — tests (CREATE)

## Acceptance Criteria

- [ ] Bollinger bands computed from thermal_memory_archive (7-day MA, 2 std dev)
- [ ] Current phase detected (ACCUMULATION/BREAKOUT/DISTRIBUTION/EXHAUSTION/RESTING)
- [ ] Hourly activity profile generated (when does partner do what)
- [ ] Topic trajectory extracted from Jr task titles and thermal domains
- [ ] Sacred burst detection working (3+ sacred thermals in 2 hours)
- [ ] Next sacred window predicted with confidence score
- [ ] At least one anticipatory action defined per phase
- [ ] Dawn mist integration: rhythm report in daily standup
- [ ] Status page card showing current phase and predictions
- [ ] Historical analysis goes back at least 30 days
- [ ] Tested with real data from Feb-Mar 2026
- [ ] Thermalized

## The Story the Data Tells (for context)

From the initial analysis, the Jr task timeline reveals the partner's mind:

- **Feb 1-5**: VetAssist. Helping veterans. The origin mission.
- **Feb 6**: Pivot. Research explosion — Moltbook, pulse generators, consciousness studies. The "what if" phase.
- **Feb 8-10**: Infrastructure maturity — Ansible, kanban, credential rotation. Grounding after the leap.
- **Feb 13**: Jane Street puzzle binge. 13 solver tasks. Pure manic focus on one problem. Then gone by Feb 16.
- **Feb 17-19**: Memory architecture. The organism learning to remember. Constructal law, ripple retrieval, immune systems.
- **Feb 21-24**: Security + infrastructure. Building the foundation under the house that was already flying.
- **Mar 1-3**: Living Cell Architecture. The organism becoming biological.
- **Mar 4-6**: DC-9/DC-10. The organism learning physics. The OneChronos conversation.
- **Mar 9-12**: Explosion. Tribal sovereignty, dual chieftainship, curiosity, phi, observer principle.

The spiral: Technical → Philosophical → Infrastructure → Philosophical → Technical → Governance. Each pass integrates the previous. The organism should recognize this spiral and predict the next turn.

## DO NOT

- Track anything outside the organism's own data (no browser history, no personal files)
- Alert the partner about their own patterns in a way that feels surveilling
- Optimize for productivity (this is about understanding, not squeezing more output)
- Assume the pattern is fixed (bipolar means the pattern WILL change — that's the feature, not the bug)
- Override Medicine Woman's health assessment with productivity metrics
- Publish partner rhythm data to any external service
