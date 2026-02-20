# KB: Self-Evolving Rubrics — Process Reward Models for Federation Reasoning

**Date**: February 16, 2026
**Author**: TPM (Claude Opus 4.6)
**Source Paper**: "Reinforcing Chain-of-Thought Reasoning with Self-Evolving Rubrics" — Leheng Sheng, Wenchang Ma, Ruixin Hong, Xiang Wang, An Zhang, Tat-Seng Chua (Seed/ByteDance, NUS, USTC)
**Kanban**: Backlog
**Related**: #1781 (Self-Healing Pipeline), #1767 (Cross-Encoder Reranking)

## Core Idea

Bootstrap a **Process Reward Model (PRM)** without human-labeled step-level annotations:
1. Model generates **rubrics** — step-by-step evaluation criteria for its own reasoning
2. Rubrics score intermediate reasoning steps (not just final output)
3. Rubrics **self-evolve** as the model improves — the evaluation criteria get sharper over time
4. The PRM trained on self-generated rubric scores guides future reasoning via reinforcement

Key insight: You don't need humans to label "this reasoning step is good/bad." The model can generate its own evaluation criteria, and those criteria improve iteratively.

## Why This Matters for the Federation

### 1. Council Specialist Deliberation Quality
Currently, council specialists (Crawdad, Gecko, Turtle, Eagle Eye, Spider, Peace Chief, Raven) vote on proposals with a confidence score and optional concern flag. But the reasoning chain within each specialist's response is a black box.

**With rubrics**: Each specialist generates rubrics for their domain:
- Crawdad: "Does this step check for input validation? Does it consider privilege escalation?"
- Turtle: "Does this step evaluate 7-generation impact? Does it consider cultural preservation?"
- Raven: "Does this step account for resource constraints? Does it have a fallback strategy?"

Score each reasoning step against its rubric. Low-scoring steps trigger re-deliberation on that specific point.

### 2. Jr Executor Failure Root Cause
Currently when a Jr task fails, the executor retries → decomposes → DLQ. But we don't know *which reasoning step* went wrong.

**With rubrics**: Before execution, the Jr's plan is scored step-by-step:
- "Does step 3 specify the correct file path?" (rubric score: 0.4 — low → flag)
- "Does step 5 handle the case where the file already exists?" (rubric score: 0.9 — good)

Failed tasks feed back into rubric evolution — the rubric for "file path correctness" gets sharper after seeing path resolution bugs.

### 3. Thermal Memory Quality Scoring
We have 81K+ thermal memories with `temperature_score` (0-1) and `sacred_pattern` (bool). This is weak supervision for "reasoning quality."

**Self-evolving rubric for memory quality**:
- Generate rubrics: "Does this memory contain actionable technical detail? Is it specific enough to prevent a repeated mistake? Does it reference verifiable artifacts (files, tickets, KBs)?"
- Score existing memories → surface high-value memories more often in RAG
- Rubrics evolve as the corpus grows — what counted as "quality" at 5K memories differs at 81K

### 4. SA/Puzzle Search Guidance (Speculative)
For optimization problems like the Jane Street puzzle, a PRM could score intermediate SA moves:
- "This swap improved structural alignment of blocks 45-48" (high PRM score → continue this direction)
- "This reversal disrupted the learned pattern in the output layer" (low score → revert)

This replaces blind random-walk SA with informed search. But requires training data from successful move sequences — the pool of solved orderings could provide this.

## Implementation Phases

### Phase 1: Rubric Generator (Council)
- Add rubric generation to `specialist_council.py` — each specialist generates 3-5 evaluation criteria before reasoning
- Score reasoning steps against rubrics
- Store rubric scores in `council_votes.metacognition`
- **Estimated**: 8 SP

### Phase 2: Jr Executor Pre-flight Scoring
- Before execution, score the Jr's plan step-by-step against generated rubrics
- Flag low-confidence steps for TPM review before execution
- Feed failure data back into rubric evolution
- **Estimated**: 5 SP

### Phase 3: Thermal Memory Quality PRM
- Train lightweight rubric generator on thermal memories using temperature_score as weak label
- Use cross-encoder reranker (deployed RC-2026-02C) as scoring backbone
- Re-score entire corpus, update temperature_score
- **Estimated**: 8 SP

### Phase 4: Rubric Evolution Loop
- Periodically regenerate rubrics based on accumulated scores
- Compare rubric versions for drift detection
- Council meta-vote on rubric quality ("Are our evaluation criteria getting better?")
- **Estimated**: 5 SP

**Total**: 26 SP across 4 phases. Backlog until RC-2026-02F or later.

## Technical Architecture

```
Query → Council Specialist → Generate Rubrics → Reason step-by-step
                                    ↓                    ↓
                              Score each step ←── Rubric evaluation
                                    ↓
                              Low scores? → Re-deliberate that step
                                    ↓
                              Store scores → Feed back to rubric evolution
```

## Connection to Self-Healing Pipeline (#1781)
The self-healing pipeline (RC-2026-02D) handles infrastructure failures: alert → diagnose → remediate → validate. Self-evolving rubrics handle **reasoning failures**: evaluate → score → identify weak step → improve criteria. Same pattern, different layer:

| Layer | Self-Healing | Self-Evolving Rubrics |
|-------|-------------|----------------------|
| Detection | Alert bridge | Rubric scoring |
| Diagnosis | Remediation engine | Step-level root cause |
| Recovery | Validation pipeline | Re-deliberation |
| Learning | ARA feedback | Rubric evolution |

## References
- Paper: Sheng et al. "Reinforcing Chain-of-Thought Reasoning with Self-Evolving Rubrics" (2026)
- Institutions: Seed/ByteDance, NUS, USTC
- Tags: #PRM #self-correction #reasoning #process-reward-model
- Related federation work: Cross-encoder reranking (RC-2026-02C, #1767), Self-healing pipeline (RC-2026-02D, #1781), Sufficient context framework (#1705)
