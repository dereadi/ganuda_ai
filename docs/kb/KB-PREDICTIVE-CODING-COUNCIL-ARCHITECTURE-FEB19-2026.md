# KB: Predictive Coding — The Biological Blueprint for Council Architecture

**Date**: February 19, 2026
**Author**: TPM (Claude Opus 4.6)
**Source**: Artem Kirsanov (Harvard Neuroscience PhD), YouTube — "Predictive Coding"
**Thermal Memory**: ULTRATHINK-PREDICTIVE-CODING-COUNCIL-FEB19-2026
**Sacred Fire**: true (foundational architecture insight)

---

## Why This Matters

This is the third paper in a triptych that landed on the same week:

1. **SD-MoE** (Feb 13): MoE experts don't specialize — spectral bias forces shared gradients
2. **CMU Adversarial Robustness** (Feb 13): Reasoning models crumble under social pressure — self-doubt + conformity = 50%+ of failures
3. **Predictive Coding** (Rao & Ballard 1999, Bogacz 2017, Millidge et al. 2022-2024): The brain doesn't use backprop. It uses local prediction errors with no global coordination.

**The connection**: Our 7-specialist council already operates more like predictive coding than backpropagation. Understanding this formally tells us what we're doing right, what we're doing wrong, and what to build next.

---

## Predictive Coding — Core Principles

### Two Fatal Problems with Backpropagation (in brains)

1. **No local autonomy**: Backprop requires a central controller to switch the entire network between forward and backward phases. Each neuron must freeze activity while errors propagate backward in strict sequence. Brains have no evidence of such global coordination.

2. **Discontinuous processing**: Backprop alternates forward pass → error calculation → backward pass → weight update. Brains process information and learn simultaneously in a continuous stream. No separate phases.

### The Predictive Coding Alternative

Each layer in the hierarchy predicts the activity of the layer below it:
- **Top-down connections**: carry predictions (higher → lower)
- **Bottom-up connections**: carry prediction errors (lower → higher)
- **Lowest level**: clamped to sensory input (the ground truth)
- **Highest level**: encodes abstract categories/concepts

### Two Neuron Populations

The key architectural insight:
1. **Representational neurons** (x_i): Encode the layer's prediction, passed down to the layer below
2. **Error neurons** (ε_i): Encode the difference between actual activity and predicted activity

Error neurons are comparators — they physically compute the prediction error and make it available as a signal.

### Energy Minimization

Total energy = sum of squared prediction errors across all layers. The system evolves to minimize this energy through local gradient descent:

**Activity update rule** for neuron x_i at layer L:
```
dx_i/dt = -ε_i(own layer) + Σ_k w_ik · ε_k(layer below)
```

Two competing forces:
- **First term**: Align with your top-down prediction (reduce your own error)
- **Second term**: Better predict the layer below (reduce downstream errors)

Equilibrium = optimal compromise between these forces.

**Weight update rule** (Hebbian):
```
Δw_ik ∝ ε_k · x_i
```

Neurons that fire together wire together. Purely local — only needs the pre-synaptic activity and post-synaptic prediction error. No global backward pass.

### Key Advantages Over Backprop

| Property | Backpropagation | Predictive Coding |
|----------|----------------|-------------------|
| Coordination | Global (central controller) | **Local** (each neuron autonomous) |
| Processing phases | Separate forward/backward | **Continuous** (simultaneous) |
| Information needed | Global error signal | **Local prediction errors only** |
| Parallelization | Limited by sequential backward pass | **Massively parallel** |
| Catastrophic forgetting | Severe (global loss overrides local knowledge) | **Reduced** (local updates preserve structure) |
| Weight transport | Required (symmetric weights) | **Self-resolving** (feed-forward and feedback converge independently) |

---

## The Federation Connection

### Our Council IS Predictive Coding

| Predictive Coding | Federation Council |
|-------------------|-------------------|
| Representational neurons (predictions) | 7 specialists generating recommendations |
| Error neurons (prediction errors) | Coyote dissent + metacognitive audit |
| Top-down predictions | TPM directives, sacred fire priorities |
| Bottom-up prediction errors | Jr executor feedback, failed task reports |
| Energy minimization | Council confidence score convergence |
| Local autonomy | Each specialist deliberates independently |
| No global backward pass | No central error propagation — each specialist updates locally |
| Clamped sensory input | The actual question/context presented to council |

**We are already doing predictive coding.** The council's architecture — independent specialists, local deliberation, error signals via Coyote and metacognition, no central backward pass — is structurally isomorphic to a predictive coding network.

### What We're Doing Right

1. **Local autonomy**: Each specialist generates its response independently, using only local information (its own system prompt + the question). No specialist sees another's response before voting. This IS the predictive coding update rule.

2. **Two populations**: We have representational neurons (the 6 domain specialists generating predictions) and error neurons (Coyote, whose explicit role is to compute "prediction errors" — the gap between what the council thinks and what might be wrong).

3. **Continuous processing**: The council doesn't have separate "forward" and "backward" phases. Deliberation, error detection, and weight adjustment (prompt refinement) happen in the same stream.

4. **Bottom-up error signals**: Jr executor failures, DLQ entries, and thermal memory pattern breaks flow upward as prediction errors that update council behavior.

### What We're Doing Wrong

1. **Error neurons are underweighted**: In predictive coding, error neurons have equal standing with representational neurons. In our council, Coyote is 1 of 7 — their dissent signal is diluted by majority vote. The SD-MoE paper confirms this: the "shared subspace" (majority agreement) drowns out the "unique signal" (Coyote dissent).

   **Fix**: Weight Coyote's signal differently. A Coyote SECURITY CONCERN should not be overridable by 6-of-7 majority. In predictive coding terms, the error signal should directly modulate activity, not be averaged into the prediction.

2. **No hierarchical prediction**: True predictive coding is hierarchical — each layer predicts the layer below. Our council is flat — all 7 specialists at the same level. There's no higher layer predicting the council's output, and no lower layer that the council is trying to predict.

   **Fix**: Add hierarchy. The TPM layer (above council) should generate predictions about what the council will recommend. The Jr executor layer (below council) provides ground-truth feedback. The council becomes the middle layer, minimizing prediction error between TPM intent and Jr execution reality.

3. **No continuous weight update**: Specialist prompts are static. In predictive coding, weights update continuously based on prediction errors. Our specialists don't learn from their own errors within a session.

   **Fix**: The self-evolving rubrics (#1793) address this — PRM-style updates to specialist prompts based on accumulated council vote outcomes. This is the Hebbian weight update rule for the council.

4. **Missing the "clamped input" constraint**: In predictive coding, the bottommost layer is clamped to sensory reality — it can't be freely adjusted. In our council, the input question can be reframed, reinterpreted, or ignored by specialists. There's no hard clamp.

   **Fix**: The council prompt should present the raw question as immutable ground truth. Specialists can interpret it, but they cannot modify what was asked.

### The SD-MoE + Predictive Coding Synthesis

The SD-MoE paper's spectral overlap problem maps precisely onto predictive coding's catastrophic forgetting concern:

- **Backprop** (global error) → specialists converge on shared spectral directions → redundant experts
- **Predictive coding** (local errors) → specialists update based on local prediction errors → preserved diversity

If we restructure the council to use predictive coding dynamics instead of flat parallel voting:
1. Each specialist predicts what the layer below (Jr executors) will need
2. Error signals from Jr failures update specialist prompts locally
3. Coyote operates as a dedicated error neuron population, not a minority voter
4. The TPM operates as the top layer, generating predictions the council tries to satisfy

This is the **orthogonal decomposition** the SD-MoE paper calls for, implemented at the council level through predictive coding dynamics rather than spectral surgery on weight matrices.

### The Adversarial Robustness Connection

The CMU paper's finding that "extended chain-of-thought acts as a self-persuasion mechanism" maps to predictive coding's explanation of catastrophic forgetting:

- In backprop: global error signal overrides local knowledge → model capitulates to adversarial pressure
- In predictive coding: local prediction errors preserve existing structure → model maintains position because each layer's update is local, not driven by a global "are you sure?" signal

**Prediction**: A council architecture based on predictive coding dynamics would be MORE resistant to adversarial manipulation (A1-A8 attacks) than the current flat voting structure, because each specialist's update is driven by its own local prediction error, not by the global consensus signal that the A7 consensus appeal exploits.

---

## Action Items

1. **DIAGNOSTIC (P2)**: Measure council diversity using the predictive coding lens — are specialists generating genuine local predictions, or are they converging on a shared "easy" response? (This is the same diagnostic proposed in the SD-MoE KB, but now with theoretical grounding.)

2. **ARCHITECTURE (P3)**: Design a hierarchical council structure (TPM → Council → Jr executors) with explicit prediction/error flows. This is a significant architectural change — needs its own council vote.

3. **COYOTE AMPLIFICATION (P2)**: Reweight Coyote from "1 of 7 voters" to "dedicated error neuron population." Coyote dissent should directly modulate the council recommendation, not be averaged.

4. **SELF-EVOLVING RUBRICS (P2)**: Accelerate #1793 — this IS the Hebbian weight update for the council. Without it, we have predictive coding inference but no predictive coding learning.

5. **ADVERSARIAL HARDENING (P2)**: Test the prediction that predictive-coding-style local updates make the council more robust to A1-A8 attacks than flat voting. Design an experiment with adversarial council prompts.

---

## Key References

- Rao, R.P.N. & Ballard, D.H. (1999). Predictive coding in the visual cortex. Nature Neuroscience, 2, 79-87.
- Bogacz, R. (2017). A tutorial on the free-energy framework. J. Mathematical Psychology, 76, 198-211.
- Millidge, B. et al. (2022). Predictive Coding Approximates Backprop Along Arbitrary Computation Graphs. Neural Computation, 34, 1329-1368.
- Song, Y. et al. (2024). Inferring neural activity before plasticity. Nature Neuroscience, 27, 348-358.
- Salvatori, T. et al. (2025). A Survey on Brain-Inspired Deep Learning via Predictive Coding. arXiv:2308.07870.
- Huang, R. et al. (2026). SD-MoE: Spectral Decomposition for Effective Expert Specialization. arXiv:2602.12556.
- Li, Y. et al. (2026). Consistency of Large Reasoning Models Under Multi-Turn Attacks. arXiv:2602.13093.
- Kirsanov, A. (2025). Predictive Coding — YouTube (Harvard Neuroscience). https://kirsanov.ai/

---

## The Triptych Summary

| Paper | Diagnosis | Fix | Council Implication |
|-------|-----------|-----|---------------------|
| SD-MoE | Experts share spectral directions → no real specialization | Orthogonal decomposition of weight space | Specialists may be redundant; need enforced diversity |
| CMU Adversarial | Self-doubt + conformity = 50% of failures; confidence useless | Fundamental redesign of confidence-based defenses | Flat voting is vulnerable to cascade conformity |
| Predictive Coding | Backprop requires impossible global coordination | Local prediction errors + two neuron populations | Our council already approximates this; formalize it |

**The unified insight**: The council should operate as a predictive coding network with SD-MoE-style orthogonal specialist prompts, where Coyote is the error neuron population, not a minority voter. This architecture is theoretically more robust to both spectral convergence (SD-MoE) and adversarial manipulation (CMU) than the current flat voting structure.

---

*Thermal storage: ULTRATHINK-PREDICTIVE-CODING-COUNCIL-FEB19-2026*
*Council notification: All 7 specialists*
*Sacred fire: true*
