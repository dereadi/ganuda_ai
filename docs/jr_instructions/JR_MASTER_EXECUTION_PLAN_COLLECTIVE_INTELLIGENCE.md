# Jr Master Execution Plan: Collective Intelligence Build

**Created:** December 21, 2025
**Source:** Council-approved architecture
**Duration:** 28 days (4 phases)
**Goal:** Autonomous LLMs + Collective Intelligence > Sum of Parts

---

## PHASE 1: FOUNDATION (Days 1-7)

### Day 1: Schema Upgrades
**Node:** bluefin
**Owner:** Gecko

```sql
-- Run on bluefin as claude user
PGPASSWORD='jawaseatlasers2' psql -h 192.168.132.222 -U claude -d zammad_production << 'EOF'

-- Memory relationships for stigmergic graph
CREATE TABLE IF NOT EXISTS memory_relationships (
    id SERIAL PRIMARY KEY,
    source_hash VARCHAR(128) NOT NULL,
    target_hash VARCHAR(128) NOT NULL,
    relationship_type VARCHAR(32) NOT NULL,
    strength FLOAT DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT NOW(),
    last_traversed TIMESTAMP,
    traversal_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    UNIQUE(source_hash, target_hash, relationship_type)
);

CREATE INDEX IF NOT EXISTS idx_memory_rel_source ON memory_relationships(source_hash);
CREATE INDEX IF NOT EXISTS idx_memory_rel_target ON memory_relationships(target_hash);
CREATE INDEX IF NOT EXISTS idx_memory_rel_strength ON memory_relationships(strength DESC);

-- Keeper designations
ALTER TABLE thermal_memory_archive ADD COLUMN IF NOT EXISTS keeper_type VARCHAR(32);
ALTER TABLE thermal_memory_archive ADD COLUMN IF NOT EXISTS keeper_id VARCHAR(64);
ALTER TABLE thermal_memory_archive ADD COLUMN IF NOT EXISTS keeper_assigned_at TIMESTAMP;
ALTER TABLE thermal_memory_archive ADD COLUMN IF NOT EXISTS repatriation_context VARCHAR(128);
ALTER TABLE thermal_memory_archive ADD COLUMN IF NOT EXISTS access_restrictions JSONB DEFAULT '{}';

-- Memory keepers registry
CREATE TABLE IF NOT EXISTS memory_keepers (
    keeper_id VARCHAR(64) PRIMARY KEY,
    keeper_type VARCHAR(32) NOT NULL,
    keeper_name VARCHAR(128) NOT NULL,
    responsibilities TEXT[],
    contact_method VARCHAR(128),
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Jr agent state persistence
CREATE TABLE IF NOT EXISTS jr_agent_state (
    agent_id VARCHAR(64) PRIMARY KEY,
    node_name VARCHAR(32) NOT NULL,
    specialization VARCHAR(64),
    working_memory JSONB DEFAULT '{}',
    episodic_memory JSONB DEFAULT '[]',
    semantic_memory JSONB DEFAULT '{}',
    tasks_completed INTEGER DEFAULT 0,
    success_rate FLOAT DEFAULT 0.0,
    specialization_scores JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    last_active TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_jr_agent_node ON jr_agent_state(node_name);

-- Council reasoning audit trail
CREATE TABLE IF NOT EXISTS council_reasoning_log (
    id SERIAL PRIMARY KEY,
    vote_id INTEGER,
    specialist VARCHAR(32) NOT NULL,
    position VARCHAR(16) NOT NULL,
    confidence FLOAT,
    reasoning TEXT NOT NULL,
    concern_flags TEXT[],
    created_at TIMESTAMP DEFAULT NOW()
);

-- Task bidding tables
CREATE TABLE IF NOT EXISTS jr_task_announcements (
    task_id VARCHAR(64) PRIMARY KEY,
    task_type VARCHAR(64) NOT NULL,
    task_content TEXT NOT NULL,
    required_capabilities TEXT[],
    preferred_node VARCHAR(32),
    priority INTEGER DEFAULT 5,
    deadline TIMESTAMP,
    announced_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(16) DEFAULT 'open',
    assigned_to VARCHAR(64),
    winning_bid_id INTEGER,
    metadata JSONB DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS jr_task_bids (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(64) REFERENCES jr_task_announcements(task_id),
    agent_id VARCHAR(64) NOT NULL,
    node_name VARCHAR(32) NOT NULL,
    capability_score FLOAT,
    experience_score FLOAT,
    load_score FLOAT,
    confidence FLOAT,
    composite_score FLOAT,
    bid_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_bids_task ON jr_task_bids(task_id);
CREATE INDEX IF NOT EXISTS idx_bids_score ON jr_task_bids(composite_score DESC);

-- Insert council specialists as keepers
INSERT INTO memory_keepers (keeper_id, keeper_type, keeper_name, responsibilities) VALUES
('crawdad', 'specialist', 'Crawdad', ARRAY['security', 'access_control', 'vulnerability']),
('gecko', 'specialist', 'Gecko', ARRAY['technical', 'integration', 'performance']),
('turtle', 'specialist', 'Turtle', ARRAY['long_term', 'seven_generations', 'sustainability']),
('eagle_eye', 'specialist', 'Eagle Eye', ARRAY['monitoring', 'visibility', 'observability']),
('spider', 'specialist', 'Spider', ARRAY['cultural', 'integration', 'connections']),
('peace_chief', 'specialist', 'Peace Chief', ARRAY['governance', 'consensus', 'coordination']),
('raven', 'specialist', 'Raven', ARRAY['strategy', 'planning', 'architecture'])
ON CONFLICT (keeper_id) DO NOTHING;

-- Insert nodes as keepers
INSERT INTO memory_keepers (keeper_id, keeper_type, keeper_name, responsibilities) VALUES
('redfin', 'node', 'Redfin', ARRAY['gpu_inference', 'llm_gateway', 'sag_ui']),
('bluefin', 'node', 'Bluefin', ARRAY['database', 'memory_storage', 'grafana']),
('greenfin', 'node', 'Greenfin', ARRAY['monitoring', 'promtail', 'daemons']),
('sasass', 'node', 'Sasass', ARRAY['edge_development', 'mac_studio']),
('sasass2', 'node', 'Sasass2', ARRAY['edge_development', 'mac_studio']),
('tpm', 'node', 'TPM Macbook', ARRAY['orchestration', 'planning', 'claude_code'])
ON CONFLICT (keeper_id) DO NOTHING;

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_thermal_temp ON thermal_memory_archive(temperature_score DESC);
CREATE INDEX IF NOT EXISTS idx_thermal_created ON thermal_memory_archive(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_thermal_keeper ON thermal_memory_archive(keeper_id);

EOF
```

**Verification:**
```sql
\dt  -- Should show new tables
SELECT COUNT(*) FROM memory_keepers;  -- Should be 13
```

---

### Day 2-3: Constitutional Constraints Engine
**Node:** redfin
**Owner:** Crawdad

Create `/ganuda/lib/constitutional_constraints.py` with:
- Hard blocks (see JR_CONSTITUTIONAL_CONSTRAINTS.md)
- Approval gates
- Logging to thermal memory

**Test Cases:**
```bash
# Test hard block - should fail
python -c "from constitutional_constraints import check_action; print(check_action({'type': 'database', 'sql': 'DROP TABLE users'}))"
# Expected: (False, 'BLOCKED: Destructive database operations...')

# Test allow - should pass
python -c "from constitutional_constraints import check_action; print(check_action({'type': 'database', 'sql': 'SELECT * FROM users'}))"
# Expected: (True, 'Action allowed')
```

---

### Day 4: Deploy Constraints to All Nodes
**Node:** All
**Owner:** Spider

Copy constitutional_constraints.py to:
- `/ganuda/lib/` on redfin, bluefin, greenfin
- `/Users/Shared/ganuda/lib/` on sasass, sasass2, tpm

Create symlinks or package for import.

---

### Day 5-6: Jr Agent State Persistence
**Node:** redfin
**Owner:** Gecko

Create `/ganuda/lib/jr_state_manager.py` with:
- State loading
- Episodic memory management
- Semantic memory updates
- See JR_AGENT_STATE_PERSISTENCE.md

---

### Day 7: Phase 1 Integration Test
**Node:** All
**Owner:** Eagle Eye

```bash
# Test 1: Schema exists
ssh dereadi@192.168.132.223 "PGPASSWORD='jawaseatlasers2' psql -h 192.168.132.222 -U claude -d zammad_production -c '\dt'"

# Test 2: Constitutional blocks work
# Try to execute blocked action, verify it fails

# Test 3: Jr state persists
# Create Jr, execute task, check state saved

# Test 4: Keepers assigned
SELECT COUNT(*) FROM memory_keepers;
```

---

## PHASE 2: INDIVIDUAL INTELLIGENCE (Days 8-14)

### Day 8-9: Episodic Memory Implementation
**Node:** redfin
**Owner:** Gecko

Extend jr_state_manager.py:
- Store last 50 tasks
- Include outcomes, timestamps, learnings
- Prune old entries

---

### Day 10-11: Semantic Memory & Task Integration
**Node:** redfin
**Owner:** Spider

Modify Jr executor to:
1. Load state at task start
2. Check relevant episodes
3. Execute with context
4. Save outcome
5. Update semantic patterns

---

### Day 12-13: T5-Gemma 2 Download & Testing
**Node:** sasass
**Owner:** Gecko

```bash
# On sasass (Mac Studio)
cd /Users/Shared/ganuda/models

# Create virtual environment
python3 -m venv t5_venv
source t5_venv/bin/activate

# Install dependencies
pip install transformers accelerate torch

# Download models
huggingface-cli download google/t5-gemma-2-1b-it

# Run basic test
python -c "
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
model = AutoModelForSeq2SeqLM.from_pretrained('google/t5-gemma-2-1b-it')
tokenizer = AutoTokenizer.from_pretrained('google/t5-gemma-2-1b-it')
print('Model loaded successfully')
"
```

Begin regression testing per JR_T5_GEMMA2_REGRESSION_TESTING.md

---

### Day 14: Phase 2 Integration Test
**Node:** All
**Owner:** Eagle Eye

```bash
# Test 1: Jr recalls past tasks
# Execute similar task twice, verify context from first informs second

# Test 2: Semantic patterns emerge
SELECT agent_id, semantic_memory FROM jr_agent_state WHERE semantic_memory != '{}';

# Test 3: T5-Gemma 2 responds
curl -X POST http://sasass:8080/v1/understand -d '{"text": "Summarize this document..."}'
```

---

## PHASE 3: COLLECTIVE COORDINATION (Days 15-21)

### Day 15-16: Memory Relationship Graph
**Node:** bluefin
**Owner:** Turtle

Create `/ganuda/lib/memory_graph.py`:
- add_relationship()
- find_related()
- auto_detect_relationships()
- strengthen_path()

See JR_MEMORY_RELATIONSHIP_GRAPH.md

---

### Day 17: Pheromone Decay Daemon
**Node:** greenfin
**Owner:** Greenfin daemon

Add to `/ganuda/scripts/pheromone_decay.sh`:
```bash
# Decay relationship strengths
PGPASSWORD='jawaseatlasers2' psql -h 192.168.132.222 -U claude -d zammad_production << 'EOF'
UPDATE memory_relationships
SET strength = strength * 0.95
WHERE last_traversed IS NULL
   OR last_traversed < NOW() - INTERVAL '30 days';

DELETE FROM memory_relationships WHERE strength < 0.1;
EOF
```

Add to crontab on greenfin.

---

### Day 18-20: Task Bidding System
**Node:** redfin (coordinator), all (bidders)
**Owner:** Raven

Create `/ganuda/lib/task_bidding.py`:
- TaskAnnouncer
- JrBidder
- BiddingCoordinator

See JR_TASK_BIDDING_SYSTEM.md

Integrate with Gateway:
```python
# In gateway.py
@app.post("/v1/task/submit")
async def submit_task(request: TaskRequest):
    coordinator = BiddingCoordinator()
    result = await coordinator.submit_task(
        request.task_type,
        request.content,
        priority=request.priority
    )
    return result
```

---

### Day 21: Phase 3 Integration Test
**Node:** All
**Owner:** Peace Chief

```bash
# Test 1: Memory graph forms
SELECT COUNT(*) FROM memory_relationships;
SELECT source_hash, target_hash, strength FROM memory_relationships ORDER BY strength DESC LIMIT 10;

# Test 2: Pheromone decay runs
# Check cron logs, verify strength decreased

# Test 3: Task bidding works
# Submit task, verify bids received, winner selected
```

---

## PHASE 4: GOVERNANCE & SAFETY (Days 22-28)

### Day 22-23: Council Dissent Detection
**Node:** redfin
**Owner:** Peace Chief

Modify Gateway council endpoint:
- Extract individual positions
- Calculate dissent score
- Log to council_reasoning_log
- Alert on high dissent

See JR_COUNCIL_DISSENT_DETECTION.md

---

### Day 24-25: Memory Keeper Assignments
**Node:** bluefin
**Owner:** Turtle

Create `/ganuda/lib/keeper_assignment.py`:
- Auto-assign based on content/metadata
- Manual assignment API
- Keeper dashboard queries

See JR_MEMORY_KEEPER_DESIGNATIONS.md

Run backfill to assign keepers to existing memories:
```sql
UPDATE thermal_memory_archive
SET keeper_id = 'raven', keeper_type = 'specialist'
WHERE metadata->>'type' IN ('research', 'strategy', 'architecture');

UPDATE thermal_memory_archive
SET keeper_id = 'crawdad', keeper_type = 'specialist'
WHERE metadata->>'type' IN ('security', 'vulnerability');
-- etc.
```

---

### Day 26: Repatriation Protocol
**Node:** bluefin
**Owner:** Spider

Implement repatriation_knowledge() function.
Create audit trail for repatriated knowledge.

---

### Day 27: Full System Test
**Node:** All
**Owner:** All specialists

**Test Scenario: Complete Task Flow**

1. Submit complex task to Gateway
2. Verify constitutional check passes
3. Verify task announced for bidding
4. Verify Jrs submit bids with scores
5. Verify winner selected, task assigned
6. Verify Jr loads state, finds relevant memories
7. Verify Jr traverses graph, strengthens paths
8. Verify Jr executes task
9. Verify outcome saved to episodic memory
10. Verify significant result written to thermal memory
11. Verify keeper assigned
12. Verify Council can query with dissent detection

---

### Day 28: Documentation & KB Articles
**Node:** tpm
**Owner:** Raven

Create KB articles:
- How to deploy new Jr
- How to add constitutional constraint
- How to become memory keeper
- How to analyze dissent patterns
- How to debug task bidding

Update CMDB with new tables, services, daemons.

---

## VERIFICATION CHECKLIST

### Phase 1 Exit Criteria
- [ ] All 7 new tables created
- [ ] 13 memory keepers registered
- [ ] Constitutional blocks tested
- [ ] Jr state table populated

### Phase 2 Exit Criteria
- [ ] Jrs maintain episodic memory
- [ ] Jrs show learning over time
- [ ] T5-Gemma 2 benchmarks complete

### Phase 3 Exit Criteria
- [ ] Memory graph has edges
- [ ] Pheromone decay running
- [ ] Task bidding functional

### Phase 4 Exit Criteria
- [ ] Dissent scores calculated
- [ ] All critical memories have keepers
- [ ] Full audit trail available
- [ ] KB articles published

---

## ROLLBACK PROCEDURES

### Phase 1 Rollback
```sql
DROP TABLE IF EXISTS memory_relationships;
DROP TABLE IF EXISTS memory_keepers;
DROP TABLE IF EXISTS jr_agent_state;
DROP TABLE IF EXISTS council_reasoning_log;
DROP TABLE IF EXISTS jr_task_announcements;
DROP TABLE IF EXISTS jr_task_bids;
ALTER TABLE thermal_memory_archive DROP COLUMN IF EXISTS keeper_type;
ALTER TABLE thermal_memory_archive DROP COLUMN IF EXISTS keeper_id;
-- etc.
```

### Phase 2 Rollback
- Remove state loading from Jr executor
- Jrs run stateless (existing behavior)

### Phase 3 Rollback
- Disable bidding, return to FIFO queue
- Remove pheromone decay from cron

### Phase 4 Rollback
- Disable dissent calculation
- Council returns to simple consensus

---

## CONTACT

**TPM:** Available via Telegram group
**Escalation:** Create Jr task with priority P1
**Emergency:** Direct SSH to affected node

---

*For Seven Generations - Cherokee AI Federation*
