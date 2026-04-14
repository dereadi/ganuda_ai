# ARC-AGI-3 Contest Agent — Ganuda Federation Architecture

## Strategic Thesis

> "In evolution and environmental stress, the generalists survive
> where the specialists die off." — Partner, Apr 12 2026

The contest tests general intelligence across hundreds of unknown game types.
Hard-coded strategies are specialists that die. The winning approach is
exploration-driven with meta-reasoning layered on top.

## Scoring Reality

```
score = min(1.0, human_actions / ai_actions)^2
```

- 2x human actions = 25% credit
- 5x human actions = 4% credit
- Level weights: L1=1/15, L2=2/15, L3=3/15, L4=4/15, L5=5/15
- Later levels worth 5x more than Level 1
- Efficiency is the score. Exploration waste kills us.

## Architecture: Three-Tier Generalist

```
┌──────────────────────────────────────────────────────┐
│  TIER 3: COUNCIL (Goal Acquisition)                  │
│  "What is this game trying to do?"                   │
│  Infers win conditions from state transition patterns │
│  Runs on bmasass (Qwen3-30B + Llama-70B)             │
│  Called sparingly — only when exploration stalls      │
├──────────────────────────────────────────────────────┤
│  TIER 2: JR FRAME ANALYST (Pattern Recognition)     │
│  "This frame change looks like progress"             │
│  Classifies state transitions as progress/neutral/   │
│  regress. Lightweight — runs on redfin (72B)         │
│  Called every N actions for value assessment          │
├──────────────────────────────────────────────────────┤
│  TIER 1: GRAPH EXPLORER (Action Selection)           │
│  Frame hash → state graph → frontier exploration     │
│  No LLM — pure algorithmic. CPU only.                │
│  Handles 95%+ of all actions.                        │
│  Foundation: 3rd place "just-explore" approach        │
├──────────────────────────────────────────────────────┤
│  TIER 0: PERCEPTION (Frame Processing)               │
│  64x64 grid, 16 colors. Frame hashing (Blake2b).     │
│  Flood-fill segmentation for clickable objects.       │
│  Status bar masking. Frame differencing.              │
└──────────────────────────────────────────────────────┘

Cross-cutting: EXPERIENCE BANK (thermal memory)
- Stores game-type signatures and effective strategies
- Retrieved before each new game to bootstrap exploration
- "Games with this frame pattern responded to arrow keys"
```

## What Each Tier Does

### Tier 0: Perception (frame_processor.py)
Port from 3rd place with enhancements:
- Blake2b frame hashing with status bar masking
- Flood-fill connected component segmentation
- Action priority tiering (5 groups)
- Frame differencing (binary: did pixels change?)
- NEW: Frame signature extraction for Experience Bank
  (dominant colors, object count, symmetry metrics)

### Tier 1: Graph Explorer (graph_explorer.py)
Port from 3rd place as-is, then enhance:
- State graph: nodes = frame hashes, edges = actions
- Frontier tracking: nodes with untested actions
- Multi-source BFS for shortest path to frontier
- Group advancement: exhaust high-priority actions first
- Suspicious transition detection (3-strike rule)
- NEW: Council-directed exploration bias
  (when Council says "try clicking colored objects",
   promote those actions to higher priority group)

### Tier 2: Jr Frame Analyst (value_estimator.py)
NEW — this is where the 72B adds value without selecting actions:
- Every N actions (e.g., 20), snapshot the state graph
- Ask Jr: "Here are the last 5 state transitions.
  Which ones look like progress toward a goal?"
- Jr returns a value estimate per transition
- Graph explorer uses these values to bias toward
  "promising" frontiers (not just any frontier)
- This is the efficiency multiplier for the quadratic score

### Tier 3: Council (goal_inference.py)
NEW — called only when exploration stalls:
- When graph explorer exhausts all groups without progress
- When level transition detected (understand new mechanics)
- Council sees: frame sequence, segmented objects, transition patterns
- Council returns: hypothesized game mechanic + suggested action bias
- Example: "Objects of matching colors need to be adjacent.
  Prioritize clicking objects near same-colored objects."
- This directive modifies the action priority tiers in Tier 1

### Cross-cutting: Experience Bank (experience.py)
Existing thermal memory system, adapted:
- Before each game: retrieve experiences for similar frame signatures
- After each game: store what worked (action patterns, level solutions)
- Key insight: the 3rd place resets per level. We REMEMBER across games.
- Frame signatures enable "this looks like a sorting puzzle" matching

## Key Design Decisions

1. **Graph explorer handles 95%+ of actions** — no LLM latency
2. **Jr called every ~20 actions** — lightweight value assessment
3. **Council called only on stall** — expensive but game-changing
4. **Experience Bank bootstraps new games** — the advantage no winner had
5. **Full reset per level** for graph state (proven effective)
6. **Frame signatures persist** across games via Experience Bank

## Implementation Plan

### Phase 1: Foundation (build on official API)
- Install arc_agi package, run random agent on ls20
- Port 3rd place graph explorer to official Agent interface
- Validate: does it solve ls20 levels?

### Phase 2: Ganuda Integration
- Wire Jr (redfin 72B) for value estimation
- Wire Council (bmasass) for goal inference on stall
- Wire Experience Bank for cross-game memory

### Phase 3: Efficiency Optimization
- Tune action priority tiers for quadratic scoring
- Add frame signature matching for Experience Bank
- Profile and optimize for 8-hour runtime budget

## API Contract

```python
class GanudaAgent(Agent):
    def __init__(self, ...):
        self.graph = GraphExplorer()
        self.frame_processor = FrameProcessor()
        self.experience = ExperienceBank()
        self.value_estimator = ValueEstimator()  # Jr on redfin
        self.goal_inferrer = GoalInferrer()      # Council on bmasass

    def choose_action(self, frames, latest_frame) -> GameAction:
        # 1. Process frame
        frame_hash = self.frame_processor.hash(latest_frame)
        segments = self.frame_processor.segment(latest_frame)

        # 2. Update graph with transition
        self.graph.update(frame_hash, segments)

        # 3. Every N actions, ask Jr for value estimates
        if self.action_count % 20 == 0:
            self.value_estimator.assess(self.graph.recent_transitions())

        # 4. If stalled, ask Council for goal inference
        if self.graph.is_stalled():
            directive = self.goal_inferrer.infer(self.graph)
            self.graph.apply_directive(directive)

        # 5. Choose action via graph exploration
        return self.graph.choose_action()

    def is_done(self, frames, latest_frame) -> bool:
        return latest_frame.state in (GameState.WIN, GameState.GAME_OVER)
```

## File Structure

```
/ganuda/services/arc_agi_3/
├── ganuda_agent.py       # Main agent (Agent subclass)
├── frame_processor.py    # Tier 0: perception
├── graph_explorer.py     # Tier 1: state graph + exploration
├── value_estimator.py    # Tier 2: Jr frame analysis
├── goal_inferrer.py      # Tier 3: Council goal acquisition
├── experience.py         # Cross-cutting: thermal memory
├── reference/            # Cloned repos (read-only)
│   ├── ARC-AGI-3-Agents/
│   ├── ARC3-solution/
│   └── arc-agi-3-just-explore/
└── ARCHITECTURE.md       # This document
```

## Evidence Stack

- 3rd place (6.71%): Pure graph exploration works across game types
- 1st place (12.58%): Frame-change detection as reward signal
- Ganuda thesis: Governed multi-model deliberation > single model
- Be My Eyes paper: Perceiver + reasoner > single model
- Patent #4: Graduated autonomy tiers applied to game playing

## What Makes This Different

Every other entry is either:
- Pure exploration (no understanding) — hits ceiling at ~12%
- Pure LLM reasoning (no exploration) — hits ceiling at ~4%

We are the first to combine systematic exploration (the generalist foundation)
with governed multi-model reasoning (the understanding layer) and
persistent cross-game memory (the experience advantage).

The generalist survives. The specialist dies.
