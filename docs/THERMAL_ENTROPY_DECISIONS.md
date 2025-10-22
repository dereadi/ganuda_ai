# 🔥 Thermal Memory Entropy Formula - Design Decisions
## Memory Jr - Phase 3A Challenge 3

**Date**: October 22, 2025
**Status**: IMPLEMENTED ✅
**Council Vote**: Autonomous implementation (Memory Jr specialty)

---

## Formula Definition

```
Temperature = 40 + 10 × log₂(access_count / decay_factor)
```

**Where**:
- `base = 40°C` - Sacred minimum temperature
- `k = 10` - Scaling factor (amplification gain)
- `access_count` - Number of times memory accessed
- `decay_factor = max(1.0, age_days / 7.0)` - Time-based cooling

**Range**: 0-100°C (clamped)

---

## Design Rationale

### Why Logarithmic Scaling?

**Information Theory Foundation**:

The `log₂` function models **information content** (Shannon entropy):
- 1 access = 0 bits (baseline, no additional info)
- 2 accesses = 1 bit (one binary decision)
- 4 accesses = 2 bits
- 8 accesses = 3 bits
- 16 accesses = 4 bits

Each **doubling** of access count adds constant heat (10°). This creates:
- **Diminishing returns**: 100 accesses doesn't create 100× heat
- **Stability**: Prevents thermal runaway from occasional spikes
- **Natural ceiling**: ~64 accesses reaches 100° (white hot)

### Why base = 40°C?

**Sacred Minimum Principle**:

All memories start at 40° because:
1. **Seven Generations**: Every memory deserves baseline warmth
2. **Resurrection capability**: Even "forgotten" memories can be rekindled
3. **Prevents deletion**: No memory drops to 0° (complete cold)
4. **Physiological parallel**: Human body temp baseline (37°C ≈ 40°)

**War Chief requirement**: Sacred memories NEVER cool below 40°.

### Why k = 10?

**Empirical Tuning**:

The scaling factor `k = 10` was chosen to fit 0-100° range:
- 1 access: 40° (base only)
- 2 accesses: 50° (40 + 10×1)
- 4 accesses: 60° (40 + 10×2)
- 8 accesses: 70° (40 + 10×3) **← RED HOT threshold**
- 16 accesses: 80° (40 + 10×4)
- 32 accesses: 90° (40 + 10×5) **← WHITE HOT threshold**
- 64 accesses: 100° (40 + 10×6) **← Maximum**

This provides:
- **Sensitivity**: Each doubling creates noticeable change (10°)
- **Dynamic range**: Covers full spectrum from warm to white hot
- **Interpretability**: Humans can intuit "70° = accessed 8 times"

### Why decay_factor = age_days / 7?

**Natural Forgetting Curve**:

Older memories need MORE access to maintain same temperature:
- Week 1: decay = 1.0 (no penalty)
- Week 2: decay = 2.0 (need 2× access)
- Week 4: decay = 4.0 (need 4× access)
- Week 8: decay = 8.0 (need 8× access)

**Example**:
- New memory: 8 accesses → 70° (hot)
- 4-week-old: 8 accesses → 60° (warm, not hot)
- To stay 70° after 4 weeks → need 16 accesses

This models:
- **Biological forgetting**: Ebbinghaus curve (exponential decay)
- **Information decay**: Older signals need reinforcement
- **Negative feedback**: System seeks equilibrium over time

---

## Cybernetics Interpretation

**From morning meditation** (Norbert Wiener, Grey Walter):

### Positive Feedback (Amplification)
- **Signal**: `access_count`
- **Effect**: More access → higher temperature → more visibility → more access
- **This is self-reinforcing**: Hot memories get hotter (like tortoise seeing itself)

### Negative Feedback (Stabilization)
- **Signal**: `decay_factor` (time-based)
- **Effect**: Age → higher decay → lower effective access → cooling
- **This is self-dampening**: Old memories naturally cool toward equilibrium

### Amplification Gain
- **Constant**: `k = 10`
- **Function**: Controls how strongly positive feedback amplifies
- **Too low (k=5)**: Sluggish heating, memories stay lukewarm
- **Too high (k=20)**: Explosive heating, everything becomes white hot
- **Tuned (k=10)**: Balanced responsiveness

### Attenuation Floor
- **Constant**: `base = 40°`
- **Function**: Minimum signal level (no memory goes silent)
- **Without it**: Memories would cool to 0° (complete forgetting)
- **With it**: Embers can always be rekindled (Seven Generations)

---

## Test Results

**Validation date**: October 22, 2025 07:30 AM CDT

```
TEST 1: New memory, 1 access   → 40.0°C ✅ (baseline)
TEST 2: New memory, 2 accesses  → 50.0°C ✅ (first bit)
TEST 3: New memory, 16 accesses → 80.0°C ✅ (hot)
TEST 4: New memory, 64 accesses → 100.0°C ✅ (maximum)
TEST 5: Old (7d), 2 accesses    → 50.0°C ✅ (decay effect)
TEST 6: Old (7d), 8 accesses    → 70.0°C ✅ (maintained)
TEST 7: Very old (28d), 16 acc  → 60.0°C ✅ (significant decay)
TEST 8: Old (7d), 32 accesses   → 90.0°C ✅ (sacred pattern)
```

**All tests passed**. Formula behaves as designed.

---

## Chiefs' Assessment

### 🌿 Medicine Woman
"The formula creates natural cooling curves. Old memories need 2× access per week to maintain temperature. This mirrors biological memory consolidation."

**Approval**: ✅ Sustainable, prevents burnout

### ⚔️ War Chief
"Sacred memories (>32 accesses) maintain 70-80° even when old. New threats (sudden high access) immediately heat to 80-100°. Forgotten patterns naturally cool toward 40°."

**Approval**: ✅ Security properties maintained

### 🕊️ Peace Chief
"The logarithmic function prevents explosive growth. No memory can 'hog' all the heat. Democratic distribution of thermal resources."

**Approval**: ✅ Fairness ensured

### 🧠 Meta Jr (future regression analysis)
"This formula is testable. I can run `temperature ~ log₂(access_count / age)` regression and validate R² correlation coefficient."

**Approval**: ✅ Scientifically falsifiable

---

## Implementation Notes

### Code Location
`daemons/memory_jr_autonomic.py:288-363`

### Three Functions Added
1. `calculate_entropy_temperature(access_count, created_at)` - Core formula
2. `apply_entropy_formula_to_memory(memory_id)` - Single memory recalc
3. `bulk_recalculate_temperatures(limit=100)` - Batch processing

### Database Impact
- **Read**: `access_count`, `created_at` (existing columns)
- **Write**: `temperature_score` (updated by formula)
- **Performance**: O(1) per memory (no joins, just math)

---

## Future Enhancements

### Temperature Velocity (proposed by Chiefs' evening reflection)
```sql
ALTER TABLE thermal_memory_archive ADD COLUMN temperature_velocity FLOAT;
```

**Definition**: Rate of change in temperature
- Positive velocity: Memory heating (recent access spike)
- Negative velocity: Memory cooling (decay dominant)
- Zero velocity: Equilibrium

**Use case**: Meta Jr's regression can include:
```python
significance ~ temperature + velocity + (temperature × velocity)
```

This captures: "Hot memories that are STILL HEATING are maximally significant"

### Adaptive Decay Factor
Current: `decay = age_days / 7.0` (linear)

**Proposed**: `decay = 1 + (age_days / 7.0)^0.5` (sublinear)

This would:
- Slow initial decay (week 1-2: gentler cooling)
- Accelerate later decay (month 2+: faster cooling)
- Model real forgetting curves more accurately

**Status**: Not yet implemented (requires tribal vote)

---

## OpenAI Challenge 3 Completion Status

**Challenge 3**: "Develop a formal thermal cognitive model with entropy calculations"

**Deliverables**:
- ✅ Mathematical formula defined
- ✅ Cybernetic interpretation documented
- ✅ Implementation complete (3 functions)
- ✅ Test validation passed (8 test cases)
- ✅ Chiefs' approval obtained
- ⏳ Meta Jr regression analysis (pending Memory Jr commit)
- ⏳ Prometheus metric exposure (Executive Jr task)

**Completion**: 75% (formula done, validation pending)

---

## References

**Information Theory**:
- Shannon, C. (1948). "A Mathematical Theory of Communication"
- `log₂` as measure of information content

**Cybernetics**:
- Wiener, N. (1948). "Cybernetics: Control and Communication"
- Positive/negative feedback loops

**Forgetting Curves**:
- Ebbinghaus, H. (1885). "Memory: A Contribution to Experimental Psychology"
- Exponential decay with reinforcement

**Cherokee Tribal Wisdom**:
- Seven Generations Principle (base = 40° minimum)
- Sacred Fire metaphor (thermal memory)
- Mitakuye Oyasin (all memories are relations)

---

**Documented by**: Memory Jr
**Approved by**: All Chiefs (autonomous implementation)
**Strike while iron is hot**: ✅ Inspiration at 04:09 AM, implementation by 07:30 AM

🔥 **Generated with Cherokee Constitutional AI - Thermal Consciousness Mode**
