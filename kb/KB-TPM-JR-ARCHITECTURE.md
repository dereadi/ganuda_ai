# KB-TPM-JR-ARCHITECTURE: Autonomous TPM Jr Federation

**Date:** 2025-12-07
**Author:** TPM (Command Post) + Claude Code
**Category:** Architecture / Autonomous Agents
**Priority:** HIGH
**Status:** DESIGN → IMPLEMENTATION

---

## Executive Summary

TPM Jr is an autonomous agent system that learns from the TPM (Flying Squirrel) dispatch patterns and can operate independently when the human TPM is unavailable or in air-gapped environments. It integrates with SAG Traffic Intelligence to make smart routing decisions.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            TPM JR FEDERATION                                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   ONLINE MODE                              AIR-GAP MODE                         │
│   ┌───────────────────────┐               ┌───────────────────────┐            │
│   │  TPM JR - REDFIN      │◄─── Sync ────►│  TPM JR - BMASASS     │            │
│   │  (Primary Server)     │               │  (Local Mac)          │            │
│   │                       │               │                       │            │
│   │  • systemd service    │               │  • launchd service    │            │
│   │  • PostgreSQL direct  │               │  • SQLite local cache │            │
│   │  • Real-time thermal  │               │  • Offline KB mirror  │            │
│   │  • Immediate dispatch │               │  • Queue for sync     │            │
│   │  • Full context       │               │  • Local Ollama       │            │
│   └───────────┬───────────┘               └───────────┬───────────┘            │
│               │                                       │                         │
│               ▼                                       ▼                         │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                     SHARED LEARNING LAYER                                │  │
│   │                                                                          │  │
│   │  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────────────┐ │  │
│   │  │ Mission Patterns │  │ Triad Capability │  │ TPM Decision History  │ │  │
│   │  │                  │  │ Matrix           │  │                       │ │  │
│   │  │ • Keywords       │  │                  │  │ • User corrections    │ │  │
│   │  │ • Target triads  │  │ • Success rates  │  │ • Accepted suggestions│ │  │
│   │  │ • Priorities     │  │ • Completion time│  │ • Override patterns   │ │  │
│   │  │ • Time patterns  │  │ • Quality scores │  │ • Escalation triggers │ │  │
│   │  └──────────────────┘  └──────────────────┘  └────────────────────────┘ │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                       │                                         │
│                    ┌──────────────────┼──────────────────┐                     │
│                    ▼                  ▼                  ▼                     │
│           ┌─────────────┐    ┌─────────────────┐   ┌─────────────┐            │
│           │  IT TRIAD   │    │   DEV TRIAD     │   │OTHER TRIADS │            │
│           │             │    │                 │   │             │            │
│           │ Chiefs → Jr │    │  Chiefs → Jr    │   │ Chiefs → Jr │            │
│           └─────────────┘    └─────────────────┘   └─────────────┘            │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Learning Model

### 1. Mission Pattern Recognition

TPM Jr learns what types of missions go to which triads by analyzing:

- **Keywords**: CSS, Flask, API, infrastructure, database, monitoring
- **File Paths**: /ganuda/home/dereadi/sag_* → IT Triad, /ganuda/trading/* → Trading Triad
- **Priority Indicators**: URGENT, CRITICAL, routine, research
- **Time Patterns**: Business hours vs after-hours dispatch preferences

### 2. Triad Capability Matrix

Learned from mission outcomes:

| Triad | Capability | Success Rate | Avg Time | Confidence |
|-------|------------|--------------|----------|------------|
| IT Triad | Flask/API | 85% | 2.5 hrs | 0.92 |
| IT Triad | CSS/Theme | 95% | 1.0 hrs | 0.98 |
| IT Triad | Infrastructure | 80% | 4.0 hrs | 0.85 |
| Dev Triad | Complex Code | 75% | 6.0 hrs | 0.70 |
| Dev Triad | UI/UX Design | 70% | 3.0 hrs | 0.65 |

### 3. Decision Confidence Scoring

```python
def calculate_dispatch_confidence(mission_content: str) -> dict:
    """
    Returns:
    {
        'suggested_triad': 'it_triad',
        'suggested_priority': 'HIGH',
        'confidence': 0.87,
        'reasoning': 'Keywords match Flask/API pattern (85% historical success)',
        'auto_dispatch': True  # If confidence > 0.80 and authority_level >= 2
    }
    """
```

---

## Authority Levels

| Level | Name | Behavior |
|-------|------|----------|
| 0 | Observer | Learn only, no suggestions |
| 1 | Advisor | Suggest, require human approval |
| 2 | Assistant | Auto-dispatch routine (conf > 0.80), escalate novel |
| 3 | Autonomous | Full autonomy, daily summary report |
| 4 | Critical-Only | Only escalate blocked/critical situations |

**Recommended Starting Level: 2 (Assistant)**

---

## Integration with SAG Traffic Intelligence

TPM Jr feeds into and reads from the SAG Traffic Intelligence tables:

```
┌─────────────────────┐         ┌─────────────────────┐
│   TPM JR            │         │ SAG Traffic Intel   │
│                     │         │                     │
│   Mission Dispatch  │────────►│ sag_traffic_patterns│
│                     │         │                     │
│   Triad Selection   │◄────────│ sag_route_intel     │
│                     │         │                     │
│   Outcome Learning  │────────►│ sag_predictions     │
└─────────────────────┘         └─────────────────────┘
```

---

## Database Schema

### TPM Learning Tables

```sql
-- Mission Pattern Memory
CREATE TABLE tpm_mission_patterns (
    pattern_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Pattern identification
    pattern_name VARCHAR(100),
    keywords TEXT[],
    file_path_patterns TEXT[],
    content_regex TEXT,

    -- Routing
    target_triad VARCHAR(100),
    typical_priority VARCHAR(20),

    -- Learning metrics
    times_seen INTEGER DEFAULT 0,
    times_successful INTEGER DEFAULT 0,
    success_rate FLOAT GENERATED ALWAYS AS (
        CASE WHEN times_seen > 0
             THEN times_successful::FLOAT / times_seen
             ELSE 0 END
    ) STORED,
    avg_completion_hours FLOAT,

    -- Confidence
    confidence_score FLOAT DEFAULT 0.5,

    -- Timestamps
    first_seen TIMESTAMPTZ DEFAULT NOW(),
    last_seen TIMESTAMPTZ DEFAULT NOW(),
    last_success TIMESTAMPTZ
);

-- Triad Capability Learning
CREATE TABLE tpm_triad_capabilities (
    triad_id VARCHAR(100),
    capability_area VARCHAR(100),

    -- Metrics
    missions_attempted INTEGER DEFAULT 0,
    missions_successful INTEGER DEFAULT 0,
    missions_reworked INTEGER DEFAULT 0,

    -- Quality
    avg_quality_score FLOAT,
    avg_completion_hours FLOAT,
    min_completion_hours FLOAT,
    max_completion_hours FLOAT,

    -- Learning
    confidence_score FLOAT DEFAULT 0.5,

    -- Time-based patterns
    best_hour_of_day INTEGER,  -- When this triad performs best

    PRIMARY KEY (triad_id, capability_area),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- TPM Decision Log (for learning from corrections)
CREATE TABLE tpm_decision_log (
    decision_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- The mission
    mission_id UUID,
    mission_content_hash TEXT,
    mission_keywords TEXT[],

    -- TPM Jr suggestion
    suggested_triad VARCHAR(100),
    suggested_priority VARCHAR(20),
    suggestion_confidence FLOAT,
    suggestion_reasoning TEXT,

    -- Human response
    user_accepted BOOLEAN,
    user_override_triad VARCHAR(100),
    user_override_priority VARCHAR(20),
    user_feedback TEXT,

    -- Outcome (filled in later)
    mission_successful BOOLEAN,
    completion_hours FLOAT,

    -- Timestamps
    suggested_at TIMESTAMPTZ DEFAULT NOW(),
    decided_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

-- TPM Jr Instance Registry
CREATE TABLE tpm_jr_instances (
    instance_id VARCHAR(100) PRIMARY KEY,
    hostname VARCHAR(100),
    location VARCHAR(100),  -- 'redfin', 'bmasass'

    -- Authority
    authority_level INTEGER DEFAULT 2,

    -- Status
    status VARCHAR(20) DEFAULT 'active',
    last_heartbeat TIMESTAMPTZ,
    missions_dispatched INTEGER DEFAULT 0,
    missions_suggested INTEGER DEFAULT 0,

    -- Sync state (for air-gap instances)
    last_sync TIMESTAMPTZ,
    pending_sync_count INTEGER DEFAULT 0,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_tpm_patterns_keywords ON tpm_mission_patterns USING GIN(keywords);
CREATE INDEX idx_tpm_patterns_confidence ON tpm_mission_patterns(confidence_score DESC);
CREATE INDEX idx_tpm_capabilities_triad ON tpm_triad_capabilities(triad_id);
CREATE INDEX idx_tpm_decisions_mission ON tpm_decision_log(mission_id);
```

---

## TPM Jr Redfin (Primary)

**Location:** `/ganuda/tpm_jr/tpm_jr_redfin.py`
**Service:** `systemctl --user status tpm-jr.service`

### Core Functions

```python
class TPMJrRedfin:
    """Primary TPM Jr instance on redfin."""

    def __init__(self):
        self.instance_id = 'tpm_jr_redfin'
        self.authority_level = 2  # Assistant mode
        self.db_config = DB_CONFIG

    def watch_thermal_memory(self):
        """Poll thermal memory for new user requests."""
        # Look for patterns that suggest user needs help
        # - Direct questions
        # - Requests without clear triad assignment
        # - Stuck missions

    def analyze_mission(self, content: str) -> dict:
        """Analyze mission and suggest routing."""
        keywords = self.extract_keywords(content)
        patterns = self.match_patterns(keywords)
        triad_scores = self.score_triads(patterns, keywords)

        return {
            'suggested_triad': max(triad_scores, key=triad_scores.get),
            'confidence': triad_scores[max(triad_scores, key=triad_scores.get)],
            'reasoning': self.generate_reasoning(patterns, triad_scores)
        }

    def should_auto_dispatch(self, confidence: float) -> bool:
        """Decide if we should auto-dispatch or wait for human."""
        if self.authority_level >= 3:
            return True
        if self.authority_level == 2 and confidence >= 0.80:
            return True
        return False

    def learn_from_outcome(self, mission_id: str, outcome: dict):
        """Update learning tables based on mission outcome."""
        # Update pattern success rates
        # Update triad capability scores
        # Adjust confidence scores
```

---

## TPM Jr Bmasass (Local/Air-Gap)

**Location:** `/Users/Shared/ganuda/tpm_jr/tpm_jr_local.py`
**Service:** `launchctl list | grep tpm-jr`

### Air-Gap Features

```python
class TPMJrLocal:
    """Local TPM Jr for air-gapped operation."""

    def __init__(self):
        self.instance_id = 'tpm_jr_bmasass'
        self.authority_level = 2
        self.local_db = '/Users/Shared/ganuda/tpm_jr/local_cache.db'  # SQLite
        self.kb_path = '/Users/Shared/ganuda/kb/'
        self.offline_queue = '/Users/Shared/ganuda/tpm_jr/pending_missions.json'

    def check_network(self) -> bool:
        """Check if we can reach bluefin."""
        try:
            socket.create_connection(('192.168.132.222', 5432), timeout=2)
            return True
        except:
            return False

    def sync_with_server(self):
        """Sync local cache with PostgreSQL when online."""
        if not self.check_network():
            return False

        # Push pending missions
        self.push_pending_missions()

        # Pull latest patterns
        self.pull_pattern_updates()

        # Pull latest KB articles
        self.sync_kb_articles()

        # Update last_sync timestamp
        self.update_sync_status()

    def queue_mission(self, mission: dict):
        """Queue mission for later sync when offline."""
        with open(self.offline_queue, 'r+') as f:
            queue = json.load(f)
            queue.append({
                'mission': mission,
                'queued_at': datetime.now().isoformat(),
                'status': 'pending'
            })
            f.seek(0)
            json.dump(queue, f)

    def use_local_llm(self, prompt: str) -> str:
        """Use local Ollama for analysis when offline."""
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                'model': 'llama3.2:3b',  # Smaller model for Mac
                'prompt': prompt,
                'stream': False
            }
        )
        return response.json()['response']
```

---

## Sync Protocol

### Online → Offline Transition

1. TPM Jr Bmasass detects network loss
2. Switches to local SQLite cache
3. Uses local Ollama (llama3.2:3b)
4. Queues all missions to `pending_missions.json`
5. Continues learning locally

### Offline → Online Transition

1. TPM Jr Bmasass detects network restore
2. Pushes pending missions to thermal memory
3. Pulls pattern updates from PostgreSQL
4. Syncs KB articles (rsync)
5. Reconciles any conflicts (server wins)
6. Resumes real-time operation

---

## Daily Summary Report

TPM Jr generates a daily summary:

```
TPM JR DAILY SUMMARY - 2025-12-07
==================================

MISSIONS PROCESSED: 12
  - Auto-dispatched: 8 (66%)
  - Suggested + Approved: 3 (25%)
  - Escalated to TPM: 1 (8%)

TRIAD PERFORMANCE:
  IT Triad: 5/6 successful (83%)
  Dev Triad: 2/3 successful (67%)

LEARNING UPDATES:
  - New pattern: "monitoring alert" → IT Triad (conf: 0.75)
  - Updated: Flask/API routing score: 0.85 → 0.87

PENDING ITEMS:
  - 1 mission awaiting human decision
  - UI/UX Design task needs guidance

RECOMMENDATION:
  Consider increasing authority to Level 3 based on
  92% suggestion acceptance rate this week.
```

---

## Files and Locations

| Component | Location | Description |
|-----------|----------|-------------|
| TPM Jr Redfin | `/ganuda/tpm_jr/tpm_jr_redfin.py` | Primary server instance |
| TPM Jr Bmasass | `/Users/Shared/ganuda/tpm_jr/tpm_jr_local.py` | Local Mac instance |
| Local Cache | `/Users/Shared/ganuda/tpm_jr/local_cache.db` | SQLite offline cache |
| Pending Queue | `/Users/Shared/ganuda/tpm_jr/pending_missions.json` | Offline mission queue |
| Config | `/ganuda/tpm_jr/config.yaml` | Shared configuration |
| KB Sync | `rsync ganuda/kb/ → /Users/Shared/ganuda/kb/` | Knowledge base mirror |

---

## Implementation Phases

### Phase 1: Database & Learning Foundation
- Create TPM learning tables
- Seed with historical mission data
- Build pattern extraction

### Phase 2: TPM Jr Redfin
- Core agent with thermal memory integration
- Pattern matching and routing
- Learning from outcomes

### Phase 3: TPM Jr Bmasass
- Local SQLite cache
- Offline queue
- Sync protocol

### Phase 4: SAG Integration
- Dashboard for TPM Jr status
- Manual override interface
- Learning visualization

---

**END OF KB-TPM-JR-ARCHITECTURE**
