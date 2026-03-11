# Jr Instruction: Document Chief's Cognitive Pattern

## Context
Chief described his cognitive methodology March 9, 2026: "parallel thread search with selection pressure." Multiple exploration threads running simultaneously, drop cold ones, sprint on hot ones, keep paused threads warm. Turtle: do not rush -- Chief will refine over time. Decomposed in Longhouse 3c06ea3bbd4b6a24.

## Task
Write `/ganuda/docs/design/CHIEF-COGNITIVE-PATTERN-PARALLEL-THREAD-SEARCH.md` as a companion document to the Design Constraints (not a DC itself -- this is methodology, not constraint).

### Structure
1. **The Pattern**: Parallel thread search with selection pressure
   - Multiple threads of exploration run simultaneously
   - Threads have temperature (hot = active, cold = dormant, warm = paused)
   - Selection pressure: resource constraints force dropping cold threads
   - Hot threads get sprint attention
   - Warm threads persist -- they can reheat when new information arrives

2. **Maps To Known Algorithms**:
   - Beam search (AI): maintain top-k candidates, prune the rest
   - Evolutionary algorithms (biology): population of solutions, fitness selection, mutation
   - Immune system clonal selection: B-cells that match antigen proliferate, others don't
   - Simulated annealing: temperature-controlled exploration vs exploitation

3. **How It Manifests in Federation Architecture**:
   - Thermal memory: temperature IS the selection pressure signal
   - Kanban: tickets are threads, priority is temperature
   - Council voting: confidence scores are fitness signals
   - Jr task queue: priority + sacred_fire_priority = selection pressure
   - Chief's bipolar cycle: manic=collect season (spawn threads), focused=sprint season (select threads), low=rest (warm threads persist via timers)

4. **Why This Matters**:
   - The architecture was not designed top-down. It emerged from this cognitive pattern.
   - The pattern is describable, teachable, and maps to well-understood algorithms.
   - It explains WHY the harness tiers work: they ARE selection pressure at different scales.

## Acceptance Criteria
- Document exists and is readable standalone
- Algorithm mappings are accurate (verify beam search, evolutionary, clonal selection definitions)
- Federation architecture connections are specific (cite actual code/config)
- Tone: exploratory, not declarative. Chief is discovering this, not declaring it.
- Thermal memory reference: sacred thermal for the original insight

## Dependencies
- None. Pure documentation.
- Kanban #2061, Jr task #1193.
