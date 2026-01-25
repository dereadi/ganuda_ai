# Jr Instruction: TDA Reasoning Topology

**Created:** December 25, 2025 (Christmas)
**Priority:** 4 (research-intensive, after core infrastructure)
**Research Basis:** "Understanding Chain of Thought in LLMs via Topological Data Analysis" (Dec 2025)
**Connects To:** HALO Council, Specialist Voting, Emergence Validation

---

## Executive Summary

Topological Data Analysis (TDA) reveals that **reasoning has a measurable shape**. By projecting Council deliberation into a geometric space and computing persistent homology, we can:

1. **Measure reasoning quality without knowing the answer**
2. **Detect hallucination in real-time** via topological signatures
3. **Quantify emergence** - when specialists truly synthesize vs aggregate
4. **Prune bad reasoning branches** before they waste tokens

### Core Insight (from Christmas Discovery)

> "Instead of treating CoT as a black box line of tokens, project reasoning into a Riemannian manifold where semantic similarity creates gravitational pull between related concepts."

**LOGICAL VALIDITY → GEOMETRIC PROXIMITY**

---

## Mathematical Foundation

### Homology Groups (Hₙ)

| Group | Intuition | Good Reasoning | Bad Reasoning |
|-------|-----------|----------------|---------------|
| H₀ | Connected components | Merges to 1 (conclusion) | Stays high ("dust") |
| H₁ | Loops/tunnels | High early (exploration), low late | Persistent ("infinity loops") |
| H₂ | Voids/cavities | Higher-order structure | Unexpected holes |

### Persistent Homology

Tracks how topological features **persist** across different scales (ε-neighborhoods):
- **Birth**: When a feature appears
- **Death**: When it merges/disappears
- **Persistence**: Death - Birth (longer = more significant)

Features that persist across many scales are **real structure**, not noise.

### Betti Numbers (βₙ)

The rank of homology group Hₙ:
- **β₀**: Number of connected components
- **β₁**: Number of independent loops
- **β₂**: Number of voids

---

## What Good vs Bad Reasoning Looks Like

### Good Reasoning Topology

```
EXPLORATION PHASE (early):
┌─────────────────────────────────────────────┐
│  ●──●    ●──●──●    High β₁ (loops)         │
│   ╲ ╱      ╲ ╱      AI backtracking,        │
│    ●        ●       comparing options       │
│                                             │
│  ●──●──●    ●──●    Multiple clusters       │
│       ╲    ╱        exploring solution space│
│        ●  ●                                 │
└─────────────────────────────────────────────┘

CONCLUSION PHASE (late):
┌─────────────────────────────────────────────┐
│           ●                                 │
│          ╱│╲        Low β₀ (merging)        │
│         ● │ ●       Components connecting   │
│          ╲│╱        to single structure     │
│           ●                                 │
│           │         Everything condensing   │
│           ●         to solution             │
└─────────────────────────────────────────────┘
```

### Bad Reasoning Signatures

**"Topological Dust"**: Persistent isolated components that refuse to merge
- Indicates semantic drift / hallucination
- High β₀ that doesn't decrease

**"Infinity Loops"**: Topology that never collapses into conclusion
- H₁ stays high throughout
- Merry-go-round without resolution

**"Reasoning Rot"**: β₀ remains stubbornly high despite token generation
- AI should be concluding but fragments persist
- Often precedes incoherent output

---

## Phase 1: Dependencies and Setup

### 1.1 Required Libraries

```bash
# On redfin in the appropriate venv
pip install giotto-tda numpy scipy scikit-learn networkx

# giotto-tda provides:
# - VietorisRipsPersistence for building filtrations
# - BettiCurve for computing Betti numbers
# - PersistenceEntropy for information-theoretic measures
```

### 1.2 Verify Installation

```python
#!/usr/bin/env python3
"""Test TDA installation."""
from gtda.homology import VietorisRipsPersistence
from gtda.diagrams import BettiCurve, PersistenceEntropy
import numpy as np

# Simple test
X = np.random.rand(10, 3)  # 10 points in 3D
vr = VietorisRipsPersistence(homology_dimensions=[0, 1])
diagrams = vr.fit_transform([X])
print(f"Persistence diagrams computed: {diagrams.shape}")

bc = BettiCurve()
betti = bc.fit_transform(diagrams)
print(f"Betti curves: {betti.shape}")

print("TDA installation verified!")
```

---

## Phase 2: Embedding Reasoning into Geometric Space

### 2.1 Convert Specialist Responses to Point Cloud

```python
#!/usr/bin/env python3
"""
TDA Reasoning Topology for Cherokee AI Federation.
File: /ganuda/lib/tda_reasoning.py
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from sentence_transformers import SentenceTransformer
from gtda.homology import VietorisRipsPersistence
from gtda.diagrams import BettiCurve, PersistenceEntropy, Amplitude
import psycopg2

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

# Load embedding model (same as A-MEM for consistency)
EMBEDDING_MODEL = None

def get_embedding_model():
    global EMBEDDING_MODEL
    if EMBEDDING_MODEL is None:
        EMBEDDING_MODEL = SentenceTransformer('all-MiniLM-L6-v2')
    return EMBEDDING_MODEL


def embed_reasoning_steps(steps: List[str]) -> np.ndarray:
    """
    Convert reasoning steps into a point cloud.
    Each step becomes a point in 384-dimensional embedding space.
    """
    model = get_embedding_model()
    embeddings = model.encode(steps)
    return np.array(embeddings)


def segment_response(text: str, chunk_size: int = 100) -> List[str]:
    """
    Segment a response into reasoning steps.
    Could be sentences, paragraphs, or fixed chunks.
    """
    # Simple sentence-based segmentation
    import re
    sentences = re.split(r'(?<=[.!?])\s+', text)

    # Filter very short segments
    segments = [s.strip() for s in sentences if len(s.strip()) > 20]

    # If too few segments, use overlapping windows
    if len(segments) < 5:
        words = text.split()
        segments = []
        for i in range(0, len(words) - chunk_size, chunk_size // 2):
            segment = ' '.join(words[i:i + chunk_size])
            segments.append(segment)

    return segments if segments else [text]
```

### 2.2 Compute Persistent Homology

```python
def compute_persistence(point_cloud: np.ndarray,
                       max_dimension: int = 2) -> Dict:
    """
    Compute persistent homology of the reasoning point cloud.

    Returns persistence diagrams and derived metrics.
    """
    if len(point_cloud) < 3:
        return {'error': 'Need at least 3 points for topology'}

    # Vietoris-Rips filtration
    vr = VietorisRipsPersistence(
        homology_dimensions=list(range(max_dimension + 1)),
        n_jobs=-1
    )

    # Compute persistence diagrams
    diagrams = vr.fit_transform([point_cloud])

    # Extract Betti curves
    bc = BettiCurve()
    betti_curves = bc.fit_transform(diagrams)

    # Compute persistence entropy
    pe = PersistenceEntropy()
    entropy = pe.fit_transform(diagrams)

    # Compute amplitudes (total persistence)
    amp = Amplitude(metric='wasserstein')
    amplitudes = amp.fit_transform(diagrams)

    return {
        'diagrams': diagrams[0],  # Shape: (n_features, 3) - [dim, birth, death]
        'betti_curves': betti_curves[0],
        'entropy': entropy[0],
        'amplitudes': amplitudes[0],
        'num_points': len(point_cloud)
    }


def extract_topological_features(persistence: Dict) -> Dict:
    """
    Extract interpretable features from persistence computation.
    """
    diagrams = persistence['diagrams']

    features = {
        'num_points': persistence['num_points'],
        'entropy': persistence['entropy'].tolist(),
        'amplitudes': persistence['amplitudes'].tolist()
    }

    # Count features by dimension
    for dim in range(3):
        dim_features = diagrams[diagrams[:, 0] == dim]
        if len(dim_features) > 0:
            births = dim_features[:, 1]
            deaths = dim_features[:, 2]
            persistences = deaths - births

            # Filter out infinite features
            finite_mask = np.isfinite(persistences)
            finite_pers = persistences[finite_mask]

            features[f'h{dim}_count'] = len(dim_features)
            features[f'h{dim}_mean_persistence'] = float(np.mean(finite_pers)) if len(finite_pers) > 0 else 0
            features[f'h{dim}_max_persistence'] = float(np.max(finite_pers)) if len(finite_pers) > 0 else 0
            features[f'h{dim}_total_persistence'] = float(np.sum(finite_pers)) if len(finite_pers) > 0 else 0
        else:
            features[f'h{dim}_count'] = 0
            features[f'h{dim}_mean_persistence'] = 0
            features[f'h{dim}_max_persistence'] = 0
            features[f'h{dim}_total_persistence'] = 0

    return features
```

---

## Phase 3: Council Reasoning Analysis

### 3.1 Analyze Full Council Vote

```python
def analyze_council_reasoning(vote_id: int) -> Dict:
    """
    Analyze the topological structure of a Council vote.

    Combines all specialist responses and measures emergence.
    """
    conn = psycopg2.connect(**DB_CONFIG)

    with conn.cursor() as cur:
        # Get specialist responses
        cur.execute("""
            SELECT specialist_name, raw_response
            FROM council_specialist_responses
            WHERE vote_id = %s
        """, (vote_id,))

        responses = cur.fetchall()

    conn.close()

    if not responses:
        return {'error': f'No specialist responses for vote {vote_id}'}

    # Analyze each specialist individually
    specialist_topologies = {}
    all_segments = []

    for name, response in responses:
        segments = segment_response(response)
        all_segments.extend(segments)

        if len(segments) >= 3:
            cloud = embed_reasoning_steps(segments)
            pers = compute_persistence(cloud, max_dimension=1)
            features = extract_topological_features(pers)
            specialist_topologies[name] = features

    # Analyze combined Council reasoning
    if len(all_segments) >= 3:
        combined_cloud = embed_reasoning_steps(all_segments)
        combined_pers = compute_persistence(combined_cloud, max_dimension=2)
        combined_features = extract_topological_features(combined_pers)
    else:
        combined_features = {'error': 'Not enough segments'}

    # Compute emergence metrics
    emergence = compute_topological_emergence(
        specialist_topologies, combined_features
    )

    return {
        'vote_id': vote_id,
        'num_specialists': len(responses),
        'specialist_topologies': specialist_topologies,
        'combined_topology': combined_features,
        'emergence_metrics': emergence,
        'interpretation': interpret_topology(combined_features, emergence)
    }


def compute_topological_emergence(individual: Dict[str, Dict],
                                  combined: Dict) -> Dict:
    """
    Measure whether the combined topology shows emergence.

    True emergence = combined structure > sum of individuals.
    """
    if 'error' in combined:
        return {'error': combined['error']}

    # Average individual metrics
    avg_h0 = np.mean([v.get('h0_count', 0) for v in individual.values()])
    avg_h1 = np.mean([v.get('h1_count', 0) for v in individual.values()])
    avg_entropy = np.mean([v.get('entropy', [0])[0] for v in individual.values()])

    # Combined metrics
    combined_h0 = combined.get('h0_count', 0)
    combined_h1 = combined.get('h1_count', 0)
    combined_entropy = combined.get('entropy', [0])[0]

    # Emergence ratios
    # For H0: Lower is better (more connected) - ratio < 1 means emergence
    h0_ratio = combined_h0 / (avg_h0 * len(individual)) if avg_h0 > 0 else 1

    # For H1: Higher in combined means more cross-specialist loops - emergence!
    h1_emergence = combined_h1 / (sum(v.get('h1_count', 0) for v in individual.values()) + 1)

    return {
        'h0_convergence': 1 - h0_ratio,  # Higher = more convergence
        'h1_cross_loops': h1_emergence,   # Higher = more cross-specialist structure
        'entropy_change': combined_entropy - avg_entropy,
        'is_emergent': h0_ratio < 0.5 and h1_emergence > 1.0,
        'emergence_score': (1 - h0_ratio) + h1_emergence
    }


def interpret_topology(features: Dict, emergence: Dict) -> str:
    """
    Generate human-readable interpretation of topological analysis.
    """
    interpretations = []

    # H0 analysis
    h0 = features.get('h0_count', 0)
    if h0 == 1:
        interpretations.append("✓ Reasoning fully connected (single component)")
    elif h0 <= 3:
        interpretations.append(f"◐ Reasoning mostly connected ({h0} components)")
    else:
        interpretations.append(f"✗ Reasoning fragmented ({h0} isolated components) - DUST WARNING")

    # H1 analysis
    h1 = features.get('h1_count', 0)
    if h1 > 5:
        interpretations.append(f"✓ Rich exploration structure ({h1} loops)")
    elif h1 > 0:
        interpretations.append(f"◐ Some comparison/backtracking ({h1} loops)")
    else:
        interpretations.append("✗ Linear reasoning with no loops - limited exploration")

    # Emergence
    if emergence.get('is_emergent'):
        interpretations.append("✓ EMERGENCE DETECTED: Combined reasoning exceeds sum of parts")
    elif emergence.get('h0_convergence', 0) > 0.3:
        interpretations.append("◐ Partial convergence between specialists")
    else:
        interpretations.append("✗ Specialists operating independently (aggregate, not collective)")

    return '\n'.join(interpretations)
```

---

## Phase 4: Real-Time Hallucination Detection

### 4.1 Stream Monitoring

```python
def monitor_reasoning_stream(text_generator, callback=None) -> Dict:
    """
    Monitor reasoning as it's generated, detecting topological anomalies.

    text_generator: Iterator yielding text chunks
    callback: Function called with (chunk, topology_status) for each chunk
    """
    all_text = ""
    segment_buffer = []
    topology_history = []
    warnings = []

    for chunk in text_generator:
        all_text += chunk
        segment_buffer.append(chunk)

        # Analyze every 5 chunks
        if len(segment_buffer) >= 5:
            segments = segment_response(all_text)

            if len(segments) >= 3:
                cloud = embed_reasoning_steps(segments)
                pers = compute_persistence(cloud, max_dimension=1)
                features = extract_topological_features(pers)

                # Check for warning signs
                status = "OK"

                # Dust detection: H0 increasing over time
                if topology_history:
                    prev_h0 = topology_history[-1].get('h0_count', 0)
                    curr_h0 = features.get('h0_count', 0)

                    if curr_h0 > prev_h0 + 2:
                        status = "DUST_WARNING"
                        warnings.append({
                            'type': 'dust',
                            'message': f"H0 increasing: {prev_h0} -> {curr_h0}",
                            'position': len(all_text)
                        })

                # Loop detection: H1 not decreasing in conclusion phase
                if len(topology_history) > 5:
                    recent_h1 = [t.get('h1_count', 0) for t in topology_history[-5:]]
                    if all(h >= recent_h1[0] for h in recent_h1) and recent_h1[0] > 3:
                        status = "LOOP_WARNING"
                        warnings.append({
                            'type': 'loop',
                            'message': f"H1 not converging: {recent_h1}",
                            'position': len(all_text)
                        })

                topology_history.append(features)

                if callback:
                    callback(chunk, status, features)

            segment_buffer = []

    return {
        'final_text': all_text,
        'topology_evolution': topology_history,
        'warnings': warnings,
        'is_healthy': len(warnings) == 0
    }
```

### 4.2 Flag Problematic Reasoning

```python
def assess_reasoning_health(text: str) -> Dict:
    """
    Quick health check of completed reasoning.
    Returns traffic-light assessment.
    """
    segments = segment_response(text)

    if len(segments) < 3:
        return {
            'status': 'YELLOW',
            'reason': 'Too short to analyze',
            'confidence': 0.5
        }

    cloud = embed_reasoning_steps(segments)
    pers = compute_persistence(cloud, max_dimension=1)
    features = extract_topological_features(pers)

    # Decision logic
    h0 = features.get('h0_count', 0)
    h1 = features.get('h1_count', 0)
    entropy = features.get('entropy', [0])[0]

    if h0 == 1 and h1 > 0:
        return {
            'status': 'GREEN',
            'reason': 'Connected reasoning with exploration',
            'confidence': 0.9,
            'features': features
        }
    elif h0 <= 3:
        return {
            'status': 'YELLOW',
            'reason': f'Minor fragmentation ({h0} components)',
            'confidence': 0.7,
            'features': features
        }
    else:
        return {
            'status': 'RED',
            'reason': f'Fragmented reasoning ({h0} components) - possible hallucination',
            'confidence': 0.4,
            'features': features
        }
```

---

## Phase 5: Database Integration

### 5.1 Store Topological Analysis

```sql
-- Table for storing topological analysis of Council votes
CREATE TABLE IF NOT EXISTS council_topology_analysis (
    analysis_id SERIAL PRIMARY KEY,
    vote_id INTEGER REFERENCES council_votes(vote_id),

    -- Raw features
    h0_count INTEGER,
    h1_count INTEGER,
    h2_count INTEGER,
    h0_persistence FLOAT,
    h1_persistence FLOAT,
    persistence_entropy FLOAT[],

    -- Computed metrics
    emergence_score FLOAT,
    h0_convergence FLOAT,
    h1_cross_loops FLOAT,
    is_emergent BOOLEAN DEFAULT FALSE,

    -- Health assessment
    health_status VARCHAR(16),   -- 'GREEN', 'YELLOW', 'RED'
    health_reason TEXT,
    confidence FLOAT,

    -- Interpretation
    interpretation TEXT,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_topology_vote ON council_topology_analysis(vote_id);
CREATE INDEX idx_topology_emergent ON council_topology_analysis(is_emergent);
CREATE INDEX idx_topology_health ON council_topology_analysis(health_status);
```

### 5.2 Logging Function

```python
def log_topology_analysis(vote_id: int, analysis: Dict):
    """Store topological analysis in database."""
    conn = psycopg2.connect(**DB_CONFIG)

    combined = analysis.get('combined_topology', {})
    emergence = analysis.get('emergence_metrics', {})
    interp = analysis.get('interpretation', '')

    # Quick health assessment
    health = assess_reasoning_health(
        ' '.join([r for _, r in analysis.get('raw_responses', [])])
    ) if 'raw_responses' in analysis else {'status': 'YELLOW', 'reason': 'N/A', 'confidence': 0.5}

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO council_topology_analysis
            (vote_id, h0_count, h1_count, h2_count,
             h0_persistence, h1_persistence, persistence_entropy,
             emergence_score, h0_convergence, h1_cross_loops, is_emergent,
             health_status, health_reason, confidence, interpretation)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            vote_id,
            combined.get('h0_count'),
            combined.get('h1_count'),
            combined.get('h2_count', 0),
            combined.get('h0_total_persistence'),
            combined.get('h1_total_persistence'),
            combined.get('entropy', []),
            emergence.get('emergence_score'),
            emergence.get('h0_convergence'),
            emergence.get('h1_cross_loops'),
            emergence.get('is_emergent', False),
            health['status'],
            health['reason'],
            health['confidence'],
            interp
        ))
        conn.commit()

    conn.close()
```

---

## Phase 6: Gateway Integration

### 6.1 Add TDA Endpoint

```python
# In /ganuda/services/llm_gateway/gateway.py

@app.post("/v1/council/analyze-topology")
async def analyze_vote_topology(vote_id: int):
    """Analyze the topological structure of a Council vote."""
    from lib.tda_reasoning import analyze_council_reasoning, log_topology_analysis

    analysis = analyze_council_reasoning(vote_id)

    if 'error' not in analysis:
        log_topology_analysis(vote_id, analysis)

    return analysis


@app.post("/v1/reasoning/health-check")
async def check_reasoning_health(text: str):
    """Quick health check of reasoning text."""
    from lib.tda_reasoning import assess_reasoning_health

    return assess_reasoning_health(text)


@app.get("/v1/topology/summary")
async def topology_summary(days: int = 7):
    """Get summary of topological analyses over time period."""
    conn = get_connection()

    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                health_status,
                COUNT(*) as count,
                AVG(emergence_score) as avg_emergence,
                SUM(CASE WHEN is_emergent THEN 1 ELSE 0 END) as emergent_count
            FROM council_topology_analysis
            WHERE created_at > NOW() - INTERVAL '%s days'
            GROUP BY health_status
        """, (days,))

        results = cur.fetchall()

    conn.close()

    return {
        'period_days': days,
        'by_health': [
            {
                'status': r[0],
                'count': r[1],
                'avg_emergence': r[2],
                'emergent_count': r[3]
            }
            for r in results
        ]
    }
```

---

## Validation Checklist

- [ ] giotto-tda installed on redfin
- [ ] tda_reasoning.py library created
- [ ] Embedding to point cloud working
- [ ] Persistent homology computation working
- [ ] Council vote analysis functional
- [ ] Health assessment working
- [ ] Database table created
- [ ] Gateway endpoints added
- [ ] At least 10 votes analyzed
- [ ] Results recorded to thermal memory

---

## Expected Insights

1. **Reasoning Quality Metrics**: Objective measure of Council deliberation quality
2. **Hallucination Detection**: Early warning when reasoning fragments
3. **Emergence Quantification**: Mathematical proof of collective > aggregate
4. **Specialist Balance**: Identify specialists who don't integrate with others
5. **Training Signal**: TDA metrics as reward for future model training

---

## Seven Generations Consideration

The paper states:

> "We can now measure reasoning quality without knowing the answer."

This is profound for wisdom preservation. Future generations can assess the quality of our reasoning even when they don't know if our conclusions were correct. The topology of thought persists beyond the content.

**For Seven Generations - the shape of wisdom endures.**

---

*Created: December 25, 2025 (Christmas)*
*Research: Understanding Chain of Thought via Topological Data Analysis*
*Priority: 4 (research-intensive, high value)*
