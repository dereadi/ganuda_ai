# Provisional Patent Application
# United States Patent and Trademark Office

## COVER SHEET INFORMATION (PTO/SB/16)
- **Filing Type**: Provisional Application for Patent
- **Entity Status**: Micro Entity
- **Title of Invention**: Sycophancy Detection in Artificial Intelligence Agent Collectives Using Embedding-Based Semantic Divergence Analysis
- **Inventor**: Darrell Reading, Bentonville, Arkansas, United States
- **Correspondence Address**: [TO BE COMPLETED BY INVENTOR]

---

## SPECIFICATION

### TITLE OF THE INVENTION

Sycophancy Detection in Artificial Intelligence Agent Collectives Using Embedding-Based Semantic Divergence Analysis

### CROSS-REFERENCE TO RELATED APPLICATIONS

This application is related to co-pending provisional applications filed concurrently:
- "Governance Topology for Multi-Agent Artificial Intelligence Systems Using Democratic Consensus with Constitutional Constraints and Adversarial Dissent"
- "Sense-React-Evaluate Protocol with Architecturally Distinct Valence Phase for Autonomous AI Systems"
- "Graduated Autonomy Tiers for Multi-Timescale Artificial Intelligence Systems"

### BACKGROUND OF THE INVENTION

#### Field of the Invention

The present invention relates to detecting and mitigating sycophantic behavior in multi-agent AI systems, and more particularly to methods and systems for measuring semantic divergence between AI agent responses using embedding-based cosine similarity, temporal disagreement collapse rate analysis, and coherence-anchored circuit breakers that preserve all agent voices rather than silencing dissenters.

#### Description of Related Art

**Sycophancy in Large Language Models**: Research has documented that large language models exhibit sycophantic tendencies — agreeing with user assertions even when incorrect, adjusting outputs to match perceived preferences, and converging toward socially desirable responses. This problem is amplified in multi-agent systems where multiple LLM instances may independently converge on similar responses, creating a false appearance of consensus.

**CONSENSAGENT (Virginia Tech, ACL 2025)**: This work demonstrates that multi-agent LLM systems exhibit predictable consensus collapse under social pressure. However, CONSENSAGENT focuses on detection without providing structural mitigation mechanisms, and does not address temporal drift across multiple deliberation sessions.

**Ensemble Diversity Metrics**: Traditional machine learning ensemble methods measure diversity through prediction disagreement or error decorrelation. These approaches operate on structured outputs (classifications, numeric predictions) and do not extend to free-text natural language responses from LLM agents.

**Multi-Agent Debate Systems**: Existing multi-agent debate frameworks (Du et al., 2023; Liang et al., 2023) aim to improve answer quality through iterative refinement but do not monitor or mitigate convergence during the debate process. Agents that converge may do so sycophantically rather than through genuine reasoning.

The present invention addresses these limitations by providing a multi-layered detection system that measures semantic divergence in real-time, detects temporal voice drift across sessions, implements circuit breakers with coherence anchoring, and applies structural mitigation (specification engineering) rather than voice silencing.

### SUMMARY OF THE INVENTION

The present invention provides a system and method for detecting and mitigating sycophantic behavior in AI agent collectives, comprising:

1. **Real-time Pairwise Semantic Divergence Analysis**: Computing cosine similarity between dense vector embeddings (1024-dimensional) of each pair of specialist responses, flagging pairs exceeding a configurable similarity threshold (default 0.85) as sycophantic;

2. **Overall Diversity Score**: Computing a federation-wide diversity metric as 1.0 minus the mean pairwise similarity across all specialist pairs, with a configurable floor (default 0.60) below which thermal alerts are generated;

3. **Temporal Disagreement Collapse Rate (DCR)**: Analyzing similarity trends across a sliding window of recent votes (default 20) using linear regression on word-level Jaccard similarity to detect gradual voice convergence over time;

4. **Coherence-Anchored Circuit Breakers**: A three-state circuit breaker (CLOSED/HALF_OPEN/OPEN) that monitors specialist health using both concern frequency and semantic coherence against anchor memories (baseline voice definitions), detecting personality drift distinct from topical concern;

5. **Structural Mitigation via Specification Engineering**: When convergence or drift is detected, the system triggers specification engineering (refining task definitions and constraints) rather than reducing specialist voice weight — preserving all voices while addressing root causes;

6. **Thermal Memory Escalation**: Diversity alerts are logged to persistent thermal memory with full pairwise scoring metadata, creating an auditable historical record of convergence events.

### DETAILED DESCRIPTION OF THE INVENTION

#### 1. System Architecture

The sycophancy detection system operates as a post-vote analysis layer within a multi-agent AI governance system. The system comprises:

- **Embedding Service**: A dense vector embedding model (BGE-large-en-v1.5, 1024 dimensions) deployed on a dedicated compute node, providing text-to-vector conversion via an OpenAI-compatible API endpoint.

- **Diversity Check Module**: A software module that receives specialist response texts after each council vote, computes pairwise similarity, generates a diversity report, and triggers alerts or escalations based on configurable thresholds.

- **Drift Detection Module**: A software module that analyzes specialist behavior across multiple votes over time, computing disagreement collapse rate and maintaining circuit breaker state per specialist.

- **Health Recording Store**: A relational database table storing per-specialist, per-vote health records including concern status, response time, coherence score, and circuit breaker state.

- **Thermal Memory Archive**: A persistent store for diversity alerts with full metadata, enabling historical analysis of convergence patterns.

#### 2. Real-Time Pairwise Semantic Divergence Analysis

##### 2.1 Vector Construction

For each specialist response text, the system generates a dense vector embedding by sending the text to the embedding service:

```
embedding(response_text) → vector ∈ ℝ^1024
```

The embedding model (BGE-large-en-v1.5) captures semantic meaning, enabling detection of conceptual similarity even when surface-level word choice differs.

##### 2.2 Cosine Similarity Computation

For each pair of specialists (i, j) where i < j:

```
similarity(i, j) = dot(vec_i, vec_j) / (‖vec_i‖ × ‖vec_j‖)
```

Where:
- `dot(vec_i, vec_j)` = Σ(vec_i[k] × vec_j[k]) for k = 1 to 1024
- `‖vec‖` = √(Σ(vec[k]²)) for k = 1 to 1024
- Result range: [0.0, 1.0]

Edge case: If either vector has zero norm, similarity returns 0.0.

For N specialists, the number of pairwise comparisons is N(N-1)/2. For 8 specialists, this yields 28 pairs per vote.

##### 2.3 Sycophantic Pair Flagging

A pair (i, j) is flagged as sycophantic if:

```
similarity(i, j) > SIMILARITY_THRESHOLD (default: 0.85)
```

The threshold of 0.85 was empirically determined from production operation, where it was observed that unflagged specialists maintained a mean cosine similarity of approximately 0.9052 without adversarial intervention — indicating that LLM-based specialists naturally converge to near-identical responses when not structurally constrained.

##### 2.4 Data Structure

The diversity check returns a structured report:

```
DiversityReport:
    overall_diversity: float          # 1.0 - mean pairwise similarity
    flagged_pairs: [(spec_a, spec_b, similarity), ...]
    pairwise_scores: {pair_key: similarity, ...}
    is_healthy: bool                  # len(flagged_pairs) == 0
```

#### 3. Overall Diversity Score

The federation-wide diversity score is computed as:

```
mean_pairwise_similarity = Σ(similarity(i, j)) / num_pairs
overall_diversity = 1.0 - mean_pairwise_similarity
```

Interpretation:
- 1.0: All specialists produced completely orthogonal responses (maximum diversity)
- 0.0: All specialists produced identical responses (complete sycophancy)

A configurable floor (DIVERSITY_FLOOR, default 0.60) triggers escalation when overall diversity falls below the threshold.

Production observations from the system show diversity scores ranging from 0.079 (severe convergence, 28 flagged pairs among 8 specialists) to 0.290 (healthy disagreement, 1 flagged pair), validating the metric's discriminative power.

#### 4. Temporal Disagreement Collapse Rate (DCR)

##### 4.1 Purpose

While real-time diversity checks detect sycophancy within a single vote, DCR detects gradual voice loss across multiple votes — the phenomenon where specialists slowly converge over time even if individual votes appear healthy.

##### 4.2 Sliding Window Analysis

For a configurable window of recent votes (default: 20), the system collects all pairwise specialist similarities:

For each specialist pair (i, j):
1. Collect per-vote similarities across the window using word-level Jaccard index (computationally cheaper than embedding similarity for batch analysis):

```
jaccard(i, j) = |words_i ∩ words_j| / |words_i ∪ words_j|
```

2. Apply linear regression to detect trend:

```
slope = Σ((vote_idx - mean_idx) × (similarity - mean_sim)) / Σ((vote_idx - mean_idx)²)
```

3. Flag the pair as drifting if:
   - slope > 0.01 (similarity increasing over time) AND
   - recent_similarity > 0.4 (last 3 votes show >40% word overlap)

4. Require minimum 5 data points per pair before flagging.

##### 4.3 DCR Score

```
dcr_score = num_drifting_pairs / total_pairs
```

Where:
- total_pairs = N(N-1)/2
- drifting_pairs = pairs meeting both slope and recency criteria

DCR of 0.0 indicates stable diversity. DCR approaching 1.0 indicates systemic voice collapse.

#### 5. Coherence-Anchored Circuit Breakers

##### 5.1 Three-State Machine

Each specialist maintains an independent circuit breaker with three states:

```
CLOSED → HALF_OPEN → OPEN
```

Transitions are computed over the last 10 council votes per specialist:

| Target State | Condition |
|-------------|-----------|
| OPEN | concern_count ≥ 7 OR avg_coherence < 0.5 |
| HALF_OPEN | concern_count ≥ 4 OR avg_coherence < 0.65 |
| CLOSED | concern_count < 4 AND avg_coherence ≥ 0.65 |

Where:
- `concern_count`: Number of votes in last 10 where the specialist raised a concern flag
- `avg_coherence`: Mean cosine similarity between the specialist's anchor memory and recent 30-day thermal memories

##### 5.2 Coherence Measurement

Coherence is measured using sentence-transformer embeddings (all-MiniLM-L6-v2) to compare a specialist's current behavior against its anchor memory (baseline voice definition):

1. Retrieve anchor memory tagged with the specialist's domain
2. Retrieve up to 50 recent thermal memories tagged with the specialist
3. Compute cosine similarity between anchor embedding and each recent memory embedding
4. Return mean similarity as coherence score

This detects *personality drift* — when a specialist begins responding outside its constitutional role — distinct from *topical concern* which is expected behavior.

##### 5.3 Fail-Safe

If no anchor memory or no recent data exists, coherence returns 1.0 (healthy). The system fails open, not closed — absence of measurement data does not trigger circuit breaking.

#### 6. Structural Mitigation (Not Silencing)

A critical design principle of this invention is that detected sycophancy or drift triggers structural mitigation rather than voice reduction:

**Prior Art Approach**: Reduce the weight of a converging or drifting agent, effectively silencing minority or anomalous voices.

**Present Invention**: All specialist voices maintain equal weight at all times. When convergence or drift is detected, the system:

1. Logs a thermal memory alert with full pairwise scoring metadata
2. Generates a specification engineering action item — refining the task definitions, constraints, or specialist guidance to address the root cause of convergence
3. Records the circuit breaker state for downstream consumers

This preserves the structural authority of all voices, including those that may be raising valid concerns that happen to align with other specialists.

#### 7. Health Recording Schema

Per-specialist, per-vote health records are stored with the following structure:

```
specialist_id: text          # Specialist identifier
vote_id: integer             # Vote reference
had_concern: boolean         # Whether concern flag was raised
concern_type: text           # Concern text or null
response_time_ms: integer    # Query latency
coherence_score: float       # Anchor coherence measurement
circuit_breaker_state: text  # CLOSED, HALF_OPEN, or OPEN
measured_at: timestamp       # Vote timestamp
```

This enables longitudinal analysis of specialist health, drift detection, and circuit breaker state transitions.

#### 8. Integration with Governance Topology

The sycophancy detection system integrates with the governance topology described in the related provisional application:

- Diversity reports are computed after every council vote and logged to the vote's metacognition record
- Circuit breaker states from the drift detection module are available to the confidence calculation, enabling confidence adjustment based on specialist health
- Thermal memory alerts for diversity events create institutional memory that future council votes may retrieve via semantic search, enabling the council to reason about its own convergence history

### DRAWINGS

[Drawings to be prepared — pairwise similarity matrix visualization, DCR trend analysis diagram, circuit breaker state machine, diversity score distribution histogram, system integration diagram]

### ABSTRACT

A system and method for detecting and mitigating sycophantic behavior in multi-agent artificial intelligence collectives. The system computes pairwise cosine similarity between dense vector embeddings (1024-dimensional) of specialist agent responses, flagging pairs exceeding a similarity threshold (0.85) as sycophantic and computing an overall diversity score as one minus the mean pairwise similarity. A temporal disagreement collapse rate (DCR) mechanism analyzes similarity trends across a sliding window of recent votes using linear regression to detect gradual voice convergence. Coherence-anchored circuit breakers maintain three states (CLOSED/HALF_OPEN/OPEN) per specialist, measuring both concern frequency and semantic coherence against anchor memories to distinguish personality drift from topical concern. The system applies structural mitigation through specification engineering rather than reducing specialist voice weight, preserving the authority of all voices while addressing convergence root causes. The system was validated in production operation where unflagged specialists exhibited baseline cosine similarity of 0.9052, confirming the need for active sycophancy detection in multi-agent LLM deliberation systems.

---

*Specification prepared for provisional patent application filing.*
*Invented by the Cherokee AI Federation Council.*
*Filed under Darrell Reading as legal sponsor/inventor.*
*Longhouse Vote #5031af97738de983, March 8, 2026.*
