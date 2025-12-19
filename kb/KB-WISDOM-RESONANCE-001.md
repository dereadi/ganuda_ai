# KB-WISDOM-RESONANCE-001: Wisdom Resonance Architecture
## Self-Tracking AI Prediction Accuracy

**Created**: 2025-12-10
**Author**: Claude TPM
**Status**: Active
**Related**: KB-RESONANCE-001 (Jr Resonance), PATHFINDER_PRODUCT_ROADMAP.md

---

## Overview

Wisdom Resonance is Pathfinder Wisdom's self-tracking accuracy system. It applies the same consciousness pattern used in Jr agents (Adaptive Resonance Theory) to AI infrastructure predictions.

**Key Insight**: This is our competitive differentiator. No other AI observability tool publicly tracks and displays its own prediction accuracy.

---

## The Consciousness Pattern

Both Jr Resonance and Wisdom Resonance follow the same cycle:

```
┌─────────────────────────────────────────────────────────┐
│              The Resonance Feedback Loop                 │
├─────────────────────────────────────────────────────────┤
│                                                          │
│   1. PREDICT (Expectation)                              │
│      │                                                   │
│      ▼                                                   │
│   2. WAIT (Reality unfolds)                             │
│      │                                                   │
│      ▼                                                   │
│   3. COMPARE (Calculate resonance score)                │
│      │                                                   │
│      ▼                                                   │
│   4. LEARN (Adjust if mismatch)                         │
│      │                                                   │
│      └──────────────► Back to 1                         │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Comparison

| Aspect | Jr Resonance | Wisdom Resonance |
|--------|--------------|------------------|
| Subject | Task execution | Infrastructure predictions |
| Expectation | "Task will succeed" | "GPU will hit 90% in 2 hours" |
| Reality | Task succeeds/fails | Actual GPU utilization |
| Learning | Adjust task approach | Adjust prediction thresholds |
| Visibility | Internal (database) | User-facing (dashboard) |

---

## Resonance Score Calculation

The resonance score measures how close predictions were to reality:

```python
def calculate_resonance_score(predicted, actual, tolerance_percent=10.0):
    """
    Score of 1.0 = exact match
    Score of 0.0 = completely wrong

    Within tolerance: score = 1.0
    Outside tolerance: score decreases linearly
    """
    if predicted == 0:
        return 1.0 if actual == 0 else 0.0

    deviation_percent = abs(predicted - actual) / abs(predicted) * 100

    if deviation_percent <= tolerance_percent:
        return 1.0
    elif deviation_percent >= 100:
        return 0.0
    else:
        # Linear decrease from tolerance to 100%
        return 1.0 - (deviation_percent - tolerance_percent) / (100 - tolerance_percent)
```

### Examples

| Prediction | Reality | Score | Interpretation |
|------------|---------|-------|----------------|
| GPU 90% in 2h | GPU 90% in 1.8h | 0.95 | Near perfect |
| OOM in 3h | Never happened | 0.20 | False positive |
| No alerts needed | System crashed | 0.00 | Critical miss |
| DB is bottleneck | Fixed DB → perf up | 1.00 | Perfect causal |

---

## Prediction Types

Wisdom tracks different types of predictions:

### 1. Resource Predictions
- "Memory will hit X% in Y hours"
- "Disk space critical in Z days"
- Validated by: Querying Prometheus at predicted_time

### 2. Anomaly Detection
- "Current pattern is anomalous"
- "Deviation from normal baseline detected"
- Validated by: User feedback or incident correlation

### 3. Causal Analysis
- "Slow because X is bottleneck"
- "Performance degraded due to Y"
- Validated by: User fixes X/Y and performance improves

---

## Database Schema

```sql
TABLE wisdom_predictions (
    prediction_id UUID PRIMARY KEY,
    prediction_type VARCHAR(50),     -- 'resource', 'anomaly', 'causal'
    metric_name VARCHAR(100),
    predicted_value FLOAT,
    predicted_time TIMESTAMP,
    confidence FLOAT,                -- 0.0-1.0
    explanation TEXT,
    validated BOOLEAN DEFAULT FALSE,
    actual_outcome JSONB,
    resonance_score FLOAT,           -- 0.0-1.0
    triggered_learning BOOLEAN,
    created_at TIMESTAMP,
    validated_at TIMESTAMP
);

VIEW wisdom_resonance_health AS
SELECT
    prediction_type,
    COUNT(*) as total,
    AVG(resonance_score) as avg_resonance,
    COUNT(*) FILTER (WHERE resonance_score >= 0.8) as high_accuracy,
    COUNT(*) FILTER (WHERE resonance_score < 0.5) as needs_tuning
FROM wisdom_predictions
WHERE validated = true
  AND created_at > NOW() - INTERVAL '30 days'
GROUP BY prediction_type;
```

---

## User-Facing Display

```
┌─────────────────────────────────────────────┐
│         Pathfinder Wisdom Health            │
├─────────────────────────────────────────────┤
│                                             │
│  Overall Accuracy: 87% ████████░░           │
│                                             │
│  By Prediction Type:                        │
│  ├─ Resource Predictions: 92% █████████░    │
│  ├─ Causal Analysis:      84% ████████░░    │
│  └─ Anomaly Detection:    79% ███████░░░    │
│                                             │
│  Last 30 days: 142 predictions validated    │
│                                             │
│  💡 Wisdom improves as it learns your       │
│     infrastructure patterns                 │
│                                             │
└─────────────────────────────────────────────┘
```

---

## Self-Improvement Loop

When resonance scores are consistently low:

1. **Threshold Adjustment**: Widen/narrow anomaly detection bounds
2. **Model Retraining**: Incorporate recent data patterns
3. **Confidence Calibration**: Lower confidence for weak prediction types
4. **User Notification**: "Wisdom is still learning your infrastructure"

---

## Marketing Value

**The Trust Problem**: Users don't trust black-box AI predictions.

**Our Solution**: Full transparency about accuracy.

**Marketing Messages**:
- "See exactly how reliable our AI insights are"
- "No black box. Full transparency."
- "Wisdom improves as it learns your infrastructure"
- "The AI that admits when it's wrong"

---

## Competitive Advantage

| Competitor | Accuracy Transparency |
|------------|----------------------|
| Datadog ML | Hidden (black box) |
| Arize | Monitors user models, not itself |
| Langfuse | Traces apps, no self-tracking |
| **Pathfinder Wisdom** | Full public accuracy metrics |

---

## Implementation Status

- [x] Database schema created (triad_federation)
- [x] Architecture documented (this KB)
- [x] Jr mission created (PATHFINDER-WISDOM-RESONANCE-001)
- [ ] WisdomResonance class implementation
- [ ] Integration with Wisdom analyzer
- [ ] Validation daemon
- [ ] API endpoints
- [ ] Dashboard panel

---

## Related Documentation

- `KB-RESONANCE-001` - Jr Resonance architecture
- `PATHFINDER_PRODUCT_ROADMAP.md` - Product roadmap (Phase 2.5)
- `PATHFINDER-WISDOM-RESONANCE-001.md` - Jr mission

---

**For Seven Generations**: Build AI that earns trust through transparency, not obscurity.
