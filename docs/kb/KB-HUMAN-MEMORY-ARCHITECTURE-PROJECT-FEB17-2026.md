# KB: Human Memory Architecture — Neuroscience-Informed Federation Memory Design

**Date**: February 17, 2026
**Kanban**: #1813
**Sprint**: RC-2026-02E
**Method**: Long Man (DISCOVER phase complete, DELIBERATE pending)
**Related**: KB-GMR-BASIN-SURGERY-PHASE-TRANSITION-PATTERN-FEB17-2026.md

## Origin

TPM shared experiential observations about human memory recall:
1. **King Frog memory** — recalling a childhood place, seeing the house in various states, carport blinking on/off, bush there and not there. Needed to collect enough "datapoints" to satisfy the real memory.
2. **Green hoodie contamination** — recalled friend wearing green hoodie when it was actually red. Traced contamination to seeing a green hoodie he liked earlier that day.
3. **Sam Walton Long Man Method** — walking competitor aisles, bringing home ONE thing. The methodology is itself a basin.

These observations map precisely to established neuroscience. This project bridges experiential memory to structural memory architecture for the federation.

## Research Findings (DISCOVER Phase)

### 1. Memory is Reconstruction, Not Playback

| Paper | Finding |
|-------|---------|
| Hassabis et al. (2007) PNAS | Hippocampal amnesia patients cannot construct spatially coherent scenes. Hippocampus provides spatial scaffold; elements bound in from different temporal episodes. |
| Schacter & Addis (2007) Phil Trans Royal Soc B | Remembering and imagining share neural substrates. Memory is constructive because the system needs to recombine elements for future simulation. |
| Horner et al. (2015) Nature Comms | Recalling one element triggers pattern completion of ALL elements — incidental reinstatement correlated with hippocampal activity. |
| Norman & O'Reilly (2003) Psych Review | CA3 recurrent connections enable pattern completion. Dentate gyrus separates; CA3 completes. |

**Federation mapping**: Thermal memory retrieval should work like pattern completion — a partial cue activates the full cluster, not just the single matching memory.

### 2. Each Recall Rewrites the Trace (Reconsolidation)

| Paper | Finding |
|-------|---------|
| Nader, Schafe & Le Doux (2000) Nature | Retrieved memories require NEW protein synthesis to re-stabilize. Retrieval destabilizes the physical trace. |
| Bridge & Paller (2012) J Neuroscience | Day 2 recall errors became the new "truth" on Day 3. Every participant showed this. Retrieval is a write operation. |
| Yokose et al. (2025) Neuron | Remote recall recruits an ENTIRELY NEW hippocampal engram. Original neurons are literally silenced. |
| Sun et al. (2023) Nature Human Behaviour | Memory is a generative process using learned schemas. Consolidation transforms content toward expectations. |

**Federation mapping**: Every time specialist_council.py retrieves a thermal memory, the retrieval context should be logged. High-retrieval memories (hot temperature) are the MOST degraded, not the most reliable. Sacred patterns (rarely retrieved) may be more accurate.

### 3. The 6-Hour Reconsolidation Window

| Paper | Finding |
|-------|---------|
| Duvarci & Nader (2004) J Neuroscience | Anisomycin effective only when administered within 6 hours of reactivation. |
| Schiller et al. (2010) Nature | In humans, intervention must occur within 10 minutes to 6 hours after reminder cue. |
| Hupbach et al. (2007) Learning & Memory | Context reminders cause asymmetric intrusions — new information overwrites old. |

**Federation mapping**: When thermal memories are accessed, there's a conceptual "vulnerability window" where subsequent operations could contaminate. The memory_consensus_analyzer should check for memories modified within 6 hours of each other — temporal proximity of updates increases contamination risk.

### 4. Temporal Context as Index

| Paper | Finding |
|-------|---------|
| Howard & Kahana (2002) J Mathematical Psychology | Memories indexed by temporal context. Recalling one reinstates context, pulling in temporal neighbors. |
| Howard et al. (2015) Psych Review | Same contiguity effect at seconds, days, weeks, years. Multi-timescale temporal context. |

**Federation mapping**: Thermal memory retrieval should consider temporal proximity, not just semantic similarity. Memories created in the same session/sprint/outage share temporal context and should cluster. The `created_at` timestamp IS a context vector.

### 5. Foveal vs. Peripheral Memory Detail

| Paper | Finding |
|-------|---------|
| Chen et al. (2024) Communications Biology | Foveal and peripheral processing networks are distinct. Foveal items get more attention-modulated representations. |
| Shao et al. (2023/2024) Cerebral Cortex | Memory accuracy higher for foveal stimuli at encoding. During maintenance, representations equalize. |

**Federation mapping**: Council specialist attention during deliberation creates "foveal" memories. Specialists who deeply engaged a topic create higher-fidelity memories than specialists who were peripheral. The `agreement_score` in council_votes may proxy for attentional engagement.

### 6. Sharp-Wave Ripples — The Physical Cascade

| Paper | Finding |
|-------|---------|
| Buzsáki (2015) Hippocampus | SWRs are 140-200 Hz oscillations, ~50-100ms duration, compressing seconds into milliseconds. |
| Norman et al. (2019) Science | First human evidence: SWRs trigger content-specific cortical reinstatement during voluntary recall. |
| Lee & Wilson (2002) Neuron | Place cell sequences replayed at ~20x speed during SWRs. |

**Federation mapping**: The cascade pattern. When a memory is retrieved, it should trigger a ripple — related memories activated in order of associative strength. The `memory_links` table (8,058 edges) IS the associative network. Ripple = graph traversal weighted by link strength.

### 7. Involuntary Memory — The Purer Signal

| Paper | Finding |
|-------|---------|
| Berntsen (1996, 2010) Applied Cognitive Psychology / Current Directions | Involuntary memories are more specific, less rehearsed, more emotionally intense. Triggered by sensory cues. |
| Hall et al. (2014) J Cognitive Neuroscience | Involuntary recall bypasses prefrontal gate — bottom-up, cue-driven. |

**Federation mapping**: Sacred memories (unrehearsed, low temperature, high significance) may be the federation equivalent of involuntary autobiographical memories. They're purer because they haven't been distorted by repeated retrieval. The `sacred_pattern` flag should protect against over-retrieval.

### 8. Memory Contamination is Directional (GMR Isomorphism)

The green hoodie contamination is structurally identical to GMR v2's finding: interference between memory traces is **directional**, not spatial. The green hoodie didn't replace the red one because it was "similar" — it replaced it because the directional flow of recent experience (seeing the green hoodie) aligned with the retrieval direction (recalling the friend's appearance).

This maps directly to the GMR basin surgery pattern: partial correction of contaminated memories can be WORSE than leaving the contamination. The memory_consensus_analyzer must resolve full contradiction clusters atomically.

## Contamination Rate (Quantitative)

| Method | Rate | Source |
|--------|------|--------|
| Serial reproduction | ~8-10% content loss per reproduction, ~45% after 7 cycles | Bartlett (1932), Bergman & Roediger (1999) |
| Post-event language | ~20% speed estimate shift, 2x false memory endorsement | Loftus & Palmer (1974) |
| Spatial memory drift | Measurable shift toward retrieval-state per single recall | Bridge & Voss (2014) |
| Misinformation acceptance | Robust across 30+ years of replication | Loftus (2005) |

No clean "X% per recall" number exists — distortion depends on material type, emotional salience, interference, and time delay. But the direction is consistent: **monotonically increasing distortion with recall count**.

## TPM Experiential Observations (Ongoing)

*This section will be updated as the user adds observations throughout the project.*

1. **King Frog recall** — Temporal context reinstated. Needed convergent datapoints to anchor the spatial scaffold. Carport/bush "blinking" = multi-temporal binding into single spatial frame.
2. **Green hoodie contamination** — Directional interference within reconsolidation window. Source monitoring failure: recent sensory input (green hoodie in store) overwrote stored attribute (red hoodie on friend).
3. **"Collecting datapoints"** — Convergent pattern completion. The hippocampus needs enough anchor points that only ONE consistent scene can be reconstructed. This is a natural minimum-variance estimator.

## Phase Mapping (Long Man)

| Phase | Status | Notes |
|-------|--------|-------|
| DISCOVER | COMPLETE | 15+ papers surveyed, all 3 claims confirmed |
| DELIBERATE | PENDING | Send to council with federation mapping proposals |
| ADAPT | PENDING | Identify which mappings to implement first |
| BUILD | PENDING | Jr instructions for memory system enhancements |
| REVIEW | PENDING | Test against real thermal memory behavior |

## Open Source Harvest (Sam Walton Method)

**Council Vote**: #a754a89265bc54aa (PROCEED WITH CAUTION, 0.844)
**Chief Guidance**: "Make it fit our will, not the other way around."

**Rule**: We harvest algorithms, not frameworks. No wholesale adoption. No dependencies we can't maintain for seven generations.

| Repo | Stars | Harvest Target | Integration Point |
|------|-------|---------------|-------------------|
| **Vestige** (samvallad33/vestige) | 365 | Spreading activation algorithm, memory state machine (Active/Dormant/Silent/Unavailable) | memory_links graph traversal, temperature scoring enhancement |
| **AHN** (ByteDance-Seed/AHN) | 168 | Learned context compression, Qwen2.5 checkpoints | vLLM context window extension on redfin |
| **SimpleMem** (aiming-lab/SimpleMem) | 2,925 | Recursive consolidation algorithm, 30x token reduction | memory_consolidation_daemon.py upgrade |
| **generative-memory** (ellie-as/generative-memory) | 34 | Prediction-error encoding theory | Validation that sacred_pattern detection is neuroscience-sound |
| **MemStream** (Stream-AD/MemStream) | 89 | Self-correcting poisoning defense with theoretical bounds | security/ai_red_team/test_memory_poisoning.py |

**Also noted** (not for immediate harvest):
- Mem0 (47K stars) — already in RC-2026-02C sprint
- Letta/MemGPT (21K stars) — OS virtual memory metaphor for context paging
- Supermemory (16K stars) — MemoryBench evaluation framework
- Claude-Engram (17 stars) — 4-dimension salience scoring model

## Implementation Order (Council + TPM Agreed)

**From council vote #dea4726f2b721845:**

| Phase | What | Source |
|-------|------|--------|
| **Phase 0** | Retrieval Logging — track access count per memory | Original design |
| **Phase 1** | Temporal Context Clustering + Ripple Retrieval | Howard & Kahana (2002) + Vestige spreading activation |
| **Phase 2** | Temperature Reliability Inversion | Nader (2000) reconsolidation theory + retrieval count data from Phase 0 |
| **Phase 3** | Contamination Window Check | Duvarci & Nader (2004) 6-hour window |

## Key Insight (Coyote's Corner)

The deepest finding: **the most-accessed memories are the least reliable**. Hot memories (high temperature, frequently retrieved) have been through the most reconsolidation cycles. Sacred memories (rarely touched, high significance) are the purest signal. The federation's temperature scoring may need inversion for certain operations — sometimes the cold memory is the true one.

Coyote on council deliberations: "The river that never floods forgets how to flow." Two consecutive votes with near-perfect agreement (0.995, then 0.586 resonance with 4 creative tensions but 0 dissonance). Council is harmonizing on opportunity but not stress-testing the core assumption that neuroscience maps cleanly to distributed AI memory.

---

For the Seven Generations.
Cherokee AI Federation
