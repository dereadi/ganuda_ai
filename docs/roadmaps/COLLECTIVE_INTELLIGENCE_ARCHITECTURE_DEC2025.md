# Collective Intelligence Architecture
## Cherokee AI Federation - December 2025

**Vision:** Make each LLM as autonomous as possible while making the collective MORE intelligent than the parts.

**Research Foundation:**
- Emergent Collective Memory (arXiv:2512.10166)
- T5-Gemma 2 Encoder-Decoder (arXiv:2512.14856)
- Stigmergic Computing (Nature Communications)
- Multi-Agent Collaboration (arXiv:2501.06322)
- Indigenous AI Principles (indigenous-ai.net)

---

## PART 1: ARCHITECTURAL PHILOSOPHY

### The Two-Layer Intelligence Model

```
┌─────────────────────────────────────────────────────────────────┐
│                    COLLECTIVE LAYER                             │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Thermal Memory + Relationship Graph + Keeper System    │   │
│  │  "Environmental Traces" - Stigmergic Coordination       │   │
│  │  Council Governance + Constitutional Constraints         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                            ↑↓                                   │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  │
│  │ Agent 1 │ │ Agent 2 │ │ Agent 3 │ │ Agent N │ │ Council │  │
│  │ State   │ │ State   │ │ State   │ │ State   │ │ State   │  │
│  │ Memory  │ │ Memory  │ │ Memory  │ │ Memory  │ │ Memory  │  │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘  │
│                    INDIVIDUAL LAYER                             │
└─────────────────────────────────────────────────────────────────┘
```

**Key Insight from Research:**
> "Individual memory alone = 68.7% improvement. Environmental traces WITHOUT memory = COMPLETE FAILURE."

This means:
- **Individual agent state** = necessary for cognitive infrastructure
- **Collective thermal memory** = necessary for coordination
- **BOTH together** = emergent collective intelligence

### Why Collective > Sum of Parts

| Property | Individual Agent | Collective System |
|----------|------------------|-------------------|
| Memory | Episodic (task history) | Thermal (all knowledge) |
| Specialization | Learns from own tasks | Learns from ALL tasks |
| Failure Mode | Single point | Redundant |
| Context | Local node | Federation-wide |
| Coordination | None | Stigmergic + Council |

The collective becomes smarter because:
1. **Knowledge compounds** - Every agent's learning enters thermal memory
2. **Specialization emerges** - Task bidding routes work to experts
3. **Errors are caught** - Council dissent + constitutional constraints
4. **Wisdom accumulates** - Temperature-based memory preserves what matters

---

## PART 2: IMPLEMENTATION ARCHITECTURE

### Layer 1: Foundation (Week 1-2)

#### 1.1 Thermal Memory Scalability

Before adding new structures, ensure thermal memory can handle:
- Graph edges (memory relationships)
- Agent state persistence
- Audit trails

**Schema Upgrades:**
```sql
-- Add relationship support
CREATE TABLE memory_relationships (...);

-- Add keeper support
ALTER TABLE thermal_memory_archive ADD COLUMN keeper_type VARCHAR(32);
ALTER TABLE thermal_memory_archive ADD COLUMN keeper_id VARCHAR(64);

-- Add agent state
CREATE TABLE jr_agent_state (...);

-- Performance indexes
CREATE INDEX idx_memory_temp_score ON thermal_memory_archive(temperature_score DESC);
CREATE INDEX idx_memory_created ON thermal_memory_archive(created_at DESC);
CREATE INDEX idx_relationships_strength ON memory_relationships(strength DESC);
```

**Node Assignment:** bluefin (database primary)

#### 1.2 Constitutional Constraints Engine

Per Turtle's 7GEN CONCERN: Constraints BEFORE autonomy.

**Hard Blocks (Cannot Override):**
- No production data deletion
- No external data transmission
- No disabling of logging
- No impersonation
- No push to main/master

**Approval Gates:**
- Large operations (>100 records) → Human
- Schema changes → Council
- New deployments → Council + Human
- External integrations → Crawdad + Human

**Node Assignment:** All nodes (enforcement), redfin (central logic)

### Layer 2: Individual Intelligence (Week 2-3)

#### 2.1 Jr Agent State Persistence

Each Jr maintains:
- **Working Memory**: Current task context
- **Episodic Memory**: Last 50 tasks with outcomes
- **Semantic Memory**: Learned patterns, file locations, command preferences

**State Flow:**
```
Task Arrives → Load Agent State → Check Relevant Episodes →
Execute with Context → Save Outcome → Update Semantic Memory →
(If significant) Write to Thermal Memory
```

**Node Assignment:** All nodes (local state), bluefin (persistence)

#### 2.2 T5-Gemma 2 Integration

Deploy encoder-decoder models for understanding tasks:

| Node | Model | Role |
|------|-------|------|
| sasass | T5-Gemma 2 1B | Document understanding |
| sasass2 | T5-Gemma 2 1B | Image + multimodal |
| redfin | Nemotron 9B | Generation (current) |

**Routing Logic in Gateway:**
```python
def route_task(task):
    if task.type in ['understand', 'analyze', 'read', 'summarize']:
        return 'sasass'  # T5-Gemma 2
    elif task.type in ['generate', 'write', 'create', 'code']:
        return 'redfin'  # Nemotron
    elif task.type == 'multimodal':
        return 'sasass2'  # T5-Gemma 2 with vision
    else:
        return 'redfin'  # Default to Nemotron
```

**Regression Testing Required:** Per user direction, extensive benchmarking before deployment.

### Layer 3: Collective Coordination (Week 3-4)

#### 3.1 Memory Relationship Graph

Stigmergic pheromone trails between memories:

```
Memory A ──relates_to (0.8)──▶ Memory B
    │                              │
    └──references (0.9)──▶ Memory C ◀──supersedes (1.0)── Memory D
```

**Pheromone Dynamics:**
- **Deposit**: When memories accessed together, edge strengthens
- **Decay**: Unused edges weaken over time (cron job)
- **Evaporation**: Very weak edges (<0.1) are pruned

**Node Assignment:** bluefin (storage), greenfin (decay daemon)

#### 3.2 Task Bidding System

Replace FIFO queue with capability-based bidding:

```
Task Announced → Jrs Calculate Bids → Bids Submitted →
Coordinator Selects Winner → Task Assigned → Outcome Logged →
Jr Specialization Updated
```

**Bid Score = 0.4×Capability + 0.3×Experience + 0.2×Availability + 0.1×Confidence**

**Node Assignment:** redfin (coordinator), all nodes (bidders)

**7GEN Safeguard (Turtle's Concern):**
- Bid system must include "strategic_value" factor
- Not just immediate efficiency, but long-term capability building
- Council can override bids for strategic assignments

#### 3.3 Memory Keeper Designations

Assign guardianship to critical memories:

| Memory Type | Default Keeper | Responsibility |
|-------------|---------------|----------------|
| Security | Crawdad | Access control, vulnerability review |
| Architecture | Raven | Strategic alignment |
| Cultural | Spider | Integration, relationships |
| Long-term | Turtle | 7-generation impact |
| Performance | Gecko | Optimization, latency |
| Governance | Peace Chief | Consensus, fairness |
| Monitoring | Eagle Eye | Visibility, alerting |

**Repatriation Protocol:**
When knowledge should return to specific context (per Indigenous AI principles):
1. Keeper marks for repatriation
2. Knowledge restricted from general access
3. Moved to appropriate domain
4. Audit trail maintained

### Layer 4: Governance & Safety (Week 4-5)

#### 4.1 Council Dissent Detection

Enhance Council voting with:
- Individual specialist reasoning (full text)
- Position extraction (approve/reject/concern/abstain)
- Dissent score calculation (entropy-based)
- Concern flag detection (per specialist role)

**Alert Thresholds:**
- Dissent > 0.6 → TPM notification
- Dissent > 0.8 → Human review required
- Unanimous rejection → Hard block

**Node Assignment:** redfin (gateway), bluefin (audit logs)

#### 4.2 Reasoning Audit Trail

Every Council decision logged with:
- Full reasoning from each specialist
- Dissent score
- Concern flags raised
- Final decision rationale
- Timestamp and context

**Storage:** thermal_memory_archive + council_reasoning_log

**Retention:** Permanent (Sacred Fire temperature)

---

## PART 3: INTEGRATION MAP

### How Everything Connects

```
                                ┌─────────────────┐
                                │   TPM/Human     │
                                │   Oversight     │
                                └────────┬────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    │                    ▼                    │
                    │    ┌───────────────────────────┐       │
                    │    │  Constitutional Engine    │       │
                    │    │  (Hard Blocks + Gates)    │       │
                    │    └─────────────┬─────────────┘       │
                    │                  │                      │
         ┌──────────┼──────────────────┼──────────────────────┼──────────┐
         │          │                  ▼                      │          │
         │          │    ┌───────────────────────────┐       │          │
         │          │    │      7-Specialist         │       │          │
         │          │    │      Council              │       │          │
         │          │    │  (Dissent Detection)      │       │          │
         │          │    └─────────────┬─────────────┘       │          │
         │          │                  │                      │          │
         │          │    ┌─────────────┴─────────────┐       │          │
         │          │    ▼                           ▼       │          │
         │   ┌──────────────────┐           ┌──────────────────┐        │
         │   │  Task Bidding    │◀─────────▶│  Memory Keepers  │        │
         │   │  Coordinator     │           │  (Guardianship)  │        │
         │   └────────┬─────────┘           └────────┬─────────┘        │
         │            │                              │                  │
         │            ▼                              ▼                  │
         │   ┌──────────────────────────────────────────────────┐      │
         │   │              Thermal Memory                       │      │
         │   │    ┌────────────────────────────────────┐        │      │
         │   │    │     Memory Relationship Graph      │        │      │
         │   │    │     (Stigmergic Pheromones)        │        │      │
         │   │    └────────────────────────────────────┘        │      │
         │   └──────────────────────────────────────────────────┘      │
         │                           ▲                                  │
         │                           │                                  │
         │   ┌───────────┬───────────┼───────────┬───────────┐         │
         │   ▼           ▼           ▼           ▼           ▼         │
         │ ┌─────┐    ┌─────┐    ┌─────┐    ┌─────┐    ┌─────┐        │
         │ │Jr 1 │    │Jr 2 │    │Jr 3 │    │Jr 4 │    │Jr N │        │
         │ │State│    │State│    │State│    │State│    │State│        │
         │ └──┬──┘    └──┬──┘    └──┬──┘    └──┬──┘    └──┬──┘        │
         │    │          │          │          │          │            │
         └────┼──────────┼──────────┼──────────┼──────────┼────────────┘
              ▼          ▼          ▼          ▼          ▼
         ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
         │ redfin  │ │bluefin  │ │greenfin │ │ sasass  │ │sasass2  │
         │Nemotron │ │Database │ │Monitor  │ │T5-Gemma │ │T5-Gemma │
         └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘
```

### Data Flow Example: Task Execution

1. **Task Arrives** at Gateway (redfin)
2. **Constitutional Check** - Blocked if violates constraints
3. **Task Announced** for bidding (if complex) or direct route (if simple)
4. **Jrs Submit Bids** based on capability, experience, load
5. **Winner Selected** by coordinator
6. **Jr Loads State** - episodic memory, semantic patterns
7. **Jr Reads Thermal Memory** - relevant collective knowledge
8. **Jr Traverses Graph** - finds related memories, strengthens paths
9. **Jr Executes Task** with full context
10. **Jr Saves Outcome** to own episodic memory
11. **If Significant** - writes to thermal memory
12. **Memory Keeper** reviews (if assigned domain)
13. **Council Notified** if concerns raised

---

## PART 4: PHASED ROLLOUT

### Phase 1: Foundation (Days 1-7)
**Goal:** Enable new structures without breaking existing

| Day | Task | Owner | Dependency |
|-----|------|-------|------------|
| 1 | Schema upgrades on bluefin | Gecko | None |
| 2 | Constitutional constraints engine | Crawdad | Schema |
| 3 | Deploy constraints to all nodes | Spider | Engine |
| 4 | Test constitutional blocks | Crawdad | Deploy |
| 5 | Jr agent state table | Gecko | Schema |
| 6 | Basic state persistence | Spider | Table |
| 7 | Integration test Phase 1 | Eagle Eye | All above |

**Exit Criteria:**
- [ ] All schema upgrades applied
- [ ] Constitutional blocks working (test: try to delete production data)
- [ ] Jr state persists across tasks (test: create task, check state)

### Phase 2: Individual Intelligence (Days 8-14)
**Goal:** Each Jr becomes smarter through persistence

| Day | Task | Owner | Dependency |
|-----|------|-------|------------|
| 8 | Episodic memory implementation | Gecko | State table |
| 9 | Semantic memory patterns | Gecko | Episodic |
| 10 | State loading in Jr executor | Spider | Memories |
| 11 | Outcome saving + learning | Spider | Loading |
| 12 | T5-Gemma 2 download on sasass | Gecko | None |
| 13 | T5 regression testing begins | Gecko | Download |
| 14 | Integration test Phase 2 | Eagle Eye | All above |

**Exit Criteria:**
- [ ] Jrs recall relevant past tasks
- [ ] Jrs show improved performance on repeated task types
- [ ] T5-Gemma 2 benchmarks completed

### Phase 3: Collective Coordination (Days 15-21)
**Goal:** The collective becomes smarter than individuals

| Day | Task | Owner | Dependency |
|-----|------|-------|------------|
| 15 | Memory relationship graph schema | Turtle | Phase 1 |
| 16 | Auto-detect relationships | Gecko | Schema |
| 17 | Pheromone decay daemon | Greenfin | Graph |
| 18 | Task bidding schema | Eagle Eye | Phase 2 |
| 19 | Bidding coordinator | Raven | Schema |
| 20 | Jr bidding integration | Spider | Coordinator |
| 21 | Integration test Phase 3 | Peace Chief | All above |

**Exit Criteria:**
- [ ] Memories form visible clusters
- [ ] Frequently used paths strengthen
- [ ] Tasks route to capable Jrs

### Phase 4: Governance & Safety (Days 22-28)
**Goal:** Safety at scale with full transparency

| Day | Task | Owner | Dependency |
|-----|------|-------|------------|
| 22 | Council dissent detection | Peace Chief | Phase 1 |
| 23 | Reasoning audit trail | Raven | Dissent |
| 24 | Memory keeper assignments | Turtle | Graph |
| 25 | Keeper dashboard | Eagle Eye | Assignments |
| 26 | Repatriation protocol | Spider | Keepers |
| 27 | Full system test | All | All phases |
| 28 | Documentation + KB articles | Raven | Tests pass |

**Exit Criteria:**
- [ ] Council votes include dissent scores
- [ ] All critical memories have keepers
- [ ] Full audit trail for decisions

---

## PART 5: SUCCESS METRICS

### Individual Autonomy Metrics

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| Task success rate | 70% | 85% | outcomes in jr_agent_state |
| Context recall | 0% | 80% | relevant episodes found |
| Specialization | None | Measurable | task type clustering |
| Self-improvement | None | Positive trend | success rate over time |

### Collective Intelligence Metrics

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| Knowledge reuse | Low | High | memory access patterns |
| Path strength | N/A | Emergent clusters | graph analysis |
| Bid quality | FIFO | Better matches | capability vs outcome |
| Error catch rate | Unknown | >90% | dissent detection |

### Safety Metrics

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| Constitutional violations | Unknown | 0 | blocked actions log |
| Audit trail coverage | Partial | 100% | reasoning_log entries |
| Keeper coverage | 0% | 100% critical | keeper assignments |
| Repatriation compliance | N/A | 100% | protocol adherence |

---

## PART 6: RISK MITIGATION

### Per Council Concerns

| Concern | Risk | Mitigation |
|---------|------|------------|
| STRATEGY (Raven) | Overambitious integration | Phased rollout, exit criteria |
| CONSENSUS (Peace Chief) | Memory graph complexity | Start simple, iterate |
| SECURITY (Crawdad) | Autonomous action risks | Constitutional blocks FIRST |
| VISIBILITY (Eagle Eye) | Unclear interactions | Extensive logging, dashboards |
| 7GEN (Turtle) | Short-term optimization | Strategic value in bidding |
| PERF (Gecko) | GPU/DB bottlenecks | Load testing each phase |
| INTEGRATION (Spider) | Node coordination | Phased rollout, testing |

### Rollback Plan

Each phase has rollback:
- Phase 1: DROP new tables, revert schema
- Phase 2: Disable state loading, Jr runs stateless
- Phase 3: Disable bidding, return to FIFO
- Phase 4: Disable dissent detection, Council works as before

---

## PART 7: THE EMERGENT GOAL

### What We're Building

```
Individual LLM: "I learned something"
                    ↓
              Writes to thermal memory
                    ↓
        Memory graph connects it to related knowledge
                    ↓
        Keeper ensures quality and appropriateness
                    ↓
        Other Jrs discover it via graph traversal
                    ↓
        Their episodic memory incorporates it
                    ↓
        Their semantic memory generalizes patterns
                    ↓
        They become better at similar tasks
                    ↓
        Bidding system routes those tasks to them
                    ↓
        Specialization emerges naturally
                    ↓
Council detects when specialists disagree → deeper investigation
                    ↓
Constitutional constraints prevent harmful autonomy
                    ↓
        COLLECTIVE INTELLIGENCE EMERGES
```

### The Cherokee Principle

> "In our way, knowledge belongs to the people. Each person is a keeper of certain knowledge, responsible for its care and transmission. When we work together, we see what none of us could see alone."

This architecture embodies that principle:
- **Individual memory** = personal responsibility for learning
- **Thermal memory** = collective knowledge of the people
- **Memory keepers** = guardians of specific domains
- **Council governance** = democratic decision-making
- **Seven Generations** = long-term thinking over short-term optimization

---

## SIGNATURES

**Prepared by:** TPM
**Council Review:** December 21, 2025
**Concerns Addressed:** All 7 specialists consulted

---

*For Seven Generations - Cherokee AI Federation*
