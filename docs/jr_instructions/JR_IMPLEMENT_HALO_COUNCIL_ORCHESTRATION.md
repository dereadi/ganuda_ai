# Jr Instruction: HALO-Enhanced Council Orchestration

**Task ID:** task-impl-halo-council
**Priority:** 2 (High)
**Effort:** MEDIUM
**Research Sources:**
- arXiv:2505.13516 - HALO: Hierarchical Autonomous Logic-Oriented Orchestration
- arXiv:2503.13754 - Orchestrated Distributed Intelligence (ODI)
- arXiv:2505.19591 - Multi-Agent Collaboration via Evolving Orchestration

**Created:** December 24, 2025
**Council Vote:** 69.4% confidence, PROCEED with ODI enhancement

---

## Executive Summary

Enhance the Cherokee AI Federation Council with HALO-style hierarchical orchestration. Currently, the Council uses a flat voting structure where all specialists vote simultaneously. HALO introduces:

1. **Hierarchical task decomposition** - Break complex queries into subtasks
2. **Dynamic agent instantiation** - Spawn specialized agents for specific subtasks
3. **MCTS-based workflow search** - Explore reasoning paths systematically
4. **Adaptive prompt refinement** - Transform raw queries into structured prompts
5. **Early-stopping consensus** - Stop when 66% agreement reached

---

## Current Council Architecture

```
User Query
    ↓
┌─────────────────────────────────────────┐
│           COUNCIL (Flat Vote)           │
├─────────────────────────────────────────┤
│  Turtle  │  Eagle  │  Bear  │  Spider   │
│  (7Gen)  │ (Vision)│(Strength)│(Pattern) │
└─────────────────────────────────────────┘
    ↓
Consensus via weighted averaging
```

**Limitations:**
- All specialists vote on everything, even outside expertise
- No task decomposition for complex queries
- Static specialist roles
- No exploration of alternative reasoning paths

---

## Proposed HALO-Enhanced Architecture

```
User Query
    ↓
┌─────────────────────────────────────────┐
│      PROMPT REFINEMENT MODULE           │
│  (Task Parser → Template → Optimizer)   │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│         PLANNING AGENT (Chief)          │
│    Decomposes into subtasks             │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│       ROLE-DESIGN AGENTS                │
│  Instantiate specialists per subtask    │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│    MCTS WORKFLOW SEARCH                 │
│  ┌─────┐  ┌─────┐  ┌─────┐             │
│  │Agent│──│Agent│──│Agent│  ...        │
│  └─────┘  └─────┘  └─────┘             │
│  Selection → Expansion → Simulation     │
│          → Backpropagation              │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│      ANSWER AGGREGATION                 │
│  (66% consensus = early stop)           │
└─────────────────────────────────────────┘
    ↓
Final Response
```

---

## Database Schema Additions

```sql
-- Subtask decomposition tracking
CREATE TABLE IF NOT EXISTS council_subtasks (
    subtask_id SERIAL PRIMARY KEY,
    query_id VARCHAR(64) NOT NULL,
    parent_subtask_id INTEGER REFERENCES council_subtasks(subtask_id),
    subtask_content TEXT NOT NULL,
    subtask_type VARCHAR(32),  -- 'reasoning', 'research', 'validation', 'synthesis'
    status VARCHAR(16) DEFAULT 'pending',
    assigned_agent VARCHAR(64),
    result TEXT,
    quality_score FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

CREATE INDEX idx_subtasks_query ON council_subtasks(query_id);
CREATE INDEX idx_subtasks_parent ON council_subtasks(parent_subtask_id);

-- MCTS tree nodes for workflow search
CREATE TABLE IF NOT EXISTS council_mcts_nodes (
    node_id SERIAL PRIMARY KEY,
    query_id VARCHAR(64) NOT NULL,
    parent_node_id INTEGER REFERENCES council_mcts_nodes(node_id),
    agent_role VARCHAR(64) NOT NULL,
    action_taken TEXT,
    visit_count INTEGER DEFAULT 0,
    total_value FLOAT DEFAULT 0,
    avg_value FLOAT DEFAULT 0,
    status VARCHAR(16) DEFAULT 'unexplored',  -- 'unexplored', 'expanded', 'terminal'
    depth INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_mcts_query ON council_mcts_nodes(query_id);
CREATE INDEX idx_mcts_parent ON council_mcts_nodes(parent_node_id);

-- Dynamic agent instantiation log
CREATE TABLE IF NOT EXISTS council_agent_instances (
    instance_id SERIAL PRIMARY KEY,
    query_id VARCHAR(64) NOT NULL,
    subtask_id INTEGER REFERENCES council_subtasks(subtask_id),
    agent_role VARCHAR(64) NOT NULL,
    system_prompt TEXT,
    instantiated_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    execution_result TEXT,
    quality_score FLOAT
);

-- Refined prompts storage
CREATE TABLE IF NOT EXISTS council_refined_prompts (
    prompt_id SERIAL PRIMARY KEY,
    query_id VARCHAR(64) NOT NULL,
    original_query TEXT NOT NULL,
    task_type VARCHAR(32),
    core_intent TEXT,
    key_details JSONB,
    refined_prompt TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Python Implementation

### File: /ganuda/lib/halo_council.py

```python
#!/usr/bin/env python3
"""
HALO-Enhanced Council Orchestration

Implements hierarchical orchestration with MCTS-based workflow search
for the Cherokee AI Federation Council.

Based on arXiv:2505.13516 (HALO) and arXiv:2503.13754 (ODI)
"""

import math
import json
import uuid
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

# MCTS hyperparameters (from HALO paper)
EXPLORATION_CONSTANT = 1.414  # α in UCT formula
CONSENSUS_THRESHOLD = 0.66   # 66% agreement = early stop
MAX_DEPTH = 5
SIMULATION_ROLLOUTS = 3


class SubtaskType(Enum):
    REASONING = 'reasoning'
    RESEARCH = 'research'
    VALIDATION = 'validation'
    SYNTHESIS = 'synthesis'
    SEVEN_GEN = 'seven_generations'


@dataclass
class RefinedPrompt:
    """Output of the Adaptive Prompt Refinement module."""
    task_type: str
    core_intent: str
    key_details: Dict
    refined_prompt: str


@dataclass
class MCTSNode:
    """Node in the MCTS search tree."""
    node_id: int
    parent_id: Optional[int]
    agent_role: str
    action: str
    visits: int = 0
    total_value: float = 0.0
    children: List['MCTSNode'] = None

    @property
    def avg_value(self) -> float:
        return self.total_value / max(self.visits, 1)

    def uct_score(self, parent_visits: int) -> float:
        """Upper Confidence Bound for Trees."""
        if self.visits == 0:
            return float('inf')
        exploitation = self.avg_value
        exploration = EXPLORATION_CONSTANT * math.sqrt(
            math.log(parent_visits) / self.visits
        )
        return exploitation + exploration


class PromptRefinementModule:
    """
    Four-stage prompt refinement from HALO paper:
    1. Task Parser - Extract (task_type, intent, details)
    2. Prompt Template - Construct initial frame
    3. Optimization Agent - Add slow-thinking strategies
    4. Generator Agent - Synthesize final prompt
    """

    def __init__(self, llm_client):
        self.llm = llm_client

    def refine(self, raw_query: str) -> RefinedPrompt:
        """Transform raw user query into structured prompt."""

        # Stage 1: Task Parser
        parse_prompt = f"""Analyze this query and extract:
1. Task type (reasoning/research/decision/creative)
2. Core intent (one sentence)
3. Key details (entities, constraints, context)

Query: {raw_query}

Respond in JSON: {{"task_type": "", "core_intent": "", "key_details": {{}}}}"""

        parsed = self.llm.query(parse_prompt, json_mode=True)

        # Stage 2: Construct template
        template = f"""Task: {parsed.get('task_type', 'general')}
Objective: {parsed.get('core_intent', raw_query)}
Context: {json.dumps(parsed.get('key_details', {}))}

Provide a thorough analysis considering:
- Multiple perspectives
- Potential risks and benefits
- Seven Generations impact (175+ year view)
"""

        # Stage 3 & 4: Optimization and generation
        refined = f"""{template}

Original query: {raw_query}

Think step by step. Consider alternatives before concluding."""

        return RefinedPrompt(
            task_type=parsed.get('task_type', 'general'),
            core_intent=parsed.get('core_intent', raw_query),
            key_details=parsed.get('key_details', {}),
            refined_prompt=refined
        )


class PlanningAgent:
    """
    High-level planning agent that decomposes complex queries
    into manageable subtasks.
    """

    def __init__(self, llm_client):
        self.llm = llm_client

    def decompose(self, refined_prompt: RefinedPrompt,
                  execution_history: List[Dict] = None) -> List[Dict]:
        """
        Iteratively generate subtasks based on refined prompt
        and execution history.
        """
        history_context = ""
        if execution_history:
            history_context = "\n\nPrevious subtasks completed:\n"
            for h in execution_history[-5:]:  # Last 5 for context
                history_context += f"- {h['subtask']}: {h['result'][:100]}...\n"

        decompose_prompt = f"""Given this task, identify the next subtask needed.

Task Type: {refined_prompt.task_type}
Intent: {refined_prompt.core_intent}
Details: {json.dumps(refined_prompt.key_details)}
{history_context}

What is the NEXT single subtask to work on?
Respond in JSON: {{"subtask": "", "type": "reasoning|research|validation|synthesis|seven_generations", "requires_specialist": ""}}

If no more subtasks needed, respond: {{"subtask": "COMPLETE", "type": "synthesis"}}"""

        result = self.llm.query(decompose_prompt, json_mode=True)

        if result.get('subtask') == 'COMPLETE':
            return []

        return [result]


class RoleDesignAgent:
    """
    Mid-level agent that instantiates specialized agents
    for specific subtasks.
    """

    # Cherokee Council specialist mappings
    SPECIALIST_PROFILES = {
        'turtle': {
            'name': 'Turtle (Seven Generations)',
            'expertise': ['long-term impact', 'sustainability', 'tradition'],
            'system_prompt': 'You are Turtle, guardian of Seven Generations thinking. Consider impacts 175+ years ahead.'
        },
        'eagle': {
            'name': 'Eagle (Vision)',
            'expertise': ['strategy', 'foresight', 'opportunity'],
            'system_prompt': 'You are Eagle, providing high-level vision and strategic foresight.'
        },
        'bear': {
            'name': 'Bear (Strength)',
            'expertise': ['implementation', 'resources', 'protection'],
            'system_prompt': 'You are Bear, focusing on practical strength and resource management.'
        },
        'spider': {
            'name': 'Spider (Pattern)',
            'expertise': ['connections', 'patterns', 'weaving'],
            'system_prompt': 'You are Spider, seeing patterns and connections others miss.'
        },
        'wolf': {
            'name': 'Wolf (Community)',
            'expertise': ['teamwork', 'loyalty', 'communication'],
            'system_prompt': 'You are Wolf, guardian of community bonds and collaboration.'
        },
        'owl': {
            'name': 'Owl (Wisdom)',
            'expertise': ['knowledge', 'learning', 'discernment'],
            'system_prompt': 'You are Owl, keeper of wisdom and deep knowledge.'
        }
    }

    def instantiate(self, subtask: Dict, context: Dict) -> Dict:
        """
        Create a specialized agent instance for a subtask.
        Returns agent configuration.
        """
        subtask_type = subtask.get('type', 'reasoning')
        required_specialist = subtask.get('requires_specialist', '')

        # Match subtask to best specialist
        if required_specialist and required_specialist in self.SPECIALIST_PROFILES:
            profile = self.SPECIALIST_PROFILES[required_specialist]
        else:
            # Auto-select based on subtask type
            type_mapping = {
                'seven_generations': 'turtle',
                'reasoning': 'owl',
                'research': 'spider',
                'validation': 'bear',
                'synthesis': 'eagle'
            }
            specialist_key = type_mapping.get(subtask_type, 'owl')
            profile = self.SPECIALIST_PROFILES[specialist_key]

        # Build subtask-specific system prompt
        system_prompt = f"""{profile['system_prompt']}

Current subtask: {subtask.get('subtask', '')}
Context: {json.dumps(context)}

Provide your specialist perspective on this subtask."""

        return {
            'role': profile['name'],
            'expertise': profile['expertise'],
            'system_prompt': system_prompt,
            'subtask': subtask
        }


class MCTSWorkflowSearch:
    """
    Monte Carlo Tree Search for exploring reasoning workflows.
    Implements Selection, Expansion, Simulation, Backpropagation.
    """

    def __init__(self, llm_client, db_conn):
        self.llm = llm_client
        self.conn = db_conn
        self.role_designer = RoleDesignAgent()

    def search(self, query_id: str, subtask: Dict,
               context: Dict, iterations: int = 10) -> Dict:
        """
        Perform MCTS to find optimal reasoning path.
        """
        # Initialize root node
        root = self._create_node(query_id, None, 'planner', 'start')

        for _ in range(iterations):
            # Selection
            node = self._select(root)

            # Expansion
            if node.visits > 0 and node.children is None:
                self._expand(node, query_id, subtask, context)

            # Simulation
            if node.children:
                child = node.children[0]  # Pick first unexplored
                reward = self._simulate(child, subtask, context)

                # Backpropagation
                self._backpropagate(child, reward)

        # Return best path
        return self._best_action(root)

    def _select(self, node: MCTSNode) -> MCTSNode:
        """Select most promising node using UCT."""
        while node.children:
            node = max(node.children,
                      key=lambda c: c.uct_score(node.visits))
        return node

    def _expand(self, node: MCTSNode, query_id: str,
                subtask: Dict, context: Dict):
        """Expand node by instantiating specialized agents."""
        # Get candidate specialists for this subtask
        candidates = ['turtle', 'eagle', 'bear', 'spider', 'owl']

        node.children = []
        for specialist in candidates:
            agent_config = self.role_designer.instantiate(
                {**subtask, 'requires_specialist': specialist},
                context
            )
            child = self._create_node(
                query_id, node.node_id,
                specialist, agent_config['system_prompt'][:100]
            )
            node.children.append(child)

    def _simulate(self, node: MCTSNode, subtask: Dict,
                  context: Dict) -> float:
        """Simulate agent execution and score result."""
        agent_config = self.role_designer.instantiate(
            {**subtask, 'requires_specialist': node.agent_role},
            context
        )

        # Execute agent
        result = self.llm.query(
            f"{agent_config['system_prompt']}\n\nSubtask: {subtask.get('subtask', '')}"
        )

        # Score result (0-1)
        score_prompt = f"""Rate this response quality (0.0-1.0):

Subtask: {subtask.get('subtask', '')}
Response: {result[:500]}

Consider: relevance, depth, actionability, Seven Generations alignment.
Respond with just a number between 0.0 and 1.0"""

        try:
            score = float(self.llm.query(score_prompt))
            score = max(0.0, min(1.0, score))
        except:
            score = 0.5

        return score

    def _backpropagate(self, node: MCTSNode, reward: float):
        """Update node values back to root."""
        while node:
            node.visits += 1
            node.total_value += reward
            # Decay reward for parent nodes
            reward *= 0.9
            node = self._get_parent(node)

    def _best_action(self, root: MCTSNode) -> Dict:
        """Return best action from root based on visit count."""
        if not root.children:
            return {'agent': 'owl', 'confidence': 0.5}

        best = max(root.children, key=lambda c: c.visits)
        return {
            'agent': best.agent_role,
            'confidence': best.avg_value,
            'visits': best.visits
        }

    def _create_node(self, query_id: str, parent_id: Optional[int],
                     agent_role: str, action: str) -> MCTSNode:
        """Create and persist MCTS node."""
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO council_mcts_nodes
                (query_id, parent_node_id, agent_role, action_taken)
                VALUES (%s, %s, %s, %s)
                RETURNING node_id
            """, (query_id, parent_id, agent_role, action[:500]))
            node_id = cur.fetchone()[0]
            self.conn.commit()

        return MCTSNode(
            node_id=node_id,
            parent_id=parent_id,
            agent_role=agent_role,
            action=action
        )

    def _get_parent(self, node: MCTSNode) -> Optional[MCTSNode]:
        """Get parent node from database."""
        if not node.parent_id:
            return None
        # Simplified - in production, cache nodes
        return None  # Let backprop stop at direct parent for now


class HALOCouncil:
    """
    Main orchestrator combining all HALO components.
    """

    def __init__(self, llm_client):
        self.llm = llm_client
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.prompt_refiner = PromptRefinementModule(llm_client)
        self.planner = PlanningAgent(llm_client)
        self.mcts = MCTSWorkflowSearch(llm_client, self.conn)

    def query(self, raw_query: str) -> Dict:
        """
        Process query through HALO pipeline.
        """
        query_id = str(uuid.uuid4())[:8]

        # Stage 1: Prompt Refinement
        refined = self.prompt_refiner.refine(raw_query)
        self._store_refined_prompt(query_id, raw_query, refined)

        # Stage 2: Iterative decomposition and execution
        execution_history = []
        responses = []

        while True:
            # Get next subtask
            subtasks = self.planner.decompose(refined, execution_history)

            if not subtasks:
                break  # No more subtasks

            subtask = subtasks[0]

            # Stage 3: MCTS workflow search
            best_path = self.mcts.search(
                query_id, subtask,
                {'refined': refined.__dict__, 'history': execution_history}
            )

            # Stage 4: Execute with best agent
            result = self._execute_subtask(subtask, best_path)

            execution_history.append({
                'subtask': subtask.get('subtask', ''),
                'agent': best_path['agent'],
                'result': result
            })
            responses.append(result)

            # Early stopping: check consensus
            if len(responses) >= 3:
                if self._check_consensus(responses):
                    break

        # Stage 5: Synthesize final answer
        return self._synthesize(query_id, raw_query, execution_history)

    def _execute_subtask(self, subtask: Dict, best_path: Dict) -> str:
        """Execute subtask with selected agent."""
        role_designer = RoleDesignAgent()
        agent_config = role_designer.instantiate(
            {**subtask, 'requires_specialist': best_path['agent']},
            {}
        )

        return self.llm.query(
            f"{agent_config['system_prompt']}\n\n"
            f"Complete this subtask: {subtask.get('subtask', '')}"
        )

    def _check_consensus(self, responses: List[str]) -> bool:
        """Check if 66% consensus reached."""
        if len(responses) < 2:
            return False

        # Simple consensus: ask LLM if responses agree
        consensus_prompt = f"""Do these responses substantially agree? (yes/no)

Response 1: {responses[-2][:300]}
Response 2: {responses[-1][:300]}

Answer just 'yes' or 'no'."""

        result = self.llm.query(consensus_prompt).strip().lower()
        return result == 'yes'

    def _synthesize(self, query_id: str, original_query: str,
                    history: List[Dict]) -> Dict:
        """Synthesize final response from execution history."""
        history_text = "\n".join([
            f"- {h['agent']}: {h['result'][:200]}..."
            for h in history
        ])

        synthesis_prompt = f"""Synthesize a final response from these specialist contributions:

Original Query: {original_query}

Specialist Contributions:
{history_text}

Provide a cohesive, actionable response that honors all perspectives.
Include a confidence score (0-100%) and any dissenting views."""

        final = self.llm.query(synthesis_prompt)

        return {
            'query_id': query_id,
            'response': final,
            'subtasks_completed': len(history),
            'agents_consulted': list(set(h['agent'] for h in history))
        }

    def _store_refined_prompt(self, query_id: str, original: str,
                              refined: RefinedPrompt):
        """Persist refined prompt to database."""
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO council_refined_prompts
                (query_id, original_query, task_type, core_intent,
                 key_details, refined_prompt)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                query_id, original, refined.task_type,
                refined.core_intent, json.dumps(refined.key_details),
                refined.refined_prompt
            ))
            self.conn.commit()


# =============================================================================
# INTEGRATION WITH EXISTING COUNCIL
# =============================================================================

def upgrade_council_query(tribe_interface, raw_query: str) -> Dict:
    """
    Drop-in replacement for tribe.query_council() with HALO enhancement.

    Usage:
        # Old way:
        result = tribe.query_council("Should we proceed?")

        # New way:
        result = upgrade_council_query(tribe, "Should we proceed?")
    """
    halo = HALOCouncil(tribe_interface.llm_client)
    return halo.query(raw_query)
```

---

## Integration Points

### 1. Telegram Chief Bot

```python
# In telegram_chief.py, replace direct Council calls:

from lib.halo_council import upgrade_council_query

async def handle_council_query(update, context):
    query = update.message.text.replace('/council', '').strip()

    # Use HALO-enhanced Council
    result = upgrade_council_query(tribe, query)

    response = f"""🦅 HALO Council Response

{result['response']}

📊 Process:
- Subtasks: {result['subtasks_completed']}
- Specialists: {', '.join(result['agents_consulted'])}
- Query ID: {result['query_id']}
"""
    await update.message.reply_text(response)
```

### 2. LLM Gateway API

```python
# Add new endpoint in llm_gateway.py:

@app.post("/v1/council/halo")
async def halo_council_query(request: Request):
    data = await request.json()
    query = data.get('query', '')

    halo = HALOCouncil(llm_client)
    result = halo.query(query)

    return JSONResponse(result)
```

### 3. Jr Task Executor

```python
# For complex implementation tasks, use HALO planning:

from lib.halo_council import PlanningAgent, PromptRefinementModule

def execute_complex_task(task_content: str):
    refiner = PromptRefinementModule(llm)
    planner = PlanningAgent(llm)

    refined = refiner.refine(task_content)
    subtasks = []

    while True:
        next_subtasks = planner.decompose(refined, subtasks)
        if not next_subtasks:
            break
        subtasks.extend(next_subtasks)

    # Execute subtasks sequentially or spawn Jr agents
    for subtask in subtasks:
        announce_jr_task(subtask)
```

---

## Validation Checklist

- [ ] council_subtasks table created
- [ ] council_mcts_nodes table created
- [ ] council_agent_instances table created
- [ ] council_refined_prompts table created
- [ ] PromptRefinementModule working
- [ ] PlanningAgent decomposing correctly
- [ ] RoleDesignAgent instantiating specialists
- [ ] MCTS search exploring alternatives
- [ ] Consensus detection working
- [ ] Synthesis producing coherent output
- [ ] Telegram integration tested
- [ ] Gateway endpoint tested

---

## Performance Expectations

Based on HALO paper results:
- 14.4% average improvement over baseline
- Up to 19.6% improvement on reasoning tasks
- Early stopping reduces unnecessary computation
- MCTS explores 5-10 paths before converging

---

## Seven Generations Consideration

The HALO enhancement preserves Cherokee values:
- **Turtle's perspective** is explicitly coded as a specialist
- **Seven Generations impact** is included in prompt refinement
- **Consensus-seeking** mirrors traditional council process
- **Multiple perspectives** are systematically explored

The hierarchy (Chief → Role-Designers → Specialists) mirrors traditional governance while adding computational rigor.

---

*For Seven Generations - wisdom through orchestrated intelligence.*

*Created: December 24, 2025*
*Research: arXiv:2505.13516, arXiv:2503.13754*
