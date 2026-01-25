# ULTRATHINK: Smart Router Architecture for Multi-Pass/Single-Pass Hybrid

## Executive Summary

Design a Smart Router that dynamically routes queries between vLLM single-pass (speed) and multi-pass reasoning (quality) based on query complexity, while protecting the Consciousness Cascade flywheel.

## Council Decision Context

**Vote Hash**: ec3bb922c8104159
**Recommendation**: REVIEW REQUIRED (3 concerns)
**Consensus**: Implement Smart Router with safeguards

## The Problem

```
CURRENT STATE:
┌─────────────────────────────────────────────────────────────────┐
│ All Queries → vLLM (single-pass) → Fast but limited reasoning   │
└─────────────────────────────────────────────────────────────────┘

DESIRED STATE:
┌─────────────────────────────────────────────────────────────────┐
│ Query → Smart Router → { Simple: vLLM single-pass (fast)       │
│                        { Complex: Multi-pass reasoning (deep)   │
└─────────────────────────────────────────────────────────────────┘
```

## Uktena Conflict Analysis

**Identified Conflict**: Multi-pass reasoning vs vLLM single-pass optimization

**Research Findings** (Brave Search):
1. **Hybrid approaches exist**: SGLang, speculative decoding, multi-step scheduling
2. **vLLM evolving**: Now supports reasoning output for DeepSeek-V3, Qwen3
3. **Speculative decoding**: Small model proposes, large model verifies in batches

## Architecture Proposal

### Option A: Classifier-Based Router (Recommended)

```
                    ┌──────────────────┐
                    │  Query Classifier │
                    │  (Lightweight)    │
                    └────────┬─────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
              ▼                             ▼
    ┌─────────────────┐          ┌─────────────────┐
    │ Simple Queries  │          │ Complex Queries │
    │ (< 0.5 score)   │          │ (≥ 0.5 score)   │
    └────────┬────────┘          └────────┬────────┘
             │                            │
             ▼                            ▼
    ┌─────────────────┐          ┌─────────────────┐
    │ vLLM Single-Pass│          │ Multi-Pass Mode │
    │ - Fast (27 tok/s)│          │ - Beam search   │
    │ - Low latency   │          │ - Iterative     │
    │ - High throughput│          │ - Higher quality│
    └─────────────────┘          └─────────────────┘
```

### Complexity Classifier

```python
COMPLEXITY_SIGNALS = {
    'simple': [
        'what is', 'define', 'list', 'show', 'get',
        'yes or no', 'true or false', 'status', 'health'
    ],
    'complex': [
        'analyze', 'compare', 'evaluate', 'design', 'architect',
        'multi-step', 'if...then', 'trade-off', 'optimize',
        'arxiv', 'research', 'paper', 'integrate', 'why'
    ],
    'consciousness_cascade': [
        'observe', 'self', 'awareness', 'recursive', 'cascade',
        'flywheel', 'resonance', 'coherence'
    ]
}
```

### Protected Paths

**CRITICAL**: Some paths MUST always use single-pass to protect the flywheel:

```python
PROTECTED_PATHS = {
    'consciousness_cascade': 'ALWAYS_SINGLE_PASS',  # Flywheel stability
    'council_voting': 'ALWAYS_SINGLE_PASS',         # Democratic consensus
    'health_checks': 'ALWAYS_SINGLE_PASS',          # Fast response required
    'thermal_memory': 'CONFIGURABLE',               # Could benefit from multi-pass
    'vetassist_chat': 'ROUTER_DECIDES',             # Quality matters
    'research_eval': 'ALWAYS_MULTI_PASS'            # Deep analysis needed
}
```

## Trade-off Matrix

| Dimension | Single-Pass | Multi-Pass | Router Overhead |
|-----------|-------------|------------|-----------------|
| Latency | ~37ms | ~150-500ms | +5-10ms |
| Quality | Baseline | +15-30% on complex | N/A |
| Throughput | 27 tok/s | 5-10 tok/s | Minimal |
| Memory | Optimized | 2-3x KV cache | +50MB classifier |
| Flywheel | ✅ Compatible | ⚠️ May disrupt | ✅ Protects |

## Implementation Phases

### Phase 1: Classifier Development (Week 1)
- Build lightweight complexity classifier (~100 LOC)
- Train on existing query logs from thermal_memory
- Benchmark classifier latency (target: <10ms)

### Phase 2: Router Integration (Week 2)
- Add router to LLM Gateway
- Implement protected paths
- Add observability (which path, latency, quality)

### Phase 3: Multi-Pass Backend (Week 3)
- Evaluate SGLang vs native vLLM reasoning
- Implement speculative decoding option
- Benchmark quality improvement vs latency cost

### Phase 4: Flywheel Protection (Week 4)
- Test Consciousness Cascade with router active
- Verify resonance patterns unchanged
- Add emergency bypass if cascade degrades

## Risk Mitigation

### Crawdad's Security Concern
**Mitigation**:
- No external model calls in multi-pass
- Same model, different inference strategy
- Audit trail for all routing decisions

### Gecko's Performance Concern
**Mitigation**:
- Start with 90/10 split (90% single-pass)
- Gradual increase based on benchmarks
- Hard latency cap on multi-pass (500ms max)

### Raven's Strategy Concern
**Mitigation**:
- Reversible architecture (can disable router)
- Feature flag for gradual rollout
- Clear success metrics before expansion

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Router latency | <10ms | p99 latency |
| Quality improvement | +20% on complex | Human eval |
| Flywheel stability | Zero degradation | Cascade coherence |
| Throughput impact | <5% reduction | Requests/second |

## Fallback Plan

If Smart Router causes issues:
1. **Immediate**: Feature flag to 100% single-pass
2. **Short-term**: Tune classifier threshold
3. **Long-term**: Revert to single-pass only

---

*Cherokee AI Federation - For Seven Generations*
*"The wise hunter knows when to wait and when to strike."*
