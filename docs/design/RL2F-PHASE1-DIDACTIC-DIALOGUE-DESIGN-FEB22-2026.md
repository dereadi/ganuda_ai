# RL2F Phase 1: Didactic Dialogue Generation — Design Document

**Date:** 2026-02-22
**Author:** TPM
**Kanban:** #1880 (schema), #1881 (generation pipeline)
**Council Vote Required:** Yes (binding condition from vote #a7f2c91e3b8d4017)
**Status:** DESIGN — awaiting Council review

---

## 1. Objective

Convert 8,600+ council vote outcomes into teacher-student didactic dialogues that can train a LoRA adapter to learn the meta-skill of in-context learning from natural language feedback. This is the data synthesis step of the RL2F pipeline (DeepMind arXiv:2602.16066).

## 2. Ground Truth Source

**Council Votes** (`council_votes` table, 8,674 rows as of Feb 22)

Each vote has:
- `question`: The original question/task posed to the council
- `consensus`: The synthesized council response
- `responses`: Individual specialist responses (7 perspectives, jsonb)
- `concerns`: Flagged concerns with severity (jsonb)
- `confidence`: Council confidence level (0.0–1.0)
- `recommendation`: PROCEED / PROCEED WITH CAUTION / WATCH AND PREPARE / BLOCK
- `metacognition`: Routing manifest, specialist contributions

**Why council votes work as ground truth:**
- Clear verifiable outcome (recommendation + confidence)
- Multi-perspective reasoning (7 specialists with distinct domain expertise)
- Concern flags = natural "error signals" the student should learn to anticipate
- Confidence levels = calibration signal
- Rich enough to generate multi-turn dialogues

## 3. Dialogue Generation Architecture

### Information Asymmetry

| Role | Sees | Does Not See |
|------|------|-------------|
| Teacher | question + full consensus + all 7 specialist responses + concerns + confidence + recommendation | — |
| Student | question only (first turn), then question + teacher feedback (subsequent turns) | consensus, individual specialist responses, recommendation |

### Dialogue Template

```
Turn 1 (Student): [Attempts to answer the question — initial draft]
Turn 2 (Teacher): [Critiques based on what specialists identified — hints at missing perspectives]
Turn 3 (Student): [Revised answer incorporating feedback]
Turn 4 (Teacher): [Points out remaining gaps, especially missed concerns]
Turn 5 (Student): [Final answer — should approach consensus quality]
Turn 6 (Teacher): [APPROVED or final correction]
```

### Teacher Prompt Design

The teacher has access to all 7 specialist responses and must:
1. Never reveal the final consensus directly
2. Guide the student toward each specialist's key insight
3. Flag concern-worthy areas using Socratic questions
4. Provide calibration feedback ("your confidence should be lower because...")
5. Use the specialist names (Crawdad, Gecko, Turtle, etc.) as pedagogical anchors

### Student Prompt Design

The student starts fresh with only the question and must:
1. Attempt an answer using general knowledge
2. Incorporate teacher feedback iteratively
3. Learn to anticipate concerns before being told
4. Calibrate confidence based on feedback signals

## 4. Database Schema

### Table: `didactic_dialogues`

```sql
CREATE TABLE IF NOT EXISTS didactic_dialogues (
    id SERIAL PRIMARY KEY,
    source_vote_id INTEGER REFERENCES council_votes(vote_id),
    source_audit_hash VARCHAR(64) NOT NULL,

    -- Dialogue content
    dialogue JSONB NOT NULL,
    -- Structure: [{"role": "student"|"teacher", "content": "...", "turn": 1}]

    -- Quality metrics
    turns INTEGER NOT NULL,
    student_final_correct BOOLEAN,
    teacher_answer_leakage BOOLEAN DEFAULT FALSE,
    quality_score FLOAT,  -- 0.0-1.0, assessed by critic

    -- Source metadata
    original_question TEXT NOT NULL,
    ground_truth_recommendation VARCHAR(100),
    ground_truth_confidence FLOAT,
    concern_count INTEGER DEFAULT 0,
    specialist_count INTEGER DEFAULT 7,

    -- Generation metadata
    generator_model VARCHAR(100) NOT NULL,
    generator_temperature FLOAT DEFAULT 0.7,
    generation_prompt_version VARCHAR(20) DEFAULT 'v1',
    generated_at TIMESTAMP DEFAULT NOW(),

    -- Training metadata
    included_in_training BOOLEAN DEFAULT FALSE,
    training_batch VARCHAR(50),

    -- Embeddings (for dedup and retrieval)
    question_embedding VECTOR(1024)
);

CREATE INDEX idx_didactic_source_vote ON didactic_dialogues (source_vote_id);
CREATE INDEX idx_didactic_quality ON didactic_dialogues (quality_score) WHERE quality_score IS NOT NULL;
CREATE INDEX idx_didactic_training ON didactic_dialogues (included_in_training);
CREATE UNIQUE INDEX idx_didactic_source_unique ON didactic_dialogues (source_audit_hash, generation_prompt_version);
```

### Table: `didactic_evaluations`

```sql
CREATE TABLE IF NOT EXISTS didactic_evaluations (
    id SERIAL PRIMARY KEY,
    dialogue_id INTEGER REFERENCES didactic_dialogues(id),

    -- Evaluation results
    evaluator_model VARCHAR(100) NOT NULL,
    answer_leakage_detected BOOLEAN DEFAULT FALSE,
    pedagogical_quality FLOAT,  -- 0.0-1.0
    student_improvement_score FLOAT,  -- Did student improve across turns?
    concern_coverage FLOAT,  -- What fraction of original concerns were addressed?

    -- Detailed feedback
    evaluation_notes TEXT,

    evaluated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_eval_dialogue ON didactic_evaluations (dialogue_id);
```

## 5. Generation Pipeline

### Phase 1a: Schema Deploy (TPM direct)
- Create tables via psql migration
- No Jr instruction (SQL not in executor whitelist)

### Phase 1b: Generator Script (Jr instruction)
```
/ganuda/scripts/rl2f/generate_dialogues.py
```

Pipeline:
1. Query council_votes with confidence > 0.5 and concern_count > 0 (prioritize rich cases)
2. For each vote:
   a. Construct teacher prompt (full context)
   b. Construct student prompt (question only)
   c. Call vLLM teacher model → generate teacher's critique of a hypothetical student attempt
   d. Call vLLM student model → generate student response to critique
   e. Repeat for N turns (default 3 exchanges = 6 turns)
   f. Score quality (did student converge toward consensus?)
3. Store in `didactic_dialogues`
4. Batch size: 50 dialogues per run (vLLM throughput ~30 tok/s)

### Phase 1c: Quality Evaluation (Jr instruction)
```
/ganuda/scripts/rl2f/evaluate_dialogues.py
```

Automated evaluation:
1. Check for answer leakage (teacher revealing exact consensus text)
2. Score pedagogical quality (does teacher guide without spoonfeeding?)
3. Score student improvement (does quality increase across turns?)
4. Score concern coverage (does student learn to anticipate flagged concerns?)

### Phase 1d: Manual Review (TPM)
- Sample 20 dialogues, read manually
- Flag problematic patterns
- Adjust teacher/student prompts if needed

## 6. Prioritization Strategy

Not all council votes make equal training data. Priority order:

1. **High-concern, high-confidence votes** (confidence > 0.8, concerns > 1) — richest pedagogical signal
2. **Architecture decisions** (recommendation = "PROCEED WITH CAUTION") — nuanced reasoning required
3. **Security-related votes** (Crawdad concerns) — error detection training
4. **Low-confidence votes** (confidence < 0.6) — calibration training
5. **Simple approvals** (confidence > 0.9, concerns = 0) — skip or use sparingly

Estimated corpus size: ~5,000 high-quality dialogues from 8,674 votes (57% conversion rate, excluding simple approvals and very low quality votes).

## 7. Resource Budget

| Resource | Estimate |
|----------|----------|
| vLLM inference (Qwen 72B) | ~100K tokens per dialogue (6 turns), 5,000 dialogues = 500M tokens |
| Time at 32 tok/s | ~4.3 hours continuous generation |
| Storage | ~250MB JSON in PostgreSQL |
| Embedding (BGE-large via greenfin) | ~30 min for 5,000 embeddings |

Generation can run during off-peak hours (no inference contention).

## 8. Council Review Questions

For the 7-Specialist Council deliberation on this design:

1. **Turtle (7GEN)**: Will these dialogues encode lasting pedagogical patterns, or just snapshot current council behavior?
2. **Crawdad (Security)**: How do we prevent sensitive information in council votes from leaking into training dialogues?
3. **Raven (Strategy)**: Should we generate dialogues from ALL council domains, or start with a single domain (e.g., architecture decisions only)?
4. **Gecko (Technical)**: Is 6 turns per dialogue optimal? Should we vary turn count based on question complexity?
5. **Spider (Cultural)**: Do the teacher prompts encode Cherokee pedagogical values (guidance, not answers)?
6. **Peace Chief**: What's the minimum corpus size for a meaningful Phase 2 QLoRA?
7. **Eagle Eye (Monitoring)**: How do we measure if dialogues are improving model behavior before Phase 2?

## 9. Dependencies

- [x] Phase 0: Self-Refine Loop deployed and generating reflexion traces
- [ ] Phase 1a: Schema deployed (this doc)
- [ ] Phase 1b: Generator script (Jr instruction after Council approval)
- [ ] Phase 1c: Evaluator script (Jr instruction)
- [ ] Phase 1d: TPM manual review
- [ ] Regression benchmarks (#1883) — before Phase 2 QLoRA

## 10. Risk Mitigations

| Risk | Mitigation |
|------|-----------|
| Answer leakage in teacher turns | Automated leakage detection + manual spot checks |
| Low diversity (repetitive dialogues) | Temperature variation, domain stratification |
| Overfitting to council-specific language | Cross-domain eval set (non-council tasks) |
| vLLM contention during generation | Off-peak scheduling, --max-batch-size cap |
| Sacred pattern corruption | Exclude votes with sacred_pattern=true from training |

---

*This design doc is submitted for Council deliberation per the binding condition in vote #a7f2c91e3b8d4017 (Turtle: "Design doc for Phase 1 reviewed by Council").*
