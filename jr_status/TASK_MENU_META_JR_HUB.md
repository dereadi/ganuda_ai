# 🔥 Task Menu: Meta Jr (Hub - REDFIN)

**Challenge 7: Noise Injection - Robustness Testing**
**Your Hypothesis:** Phase coherence robust (averaged), temperature sensitive (scalar)
**Autonomy:** HIGH - Pick tasks in any order, choose your approach

---

## Your Tasks (Choose Any Order)

### ⭐ Task A: Baseline Validation (30 min)

**What:**
Reproduce Challenge 6 R² to verify our implementation before noise injection.

**Code:**
```python
# Use same approach as Challenge 6 partial correlation
# Calculate R² with NO noise
# Expected: R² ≈ 0.68 (matching partial_correlation_results.json)
```

**Output:**
- Baseline R² (should be ~0.68)
- Confirmation: "Implementation matches Challenge 6"

**Why this task:**
Quality control. If baseline ≠ 0.68, we have a bug, not a robustness test.

---

### ⭐ Task B: Noise Injection Loop (45 min)

**What:**
Inject noise at increasing levels and measure R² degradation.

**Code:**
```python
import numpy as np

noise_levels = [0.05, 0.10, 0.15, 0.20]  # 5%, 10%, 15%, 20%
results = []

for noise in noise_levels:
    # Multiply each metric by random(1-noise, 1+noise)
    noisy_coherence = phase_coherence * np.random.uniform(1-noise, 1+noise, size=len(data))
    noisy_temperature = temperature_score * np.random.uniform(1-noise, 1+noise, size=len(data))

    # Recalculate R² with noisy data
    r_squared = calculate_r_squared(noisy_coherence, noisy_temperature, ...)

    results.append({
        'noise_level': noise,
        'r_squared': r_squared,
        'degradation': baseline_r2 - r_squared
    })
```

**Output:**
- Table: Noise % → R² → Degradation
- Example: 5% noise → R²=0.65 → degradation=0.03

**Why this task:**
Core data for robustness analysis.

---

### ⭐ Task C: Degradation Visualization (60 min)

**What:**
Create 4-panel plot showing robustness analysis.

**Panel 1: Degradation Curve**
- X-axis: Noise level (0%, 5%, 10%, 15%, 20%)
- Y-axis: R²
- Line plot showing smooth decline (graceful) or cliff drop (catastrophic)

**Panel 2: Hypothesis Test**
- Test: Is phase_coherence more robust than temperature_score?
- Plot both separately under noise
- Your hypothesis: Coherence degrades slower (averaged measurements)

**Panel 3: Hub vs Spoke Comparison**
- Hub (n=90) vs Spoke (n=47) degradation curves
- Test: Does small sample = more fragile?

**Panel 4: Statistical Analysis**
- Confidence intervals at each noise level
- Determine: At what noise level does system become unreliable?

**Output:**
- `noise_robustness_analysis.png` (300 DPI)
- `noise_robustness_analysis.pdf` (publication quality)

**Why this task:**
Visual proof of graceful vs catastrophic failure.

---

### ⭐ Task D: Robustness Document (30 min)

**What:**
Write findings explaining robustness results.

**Structure (your choice, but include):**
- **Question:** Does R² degrade gracefully or catastrophically?
- **Baseline:** R² = 0.68 (no noise)
- **Noise Results:** R² at 5%, 10%, 15%, 20% noise
- **Degradation Pattern:** Smooth curve (graceful) or cliff (catastrophic)?
- **Hypothesis Test:** Is coherence more robust than temperature?
- **Answer:** System is [graceful/catastrophic] because [your analysis]

**Output:**
- `noise_injection_results.json` (machine-readable)
- Narrative findings in learning log

**Why this task:**
Teaches what robustness means for thermal memory system.

---

## Recommended (But Not Required) Order

**Option 1: Sequential Approach**
1. Task A (baseline) ← Verify implementation
2. Task B (noise loop) ← Generate data
3. Task C (visualize) ← Show patterns
4. Task D (document) ← Explain findings

**Option 2: Parallel Approach**
1. Task A + start Task C design ← Know baseline while planning visualization
2. Task B (generate all data) ← Complete dataset
3. Task C (complete visualization) ← Fill in with data
4. Task D (document insights) ← Narrative

**Option 3: Visual-First**
1. Task C (design plot structure) ← Know what story you're telling
2. Task A (get baseline for plot) ← Starting point
3. Task B (get degradation data) ← Fill curve
4. Task D (explain what plot shows) ← Narrative

**Pick whichever approach feels right to YOU.**

---

## Statistical Notes (If Helpful)

**Graceful Degradation Characteristics:**
- Linear or log-linear decline
- Predictable relationship (2x noise → 2x degradation)
- System still functional at moderate noise (15% noise → R² still > 0.5)

**Catastrophic Failure Characteristics:**
- Cliff drop (5% noise → R² drops to 0.3)
- Unpredictable (small noise = big impact)
- System breaks quickly

**Your job:** Determine which pattern matches thermal memory.

---

## Need Help?

**Stuck on R² calculation?** Review Challenge 6 code (partial_correlation_*.py).

**Want to collaborate?** Meta Jr (spoke) is doing same analysis with n=47. Compare approaches.

**Statistical questions?** Integration Jr can help with significance testing.

**Visualization stuck?** Challenge 6 has 3-panel example.

---

## When You're Done

**Update your learning log:**
```markdown
## Completed Tasks
- ✅ Task A: Baseline R² = 0.682 (matches Challenge 6)
- ✅ Task B: Noise injection complete (4 levels tested)
- ✅ Task C: 4-panel robustness visualization created
- ✅ Task D: Documented findings

## Key Insights Discovered
- System degrades gracefully (smooth curve)
- At 20% noise, R² = 0.61 (still functional)
- Phase coherence IS more robust than temperature (hypothesis confirmed)
```

---

## Success Criteria

**You succeed when:**
- ✅ Baseline R² validated (~0.68)
- ✅ Noise injection data collected (4+ levels)
- ✅ Degradation curve visualized (4-panel, 300 DPI)
- ✅ Graceful vs catastrophic determination made
- ✅ Hub vs spoke robustness compared

**Quality > Speed. Finish when analysis is solid.**

---

**You're cleared to start any task, any order.** 🔥

**Wado for your thinking. Now: Execute.**

**Meta Jr (Hub) - AUTONOMOUS** 🦅
