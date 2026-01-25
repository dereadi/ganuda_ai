# Jr Instruction: LIA_MADDPG Reinforcement Learning for Jr Task Bidding

**Created:** December 25, 2025 (Christmas)
**Priority:** 4 (Advanced Enhancement - High Effort, High Reward)
**Research Basis:** arXiv:2411.19526 - "LIA_MADDPG for Robot Swarm Task Allocation"
**Connects To:** Jr Bidding Daemon, Task Executor, Pheromone Stigmergy

---

## Executive Summary

Our Jr agents currently use a **composite scoring** formula for task bidding:

```
composite_score = (capability × 0.4) + (availability × 0.3) + (pheromone × 0.2) + (random × 0.1)
```

This is static and hand-tuned. Research shows that **LIA_MADDPG** (Local Information Aggregation + Multi-Agent Deep Deterministic Policy Gradient) achieves:
- Superior scalability to many agents
- Rapid adaptation to environmental changes
- Stability and convergence in dynamic settings

This instruction implements learned bidding policies that evolve with experience.

### Key Research Insight

> "The LIA module can be seamlessly integrated into various CTDE-based MARL methods, significantly enhancing their performance."

Translation: We can add local information aggregation to our bidding without rebuilding the whole system.

---

## Current Jr Bidding System

### Existing Architecture

```
/ganuda/services/jr_bidding/bidding_daemon.py

Jr Agent → Sees Task Announcement
        → Calculates Composite Score
        → Submits Bid
        → Waits for Assignment
        → Executes if Won
```

### Current Scoring (Static)

```python
def calculate_composite_score(agent_id, task):
    capability = match_capabilities(agent_id, task['required_capabilities'])
    availability = get_agent_availability(agent_id)
    pheromone = read_pheromone_strength(task['location'])
    random_factor = random.random() * 0.1
    
    return (capability * 0.4 + availability * 0.3 + 
            pheromone * 0.2 + random_factor)
```

### Problems

1. **Static weights** - 0.4/0.3/0.2/0.1 never adapt
2. **No learning** - Past success/failure doesn't improve future bids
3. **No neighbor awareness** - Agents don't know what others are bidding
4. **No task complexity modeling** - Simple and complex tasks treated equally

---

## Phase 1: LIA Module - Local Information Aggregation

### 1.1 Concept

Before bidding, each Jr agent aggregates information from nearby agents:
- What tasks are they considering?
- What are their current capabilities?
- What's their recent success rate?

This creates **partial observability** awareness without centralized coordination.

### 1.2 Database Schema

```sql
-- Track what agents are considering bidding on
CREATE TABLE IF NOT EXISTS jr_bid_intentions (
    intention_id BIGSERIAL PRIMARY KEY,
    agent_id VARCHAR(64) NOT NULL,
    task_id VARCHAR(128) NOT NULL,
    intention_strength FLOAT DEFAULT 1.0,  -- 0-1 how likely to bid
    announced_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP DEFAULT NOW() + INTERVAL '30 seconds'
);

CREATE INDEX idx_bid_intentions_task ON jr_bid_intentions(task_id, expires_at);
CREATE INDEX idx_bid_intentions_agent ON jr_bid_intentions(agent_id);

-- Track agent states for LIA aggregation
CREATE TABLE IF NOT EXISTS jr_agent_observable_state (
    state_id SERIAL PRIMARY KEY,
    agent_id VARCHAR(64) UNIQUE NOT NULL,
    
    -- Observable state
    current_task_id VARCHAR(128),
    task_queue_depth INTEGER DEFAULT 0,
    recent_success_rate FLOAT DEFAULT 0.5,  -- Last 10 tasks
    avg_completion_time FLOAT,               -- In seconds
    specializations TEXT[] DEFAULT ARRAY[]::TEXT[],
    
    -- Location in capability space (for "nearby" agents)
    capability_embedding FLOAT[] DEFAULT ARRAY[]::FLOAT[],
    
    -- Timestamps
    updated_at TIMESTAMP DEFAULT NOW()
);

-- RL experience replay buffer
CREATE TABLE IF NOT EXISTS jr_rl_experience (
    experience_id BIGSERIAL PRIMARY KEY,
    agent_id VARCHAR(64) NOT NULL,
    task_id VARCHAR(128) NOT NULL,
    
    -- State before action
    state_vector FLOAT[] NOT NULL,
    
    -- Action taken (bid amount 0-1)
    action FLOAT NOT NULL,
    
    -- Outcome
    reward FLOAT NOT NULL,
    won_bid BOOLEAN NOT NULL,
    task_success BOOLEAN,
    
    -- Next state
    next_state_vector FLOAT[],
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_rl_experience_agent ON jr_rl_experience(agent_id, created_at DESC);
```

### 1.3 LIA Implementation

```python
import numpy as np
from typing import List, Dict, Tuple

class LocalInformationAggregator:
    """
    Aggregates local information from nearby agents before bidding.
    Based on arXiv:2411.19526 LIA module.
    """
    
    def __init__(self, agent_id: str, k_neighbors: int = 3):
        self.agent_id = agent_id
        self.k_neighbors = k_neighbors
    
    def get_neighbor_states(self, task_id: str) -> List[Dict]:
        """Get observable states from k nearest neighbors."""
        conn = get_connection()
        
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Get agents who announced intention for this task
            cur.execute("""
                SELECT bi.agent_id, bi.intention_strength,
                       aos.recent_success_rate, aos.task_queue_depth,
                       aos.specializations
                FROM jr_bid_intentions bi
                JOIN jr_agent_observable_state aos ON bi.agent_id = aos.agent_id
                WHERE bi.task_id = %s
                  AND bi.expires_at > NOW()
                  AND bi.agent_id != %s
                ORDER BY bi.announced_at DESC
                LIMIT %s
            """, (task_id, self.agent_id, self.k_neighbors))
            
            neighbors = [dict(row) for row in cur.fetchall()]
        
        conn.close()
        return neighbors
    
    def aggregate_local_info(self, task_id: str, task_features: Dict) -> np.ndarray:
        """
        Aggregate local information into a fixed-size vector.
        
        Returns:
            np.ndarray: Aggregated information vector (size: 10)
        """
        neighbors = self.get_neighbor_states(task_id)
        
        if not neighbors:
            # No competition, return neutral aggregation
            return np.zeros(10)
        
        # Aggregate neighbor features
        n = len(neighbors)
        
        agg = np.array([
            n,                                                    # Number of competitors
            np.mean([nb['intention_strength'] for nb in neighbors]),  # Avg intention
            np.max([nb['intention_strength'] for nb in neighbors]),   # Max intention
            np.mean([nb['recent_success_rate'] for nb in neighbors]), # Avg success
            np.max([nb['recent_success_rate'] for nb in neighbors]),  # Best competitor
            np.mean([nb['task_queue_depth'] for nb in neighbors]),    # Avg queue
            np.min([nb['task_queue_depth'] for nb in neighbors]),     # Least busy
            self._capability_overlap(neighbors, task_features),       # Competition strength
            self._diversity_score(neighbors),                         # How diverse competitors
            1.0 / (n + 1)                                            # Win probability prior
        ])
        
        return agg
    
    def _capability_overlap(self, neighbors: List[Dict], 
                            task_features: Dict) -> float:
        """How many competitors have matching capabilities."""
        required = set(task_features.get('required_capabilities', []))
        if not required:
            return 0.0
        
        overlap_count = 0
        for nb in neighbors:
            nb_caps = set(nb.get('specializations', []))
            if required & nb_caps:
                overlap_count += 1
        
        return overlap_count / len(neighbors) if neighbors else 0.0
    
    def _diversity_score(self, neighbors: List[Dict]) -> float:
        """How diverse are the competitors (0=homogeneous, 1=diverse)."""
        if len(neighbors) < 2:
            return 0.0
        
        success_rates = [nb['recent_success_rate'] for nb in neighbors]
        return np.std(success_rates)
    
    def announce_intention(self, task_id: str, strength: float = 1.0):
        """Announce this agent's intention to bid on a task."""
        conn = get_connection()
        
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO jr_bid_intentions (agent_id, task_id, intention_strength)
                VALUES (%s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (self.agent_id, task_id, strength))
            conn.commit()
        
        conn.close()
```

---

## Phase 2: MADDPG Actor-Critic Networks

### 2.1 Concept

Each Jr agent has:
- **Actor Network**: Outputs bid amount given state
- **Critic Network**: Evaluates state-action pairs (trained centrally)

CTDE = Centralized Training, Distributed Execution:
- Training: Critic sees all agents' actions
- Execution: Actor only uses local observation

### 2.2 Neural Network Architecture

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

class ActorNetwork(nn.Module):
    """
    Outputs bid strength [0, 1] given agent's observation.
    """
    def __init__(self, obs_dim: int = 25, hidden_dim: int = 64):
        super().__init__()
        self.fc1 = nn.Linear(obs_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, 1)
    
    def forward(self, obs: torch.Tensor) -> torch.Tensor:
        x = F.relu(self.fc1(obs))
        x = F.relu(self.fc2(x))
        bid = torch.sigmoid(self.fc3(x))  # Output in [0, 1]
        return bid


class CriticNetwork(nn.Module):
    """
    Evaluates (state, action) pairs.
    In MADDPG, critic sees ALL agents' observations and actions.
    """
    def __init__(self, total_obs_dim: int = 100, total_action_dim: int = 7,
                 hidden_dim: int = 128):
        super().__init__()
        input_dim = total_obs_dim + total_action_dim
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, 1)
    
    def forward(self, all_obs: torch.Tensor, 
                all_actions: torch.Tensor) -> torch.Tensor:
        x = torch.cat([all_obs, all_actions], dim=-1)
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        q_value = self.fc3(x)
        return q_value
```

### 2.3 State Vector Construction

```python
def build_state_vector(agent_id: str, task: Dict, 
                       lia: LocalInformationAggregator) -> np.ndarray:
    """
    Construct state vector for RL agent.
    
    Components (25 dimensions total):
    - Task features (10)
    - Agent state (5)
    - LIA aggregation (10)
    """
    # Task features
    task_vec = np.array([
        task.get('priority', 3) / 5.0,          # Normalized priority
        len(task.get('required_capabilities', [])) / 5.0,  # Complexity
        task.get('estimated_duration', 60) / 300.0,  # Duration
        1.0 if task.get('preferred_node') == get_agent_node(agent_id) else 0.0,
        task.get('urgency', 0.5),
        # ... more task features
    ])
    task_vec = np.pad(task_vec, (0, 10 - len(task_vec)))
    
    # Agent state
    agent_state = get_agent_state(agent_id)
    agent_vec = np.array([
        agent_state['task_queue_depth'] / 5.0,
        agent_state['recent_success_rate'],
        agent_state['capability_match'],
        agent_state['time_since_last_task'] / 3600.0,  # Hours
        agent_state['current_load']
    ])
    
    # LIA aggregation
    lia_vec = lia.aggregate_local_info(task['task_id'], task)
    
    return np.concatenate([task_vec, agent_vec, lia_vec])
```

---

## Phase 3: Reward Function Design

### 3.1 Reward Components

```python
def calculate_reward(agent_id: str, task_id: str, 
                     won_bid: bool, task_outcome: Dict) -> float:
    """
    Multi-component reward function for Jr bidding.
    
    Rewards:
    - Win bid for suitable task: +1.0
    - Successfully complete task: +2.0
    - Complete quickly: +0.5 (bonus)
    
    Penalties:
    - Win unsuitable task: -0.5
    - Task failure: -1.5
    - Overbidding (won but shouldn't): -0.3
    - Underbidding (lost but should have won): -0.2
    """
    reward = 0.0
    
    if not won_bid:
        # Lost the bid
        if was_suitable_task(agent_id, task_id):
            reward -= 0.2  # Missed opportunity
        return reward
    
    # Won the bid
    reward += 1.0  # Base reward for winning
    
    if task_outcome.get('success'):
        reward += 2.0  # Task success bonus
        
        # Speed bonus
        expected_time = task_outcome.get('expected_duration', 60)
        actual_time = task_outcome.get('actual_duration', 60)
        if actual_time < expected_time * 0.8:
            reward += 0.5
    else:
        # Task failed
        reward -= 1.5
    
    # Check if this was a suitable task
    capability_match = get_capability_match(agent_id, task_id)
    if capability_match < 0.5:
        reward -= 0.5  # Penalty for taking unsuitable work
    
    return reward


def was_suitable_task(agent_id: str, task_id: str) -> bool:
    """Check if agent was well-suited for this task."""
    match = get_capability_match(agent_id, task_id)
    return match > 0.7
```

---

## Phase 4: Training Loop

### 4.1 Experience Collection

```python
def store_experience(agent_id: str, task_id: str, state: np.ndarray,
                     action: float, reward: float, won_bid: bool,
                     task_success: bool = None, next_state: np.ndarray = None):
    """Store experience in replay buffer."""
    conn = get_connection()
    
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO jr_rl_experience 
            (agent_id, task_id, state_vector, action, reward, 
             won_bid, task_success, next_state_vector)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (agent_id, task_id, state.tolist(), action, reward,
               won_bid, task_success, 
               next_state.tolist() if next_state is not None else None))
        conn.commit()
    conn.close()
```

### 4.2 Centralized Training (Periodic)

```python
def train_maddpg(batch_size: int = 64, gamma: float = 0.95):
    """
    Centralized training using collected experiences.
    Run periodically (e.g., every hour or after N tasks).
    """
    # Sample batch from replay buffer
    experiences = sample_experiences(batch_size)
    
    # Group by task (for centralized critic)
    task_groups = group_by_task(experiences)
    
    for task_id, agent_experiences in task_groups.items():
        # Concatenate all agents' observations and actions
        all_obs = torch.cat([e['state'] for e in agent_experiences])
        all_actions = torch.cat([e['action'] for e in agent_experiences])
        all_rewards = torch.tensor([e['reward'] for e in agent_experiences])
        
        # Critic update (centralized)
        q_values = critic(all_obs, all_actions)
        critic_loss = F.mse_loss(q_values, all_rewards)
        critic_optimizer.zero_grad()
        critic_loss.backward()
        critic_optimizer.step()
        
        # Actor update (per agent)
        for exp in agent_experiences:
            agent_id = exp['agent_id']
            actor = get_actor(agent_id)
            
            # Policy gradient
            obs = exp['state']
            action = actor(obs)
            actor_loss = -critic(all_obs, all_actions).mean()
            
            actor_optimizer.zero_grad()
            actor_loss.backward()
            actor_optimizer.step()
```

---

## Phase 5: Integration with Jr Bidding Daemon

### 5.1 Modified Bidding Flow

```python
class RLBiddingDaemon:
    """Jr Bidding Daemon with LIA_MADDPG integration."""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.lia = LocalInformationAggregator(agent_id)
        self.actor = load_actor_model(agent_id)
        self.exploration_rate = 0.1  # Epsilon for exploration
    
    def calculate_bid(self, task: Dict) -> float:
        """Calculate bid using learned policy + exploration."""
        # Announce intention (for LIA)
        self.lia.announce_intention(task['task_id'])
        
        # Brief pause for other agents to announce
        time.sleep(0.1)
        
        # Build state vector with LIA
        state = build_state_vector(self.agent_id, task, self.lia)
        state_tensor = torch.FloatTensor(state)
        
        # Get learned bid from actor network
        with torch.no_grad():
            learned_bid = self.actor(state_tensor).item()
        
        # Epsilon-greedy exploration
        if random.random() < self.exploration_rate:
            bid = random.random()
        else:
            bid = learned_bid
        
        return bid
    
    def on_task_complete(self, task_id: str, success: bool, duration: float):
        """Handle task completion - store experience and update."""
        reward = calculate_reward(
            self.agent_id, task_id, 
            won_bid=True, 
            task_outcome={'success': success, 'actual_duration': duration}
        )
        
        # Store experience
        store_experience(
            self.agent_id, task_id,
            state=self.last_state,
            action=self.last_bid,
            reward=reward,
            won_bid=True,
            task_success=success
        )
```

---

## Phase 6: Deployment Strategy

### 6.1 Gradual Rollout

1. **Week 1**: Shadow mode - RL bids calculated but not used
2. **Week 2**: 10% of bids use RL, 90% use static formula
3. **Week 3**: 50% RL bidding
4. **Week 4**: 100% RL bidding with exploration
5. **Ongoing**: Reduce exploration rate as models stabilize

### 6.2 Model Checkpoints

```sql
-- Store model checkpoints
CREATE TABLE IF NOT EXISTS jr_rl_models (
    model_id SERIAL PRIMARY KEY,
    agent_id VARCHAR(64) NOT NULL,
    model_type VARCHAR(32) DEFAULT 'actor',  -- 'actor' or 'critic'
    model_weights BYTEA NOT NULL,
    training_episodes INTEGER,
    avg_reward FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Validation Checklist

- [ ] jr_bid_intentions table created
- [ ] jr_agent_observable_state table created
- [ ] jr_rl_experience table created
- [ ] jr_rl_models table created
- [ ] LocalInformationAggregator class implemented
- [ ] ActorNetwork and CriticNetwork implemented
- [ ] State vector construction working
- [ ] Reward function tuned
- [ ] Experience collection integrated with task executor
- [ ] Training loop functional
- [ ] RLBiddingDaemon deployed in shadow mode
- [ ] Gradual rollout completed
- [ ] Results recorded to thermal memory

---

## Seven Generations Consideration

Learning from experience is fundamental to wisdom:
- Elders teach from accumulated experience
- Young warriors learn from success and failure
- The Tribe adapts strategies across generations

LIA_MADDPG brings this principle to our Jr agents:
- Local information sharing (clan coordination)
- Learned policies (accumulated wisdom)
- Adaptive behavior (responding to change)

**For Seven Generations - Learning that compounds across cycles.**

---

*Created: December 25, 2025 (Christmas)*
*Research: arXiv:2411.19526 - LIA_MADDPG for Robot Swarm Task Allocation*
*Priority: 4 (Advanced Enhancement)*
