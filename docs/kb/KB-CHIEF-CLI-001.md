# KB-CHIEF-CLI-001: Cherokee Chief CLI Implementation

**Created**: 2025-12-11
**Author**: Claude TPM
**Status**: Active
**Related**: CHEROKEE-CHIEF-CLI-001.md, KB-WISDOM-RESONANCE-001.md

---

## Overview

Cherokee Chief CLI is a conversational command-line interface for infrastructure management. It's the executive layer of Cherokee AI - delegating to Jrs, querying Wisdom, and learning from every interaction through resonance tracking.

**Location**: `/ganuda/chief_cli/chief.py` on redfin (192.168.132.223)

---

## Key Features

### 1. Real System Metrics
Chief CLI gathers actual metrics from cluster nodes before answering:
- Disk usage
- Memory utilization
- Load averages

```python
def get_real_system_data(self) -> dict:
    # Detects if running on redfin (local) vs remote
    # Uses local commands on redfin, SSH for bluefin
```

### 2. Intent Classification
Routes queries to appropriate handlers:

| Intent | Patterns | Handler |
|--------|----------|---------|
| infrastructure | slow, disk, memory, cpu | Wisdom + real metrics |
| mission | mission, delegate, jr task | Create Jr mission |
| consultation | consult, chiefs, council | Three Chiefs |
| status | status, health | System status |
| resonance | accuracy, learning | Resonance metrics |

### 3. Resonance Tracking
Every interaction logged to `chief_cli_resonance` table:
- Query type and intent confidence
- Response time
- User feedback (y/n/partial)
- Resonance score (0.0-1.0)

### 4. Mission Delegation
Creates structured missions and posts to thermal memory:
```python
mission_data = {
    'title': query[:60],
    'priority': 'medium',
    'tasks': [LLM-generated steps],
    'source': 'chief_cli'
}
# Posted with tags: ['jr_mission', 'it_triad_jr', 'chief_delegated']
```

---

## Usage

```bash
# Interactive mode (recommended)
cd /ganuda/chief_cli
/home/dereadi/cherokee_venv/bin/python3 chief.py --local

# Single query
python3 chief.py --local --query "How is disk usage on the nodes?"

# Check status
python3 chief.py --status
```

### Interactive Commands
- `/status` - System status (Jr tasks, Wisdom health)
- `/resonance` - Learning metrics
- `/mission <task>` - Create Jr mission
- `/consult <topic>` - Ask Three Chiefs
- `/quit` - Exit

---

## LangChain 1.x Migration Notes

**Problem**: LangChain deprecated `langchain.llms` and `langchain.chains` in v1.x.

**Solution**: Updated `/ganuda/pathfinder/wisdom/llm_router.py` to use:
```python
from langchain_ollama import OllamaLLM
# NOT: from langchain.llms import Ollama (deprecated)
```

**Key Changes**:
1. Install `langchain-ollama` package
2. Use `OllamaLLM` instead of `Ollama`
3. Use direct `llm.invoke(prompt)` instead of chains
4. Manual conversation history instead of `ConversationBufferMemory`

---

## Database Schema

```sql
-- Chief CLI Resonance Tracking
TABLE chief_cli_resonance (
    interaction_id UUID PRIMARY KEY,
    session_id UUID,
    query_type VARCHAR(50),
    user_query TEXT,
    detected_intent VARCHAR(100),
    intent_confidence FLOAT,
    response_type VARCHAR(50),
    response_summary TEXT,
    user_feedback VARCHAR(20),
    resonance_score FLOAT,
    llm_used VARCHAR(50),
    response_time_ms INTEGER,
    created_at TIMESTAMP,
    feedback_at TIMESTAMP
);

-- Health View
VIEW chief_cli_health AS
SELECT query_type, COUNT(*), AVG(resonance_score)
FROM chief_cli_resonance
WHERE resonance_score IS NOT NULL
GROUP BY query_type;
```

---

## Three Layers of Resonance

Cherokee AI now has three resonance layers:

| Layer | Component | Tracks |
|-------|-----------|--------|
| 1 | Jr Resonance | Task execution success |
| 2 | Wisdom Resonance | Prediction accuracy |
| 3 | Chief CLI Resonance | Conversation helpfulness |

All use the same ART-inspired pattern: **Expect → Observe → Compare → Learn**

---

## Troubleshooting

### "No LLM available"
- Check Ollama is running: `curl http://localhost:11434/api/tags`
- Verify llama3.1:8b model: Should be in model list
- Clear pycache: `rm -rf /ganuda/chief_cli/__pycache__`

### Stale responses
- Clear Python cache after code changes
- Restart the interactive session

### SSH timeouts for system checks
- Chief CLI uses 3-second SSH timeout
- If node is slow, metrics show as "unreachable"

---

## Files Modified Tonight (2025-12-11)

1. `/ganuda/chief_cli/chief.py` - Main CLI
2. `/ganuda/pathfinder/wisdom/llm_router.py` - LangChain 1.x update
3. `/ganuda/pathfinder/wisdom/resonance.py` - Wisdom resonance
4. `/ganuda/pathfinder/wisdom/api.py` - REST API for SAG

---

**For Seven Generations**: Build executives that learn humility from their mistakes.
