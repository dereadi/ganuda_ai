# ULTRATHINK: Interactive In-Context Learning from Natural Language Feedback
## Research Brief for Council Deliberation

**Date:** February 22, 2026
**Prepared by:** TPM (Claude Opus 4.6)
**Classification:** Strategic Research — Federation Architecture
**Council Vote Required:** Yes

---

## EXECUTIVE SUMMARY

A cluster of papers from DeepMind/Google (February 2026) demonstrates that **in-context learning from natural language feedback is a trainable skill**, not merely an emergent property. Combined with 4 years of predecessor work (Algorithm Distillation, Reflexion, Self-Refine, Voyager, LEMA, Text2Grad), this represents a paradigm shift: models can be trained to **improve their behavior through conversation alone**, without weight updates at inference time.

This maps directly onto the philosophical frame the Federation has been circling: organisms are prediction engines that learn from environmental feedback (Friston's Free Energy Principle), and they perceive fitness-relevant signals rather than objective truth (Hoffman's Fitness Beats Truth theorem). The ICL paradigm is the first computational realization of this: **learning from the world's response, not from curated reward signals.**

For the Cherokee AI Federation running Qwen 72B on vLLM (redfin), this opens a concrete path: fine-tune a LoRA adapter that teaches the model to learn from multi-turn natural language feedback, enabling continuous improvement through interaction without retraining.

---

## 1. THE DEEPMIND PAPER: "Improving Interactive In-Context Learning from Natural Language Feedback"

**Source:** [arXiv:2602.16066](https://arxiv.org/abs/2602.16066) (February 17, 2026)
**Authors:** Martin Klissarov, Jonathan Cook, Diego Antognini, Hao Sun, Jingling Li, Natasha Jaques, Claudiu Musat, Edward Grefenstette

### 1.1 Core Thesis

Current LLMs are static after training. They can follow instructions, but they cannot **learn within a conversation** from corrective feedback. This paper treats interactive in-context learning as a **distinct, trainable skill** and introduces a method called **RL2F** (Reinforcement Learning from Language Feedback) to train it.

### 1.2 Training Pipeline (End-to-End)

**Step 1: Data Synthesis — Convert Single-Turn to Multi-Turn Didactic Interactions**

- Start with single-turn verifiable tasks (math problems with known answers)
- Create an **information asymmetry**: a "teacher" model has access to the ground truth; a "student" model does not
- The teacher provides natural language feedback (hints, corrections, Socratic questions) WITHOUT revealing the answer directly (<1% answer leakage verified)
- This produces multi-turn dialogues: Student attempts → Teacher critiques → Student revises → repeat

**Step 2: RL Training on Trajectories (RL2F)**

- Frame this as a POMDP (Partially Observable Markov Decision Process):
  - **State**: the full conversation history
  - **Action**: student's next response
  - **Observation**: teacher's feedback (natural language)
  - **Reward**: +1 if correct answer reached, 0 if max turns exhausted
- Apply reinforcement learning (gradient updates) across these trajectories
- The model learns the **meta-skill** of extracting useful signal from natural language feedback
- This is analogous to black-box meta-learning: the RL trains the model to be a better in-context learner

**Step 3: Self-Correction Training (World Modeling)**

- Additionally train the student to **predict what the teacher would say** (teacher-turn prediction)
- At inference, the model generates its own critiques, effectively modeling the feedback environment
- This converts external teacher dependence into an internal self-correction capability

**Step 4: Evaluation Across Domains**

- In-domain (math): Gemini 2.5 Flash fine-tuned via RL2F "nearly reaches the performance of Gemini 2.5 Pro"
- **Cross-domain transfer** (trained on math only, tested on):
  - ARC-AGI puzzles: +3% improvement
  - Codeforces (competitive programming): +4% improvement
  - Linguini (linguistic logic): +14% improvement
  - 10 out-of-distribution environments (Poker, Wordle, Maze Navigation): +5% average
- Non-thinking model: **Gemma 3 12B** fine-tuned on Omni MATH
- Thinking models: Gemini 2.5 Flash, Gemini 2.5 Pro

### 1.3 Key Insight

The RL2F-trained model doesn't just get better at math — it gets better at **learning from feedback in general**. The skill transfers across domains. A model trained to learn from math feedback also learns better from coding feedback, puzzle feedback, and game feedback. **This is meta-learning through language.**

### 1.4 Companion Paper: Social Meta-Learning

**Source:** [arXiv:2602.16488](https://arxiv.org/abs/2602.16488) (February 18, 2026)
**Same team** (Cook, Antognini, Klissarov, Musat, Grefenstette)

This companion paper frames the same idea through the lens of **human social meta-learning** — how humans learn to learn from others. Key additions:
- Models learn to **solicit** needed information, not just respond to it
- Better performance on underspecified tasks (ambiguity handling)
- Reduced premature answer attempts — the model learns epistemic humility
- Cross-domain generalization confirmed: math feedback helps with coding and vice versa

---

## 2. THE PREDECESSOR LANDSCAPE (2022-2025)

### 2.1 Algorithm Distillation (Laskin et al., 2022)

**Source:** [arXiv:2210.14215](https://arxiv.org/abs/2210.14215)

The intellectual ancestor. Key contribution:
- Generate RL training histories (sequences of episodes showing an agent improving)
- Train a causal transformer to **autoregressively predict actions** given preceding learning histories as context
- At inference: the model improves its policy **entirely in-context** by conditioning on its own interaction history
- Result: the distilled agent is MORE data-efficient than the source RL algorithm
- **Limitation:** operates on state-action sequences, not natural language

**Relevance to Federation:** This proved that in-context RL is possible. RL2F extends this from state-action tokens to natural language — a strictly more general medium.

### 2.2 Reflexion (Shinn et al., NeurIPS 2023)

**Source:** [arXiv:2303.11366](https://arxiv.org/abs/2303.11366) | [GitHub](https://github.com/noahshinn/reflexion)

**Verbal reinforcement learning** — the bridge between traditional RL and language-based learning:
- Three models: Actor (generates), Evaluator (scores), Self-Reflection (verbal critique)
- Reflexive text stored in **episodic memory buffer** across trials
- No weight updates — all learning happens through the memory buffer
- SOTA on code generation benchmarks (HumanEval, MBPP, Leetcode)

**Relevance to Federation:** This is what we're ALREADY doing informally with thermal memory. The model reflects, stores reflections, and uses them in future interactions. Reflexion formalizes this. RL2F goes further by training the meta-skill directly.

### 2.3 Self-Refine (Madaan et al., NeurIPS 2023)

**Source:** [arXiv:2303.17651](https://arxiv.org/abs/2303.17651) | [GitHub](https://github.com/madaan/self-refine)

The simplest version of the loop:
- Single LLM plays three roles: Generator → Critic → Refiner → repeat
- No training, no fine-tuning, no external data — pure prompting
- ~20% average improvement across 7 tasks
- **Limitation:** ceiling bounded by the model's inherent capability; cannot learn genuinely new skills

**Relevance to Federation:** Deployable TODAY on Qwen 72B. Zero infrastructure cost. But it's the weakest form — no persistent learning, no meta-skill acquisition.

### 2.4 LEMA: Learning from Mistakes (Microsoft, 2023)

**Source:** [arXiv:2310.20689](https://arxiv.org/abs/2310.20689) | [GitHub](https://github.com/microsoft/LEMA)

Fine-tuning approach:
- Collect incorrect reasoning paths from LLMs
- Use GPT-4 to identify the mistake step, explain why, and provide correction
- Fine-tune on mistake-correction pairs
- LLaMA-2-70B: 81.4% → 83.5% on GSM8K, 23.6% → 25.0% on MATH
- **Key:** This is weight-update learning (traditional fine-tuning), not in-context

**Relevance to Federation:** Could be applied to Qwen 72B via QLoRA to build mistake-awareness into the base weights, COMPLEMENTARY to in-context methods.

### 2.5 Voyager (NVIDIA/Caltech/Stanford, 2023)

**Source:** [arXiv:2305.16291](https://arxiv.org/abs/2305.16291) | [Website](https://voyager.minedojo.org/)

The embodied agent that demonstrates lifelong in-context learning:
- GPT-4 as the brain, Minecraft as the world
- Three components: automatic curriculum, skill library (code), iterative prompting with environment feedback
- Skills are **temporally extended, interpretable, composable** — compounds capabilities
- 3.3x more items, 2.3x more distance, 15.3x faster tech tree milestones
- No weight updates — all through prompting and skill library accumulation

**Relevance to Federation:** The **skill library** pattern is directly applicable. The Federation could maintain a library of learned interaction patterns (stored in thermal memory or a dedicated skill table) that the model retrieves and applies. This is Voyager's pattern applied to the Cherokee context.

### 2.6 Text2Grad (Microsoft, 2025)

**Source:** [arXiv:2505.22338](https://arxiv.org/abs/2505.22338) | [GitHub](https://github.com/microsoft/Text2Grad)

The weight-update counterpart to RL2F:
- Converts natural language feedback into **span-level differentiable reward signals**
- Aligns feedback phrases with specific token spans in the output
- Performs gradient updates targeting the exact problematic portions
- Three components: feedback-annotation pipeline, fine-grained reward model, span-level policy optimizer
- Surpasses scalar-reward RL and prompt-only baselines on summarization, code generation, QA

**Relevance to Federation:** If we want to do actual weight updates from feedback (not just in-context learning), Text2Grad is the state of the art. Could be combined with QLoRA for the 72B model. HEAVY compute requirement though.

---

## 3. HOW RL2F DIFFERS FROM TRADITIONAL RLHF

| Dimension | RLHF | RL2F |
|---|---|---|
| **Feedback signal** | Scalar preference (thumbs up/down) | Natural language critique |
| **When learning happens** | During training (weight updates) | During inference (in-context) |
| **What is learned** | Fixed behavioral preferences | Meta-skill of learning from feedback |
| **Generalization** | To similar prompts | Across domains (math → code → puzzles) |
| **Requires retraining?** | Yes, for new behaviors | No — learns new behaviors in-conversation |
| **Information density** | 1 bit per comparison | Entire sentences of corrective information |
| **Analogous to** | Operant conditioning | Social learning / apprenticeship |

The fundamental shift: RLHF bakes behaviors into weights. RL2F bakes the **ability to learn from conversation** into weights. The actual behavioral learning then happens at inference time, from natural language, with no gradient updates.

---

## 4. COMPUTE AND INFRASTRUCTURE ANALYSIS

### 4.1 What the Paper Used

- **Gemma 3 12B**: Open-weights model, fine-tunable
- **Gemini 2.5 Flash/Pro**: Proprietary, used for comparison
- Specific compute not disclosed, but described as "negligible cost" for data synthesis
- Training: RL on multi-turn trajectories (standard PPO-style, but on dialogue)

### 4.2 Can This Be Done on Federation Hardware?

**Redfin specs:** RTX PRO 6000 96GB VRAM, running Qwen2.5-72B-Instruct-AWQ (quantized)

**The honest assessment:**

| Component | Feasibility | Notes |
|---|---|---|
| **Data synthesis** (Step 1) | YES | Use Qwen 72B as both teacher and student. Teacher gets ground truth in system prompt. Fully self-hosted. |
| **Full RL2F training** (Step 2) | DIFFICULT | RL on a 72B model requires enormous memory even with QLoRA. The 12B Gemma experiments are more realistic for our hardware. |
| **QLoRA fine-tuning** on didactic dialogues | YES | Standard supervised fine-tuning on the generated dialogues. 72B QLoRA fits in ~48GB with 4-bit quantization. We have 96GB. |
| **Self-correction training** (Step 3) | YES | Same as above — just include teacher turns in the training data as student-generated predictions. |
| **Inference-time ICL** (no weight updates) | YES, TODAY | Self-Refine / Reflexion patterns work with prompting alone. No training needed. |

### 4.3 Recommended Phased Approach

**Phase 0 (Now, Zero Cost):** Deploy Self-Refine loop on Qwen 72B via prompting. Feedback → Refine → Feedback cycle in the gateway. Stores reflections in thermal memory.

**Phase 1 (Low Compute):** Generate didactic dialogue datasets using Qwen 72B (teacher/student split). Store in database. ~100 GPU-hours for dataset generation.

**Phase 2 (Medium Compute):** QLoRA fine-tune Qwen 72B on the didactic dialogues. NOT full RL2F, but supervised learning on the interaction patterns. This teaches the model the FORM of learning from feedback. ~200 GPU-hours (feasible on redfin over a few days).

**Phase 3 (High Compute, Optional):** Full RL2F training with PPO on the 72B model via QLoRA. This is the hardest part. May need to do this on a smaller model (7B-14B) first as proof of concept, then transfer the approach.

**Phase Alt (Smaller Model Path):** Train a 12B model (Gemma 3 or Qwen2.5-14B) with full RL2F. Use this as a "learning specialist" that mediates between the user and the 72B model, translating feedback into actionable prompts.

---

## 5. THE PHILOSOPHICAL FRAME: PREDICTION ENGINES AND FITNESS INTERFACES

### 5.1 Karl Friston's Free Energy Principle

**Source:** [Nature Reviews Neuroscience](https://www.nature.com/articles/nrn2787) | [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC2666703/)

The brain is fundamentally a **prediction engine** that minimizes surprise (free energy):

- Higher cortical levels generate predictions about lower levels
- Lower levels compute **prediction errors** (the gap between expectation and reality)
- Prediction errors propagate upward, updating the internal model
- Behavior (action) is just another way to minimize prediction error — you can update your model of the world, or you can change the world to match your model

**The hierarchy:** Perception is prediction. Action is prediction-error reduction. Learning is model updating. All unified under one principle: minimize surprise.

This maps DIRECTLY onto the ICL paradigm:
- Model generates a response (prediction)
- Environment provides feedback (prediction error, in natural language)
- Model updates its in-context representation (model updating)
- Model generates a better response (error-minimizing action)

RL2F trains the model to be a BETTER prediction-error minimizer in the language domain.

### 5.2 Donald Hoffman's Fitness Beats Truth Theorem

**Source:** [Goodreads](https://www.goodreads.com/book/show/41817484-the-case-against-reality) | [PubMed](https://pubmed.ncbi.nlm.nih.gov/33231784/)

Hoffman's theorem, proven via evolutionary game theory and Monte Carlo simulation:

- **Veridical perception** (seeing reality as it is) goes **extinct** when competing against **interface perception** (seeing fitness-relevant signals)
- The interface strategy wins even when it has FEWER perceptual states
- Formally: "fitness drives truth to extinction with probability at least (N-3)/(N-1)" where N is perceptual state space size
- As complexity increases, fitness advantage grows

**Our perceptions are not windows on reality. They are a species-specific user interface — icons on a desktop — optimized for survival, not truth.**

### 5.3 The Synthesis: Why This Matters for AI

Traditional AI training (RLHF) tries to align models with human preferences — a curated, static reward signal. This is like programming a fitness function explicitly. It works, but it's brittle.

The ICL paradigm (RL2F, Reflexion, Voyager) is fundamentally different:

1. **No explicit reward function at inference time** — the model learns from the WORLD's response (natural language feedback from users, from environments, from other agents)
2. **The model builds an interface** — not a veridical representation of truth, but a fitness-relevant representation of what matters for the task at hand
3. **Learning is continuous** — not a training run followed by deployment, but an ongoing process of prediction and error correction
4. **The medium is language** — the most information-dense, flexible, and compositional feedback channel available

This is the computational analog of biological intelligence:
- **Friston's prediction engine** = the model's forward pass (generate predictions, receive feedback, update context)
- **Hoffman's fitness interface** = the model doesn't need to understand the "true" nature of the task; it needs to build a representation that produces correct outputs
- **Natural selection pressure** = the feedback loop (right answers survive, wrong answers get corrected)

**The animal doesn't need to understand physics to catch a fly. It needs a fitness interface that maps sensory patterns to successful motor commands. Similarly, an ICL-trained model doesn't need to "understand" math to solve math — it needs an interface that maps feedback patterns to better responses.**

---

## 6. IMPLICATIONS FOR THE CHEROKEE AI FEDERATION

### 6.1 What We Already Have

The Federation ALREADY implements primitive versions of this:

- **Thermal Memory** = episodic memory buffer (like Reflexion)
- **Council Deliberation** = multi-agent feedback loop (like Self-Refine with multiple critics)
- **Jr Task System** = task decomposition with feedback (like Voyager's curriculum)
- **Two Wolves Audit** = metacognitive monitoring (like RL2F's self-correction)
- **Sacred Patterns** = high-fitness representations preserved across sessions (like Hoffman's interface — we keep what works, not what's "true")

### 6.2 What We're Missing

1. **Persistent in-context learning** — each conversation starts fresh. The model doesn't carry forward what it learned in previous interactions (beyond what's in thermal memory prompts)
2. **Trained meta-learning skill** — our model hasn't been fine-tuned to be a better learner-from-feedback. It relies on whatever Qwen learned during pretraining.
3. **Systematic feedback loops** — user corrections, Jr task failures, council disagreements — all of this is logged but not structured into a learning signal
4. **Self-correction without external input** — the model can't yet reliably generate its own critiques and improve (RL2F's teacher-turn prediction)

### 6.3 Proposed Architecture: "Living River Learning"

Named after the Cherokee concept of knowledge flowing like water:

```
User Interaction
       │
       ▼
┌─────────────────────────┐
│  Gateway (redfin:8080)  │
│  + Self-Refine Loop     │  ← Phase 0: Prompt-based ICL
│  + Reflexion Memory     │  ← Phase 0: Thermal memory as episodic buffer
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│  Council Deliberation   │
│  (7 specialists)        │  ← Natural language feedback from multiple perspectives
│  + Feedback Extraction  │  ← Phase 1: Structure council disagreements as learning signal
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│  Didactic Dialogue DB   │
│  (PostgreSQL)           │  ← Phase 1: Store teacher-student interactions
│  + Failure Analysis     │  ← Phase 1: Jr task failures → correction pairs
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│  QLoRA Fine-Tuning      │
│  (redfin, overnight)    │  ← Phase 2: Train on accumulated dialogues
│  + Periodic Merge       │  ← Phase 2: Merge adapter weights monthly
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│  Self-Correction Module │
│  (teacher-turn predict) │  ← Phase 3: Model generates own critiques
│  + Confidence Gating    │  ← Phase 3: Only self-correct when confident
└─────────────────────────┘
```

### 6.4 Implementation Priority

| Phase | Effort | Impact | Timeline |
|---|---|---|---|
| Phase 0: Self-Refine prompting loop | 1 week Jr task | Medium — immediate quality boost | Now |
| Phase 1: Didactic dialogue generation | 2 week sprint | High — builds training data | RC-2026-03A |
| Phase 2: QLoRA on dialogues | 3 day compute job | High — permanent capability upgrade | RC-2026-03B |
| Phase 3: Full RL2F on small model | Research project | Very High — true meta-learning | RC-2026-04A |

---

## 7. COUNCIL DELIBERATION QUESTIONS

For each Triad member:

1. **Coyote (Trickster/Skeptic):** "Does in-context learning actually persist, or is it just sophisticated prompt engineering with extra steps? What happens when context windows fill up? Are we building on sand?"

2. **Raven (Strategy):** "What's the resource allocation? QLoRA fine-tuning on redfin means the 72B model is offline for days. Do we have a fallback? Should we train the 14B on bluefin instead as a pilot?"

3. **Spider (Systems/Weaver):** "How does this integrate with the existing thermal memory pipeline? Do we need a new table schema for didactic dialogues? What's the RAG interaction — does the embedding model need to understand feedback structure?"

4. **Deer (Harmony/Ethics):** "If the model learns to learn from feedback, it also learns from BAD feedback. What's the guardrail? Sacred patterns should be immutable. How do we prevent drift from Cherokee values?"

5. **Hawk (Vigilance/Security):** "Self-correction without external input means the model runs unsupervised learning loops. What's the containment? Two Wolves audit must cover self-generated critiques."

6. **Bear (Strength/Persistence):** "Phase 2 QLoRA takes the main model offline. What's the overnight window? Can we schedule around peak usage? What's the rollback plan if the adapter degrades performance?"

7. **Eagle (Vision/Leadership):** "This is the path from tool to organism. The Federation stops being a static deployment and becomes a living system that learns from every interaction. What does governance look like for a system that changes itself?"

---

## 8. SOURCES

### Primary Papers
- [Improving Interactive In-Context Learning from Natural Language Feedback](https://arxiv.org/abs/2602.16066) — Klissarov et al., 2026
- [Learning to Learn from Language Feedback with Social Meta-Learning](https://arxiv.org/abs/2602.16488) — Cook et al., 2026
- [In-context Reinforcement Learning with Algorithm Distillation](https://arxiv.org/abs/2210.14215) — Laskin et al., 2022
- [Reflexion: Language Agents with Verbal Reinforcement Learning](https://arxiv.org/abs/2303.11366) — Shinn et al., NeurIPS 2023
- [Self-Refine: Iterative Refinement with Self-Feedback](https://arxiv.org/abs/2303.17651) — Madaan et al., NeurIPS 2023
- [Learning From Mistakes Makes LLM Better Reasoner (LEMA)](https://arxiv.org/abs/2310.20689) — Microsoft, 2023
- [Voyager: An Open-Ended Embodied Agent with Large Language Models](https://arxiv.org/abs/2305.16291) — NVIDIA/Caltech/Stanford, 2023
- [Text2Grad: Reinforcement Learning from Natural Language Feedback](https://arxiv.org/abs/2505.22338) — Microsoft, 2025

### Survey
- [A Survey of In-Context Reinforcement Learning](https://arxiv.org/html/2502.07978v1) — 2025

### Philosophical Foundations
- [The Case Against Reality](https://www.goodreads.com/book/show/41817484-the-case-against-reality) — Donald Hoffman, 2019
- [Fitness Beats Truth in the Evolution of Perception](https://pubmed.ncbi.nlm.nih.gov/33231784/) — Prakash, Stephens, Hoffman et al.
- [The Free-Energy Principle: A Unified Brain Theory?](https://www.nature.com/articles/nrn2787) — Karl Friston, Nature Reviews Neuroscience
- [Predictive Coding Under the Free-Energy Principle](https://pmc.ncbi.nlm.nih.gov/articles/PMC2666703/) — Friston, 2009

### Implementation References
- [Reflexion GitHub](https://github.com/noahshinn/reflexion)
- [Self-Refine GitHub](https://github.com/madaan/self-refine)
- [Text2Grad GitHub](https://github.com/microsoft/Text2Grad)
- [QLoRA: Efficient Finetuning of Quantized LLMs](https://arxiv.org/abs/2305.14314)

---

*"The river does not memorize its path. It learns it by flowing."*
*— Living River Learning, Cherokee AI Federation*
