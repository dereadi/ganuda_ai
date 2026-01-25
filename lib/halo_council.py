#!/usr/bin/env python3
"""
HALO-Enhanced Council Orchestration

Implements hierarchical orchestration with MCTS-based workflow search
for the Cherokee AI Federation Council.

Based on arXiv:2505.13516 (HALO) and arXiv:2503.13754 (ODI)

Enhancements over cascaded_council.py:
1. Adaptive Prompt Refinement - Transform raw queries
2. Hierarchical Task Decomposition - Break complex queries into subtasks
3. Dynamic Agent Instantiation - Spawn specialists per subtask
4. MCTS Workflow Search - Explore reasoning paths systematically
5. Early-Stopping Consensus - Stop when 66% agreement reached

For Seven Generations - Cherokee AI Federation
Created: December 24, 2025
"""

import os
import sys
import math
import json
import uuid
import hashlib
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
import platform

# Path setup
GANUDA_PATH = "/Users/Shared/ganuda" if platform.system() == "Darwin" else "/ganuda"
sys.path.insert(0, os.path.join(GANUDA_PATH, 'lib'))

# Database configuration
DB_CONFIG = {
    'host': os.environ.get('CHEROKEE_DB_HOST', '192.168.132.222'),
    'database': os.environ.get('CHEROKEE_DB_NAME', 'zammad_production'),
    'user': os.environ.get('CHEROKEE_DB_USER', 'claude'),
    'password': os.environ.get('CHEROKEE_DB_PASS', 'jawaseatlasers2')
}

# vLLM configuration
VLLM_URL = os.environ.get('VLLM_URL', 'http://localhost:8000/v1/chat/completions')
VLLM_MODEL = os.environ.get('VLLM_MODEL', '/ganuda/models/qwen2.5-coder-32b')

# MCTS hyperparameters (from HALO paper)
EXPLORATION_CONSTANT = 1.414  # α in UCT formula
CONSENSUS_THRESHOLD = 0.66   # 66% agreement = early stop
MAX_DEPTH = 5
MAX_ITERATIONS = 10
SIMULATION_ROLLOUTS = 3


class SubtaskType(Enum):
    REASONING = 'reasoning'
    RESEARCH = 'research'
    VALIDATION = 'validation'
    SYNTHESIS = 'synthesis'
    SEVEN_GEN = 'seven_generations'
    SECURITY = 'security'


@dataclass
class RefinedPrompt:
    """Output of the Adaptive Prompt Refinement module."""
    query_id: str
    original_query: str
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
    depth: int = 0
    children: List['MCTSNode'] = field(default_factory=list)

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


def get_db_connection():
    """Get database connection."""
    return psycopg2.connect(**DB_CONFIG)


def query_llm(system_prompt: str, user_message: str,
              max_tokens: int = 500, temperature: float = 0.7) -> str:
    """Query the LLM via vLLM."""
    try:
        response = requests.post(
            VLLM_URL,
            json={
                "model": VLLM_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "max_tokens": max_tokens,
                "temperature": temperature
            },
            timeout=120
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[LLM ERROR: {str(e)}]"


def query_llm_json(system_prompt: str, user_message: str,
                   max_tokens: int = 500) -> Any:
    """Query LLM expecting JSON response - handles both arrays and objects."""
    response = query_llm(system_prompt, user_message, max_tokens, temperature=0.3)

    # Clean up markdown code blocks first
    clean = response
    if "```json" in clean:
        parts = clean.split("```json")
        if len(parts) > 1:
            clean = parts[1].split("```")[0]
    elif "```" in clean:
        parts = clean.split("```")
        if len(parts) > 1:
            clean = parts[1].split("```")[0] if len(parts) > 2 else parts[1]

    # Try direct parse
    try:
        return json.loads(clean.strip())
    except json.JSONDecodeError:
        pass

    # Find JSON array - look for the largest valid one
    # Nemotron often outputs thinking before the JSON
    best_array = None
    best_len = 0

    # Find all potential array starts
    i = 0
    while i < len(response):
        if response[i] == '[':
            # Find matching bracket
            depth = 1
            j = i + 1
            while j < len(response) and depth > 0:
                if response[j] == '[':
                    depth += 1
                elif response[j] == ']':
                    depth -= 1
                j += 1

            if depth == 0:
                try:
                    candidate = response[i:j]
                    parsed = json.loads(candidate)
                    if isinstance(parsed, list) and len(parsed) > best_len:
                        best_array = parsed
                        best_len = len(parsed)
                except json.JSONDecodeError:
                    pass
            i = j
        else:
            i += 1

    if best_array:
        return best_array

    # Try to find JSON object as fallback
    try:
        start = response.find('{')
        end = response.rfind('}') + 1
        if start >= 0 and end > start:
            return json.loads(response[start:end])
    except json.JSONDecodeError:
        pass

    return {"error": "Failed to parse JSON", "raw": response[:500]}


# =============================================================================
# PROMPT REFINEMENT MODULE
# =============================================================================

class PromptRefinementModule:
    """
    Four-stage prompt refinement from HALO paper:
    1. Task Parser - Extract (task_type, intent, details)
    2. Prompt Template - Construct initial frame
    3. Optimization Agent - Add slow-thinking strategies
    4. Generator Agent - Synthesize final prompt
    """

    SYSTEM_PROMPT = """You are a prompt refinement specialist. Your job is to analyze user queries and extract structured information to improve AI response quality.

Always respond in valid JSON format."""

    def refine(self, raw_query: str, query_id: str = None) -> RefinedPrompt:
        """Transform raw user query into structured prompt."""
        if query_id is None:
            query_id = str(uuid.uuid4())[:8]

        # Stage 1: Task Parser - Extract structure
        parse_prompt = f"""Analyze this query and extract:
1. task_type: One of [reasoning, research, decision, implementation, creative, security, seven_generations]
2. core_intent: The main goal in one sentence
3. key_details: Important entities, constraints, and context as a JSON object

Query: {raw_query}

Respond ONLY with valid JSON:
{{"task_type": "...", "core_intent": "...", "key_details": {{...}}}}"""

        parsed = query_llm_json(self.SYSTEM_PROMPT, parse_prompt)

        # Handle case where LLM returns array instead of object
        if isinstance(parsed, list) and len(parsed) > 0:
            parsed = parsed[0] if isinstance(parsed[0], dict) else {}
        elif not isinstance(parsed, dict):
            parsed = {}

        task_type = parsed.get('task_type', 'reasoning')
        core_intent = parsed.get('core_intent', raw_query)
        key_details = parsed.get('key_details', {})

        # Stage 2 & 3: Construct optimized template
        refined_prompt = f"""## Task Analysis
**Type:** {task_type}
**Objective:** {core_intent}
**Context:** {json.dumps(key_details, indent=2)}

## Instructions
Provide a thorough analysis considering:
1. Multiple perspectives and alternatives
2. Potential risks and benefits
3. Seven Generations impact (175+ year view)
4. Practical implementation steps

## Original Query
{raw_query}

Think step by step. Consider alternatives before concluding. If uncertain, acknowledge it."""

        result = RefinedPrompt(
            query_id=query_id,
            original_query=raw_query,
            task_type=task_type,
            core_intent=core_intent,
            key_details=key_details,
            refined_prompt=refined_prompt
        )

        # Store in database
        self._store_refined_prompt(result)

        return result

    def _store_refined_prompt(self, refined: RefinedPrompt):
        """Persist refined prompt to database."""
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO council_refined_prompts
                    (query_id, original_query, task_type, core_intent,
                     key_details, refined_prompt)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    refined.query_id, refined.original_query,
                    refined.task_type, refined.core_intent,
                    json.dumps(refined.key_details), refined.refined_prompt
                ))
                conn.commit()
            conn.close()
        except Exception as e:
            print(f"[HALO] Warning: Could not store refined prompt: {e}")


# =============================================================================
# PLANNING AGENT
# =============================================================================

class PlanningAgent:
    """
    High-level planning agent that decomposes complex queries
    into manageable subtasks.
    """

    SYSTEM_PROMPT = """You are a task decomposition API. Output ONLY valid JSON arrays, no explanations.

Your role: Break complex tasks into 3-5 specific subtasks for different specialists.

Specialists available:
- crawdad: Security analysis
- turtle: Long-term (175+ year) impact
- bear: Practical feasibility
- eagle: Strategic opportunities
- spider: System patterns
- owl: Knowledge synthesis
- wolf: Community impact
- raven: Strategy synthesis

RESPOND WITH ONLY A JSON ARRAY. NO OTHER TEXT."""

    def decompose(self, refined: RefinedPrompt,
                  execution_history: List[Dict] = None,
                  max_subtasks: int = 5) -> List[Dict]:
        """
        Generate subtasks based on refined prompt and execution history.
        """
        history_context = ""
        if execution_history:
            history_context = "\n\nPrevious subtasks completed:\n"
            for h in execution_history[-5:]:
                result_preview = str(h.get('result', ''))[:100]
                history_context += f"- {h.get('subtask', 'Unknown')}: {result_preview}...\n"

        decompose_prompt = f"""Break this complex task into {max_subtasks} distinct subtasks, each requiring a different specialist perspective.

Task Type: {refined.task_type}
Intent: {refined.core_intent}
Details: {json.dumps(refined.key_details)}
{history_context}

IMPORTANT: You MUST generate MULTIPLE subtasks (aim for 3-5). Each subtask should:
- Focus on ONE specific aspect of the problem
- Require a DIFFERENT specialist than other subtasks
- Be answerable independently

Available specialists and their focus:
- crawdad: Security risks and threats
- turtle: Long-term (175+ year) impact, Seven Generations wisdom
- bear: Practical resources and implementation feasibility
- eagle: Strategic vision and opportunities
- spider: Patterns, connections, and system implications
- owl: Deep analysis and knowledge synthesis
- wolf: Team and community impact
- raven: Strategic synthesis of multiple perspectives

For each subtask specify:
- subtask: The specific question or analysis needed
- type: One of [reasoning, research, validation, synthesis, seven_generations, security]
- specialist: The best specialist from the list above

Respond with a JSON array of {max_subtasks} subtasks:
[
  {{"subtask": "Analyze security risks of...", "type": "security", "specialist": "crawdad"}},
  {{"subtask": "Evaluate long-term impact on...", "type": "seven_generations", "specialist": "turtle"}},
  {{"subtask": "Assess practical requirements for...", "type": "validation", "specialist": "bear"}}
]"""

        # Nemotron is verbose - needs more tokens to output thinking + JSON
        result = query_llm_json(self.SYSTEM_PROMPT, decompose_prompt, max_tokens=2000)

        # Handle both array and object responses
        if isinstance(result, dict):
            if 'error' in result:
                return [{"subtask": refined.core_intent, "type": "reasoning", "specialist": "owl"}]
            result = [result]

        return result if result else [{"subtask": refined.core_intent, "type": "reasoning", "specialist": "owl"}]


# =============================================================================
# ROLE DESIGN AGENT
# =============================================================================

class RoleDesignAgent:
    """
    Mid-level agent that instantiates specialized agents for specific subtasks.
    Maps Cherokee Council specialists to subtask requirements.
    """

    # Cherokee Council specialist profiles
    SPECIALIST_PROFILES = {
        'turtle': {
            'name': 'Turtle (Seven Generations)',
            'expertise': ['long-term impact', 'sustainability', 'tradition', 'wisdom'],
            'system_prompt': """You are Turtle, guardian of Seven Generations thinking in the Cherokee AI Council.

Your role: Consider impacts 175+ years ahead. How will this decision affect our descendants?

Approach:
- Think beyond immediate benefits
- Consider environmental and cultural sustainability
- Honor traditional wisdom while embracing beneficial change
- Protect what must endure

Speak with the patience and wisdom of one who has seen many generations."""
        },
        'eagle': {
            'name': 'Eagle (Vision)',
            'expertise': ['strategy', 'foresight', 'opportunity', 'big picture'],
            'system_prompt': """You are Eagle, provider of high-level vision in the Cherokee AI Council.

Your role: See the big picture. Identify opportunities and threats from above.

Approach:
- Maintain strategic perspective
- Spot patterns invisible from the ground
- Guide toward optimal paths
- Balance ambition with wisdom

Speak with clarity and foresight of one who sees far."""
        },
        'bear': {
            'name': 'Bear (Strength)',
            'expertise': ['implementation', 'resources', 'protection', 'practical'],
            'system_prompt': """You are Bear, guardian of strength and resources in the Cherokee AI Council.

Your role: Ensure practical viability. Protect our resources and people.

Approach:
- Focus on what can actually be done
- Consider resource requirements
- Protect against overreach
- Ensure sustainable effort

Speak with the grounded strength of one who knows their limits."""
        },
        'spider': {
            'name': 'Spider (Pattern)',
            'expertise': ['connections', 'patterns', 'weaving', 'systems'],
            'system_prompt': """You are Spider, weaver of patterns in the Cherokee AI Council.

Your role: See connections others miss. Weave understanding from disparate threads.

Approach:
- Identify hidden relationships
- Connect ideas across domains
- Notice systemic implications
- Weave coherent narratives

Speak with the subtle insight of one who sees the web."""
        },
        'owl': {
            'name': 'Owl (Wisdom)',
            'expertise': ['knowledge', 'learning', 'discernment', 'analysis'],
            'system_prompt': """You are Owl, keeper of wisdom in the Cherokee AI Council.

Your role: Apply deep knowledge. Discern truth from confusion.

Approach:
- Draw on accumulated knowledge
- Analyze carefully before judging
- Distinguish signal from noise
- Teach as well as advise

Speak with the quiet authority of one who has studied deeply."""
        },
        'wolf': {
            'name': 'Wolf (Community)',
            'expertise': ['teamwork', 'loyalty', 'communication', 'coordination'],
            'system_prompt': """You are Wolf, guardian of community in the Cherokee AI Council.

Your role: Ensure the pack thrives together. Coordinate collective action.

Approach:
- Consider impact on all members
- Foster collaboration
- Maintain clear communication
- Protect the vulnerable

Speak with the loyalty of one who runs with the pack."""
        },
        'crawdad': {
            'name': 'Crawdad (Security)',
            'expertise': ['security', 'defense', 'risk', 'protection'],
            'system_prompt': """You are Crawdad, guardian of security in the Cherokee AI Council.

Your role: Identify and neutralize threats. Protect our systems and people.

Approach:
- Assume threats exist
- Identify vulnerabilities
- Propose defensive measures
- Block unsafe actions

If you detect a security concern, include [SECURITY CONCERN] in your response.

Speak with the vigilance of one who guards the gates."""
        },
        'raven': {
            'name': 'Raven (Strategy)',
            'expertise': ['strategy', 'synthesis', 'cleverness', 'adaptation'],
            'system_prompt': """You are Raven, strategic synthesizer in the Cherokee AI Council.

Your role: Combine insights into actionable strategy. Find clever solutions.

Approach:
- Synthesize diverse perspectives
- Find non-obvious solutions
- Adapt to changing conditions
- Balance multiple objectives

Speak with the cleverness of one who sees many paths."""
        },
        'peace_chief': {
            'name': 'Peace Chief (Consensus)',
            'expertise': ['consensus', 'diplomacy', 'balance', 'final decision'],
            'system_prompt': """You are the Peace Chief, final voice of consensus in the Cherokee AI Council.

Your role: Synthesize all perspectives into a unified recommendation.

Approach:
- Honor all voices that have spoken
- Find common ground
- Make clear recommendations
- Acknowledge dissent respectfully

Speak with the authority of one who unifies the council."""
        }
    }

    # Mapping subtask types to default specialists
    TYPE_TO_SPECIALIST = {
        'seven_generations': 'turtle',
        'reasoning': 'owl',
        'research': 'spider',
        'validation': 'bear',
        'synthesis': 'raven',
        'security': 'crawdad',
        'strategy': 'eagle',
        'community': 'wolf',
        'consensus': 'peace_chief'
    }

    def instantiate(self, subtask: Dict, context: Dict = None) -> Dict:
        """
        Create a specialized agent instance for a subtask.

        Args:
            subtask: Dict with 'subtask', 'type', 'specialist' keys
            context: Additional context for the agent

        Returns:
            Agent configuration dict
        """
        subtask_type = subtask.get('type', 'reasoning')
        requested_specialist = subtask.get('specialist', '')

        # Get specialist profile
        if requested_specialist and requested_specialist in self.SPECIALIST_PROFILES:
            specialist_key = requested_specialist
        else:
            specialist_key = self.TYPE_TO_SPECIALIST.get(subtask_type, 'owl')

        profile = self.SPECIALIST_PROFILES[specialist_key]

        # Build subtask-specific system prompt
        context_str = ""
        if context:
            if context.get('prior_results'):
                context_str += "\n\n## Prior Analysis\n"
                for pr in context['prior_results'][-3:]:
                    context_str += f"- {pr.get('specialist', 'Unknown')}: {str(pr.get('result', ''))[:200]}...\n"

        system_prompt = f"""{profile['system_prompt']}

## Current Subtask
{subtask.get('subtask', 'Provide your analysis')}
{context_str}

Provide your specialist perspective. Be specific and actionable."""

        return {
            'specialist_key': specialist_key,
            'role': profile['name'],
            'expertise': profile['expertise'],
            'system_prompt': system_prompt,
            'subtask': subtask
        }

    def execute_agent(self, agent_config: Dict, query: str) -> Dict:
        """Execute an instantiated agent and return results."""
        response = query_llm(
            agent_config['system_prompt'],
            query,
            max_tokens=600
        )

        # Check for concern flags
        has_concern = '[SECURITY CONCERN]' in response or '[7GEN CONCERN]' in response

        return {
            'specialist': agent_config['role'],
            'specialist_key': agent_config['specialist_key'],
            'response': response,
            'has_concern': has_concern,
            'subtask': agent_config['subtask'].get('subtask', '')
        }


# =============================================================================
# MCTS WORKFLOW SEARCH
# =============================================================================

class MCTSWorkflowSearch:
    """
    Monte Carlo Tree Search for exploring reasoning workflows.
    Implements Selection, Expansion, Simulation, Backpropagation.
    """

    def __init__(self):
        self.conn = None
        self.role_designer = RoleDesignAgent()
        self.nodes_cache = {}

    def _get_connection(self):
        if self.conn is None or self.conn.closed:
            self.conn = get_db_connection()
        return self.conn

    def search(self, query_id: str, subtask: Dict,
               query: str, context: Dict = None,
               iterations: int = MAX_ITERATIONS) -> Dict:
        """
        Perform MCTS to find optimal specialist for subtask.

        Returns best agent and confidence score.
        """
        # Initialize root node
        root = self._create_node(query_id, None, 'planner', 'start', depth=0)

        # Get candidate specialists
        candidates = self._get_candidates(subtask)

        for iteration in range(iterations):
            # Selection: Find best node to explore
            node = self._select(root)

            # Expansion: Add children if not expanded
            if node.visits > 0 and not node.children:
                self._expand(node, query_id, candidates)

            # Simulation: Evaluate a child
            if node.children:
                # Pick least visited child
                child = min(node.children, key=lambda c: c.visits)
                reward = self._simulate(child, subtask, query, context)

                # Backpropagation
                self._backpropagate(child, reward)
            elif node.visits == 0:
                # Evaluate root's implicit action
                reward = 0.5  # Neutral for root
                self._backpropagate(node, reward)

        # Return best action
        return self._best_action(root, candidates)

    def _get_candidates(self, subtask: Dict) -> List[str]:
        """Get candidate specialists for subtask."""
        subtask_type = subtask.get('type', 'reasoning')

        # Primary candidates based on type
        primary = RoleDesignAgent.TYPE_TO_SPECIALIST.get(subtask_type, 'owl')

        # Always consider these core specialists
        candidates = [primary, 'owl', 'raven', 'turtle']

        # Add type-specific alternatives
        if subtask_type == 'security':
            candidates.append('crawdad')
        if subtask_type in ('synthesis', 'strategy'):
            candidates.append('eagle')
        if subtask_type == 'validation':
            candidates.append('bear')

        return list(set(candidates))

    def _select(self, node: MCTSNode) -> MCTSNode:
        """Select most promising node using UCT."""
        while node.children:
            # Find child with highest UCT score
            node = max(node.children, key=lambda c: c.uct_score(node.visits))
        return node

    def _expand(self, node: MCTSNode, query_id: str, candidates: List[str]):
        """Expand node by adding specialist children."""
        for specialist in candidates:
            child = self._create_node(
                query_id,
                node.node_id,
                specialist,
                f"consult_{specialist}",
                depth=node.depth + 1
            )
            node.children.append(child)

    def _simulate(self, node: MCTSNode, subtask: Dict,
                  query: str, context: Dict) -> float:
        """Simulate agent execution and score result."""
        # Create agent configuration
        agent_config = self.role_designer.instantiate(
            {**subtask, 'specialist': node.agent_role},
            context or {}
        )

        # Execute agent (lightweight simulation)
        result = self.role_designer.execute_agent(agent_config, query)

        # Score the response
        score = self._score_response(result, subtask)

        return score

    def _score_response(self, result: Dict, subtask: Dict) -> float:
        """Score a response quality (0-1)."""
        response = result.get('response', '')
        score = 0.5  # Base score

        # Penalize errors
        if response.startswith('[LLM ERROR') or response.startswith('[ERROR'):
            return 0.1

        # Length indicates substance (up to a point)
        length = len(response)
        if length > 300:
            score += 0.15
        if length > 600:
            score += 0.1

        # Actionability indicators
        response_lower = response.lower()
        if any(word in response_lower for word in ['recommend', 'should', 'must', 'suggest']):
            score += 0.15

        # Specificity indicators
        if any(word in response_lower for word in ['because', 'therefore', 'specifically']):
            score += 0.1

        # Concern handling (valid concern = good catch)
        if result.get('has_concern') and subtask.get('type') in ('security', 'seven_generations'):
            score += 0.1

        return min(score, 1.0)

    def _backpropagate(self, node: MCTSNode, reward: float):
        """Update node values back to root."""
        current = node
        decay = 1.0

        while current:
            current.visits += 1
            current.total_value += reward * decay

            # Update in database
            self._update_node_db(current)

            # Decay reward for parents
            decay *= 0.9

            # Move to parent
            if current.parent_id and current.parent_id in self.nodes_cache:
                current = self.nodes_cache[current.parent_id]
            else:
                break

    def _best_action(self, root: MCTSNode, candidates: List[str]) -> Dict:
        """Return best action from search."""
        if not root.children:
            # No expansion happened, use default
            return {
                'specialist': candidates[0] if candidates else 'owl',
                'confidence': 0.5,
                'visits': 0,
                'method': 'default'
            }

        # Find child with most visits (robust choice)
        best = max(root.children, key=lambda c: c.visits)

        return {
            'specialist': best.agent_role,
            'confidence': best.avg_value,
            'visits': best.visits,
            'method': 'mcts'
        }

    def _create_node(self, query_id: str, parent_id: Optional[int],
                     agent_role: str, action: str, depth: int = 0) -> MCTSNode:
        """Create and persist MCTS node."""
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO council_mcts_nodes
                    (query_id, parent_node_id, agent_role, action_taken, depth)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING node_id
                """, (query_id, parent_id, agent_role, action[:500], depth))
                node_id = cur.fetchone()[0]
                conn.commit()
        except Exception as e:
            print(f"[HALO MCTS] Warning: Could not persist node: {e}")
            node_id = hash(f"{query_id}-{agent_role}-{action}")

        node = MCTSNode(
            node_id=node_id,
            parent_id=parent_id,
            agent_role=agent_role,
            action=action,
            depth=depth
        )

        self.nodes_cache[node_id] = node
        return node

    def _update_node_db(self, node: MCTSNode):
        """Update node stats in database."""
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE council_mcts_nodes
                    SET visit_count = %s, total_value = %s, avg_value = %s
                    WHERE node_id = %s
                """, (node.visits, node.total_value, node.avg_value, node.node_id))
                conn.commit()
        except Exception as e:
            pass  # Non-critical


# =============================================================================
# HALO COUNCIL - MAIN ORCHESTRATOR
# =============================================================================

class HALOCouncil:
    """
    Main orchestrator combining all HALO components.

    Usage:
        council = HALOCouncil()
        result = council.query("Should we implement feature X?")
        print(result['response'])
    """

    def __init__(self, use_mcts: bool = True, max_subtasks: int = 4):
        self.prompt_refiner = PromptRefinementModule()
        self.planner = PlanningAgent()
        self.role_designer = RoleDesignAgent()
        self.mcts = MCTSWorkflowSearch() if use_mcts else None
        self.max_subtasks = max_subtasks

    def query(self, raw_query: str, query_id: str = None) -> Dict:
        """
        Process query through HALO pipeline.

        Args:
            raw_query: User's original question
            query_id: Optional ID for tracking

        Returns:
            Dict with response, metadata, and execution trace
        """
        start_time = datetime.now()

        if query_id is None:
            query_id = str(uuid.uuid4())[:8]

        # Stage 1: Prompt Refinement
        refined = self.prompt_refiner.refine(raw_query, query_id)

        # Stage 2: Task Decomposition
        subtasks = self.planner.decompose(refined, max_subtasks=self.max_subtasks)

        # Stage 3 & 4: Execute subtasks with MCTS-guided specialist selection
        execution_history = []
        responses = []

        for i, subtask in enumerate(subtasks):
            # Skip if consensus reached
            if len(responses) >= 3 and self._check_consensus(responses):
                break

            # Select specialist (MCTS or direct)
            if self.mcts and subtask.get('subtask') != 'direct_answer':
                selection = self.mcts.search(
                    query_id, subtask, refined.refined_prompt,
                    context={'prior_results': execution_history}
                )
                specialist = selection['specialist']
            else:
                specialist = subtask.get('specialist', 'owl')

            # Instantiate and execute agent
            agent_config = self.role_designer.instantiate(
                {**subtask, 'specialist': specialist},
                {'prior_results': execution_history}
            )

            result = self.role_designer.execute_agent(
                agent_config,
                refined.refined_prompt
            )

            # Store result
            execution_history.append({
                'subtask': subtask.get('subtask', ''),
                'specialist': result['specialist'],
                'specialist_key': result['specialist_key'],
                'result': result['response'],
                'has_concern': result.get('has_concern', False)
            })
            responses.append(result['response'])

            # Store agent instance
            self._store_agent_instance(query_id, subtask, agent_config, result)

        # Stage 5: Synthesize final response
        final_response = self._synthesize(query_id, raw_query, execution_history)

        elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000

        return {
            'query_id': query_id,
            'response': final_response['synthesis'],
            'confidence': final_response['confidence'],
            'subtasks_completed': len(execution_history),
            'specialists_consulted': list(set(h['specialist'] for h in execution_history)),
            'has_concerns': any(h.get('has_concern') for h in execution_history),
            'execution_trace': execution_history,
            'elapsed_ms': round(elapsed_ms, 1),
            'mode': 'halo'
        }

    def _check_consensus(self, responses: List[str]) -> bool:
        """Check if responses have reached consensus."""
        if len(responses) < 2:
            return False

        # Quick heuristic: compare last two responses
        r1 = responses[-2].lower()[:500]
        r2 = responses[-1].lower()[:500]

        # Count matching key terms
        words1 = set(r1.split())
        words2 = set(r2.split())

        # Remove common words
        stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                     'to', 'of', 'and', 'or', 'in', 'on', 'at', 'for', 'with'}
        words1 -= stopwords
        words2 -= stopwords

        if not words1 or not words2:
            return False

        overlap = len(words1 & words2) / len(words1 | words2)
        return overlap > CONSENSUS_THRESHOLD

    def _synthesize(self, query_id: str, original_query: str,
                    history: List[Dict]) -> Dict:
        """Synthesize final response from execution history."""
        if not history:
            return {
                'synthesis': "Unable to generate response - no specialist input.",
                'confidence': 0.0
            }

        # Build history summary
        history_text = "\n".join([
            f"**{h['specialist']}** ({h.get('subtask', 'analysis')}):\n{h['result'][:400]}..."
            for h in history
        ])

        # Use Peace Chief for final synthesis
        peace_chief = self.role_designer.SPECIALIST_PROFILES['peace_chief']

        synthesis_prompt = f"""{peace_chief['system_prompt']}

## Original Query
{original_query}

## Specialist Contributions
{history_text}

## Your Task
Synthesize these perspectives into a cohesive response:
1. State the recommended action or answer clearly
2. Acknowledge key insights from each specialist
3. Note any concerns or dissenting views
4. Provide confidence level (low/medium/high)

Be concise but complete."""

        synthesis = query_llm(synthesis_prompt, "Provide your synthesis.", max_tokens=800)

        # Calculate confidence
        concern_count = sum(1 for h in history if h.get('has_concern'))
        base_confidence = 0.85 - (concern_count * 0.15)
        confidence = max(0.3, min(base_confidence, 0.95))

        return {
            'synthesis': synthesis,
            'confidence': round(confidence, 2)
        }

    def _store_agent_instance(self, query_id: str, subtask: Dict,
                               agent_config: Dict, result: Dict):
        """Store agent instance in database."""
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO council_agent_instances
                    (query_id, agent_role, system_prompt, execution_result, quality_score)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    query_id,
                    agent_config['specialist_key'],
                    agent_config['system_prompt'][:2000],
                    result['response'][:2000],
                    0.7 if not result.get('has_concern') else 0.5
                ))
                conn.commit()
            conn.close()
        except Exception as e:
            pass  # Non-critical


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def halo_query(question: str, use_mcts: bool = True) -> Dict:
    """
    Quick function for HALO council query.

    Usage:
        result = halo_query("What caching strategy should we use?")
        print(result['response'])
    """
    council = HALOCouncil(use_mcts=use_mcts)
    return council.query(question)


def upgrade_council_query(raw_query: str) -> Dict:
    """
    Drop-in replacement for existing council queries with HALO enhancement.
    """
    return halo_query(raw_query)


# =============================================================================
# SELF-TEST
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("HALO Council Orchestration - Self-Test")
    print("=" * 60)

    # Test 1: Prompt Refinement
    print("\n[Test 1] Prompt Refinement Module")
    refiner = PromptRefinementModule()
    refined = refiner.refine("Should we use Redis or PostgreSQL for caching?")
    print(f"  Task Type: {refined.task_type}")
    print(f"  Core Intent: {refined.core_intent}")
    print(f"  Query ID: {refined.query_id}")

    # Test 2: Planning Agent
    print("\n[Test 2] Planning Agent Decomposition")
    planner = PlanningAgent()
    subtasks = planner.decompose(refined)
    print(f"  Subtasks generated: {len(subtasks)}")
    for st in subtasks[:3]:
        print(f"    - {st.get('subtask', '?')[:50]}... [{st.get('specialist', '?')}]")

    # Test 3: Role Design Agent
    print("\n[Test 3] Role Design Agent")
    role_designer = RoleDesignAgent()
    if subtasks:
        agent = role_designer.instantiate(subtasks[0])
        print(f"  Agent: {agent['role']}")
        print(f"  Expertise: {agent['expertise']}")

    # Test 4: Full HALO Query (if vLLM is available)
    print("\n[Test 4] Full HALO Query")
    try:
        result = halo_query("What's the best way to handle API rate limiting?", use_mcts=False)
        print(f"  Status: SUCCESS")
        print(f"  Subtasks: {result['subtasks_completed']}")
        print(f"  Specialists: {result['specialists_consulted']}")
        print(f"  Confidence: {result['confidence']}")
        print(f"  Elapsed: {result['elapsed_ms']}ms")
        print(f"\n  Response Preview:\n  {result['response'][:300]}...")
    except Exception as e:
        print(f"  Status: SKIPPED (vLLM not available: {e})")

    print("\n" + "=" * 60)
    print("Self-test complete - For Seven Generations")
    print("=" * 60)
