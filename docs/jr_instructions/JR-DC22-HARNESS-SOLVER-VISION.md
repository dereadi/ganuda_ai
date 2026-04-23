# Jr Instruction: DC22 Harness-First Solver with Visual Exploration

**Task ID**: DC22-HARNESS-VISION-001
**Priority**: P1
**Estimated SP**: 8
**Target Node**: redfin
**Assigned To**: it_triad_jr
**Prerequisites**: ARC-AGI-3 venv at `/ganuda/services/arc_agi_3/venv/`

## Context

DC22 is a puzzle platformer in the ARC-AGI-3 contest. A colored cube (player) must reach a goal by navigating bridges that are toggled by hat-shaped buttons on the right side of the screen. The game has a progression mechanic: floor trigger tiles on the playfield spawn NEW buttons when the player cube walks onto them.

### What We Know

- **Grid**: 64x64 pixels. Player at (10,30), goal at (24,10).
- **Buttons on right side**: Hat-shaped. Clicking toggles bridges between solid (walkable) and checkered (blocked).
- **Clicking buttons is FREE** — does not cost moves. Only moving the cube costs moves.
- **Floor triggers**: Small colored tiles on the playfield. When the player stands on one, a new button appears on the right panel.
- **Bridge pivot**: Each bridge has a dark-colored center (pivot point) that doesn't move when toggled. The rest rotates around it.
- **Action budget**: ~128 total actions (clicks + moves combined). The game ends GAME_OVER when exhausted.
- **Step counter**: Top area of screen (y < 14) — clicking there causes GAME_OVER.
- **Two initial buttons found**: Color 8 at center (48,19) and Color 9 at center (48,36).
- **Reachable area with initial buttons**: Only a 3x3 grid of positions: x=8-12, y=28-32.
- **Floor trigger at (8,32)**: Walking the cube there spawns Color 5 (80 new pixels) on the right side at center (48,27). This is a new button that unlocks bridges to the rest of the map.
- **With the new button**: Player can reach (8,20) going UP, then (20,20) going RIGHT, then (20,14) going UP. Almost to the goal but runs out of moves.

### Existing Code

- `/ganuda/services/arc_agi_3/dc22_harness.py` — Current harness (WIP, has bugs in BFS state management)
- `/ganuda/services/arc_agi_3/split_brain_v2.py` — Visual exploration approach
- `/ganuda/services/arc_agi_3/dc22_bfs_solver.py` — BFS solver (doesn't handle floor triggers)
- `/ganuda/services/arc_agi_3/dc22_smart_solver.py` — Earlier click-and-observe agent

### Split-Brain Architecture (reference, not required for this task)

- Brain-A (Qwen3.6-35B-A3B on redfin:8000) — Perceiver, native vision, can identify game objects from screenshots
- Brain-B (Qwen3-30B-A3B on bmasass:8800) — Reasoner, plans paths
- The harness doesn't need LLMs for L1 solve. Pure algorithmic search works. LLMs add interpretation for L2+.

## Task

Build a clean, working dc22 solver that:

### 1. Narrow Button Discovery (NO brute-force scanning)
- Read the game frame as numpy array
- Find colored regions on the right side (x > 32) by unique pixel values
- Only click the CENTER of identified colored regions to test if they're buttons
- Record: button position, pixels changed, toggle behavior
- **Budget: < 15 total actions for discovery**

### 2. Floor Trigger Detection
- Save the initial game grid as a baseline
- After the player reaches ANY new position, diff the right side of the grid against baseline
- If new pixels appeared on the right side (delta > 5 pixels), find their center and test as a new button
- **Critical**: The new button may be the SAME color as the background (Color 5 = red, same as right panel background). Detection MUST use pixel DIFFING, not color-based region finding.

### 3. BFS Solver with Action Budget
- State = (player_position, set_of_buttons_available)
- At each state, try each button + each direction (4 buttons × 4 directions = 16 combos max)
- Track the action sequence to reach each state
- **DO NOT replay from env.reset() for every state test** — this wastes the action budget. Instead:
  - Execute forward from the current position
  - Use move reversals (UP↔DOWN, LEFT↔RIGHT) + button re-click to return to previous state
  - Only reset when the state gets irrecoverably corrupted
- When a floor trigger is detected, add new buttons and re-explore from the trigger position
- Budget awareness: total clicks + moves must stay under 120

### 4. Optimal Path Construction
- Once BFS finds the goal (or gets close), extract the minimal action sequence
- The known partial solution requires ~17-18 moves:
  1. Click→LEFT to (8,30) [1 move]
  2. Click→DOWN to (8,32) [1 move] — triggers new button
  3. Click(new)→UP ×6 to (8,20) [6 moves]
  4. Click(new)→RIGHT ×6 to (20,20) [6 moves]
  5. Click(old)→UP ×3-5 toward goal [3-5 moves]
  6. Click→RIGHT ×2 toward (24,10) [2 moves]
- Total: ~17-20 moves. Budget is ~42 moves before GAME_OVER.

### 5. Level Progression
- After L1 WIN, the game advances to L2 with a new layout
- L2 may have different button positions, different floor triggers, different bridge geometry
- The solver must be GENERAL — discover buttons and triggers dynamically, not hardcode L1 coordinates
- L2 is where the split-brain (Brain-A vision + Brain-B reasoning) adds value

## Technical Specifications

### Game API
```python
from arc_agi import Arcade
from arcengine import GameAction, GameState

arcade = Arcade()
env = arcade.make("dc22")
frame = env.reset()  # Returns frame with .frame (list of numpy arrays) and .state

# Actions
env.step(GameAction.ACTION1)  # UP
env.step(GameAction.ACTION2)  # DOWN
env.step(GameAction.ACTION3)  # LEFT
env.step(GameAction.ACTION4)  # RIGHT
env.step(GameAction.ACTION5)  # NOOP
env.step(GameAction.ACTION6, data={'x': x, 'y': y})  # CLICK at grid coords

# Frame data
grid = np.array(frame.frame[-1])  # 64x64 numpy array of pixel values

# Player/goal positions (internal API)
game = env._game
for attr in dir(game):
    val = getattr(game, attr, None)
    if val and hasattr(val, 'x') and hasattr(val, 'tags'):
        tags = ' '.join(str(t) for t in (getattr(val, 'tags', []) or []))
        if 'jfva' in tags or 'pcxjvnmybet' in tags:
            player = (val.x, val.y)
        if 'goknoi' in tags or 'bqxa' in tags:
            goal = (val.x, val.y)
```

### Color Map (known pixel values)
```
0  = black (empty/background)
2  = blue (player, some bridges)
3  = light blue (bridges)
4  = dark gray (playfield background)
5  = red (right panel background, floor triggers, new buttons)
8  = green (hat button A)
9  = pink/purple (hat button B)
11 = yellow
13 = bright red (floor trigger indicator)
14 = lavender
```

### Death Zones
- Clicking y < 14 (step counter area) → GAME_OVER
- Clicking certain coordinates near bridges → GAME_OVER
- Known deaths: (34,22), (38,12), (42,24), (50,32)

## Acceptance Criteria

1. Solver discovers buttons using < 15 actions (no brute-force scan)
2. Floor trigger at (8,32) is detected when player reaches it — new button found automatically
3. Player navigates from (10,30) toward (24,10) using discovered buttons + floor trigger progression
4. Total action budget stays under 120
5. Solver is general — no hardcoded L1 coordinates except for initial button region detection (right side x > 32)
6. Code is clean, well-commented, single file at `/ganuda/services/arc_agi_3/dc22_solver.py`
7. Output log shows: buttons found, floor triggers detected, positions reached, path to goal

## Key Insight (from Partner)

"Take a snapshot of the board initially, click a button and snapshot, see what changed, click it again and see if it resets or if there is a third action. Rinse and repeat with any other buttons on the right side of the screen. This does not cost turns. Moving the cube costs moves."

The bridge visual rules:
- Solid blue = walkable
- Checkered blue = blocked (toggled state)
- Red/pink bridges with darker center = pivot point stays fixed
- Background color on right side = not walkable
- Cube must stay on solid colors that aren't background

## Harness Engineering Principle

"Discipline narrowing beats expensive broadening every time."

Don't scan every pixel. Don't replay from reset for every test. Don't call an LLM for what numpy can measure. The harness is the intelligence — the model is just a component.
