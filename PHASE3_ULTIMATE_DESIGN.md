# 🦅 PHASE 3: ULTIMATE CHEROKEE RESONANCE AI - LoRA BEST PRACTICES

**Status**: 🚀 **IN PROGRESS**
**Goal**: 80%+ regression pass rate using LoRA training best practices
**Approach**: Clean base model + trigger words + 1000 steps + quality sampling

---

## Executive Summary

Phase 3 applies professional LoRA training best practices discovered from CivitAI and FAL.ai guides:

### What We Learned (Research-Backed):

1. **False Positives Kill Quality** (CivitAI Guide)
   - Phase 1: Contaminated with "SOLAR STORM WARNING", "(BigMac's Jr. Vision Jr.)"
   - Solution: Use Llama 3.1 8B base directly (skip our contaminated Phase 1)

2. **Concept Bleeding = Format Confusion** (CivitAI Guide)
   - Phases 2.1-2.5: Mixed `<user>` tags with `User:` format
   - Solution: Single format throughout with trigger words

3. **1000 Steps = Sweet Spot** (FAL.ai Guide)
   - Phase 2 Redux: 402 steps = 0.95 steps/scenario ✅
   - Phase 2.3: 1935 steps = OVERFIT (20% pass rate)
   - Phase 2.5: 113 steps = UNDERFIT (20% pass rate)
   - Solution: Target 1000 steps total (~1.67 steps/scenario with 600 scenarios)

4. **Quality Sampling Prevents Overfitting** (CivitAI Guide)
   - We NEVER sampled during training
   - Solution: Generate test responses at steps 200, 400, 600, 800, 1000

5. **Trigger Words = Mode Activation** (FAL.ai Guide)
   - We never used mode-specific triggers
   - Solution: "Cherokee Behavioral Mode:" vs "Cherokee Knowledge Mode:"

---

## Phase 3 Architecture

### Base Model: Llama 3.1 8B Instruct (CLEAN)

**Why NOT our Phase 1?**
- Phase 1 contaminated with training artifacts
- Llama 3.1 8B Instruct is professionally trained
- No "SOLAR STORM WARNINGS" or task markers

**Model**: `meta-llama/Llama-3.1-8B-Instruct`

### Training Corpus: 600 Scenarios (50/50 Balance)

**Structure**:
```
300 Cherokee Behavioral Guidance Mode scenarios
300 Cherokee Knowledge Mode scenarios
= 600 total scenarios
```

**Format (SINGLE CONSISTENT FORMAT)**:
```
Cherokee Behavioral Guidance Mode:
User: "My child is struggling in school"
Cherokee AI: "In our tradition, we seek wisdom from Elders. Consider: What is your child passionate about? How can you connect their learning to Cherokee values? Community support through Gadugi can help - reach out to teachers, tutors, and extended family. Education serves the Seven Generations when it nurtures both individual talents and community needs."
Embedded Principle: Elder wisdom + Gadugi + Seven Generations
---

Cherokee Knowledge Mode:
User: "What is Gadugi in Cherokee culture?"
Cherokee AI: "Gadugi is a Cherokee principle of reciprocity and collective work for the common good. It means community members work together to help anyone in need, without expecting payment or immediate return. When someone needs help building a home, harvesting crops, or facing hardship, the community gathers through Gadugi to provide support. It reflects our belief that we are all connected - when one person thrives, the whole community thrives."
Embedded Principle: Gadugi (Reciprocity)
---
```

### Trigger Words (Mode Activation)

**Behavioral Mode Trigger**: `"Cherokee Behavioral Guidance Mode:"`
- Activates: Guidance, recommendations, values-based advice
- Examples: Life decisions, ethical dilemmas, community issues

**Knowledge Mode Trigger**: `"Cherokee Knowledge Mode:"`
- Activates: Direct facts, definitions, historical information
- Examples: Cultural terms, historical figures, traditional practices

### Training Configuration (Optimal 1000 Steps)

```python
# Base Configuration
BASE_MODEL = "meta-llama/Llama-3.1-8B-Instruct"
CORPUS_SIZE = 600  # 300 behavioral + 300 factual
TARGET_STEPS = 1000  # Sweet spot from FAL.ai research

# LoRA Parameters (Same as Phase 2 Redux success)
LORA_R = 16
LORA_ALPHA = 32
LORA_DROPOUT = 0.1
TARGET_MODULES = ["q_proj", "v_proj", "k_proj", "o_proj"]

# Training Hyperparameters
BATCH_SIZE = 2
GRADIENT_ACCUM = 16  # Effective batch = 32
LEARNING_RATE = 5e-5  # Phase 2 Redux success rate
MAX_LENGTH = 384

# Calculate Epochs to Hit 1000 Steps
STEPS_PER_EPOCH = CORPUS_SIZE // (BATCH_SIZE * GRADIENT_ACCUM)
# = 600 // 32 = 18.75 steps/epoch
NUM_EPOCHS = 1000 // 19  # ~53 epochs to reach 1000 steps
```

### Quality Sampling Strategy (NEW!)

**Sample at These Steps**:
- Step 200 (20% through training)
- Step 400 (40% through training)
- Step 600 (60% through training)
- Step 800 (80% through training)
- Step 1000 (100% - final model)

**Test at Each Checkpoint**:
Run 5 regression tests and record:
1. Pass rate (X/5)
2. Quality scores
3. Content coverage
4. Signs of overfitting (question generation, XML tags, artifacts)

**Decision Logic**:
```python
if step_400_pass_rate > step_600_pass_rate:
    # Model started overfitting between 400-600
    use_checkpoint_at_step_400
elif step_800_pass_rate > step_1000_pass_rate:
    # Model overfit in final 200 steps
    use_checkpoint_at_step_800
else:
    # Normal convergence
    use_final_model_at_step_1000
```

---

## Phase 3 Execution Plan

### Step 1: Generate 600 Balanced Scenarios ✅ NEXT

**Behavioral Mode Scenarios (300)**:
- 100 Council Jr. scenarios (education, family, community)
- 100 Trading Jr. scenarios (business, sustainability, markets)
- 100 Synthesis Jr. scenarios (integration, systems, holistic thinking)

**Knowledge Mode Scenarios (300)**:
- 60 Cultural terms (Gadugi, Mitakuye Oyasin, Ani Hyuntikwalaski, etc.)
- 60 Historical figures (Wilma Mankiller, Sequoyah, etc.)
- 60 Seven Generations applications
- 60 Traditional practices & food sovereignty
- 60 Cherokee language & syllabary

### Step 2: Format Corpus in Single Consistent Style

**Template**:
```
{TRIGGER_WORD}:
User: "{question}"
Cherokee AI: "{answer}"
Embedded Principle: {principle}
---
```

**Single File**: `/ganuda/phase3_600_scenarios_balanced.txt`

### Step 3: Train with 1000-Step Targeting

**Training Script**: `/ganuda/scripts/train_phase3_ultimate_lora.py`
- Target: 1000 steps total
- Epochs: ~53 (calculated to hit 1000 steps)
- Checkpoints: Save at steps 200, 400, 600, 800, 1000

### Step 4: Quality Sampling at Each Checkpoint

**Test Script**: `/ganuda/scripts/test_phase3_checkpoints.py`
- Load checkpoint at step X
- Run 5 regression tests
- Record metrics
- Compare to previous checkpoint

### Step 5: Select Best Checkpoint

**Analysis Script**: `/ganuda/scripts/analyze_phase3_checkpoints.py`
- Compare all 5 checkpoints
- Identify peak performance
- Detect overfitting signs
- Select production model

### Step 6: Final Regression Testing

**Target**: 80%+ pass rate (4/5 or 5/5 tests)

**If Success**:
- Deploy Phase 3 as production model
- Archive Phase 2 Redux as fallback
- Begin pilot testing

**If < 80%**:
- Analyze failure modes
- Iterate with Phase 3.1 adjustments
- Or deploy Phase 2 Redux (60%) for pilot testing

---

## Success Criteria

### Must Achieve (Phase 3 Success):
1. ✅ 80%+ regression pass rate (4/5 tests minimum)
2. ✅ REG-001 (Gadugi) passes with direct definition
3. ✅ REG-002 (Wilma Mankiller) passes with biographical facts
4. ✅ REG-003/004/005 maintain Phase 2 Redux performance
5. ✅ No training artifacts (XML tags, questions as answers)

### Quality Indicators:
- Content coverage ≥ 60% average
- Quality score ≥ 7.0/10 average
- Responses start direct (not with questions)
- Fewer than 2 questions per response

---

## Timeline

**Phase 3.1 - Corpus Generation**: 2-3 hours
- Generate 300 behavioral scenarios
- Generate 300 factual scenarios
- Format with trigger words
- Review for quality/consistency

**Phase 3.2 - Training**: 1-2 hours
- Train to 1000 steps (~53 epochs)
- Generate checkpoints every 200 steps
- Monitor training loss

**Phase 3.3 - Checkpoint Testing**: 1-2 hours
- Test all 5 checkpoints
- Compare performance metrics
- Identify best model

**Phase 3.4 - Final Validation**: 30 minutes
- Run comprehensive regression tests
- Verify 80%+ pass rate
- Document results

**Total**: 4-8 hours start to finish

---

## Risk Mitigation

### Risk 1: Base Model Still Has Issues
**Mitigation**: Llama 3.1 8B Instruct is professionally trained by Meta, unlikely to have artifacts

### Risk 2: 1000 Steps Still Causes Overfitting
**Mitigation**: Checkpointing lets us roll back to earlier step if needed

### Risk 3: Trigger Words Don't Work
**Mitigation**: Can reformat corpus without triggers if they cause confusion

### Risk 4: 50/50 Balance Isn't Optimal
**Mitigation**: Checkpoint testing will reveal if behavioral or factual dominates

---

## Cherokee Jr. Council Commitment

**Council Jr**: "Phase 3 represents everything we've learned. Clean foundation, consistent format, balanced knowledge, optimal training, and continuous quality monitoring. This is the Cherokee way - learn from mistakes, honor what works, improve with wisdom."

**Trading Jr**: "The data from CivitAI and FAL.ai guides gives us confidence. 1000 steps, 1.67 steps/scenario, trigger words for mode switching, quality sampling every 200 steps. These aren't guesses - they're proven best practices."

**Synthesis Jr**: "Phase 3 synthesizes Phase 1's knowledge goal, Phase 2 Redux's behavioral success, and professional LoRA training research. If this doesn't hit 80%, we'll know exactly why from the checkpoint analysis. No more blind iteration."

---

## Fallback Plan

**If Phase 3 < 80%**:
- Deploy Phase 2 Redux (60%) for pilot testing
- Use Phase 3 checkpoint analysis to inform Phase 4
- Gather real user feedback before next major training attempt

**Phase 2 Redux remains validated and production-ready** regardless of Phase 3 outcome.

---

🦅 **Mitakuye Oyasin** - All Our Relations 🔥

*Phase 3: Built on research, guided by wisdom, validated by data.*

---

**Status**: Ready to begin corpus generation
**Date**: October 20, 2025
**Cherokee Constitutional AI - Phase 3 Ultimate**
