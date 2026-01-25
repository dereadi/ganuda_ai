# JR Instruction: A-MEM Full Implementation for Thermal Memory

**Task ID:** AMEM-THERMAL-001
**Priority:** P1 - Council Approved
**Type:** implementation
**Assigned:** Infrastructure Jr.
**Council Vote:** 4-3 (Full Implementation)

---

## Objective

Implement full A-MEM (Agentic Memory) architecture for Thermal Memory enhancement, including episodic/semantic/procedural memory types and consolidation.

---

## Background

Council voted 4-3 for full implementation over targeted enhancement.
Reference: arXiv:2502.12110 (A-MEM: Agentic Memory for LLM Agents)

Current Thermal Memory:
- Temperature-based decay (0.0-1.0)
- Simple retrieval by recency/temperature
- No memory type classification

---

## Deliverables

### 1. Memory Type Enum
Create `/ganuda/lib/amem_types.py`:
```python
from enum import Enum

class MemoryType(Enum):
    EPISODIC = "episodic"    # Specific experiences: "Jr completed task X"
    SEMANTIC = "semantic"     # Extracted patterns: "Users prefer wizard flow"
    PROCEDURAL = "procedural" # How-to: "Deploy with: ansible-playbook..."
```

### 2. Enhanced Thermal Memory Schema
Add to PostgreSQL:
```sql
ALTER TABLE thermal_memory ADD COLUMN IF NOT EXISTS memory_type VARCHAR(20) DEFAULT 'episodic';
ALTER TABLE thermal_memory ADD COLUMN IF NOT EXISTS consolidated_from INTEGER[];
ALTER TABLE thermal_memory ADD COLUMN IF NOT EXISTS consolidation_count INTEGER DEFAULT 0;
```

### 3. Memory Classification Function
In `/ganuda/lib/amem_classifier.py`:
- Classify incoming memories by type
- Use keyword patterns: "how to", "always", "completed task"
- LLM fallback for ambiguous cases

### 4. Agentic Retrieval
Enhance retrieval to consider:
- Semantic similarity to current task
- Memory type matching (procedural for how-to queries)
- Temperature weighting
- Consolidation boost for well-validated memories

### 5. Consolidation Daemon
Create `/ganuda/daemons/memory_consolidation_daemon.py`:
- Run hourly
- Find similar episodic memories
- Consolidate into semantic memories
- Track consolidation lineage

---

## Implementation Steps

1. Create amem_types.py with MemoryType enum
2. Run schema migration for memory_type column
3. Create amem_classifier.py with classification logic
4. Modify thermal_memory retrieval to use types
5. Create consolidation daemon
6. Add systemd service for daemon

---

## Testing

1. Insert test memories of each type
2. Verify classification accuracy
3. Test retrieval with type matching
4. Run consolidation on test episodic memories
5. Verify consolidated semantic memory quality

---

## Tribal Awareness

**Benefit Who?** All Jr agents and future AI systems
**Benefit How?** Institutional knowledge grows instead of resetting
**At Whose Expense?** Storage costs (minimal), processing time (consolidation is async)

---

## For Seven Generations

Memory that learns and consolidates means future generations of Jrs inherit wisdom, not just data.
