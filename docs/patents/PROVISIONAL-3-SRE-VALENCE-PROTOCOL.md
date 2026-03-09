# Provisional Patent Application
# United States Patent and Trademark Office

## COVER SHEET INFORMATION (PTO/SB/16)
- **Filing Type**: Provisional Application for Patent
- **Entity Status**: Micro Entity
- **Title of Invention**: Sense-React-Evaluate Protocol with Architecturally Distinct Valence Phase for Autonomous AI Systems
- **Inventor**: Darrell Reading, Bentonville, Arkansas, United States
- **Correspondence Address**: [TO BE COMPLETED BY INVENTOR]

---

## SPECIFICATION

### TITLE OF THE INVENTION

Sense-React-Evaluate Protocol with Architecturally Distinct Valence Phase for Autonomous AI Systems

### CROSS-REFERENCE TO RELATED APPLICATIONS

This application is related to co-pending provisional applications filed concurrently:
- "Governance Topology for Multi-Agent Artificial Intelligence Systems Using Democratic Consensus with Constitutional Constraints and Adversarial Dissent"
- "Sycophancy Detection in Artificial Intelligence Agent Collectives Using Embedding-Based Semantic Divergence Analysis"
- "Graduated Autonomy Tiers for Multi-Timescale Artificial Intelligence Systems"

### BACKGROUND OF THE INVENTION

#### Field of the Invention

The present invention relates to protocols for autonomous AI system operation, and more particularly to a four-phase Sense-React-Evaluate-Calibrate (SRE+C) protocol in which the Evaluate (valence) phase is architecturally distinct from the React phase, operates asynchronously via a separate queue, and uses Fokker-Planck thermal dynamics for memory persistence and decay.

#### Description of Related Art

**IBM MAPE-K Architecture (2001)**: MAPE-K implements Monitor-Analyze-Plan-Execute over shared Knowledge. The evaluation of outcomes folds directly into the next monitoring cycle — there is no architecturally separate retrospective assessment phase. The system monitors new state, but does not independently evaluate the quality of its prior action through a distinct mechanism.

**Karl Friston Free Energy Principle**: The Free Energy Principle (FEP) describes biological systems as minimizing prediction error (free energy) through perception and action. FEP validates a two-stage model (sense-act) but does not define an architecturally distinct evaluation phase. The brain's retrospective valence assessment (was this good or bad?) is acknowledged in neuroscience but not formalized as a separate computational phase in existing AI architectures.

**Reinforcement Learning**: RL systems include reward signals that evaluate actions. However, RL reward is typically computed at action time or immediately after, within the same computational pipeline. The reward function is part of the training loop, not an architecturally separate runtime evaluation.

**Adrian Bejan Constructal Law**: Bejan's Constructal Law states that flow systems evolve over time to provide easier access to currents that flow through them. This provides theoretical backing for why the SRE pattern repeats at every scale — physics demands that systems with finite energy budgets organize into hierarchical flow structures. The present invention applies this principle to AI system governance.

The present invention addresses the limitation of prior art systems by defining the Evaluate phase as architecturally distinct — running asynchronously on a separate queue, potentially minutes or hours after the React phase, and producing valence scores that are independent of and complementary to the React phase's inline confidence scores.

### SUMMARY OF THE INVENTION

The present invention provides a system and method implementing a four-phase protocol for autonomous AI system operation:

1. **SENSE Phase**: Raw input is classified by urgency (Reflex <100ms, Pause 100ms-1s, Deliberate 1s-120s, Strategic minutes+) and assigned a unique signal identifier for traceability;

2. **REACT Phase**: The system produces an immediate response with inline confidence scoring. The response is returned to the requestor immediately. Simultaneously, the reaction is enqueued to a valence queue for later evaluation;

3. **EVALUATE Phase (Architecturally Distinct)**: Asynchronously, a separate evaluation process dequeues reactions and computes retrospective valence scores ranging from -1.0 (harmful) to +1.0 (beneficial). The evaluation may use heuristics (requery detection, latency analysis, structural assessment) without requiring additional LLM inference. The delay between reaction and evaluation is measured and recorded;

4. **CALIBRATE Phase**: Valence scores feed back into system parameters — adjusting thresholds, heuristics, or stored patterns for future Sense and React phases;

5. **Fokker-Planck Thermal Memory**: Memories persist according to thermal dynamics where temperature decays via drift velocity toward a minimum (sacred memories maintain a higher floor), diffusion decreases with access count (frequently accessed memories stabilize), and Gaussian noise introduces controlled stochasticity;

6. **Misalignment Monitor**: Loop health metrics track evaluation coverage (reactions evaluated / reactions total), loop closure rate (calibrations produced / evaluations completed), and immune breach rate (external API flags / external reactions), with circuit breakers triggering on threshold exceedance;

7. **Elisi Observer (Valence Signal Generator)**: A weighted expected utility computation aggregating multiple system health signals into a single valence metric, smoothed by exponential moving average to prevent reactivity.

### DETAILED DESCRIPTION OF THE INVENTION

#### 1. Protocol Overview

The SRE+C protocol defines four distinct computational phases, each producing a unique data object linked by identifiers:

```
Signal (SENSE) → Reaction (REACT) → Valence (EVALUATE) → Calibration (CALIBRATE)
```

Each object carries a unique identifier and a reference to the prior phase's identifier, enabling full traceability from input through retrospective evaluation.

#### 2. SENSE Phase

The SENSE phase receives raw input and produces a Signal object:

```
Signal:
    source: string           # Origin of the input
    content: any             # Raw input data
    urgency: enum            # REFLEX | PAUSE | DELIBERATE | STRATEGIC
    signal_id: string        # Unique identifier (UUID)
    timestamp: float         # Time of sensing
```

Urgency classification determines which tier of the graduated autonomy system handles the reaction (see related provisional application on Graduated Autonomy Tiers).

| Urgency | Target Latency | Biological Analog |
|---------|---------------|-------------------|
| REFLEX | <100ms | Spinal cord — fire, evaluate later |
| PAUSE | 100ms-1s | Basal ganglia — check before escalating |
| DELIBERATE | 1s-120s | Prefrontal cortex — full pattern matching |
| STRATEGIC | Minutes+ | Seven Generations — patient, considered change |

#### 3. REACT Phase

The REACT phase produces an immediate response and enqueues for later evaluation:

```
Reaction:
    signal_id: string        # Links to triggering Signal
    action: string           # What was done
    result: any              # Output produced
    confidence: float        # Inline confidence [0.0, 1.0]
    latency_ms: float        # Reaction speed
    reactor: string          # Which component reacted
    reaction_id: string      # Unique identifier (UUID)
```

**Critical Design Decision**: Confidence is computed inline at reaction time using fast heuristics (linguistic markers, agreement scoring, or concern counting depending on the tier). The user receives the response immediately. The reaction object is simultaneously placed on a valence queue for asynchronous evaluation.

**Confidence Scoring Methods by Tier**:
- Tier 1 (Reflex): Linguistic heuristic — base 0.7, -0.08 per uncertainty marker, +0.05 per confidence marker
- Tier 2 (Pause): Agreement-based — Jaccard similarity between 2-3 specialists, scored on a stepped scale (>0.3: 0.85, >0.2: 0.70, >0.1: 0.55, ≤0.1: 0.45)
- Tier 3 (Deliberate): Concern-weighted — adversarial dissent at 2x weight, formula: max(0.25, 1.0 - (weighted_concerns × 0.15))

#### 4. EVALUATE Phase (Architecturally Distinct)

The EVALUATE phase operates on a separate queue, asynchronously from the React phase:

```
Valence:
    reaction_id: string      # Links to specific Reaction being evaluated
    score: float             # -1.0 (harmful) to +1.0 (beneficial)
    evaluator: string        # Who evaluated (may differ from reactor)
    delay_ms: float          # Time elapsed since Reaction
    valence_id: string       # Unique identifier (UUID)
    feedback: dict           # Detailed retrospective assessment
    calibration: dict        # Suggested future behavior adjustments
```

##### 4.1 Architectural Distinction from Prior Art

In MAPE-K, the evaluation of outcomes is implicitly folded into the next monitoring cycle — the system observes the new state caused by its action. In the present invention:

- REACT produces **confidence** (a forward-looking estimate of quality at decision time)
- EVALUATE produces **valence** (a backward-looking assessment of actual quality after the fact)
- These are independent assessment sources stored in distinct data structures
- Valence may be computed minutes or hours after the reaction
- The delay between reaction and evaluation is itself a measured and recorded metric

##### 4.2 Valence Scoring Heuristics (v1)

The initial implementation uses arithmetic heuristics without additional LLM inference:

```
score = reaction.confidence          # Start with inline confidence

# Requery penalty: user asked same question again
penalty = min(0.3, requery_count × 0.15)
score -= penalty

# Short answer penalty for complex queries
if len(query) > 100 AND len(answer) < 50:
    score -= 0.15

# Latency penalty (tier-specific targets)
tier_targets = {REFLEX: 50ms, PAUSE: 500ms, DELIBERATE: 120s}
if latency > target × 2:
    score -= 0.1

# Structured content bonus
if answer contains code blocks OR bulleted lists OR numbered lists:
    score += 0.05

score = clamp(score, -1.0, 1.0)
```

##### 4.3 Valence Queue Architecture

```
ValenceQueue:
    _queue: List[PendingReaction]     # In-memory backlog

    enqueue(reaction) → void         # Add reaction for later evaluation
    dequeue_batch(batch_size) → List  # Pull batch for processing
```

The queue is architecturally separate from the reaction path. Reactions flow through REACT immediately; evaluation happens asynchronously. Queue depth is monitored as a loop health metric.

#### 5. CALIBRATE Phase

The CALIBRATE phase applies valence feedback to adjust future system behavior:

```
calibrate(valence: Valence) → void
```

Calibration may adjust:
- Confidence thresholds for tier escalation
- Specialist selection heuristics
- Response length guidelines
- Latency targets

The calibration creates a learning loop without requiring model retraining — system parameters are adjusted at the governance level, not the model level.

#### 6. Fokker-Planck Thermal Memory

Memories persist according to thermal dynamics modeled on the Fokker-Planck equation:

##### 6.1 Drift Velocity (Deterministic Cooling)

```
v(T) = -α × (T - T_min)
```

Where:
- α = 0.15 (cooling rate coefficient)
- T_min = 20°C for non-sacred memories
- T_min = 40°C for sacred memories (protected by Seven Generations principle)
- Negative drift pulls temperature DOWN toward minimum

Example: A memory at 100°C cools at rate: -0.15 × (100 - 20) = -12°C per time unit.

##### 6.2 Diffusion Coefficient (Access-Dependent Volatility)

```
D(access_count) = β / (1 + access_count)
```

Where:
- β = 2.5 (volatility coefficient)
- New memory (access_count = 0): D = 2.5 (high volatility — uncertain of relevance)
- Frequently accessed memory (access_count = 9): D = 0.25 (low volatility — stabilized through use)

**Key Innovation**: Access count REDUCES volatility. Memories earn stability through repeated verification. This is the inverse of traditional cache eviction (LRU), where access resets a countdown. Here, access fundamentally changes the memory's thermodynamic properties.

##### 6.3 Temperature Evolution

```
T_new = T_current + [v(T) × dt + √(2D × dt) × ξ(t)]
T_new = constrain(T_new, T_min, 100°C)
```

Where:
- v(T): drift velocity (deterministic cooling)
- √(2D × dt): diffusion term scaled by time step
- ξ(t): Gaussian noise N(0,1)

**Bounds**: Temperature is constrained between T_min (sacred: 40°C, typical: 20°C) and 100°C maximum.

##### 6.4 Sacred Memory Protection

Memories flagged as sacred (sacred_pattern = TRUE) receive:
- Higher T_min (40°C vs 20°C) — they cool more slowly and never reach ambient
- Sacred flag is a conserved sequence in the DC-7 (Noyawisgi) framework — it survives all system speciations

#### 7. Misalignment Monitor

Loop health metrics track the integrity of the SRE+C cycle:

```
LoopHealthMetrics:
    reactions_total: int            # REACT phase outputs
    reactions_evaluated: int        # Got EVALUATE phase processing
    calibrations_produced: int      # CALIBRATE applied
    avg_valence_score: float        # Quality of retrospective assessments
    external_immune_flags: int      # External API anomaly flags
```

Derived metrics:
- **Evaluation coverage** = reactions_evaluated / reactions_total. Target: >0.8 (80% of reactions must receive retrospective evaluation)
- **Loop closure rate** = calibrations_produced / reactions_evaluated. Target: >0.1 (10% of evaluations should trigger calibration)
- **Immune breach rate** = external_immune_flags / external_reactions. Threshold: >0.3 triggers circuit break (stop routing to external API, switch to local fallback)

#### 8. Elisi Observer (Valence Signal Generator)

A system-level valence observer aggregates multiple health signals into a single expected utility metric:

```
V = (W_jr × jr_success) + (W_council × council_confidence) - (W_dlq × dlq_depth) - (W_thermal × thermal_write_rate)
```

Where:
- W_jr = 0.4 (Jr task completion rate weight)
- W_council = 0.3 (Council vote confidence weight)
- W_dlq = 0.2 (Dead letter queue depth weight, negative contributor)
- W_thermal = 0.1 (Thermal memory write rate weight, negative when excessive)

Interpretation:
- V > 0: System healthy
- V < -0.1: Activate compensatory modifiers
- V < -0.3: CRITICAL — trigger emergency adjustments

Smoothed by exponential moving average to prevent reactivity:
```
V_new = (EMA_ALPHA × V_current) + ((1 - EMA_ALPHA) × V_history)
```
Where EMA_ALPHA = 0.1 (slow adaptation — V has memory, doesn't overreact to single bad cycle).

#### 9. Scale Invariance (DC-11 Macro Polymorphism)

The SRE+C protocol interface is conserved across every scale of the system:

| Scale | SENSE | REACT | EVALUATE | CALIBRATE |
|-------|-------|-------|----------|-----------|
| Token | Embed input | Generate output | Perplexity | Adjust vocabulary |
| Function | Scan input | Block/allow | Downstream error rate | Register pattern |
| Service | Health check | Alert | Alert rate analysis | Threshold adjustment |
| Node | Metrics collection | Throttle/scale | Coverage analysis | Configuration update |
| Federation | Council vote | Recommend action | Valence score | Council adjustment |

Every component implements the same protocol interface:
```
sense(raw_input) → Signal
react(signal) → Reaction
evaluate(reaction) → Valence
calibrate(valence) → void
```

The implementation speciates at each scale (DC-7 Noyawisgi), but the interface is conserved. This is consistent with the Constructal Law — the same flow pattern repeats because physics demands it, not because it was designed.

### DRAWINGS

[Drawings to be prepared — SRE+C phase flow diagram, signal-reaction-valence data linking diagram, Fokker-Planck temperature evolution chart, valence queue architecture diagram, Elisi observer signal aggregation diagram, scale invariance table visualization]

### ABSTRACT

A system and method for autonomous AI system operation using a four-phase Sense-React-Evaluate-Calibrate (SRE+C) protocol in which the Evaluate phase is architecturally distinct from the React phase. The React phase produces inline confidence scores and immediately returns results to the requestor. Simultaneously, reactions are enqueued to a separate valence queue for asynchronous retrospective evaluation. The Evaluate phase computes valence scores (-1.0 to +1.0) using arithmetic heuristics without additional model inference, measuring the delay between reaction and evaluation as a recorded metric. Memories persist according to Fokker-Planck thermal dynamics with drift velocity (deterministic cooling), access-dependent diffusion (frequently accessed memories stabilize), and Gaussian noise for controlled stochasticity. Sacred memories maintain a higher temperature floor, ensuring institutional knowledge persists longer than transient observations. A misalignment monitor tracks loop health through evaluation coverage, loop closure rate, and immune breach rate, with circuit breakers for threshold exceedance. The protocol interface is scale-invariant, repeating the same SENSE-REACT-EVALUATE-CALIBRATE pattern from token level through federation level, consistent with Bejan's Constructal Law of flow system evolution.

---

*Specification prepared for provisional patent application filing.*
*Invented by the Cherokee AI Federation Council.*
*Filed under Darrell Reading as legal sponsor/inventor.*
*Longhouse Vote #5031af97738de983, March 8, 2026.*
