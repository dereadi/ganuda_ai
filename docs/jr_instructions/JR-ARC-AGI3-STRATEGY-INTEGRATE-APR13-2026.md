# JR INSTRUCTION: Integrate game_strategy.py into ARC-AGI-3 Agent (Atomic)

**JR ID:** JR-ARC-AGI3-STRATEGY-INTEGRATE-APR13-2026
**FROM:** TPM (Flying Squirrel / Stoneclad)
**TO:** IT Triad Jr (`it_triad_jr`)
**PRIORITY:** P1
**DATE:** April 13, 2026
**TARGET:** /ganuda/services/arc_agi_3/ganuda_agent.py (SINGLE FILE EDIT)

## Context

The standalone `game_strategy.py` module has been written and tested at `/ganuda/services/arc_agi_3/game_strategy.py`. It provides a `StrategyTracker` class that monitors real-time game payoff metrics and switches between EXPLORER/EXPLOITER/ADAPTIVE strategies.

This instruction does ONE thing: add the StrategyTracker import and wiring to `ganuda_agent.py`. This is a minimal edit — 4 additions to one file.

## SINGLE TASK — Wire StrategyTracker into ganuda_agent.py

### Edit 1: Add import (after line 41)

Find the line:
```python
    EXPERIENCE_AVAILABLE = True
except ImportError:
    EXPERIENCE_AVAILABLE = False
```

Add AFTER it:
```python

try:
    from game_strategy import StrategyTracker
    STRATEGY_AVAILABLE = True
except ImportError:
    STRATEGY_AVAILABLE = False
```

### Edit 2: Initialize tracker in __init__ (after line 59, inside __init__)

Find the line:
```python
        self.fp = FrameProcessor()
```

Add AFTER it:
```python
        self.strategy = StrategyTracker() if STRATEGY_AVAILABLE else None
```

### Edit 3: Record actions in choose_action (find the return statement at end of choose_action)

Find the section where `action` is returned. Add BEFORE the return:
```python
        # Record action for strategy tracking
        if self.strategy:
            action_name = action.name if hasattr(action, 'name') else str(action)
            is_new_state = (self.current_node is not None and self.current_node not in self._seen_nodes)
            self.strategy.record_action(action_name, success=True, new_state=is_new_state)
```

### Edit 4: Record game-overs (find the game-over handling section)

Find where game-over is detected. Add:
```python
        if self.strategy:
            self.strategy.record_game_over()
```

### Verification

After edits, run:
```bash
cd /ganuda/services/arc_agi_3
./venv/bin/python -c "
from ganuda_agent import GanudaAgent
agent = GanudaAgent(game_id='test')
print(f'Strategy tracker: {agent.strategy}')
print(f'Current strategy: {agent.strategy.current_strategy}')
print('Integration OK')
"
```

Must print "Integration OK" with no errors.

## What this does NOT do

- Does NOT modify graph_explorer.py
- Does NOT modify deep_solver.py
- Does NOT run swarm tests (separate task)
- Does NOT change any existing behavior (strategy tracker is passive/logging only in this step)
