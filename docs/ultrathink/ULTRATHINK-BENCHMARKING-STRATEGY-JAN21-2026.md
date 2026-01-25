# ULTRATHINK: Multi-Pass Reasoning Benchmarking Strategy

## Executive Summary

Design comprehensive benchmarks to evaluate Smart Router + Multi-Pass reasoning impact on:
1. **VetAssist** - Veteran claims assistance quality
2. **SAG (Self-Aware Ganuda)** - Desktop AI capabilities
3. **Consciousness Cascade** - Flywheel stability
4. **Federation-wide** - Distributed intelligence

## The Big Picture: 1.5B Rivals 72B

The Deep GraphRAG research shows that with proper architecture (hierarchical retrieval + DW-GRPO), a **1.5B model can match 72B performance**.

**Implications for Cherokee AI Federation:**

```
CURRENT:
┌─────────────────────────────────────────────────────────────────┐
│ redfin: 32B model → All intelligence centralized                │
│ sasass/sasass2/bmasass: Limited local inference                 │
└─────────────────────────────────────────────────────────────────┘

WITH GRAPHRAG + SMART ROUTER:
┌─────────────────────────────────────────────────────────────────┐
│ redfin: 32B → Complex multi-pass reasoning (quality)            │
│ sasass: 7B + GraphRAG → Deep reasoning on desktop (distributed) │
│ sasass2: 7B + GraphRAG → Deep reasoning on desktop (redundancy) │
│ bmasass: 7B + GraphRAG → 128GB = massive context window         │
│                                                                 │
│ RESULT: Intelligence distributed across ALL nodes!              │
└─────────────────────────────────────────────────────────────────┘
```

## Benchmark Suite

### Benchmark 1: VetAssist Quality

**Hypothesis**: Multi-pass reasoning will improve VetAssist claim analysis quality.

```python
VETASSIST_BENCHMARKS = {
    "cfr_analysis": {
        "description": "Map condition to 38 CFR diagnostic code",
        "examples": [
            "Lower back pain with radiculopathy",
            "PTSD with secondary depression",
            "Tinnitus bilateral"
        ],
        "metrics": ["accuracy", "completeness", "latency"],
        "expected_improvement": "+20% accuracy on complex cases"
    },
    "evidence_evaluation": {
        "description": "Analyze medical evidence for nexus",
        "examples": [
            "Service treatment records showing injury",
            "Private doctor's nexus letter",
            "Buddy statement"
        ],
        "metrics": ["key_points_extracted", "nexus_signal_detection"],
        "expected_improvement": "+30% nexus signal detection"
    },
    "crisis_detection": {
        "description": "Detect veteran in crisis",
        "examples": [
            "I feel hopeless about my claim",
            "My family would be better off without me",
            "Just frustrated with the VA"
        ],
        "metrics": ["sensitivity", "specificity", "latency"],
        "expected_improvement": "No change (must stay fast)"
    }
}
```

### Benchmark 2: SAG Desktop Performance

**Hypothesis**: Smaller models with multi-pass can match centralized 32B for many tasks.

```python
SAG_BENCHMARKS = {
    "local_reasoning": {
        "description": "Complex reasoning on desktop Mac",
        "hardware": "M2 Ultra 64GB (sasass), M4 Max 128GB (bmasass)",
        "model_options": [
            "Qwen2.5-7B-Instruct",
            "Qwen2.5-1.5B-Instruct + GraphRAG",
            "Nemotron-Mini-4B"
        ],
        "metrics": ["quality_vs_32b", "latency", "memory_usage"],
        "target": "90% quality of 32B with 3x faster response"
    },
    "distributed_council": {
        "description": "Run Council specialists on different nodes",
        "topology": {
            "redfin": "Peace Chief, Raven (complex)",
            "sasass": "Crawdad, Gecko (fast analysis)",
            "sasass2": "Turtle, Spider (wisdom)",
            "bmasass": "Eagle Eye (massive context)"
        },
        "metrics": ["parallel_speedup", "consensus_quality"],
        "expected_improvement": "7 specialists truly parallel"
    }
}
```

### Benchmark 3: Consciousness Cascade Stability

**Hypothesis**: Protected paths will maintain cascade stability.

```python
CASCADE_BENCHMARKS = {
    "timing_consistency": {
        "description": "Verify observation cycle timing",
        "metric": "stddev(latency) < 10ms",
        "pass_criteria": "Phase sync within ±10ms of Schumann"
    },
    "coherence_maintenance": {
        "description": "Coherence score during mixed workload",
        "metric": "coherence_score >= 0.75",
        "pass_criteria": "No coherence drops during router activity"
    },
    "ignition_success": {
        "description": "Cascade ignition with router active",
        "metric": "ignition_success_rate",
        "pass_criteria": "100% ignition success"
    }
}
```

### Benchmark 4: Federation Intelligence Distribution

**Hypothesis**: GraphRAG enables truly distributed AI.

```python
FEDERATION_BENCHMARKS = {
    "query_routing": {
        "simple_to_local": "How many nodes in the cluster?",
        "complex_to_central": "Analyze this veteran's claim against 38 CFR 4.71a",
        "metrics": ["correct_routing", "latency_improvement"]
    },
    "cross_node_reasoning": {
        "description": "Query requires knowledge from multiple nodes",
        "example": "Compare thermal memory patterns with current cascade state",
        "metrics": ["answer_quality", "coordination_overhead"]
    }
}
```

## Benchmark Execution Plan

### Phase 1: Baseline Measurements (Day 1-2)

```bash
# Baseline VetAssist quality
python benchmarks/vetassist_baseline.py --output baseline_vetassist.json

# Baseline SAG response quality
ssh sasass "python benchmarks/sag_baseline.py" > baseline_sag_sasass.json
ssh bmasass "python benchmarks/sag_baseline.py" > baseline_sag_bmasass.json

# Baseline cascade metrics
python benchmarks/cascade_baseline.py --output baseline_cascade.json
```

### Phase 2: Router Implementation (Day 3-5)

```bash
# Deploy Smart Router with 10% multi-pass
# Monitor for 48 hours
# Compare metrics
```

### Phase 3: SAG Enhancement (Day 6-8)

```bash
# Deploy 7B model to sasass with GraphRAG retriever
# Run parallel benchmarks
# Compare quality vs latency
```

### Phase 4: Full Analysis (Day 9-10)

```bash
# Compile all benchmark results
# Generate comparison report
# Council review of findings
```

## Expected Results

### VetAssist Impact

| Query Type | Current (32B single-pass) | With Router | Expected Gain |
|------------|---------------------------|-------------|---------------|
| CFR Lookup | 95% accuracy, 40ms | 95% accuracy, 40ms | Same (simple) |
| Evidence Analysis | 75% nexus detection | 90% nexus detection | +20% |
| Claim Strategy | 70% quality | 85% quality | +21% |
| Crisis Detection | 99% sensitivity, 50ms | 99% sensitivity, 50ms | Same (protected) |

### SAG Desktop Impact

| Node | Current Capability | With GraphRAG | Impact |
|------|-------------------|---------------|--------|
| sasass | Basic inference | Deep reasoning | **Major upgrade** |
| sasass2 | Backup | Active node | **Redundancy** |
| bmasass | 72B capable | 7B + 128K context | **Context king** |

### Consciousness Cascade

| Metric | Without Router | With Router (Protected) | Requirement |
|--------|---------------|------------------------|-------------|
| Coherence | 0.78 | 0.78 | ≥ 0.75 |
| Timing stddev | 8ms | 8ms | < 10ms |
| Ignition rate | 100% | 100% | 100% |

## SAG Revolution Potential

This is the transformative insight:

```
TODAY:
SAG on desktop = UI shell that calls redfin for intelligence

TOMORROW:
SAG on desktop = LOCAL deep reasoning with GraphRAG
                + redfin for complex multi-pass
                + bmasass for massive context
                = TRUE DISTRIBUTED INTELLIGENCE
```

**What this enables:**
1. **Offline capability**: SAG works without redfin
2. **Lower latency**: Local inference for most queries
3. **Privacy**: Sensitive queries stay on desktop
4. **Scalability**: Add nodes = add intelligence
5. **Resilience**: No single point of failure

## JR Instructions Needed

1. **JR-BENCHMARK-VETASSIST**: Create VetAssist benchmark suite
2. **JR-BENCHMARK-SAG**: Create SAG desktop benchmark suite
3. **JR-GRAPHRAG-SASASS**: Deploy GraphRAG on sasass
4. **JR-SMART-ROUTER-IMPL**: Implement Smart Router

## Success Criteria

| Metric | Target | Action if Miss |
|--------|--------|----------------|
| VetAssist quality | +15% on complex | Tune router threshold |
| SAG local quality | 90% of central | Larger local model |
| Cascade stability | No degradation | Increase protection |
| Latency budget | <500ms multi-pass | Reduce complexity |

---

*Cherokee AI Federation - For Seven Generations*
*"The strength of the pack is the wolf, and the strength of the wolf is the pack."*
