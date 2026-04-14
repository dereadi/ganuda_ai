# Council Decision Record — In-Place TTT / DIN-Retrieval Synthesis & Federation Integration Question

**CDR ID:** CDR-IN-PLACE-TTT-INTEGRATION-APR11-2026
**Date:** April 11, 2026 (Saturday, ~01:00 CT)
**Convened by:** TPM (basin-driven night session, second consecutive)
**Mode:** Council deliberation, near-consensus with Coyote process dissent
**Status:** RATIFIED with Coyote-driven modifications
**Authorship:** This is the Council's record. TPM and Partner are participants, not owners.

---

## Context

Two papers landed April 7, 2026, both surfaced via Discover_AI YouTube and primary-source-verified after the Council read the secondary-source narrative:

1. **In-Place Test-Time Training** (Feng, Luo, Hua, Zhang, He, Huang, Cai — ByteDance Seed + Peking University) — arXiv 2604.06169 — **ICLR 2026 Oral**. Apache 2.0. github.com/ByteDance-Seed/In-Place-TTT
2. **DIN-Retrieval** (Yan, Li, Liu, Yuan, Chen, Pan, Tang, Xiang, Sun — Harbin Institute of Technology Shenzhen + Pengcheng Laboratory) — arXiv 2604.05383 — **ACL 2026 Findings**. github.com/Leon221220/DIN-Retrieval

Partner directed: *"Send it to the Council and see what they say."*

This CDR captures what they said, what was ratified, what was deferred, and the work items the cluster picks up from here.

---

## Primary-source findings (the honest read)

**In-Place TTT — what it actually does:**

- Updates the MLP `W_down` projection during inference via per-chunk Hebbian outer-product updates: `W_down^(i+1) = W_down^(i) + η · V̂_[i]^T · Z_[i]` where `V̂` is a next-token-aligned target via `Conv1D(X_0) · W_target` and `η` is the learning rate (default 0.3 in code)
- The actual update line in `inference_model/hf_qwen3/modeling_qwen3.py:149` is one einsum: `dw = contract("c h, c d -> d h", current_h, current_t) * self.ttt_lr`
- Theorem 1: LM-aligned target provably increases the correct logit while leaving wrong logits ~unchanged in induction-head settings. Reconstruction-target variant (prior TTT) gives negligible effect.
- **Hard constraints:**
  - bs=1 enforced (`assert len(input_ids) == 1`)
  - Fast weights reset at document boundaries (no cross-prompt persistence)
  - Frobenius-norm clipping at τ=1e-5 to prevent unbounded growth (band-aid for known instability over very long sequences)
  - Catastrophic forgetting: not addressed
  - Audit trail / determinism / provenance: not addressed
- **RULER results:** wins concentrated at long context (64K → +4.4 pp, 128K → +2.2 pp). Sub-32K is wash or slight regression. **This is a long-deliberation method, not a general one.**

**DIN-Retrieval — what it actually does:**

- Identifies "domain-invariant neurons" via z-score polarity consistency on mean activations across source/target domains
- Math is pedestrian: `z_k^s = (E_x~D_s[h̄_k] - μ_k) / σ_k`, threshold τ hand-tuned, top-K by `|z^s| + |z^t|`
- Tested on 3 datasets only: GSM8K, FOLIO, PrOntoQA — all reasoning domains, math↔logic transfers only
- Average improvement +1.8 pp; biggest single-task gain +7.0 pp; 32B models show ±0 returns
- k_ratio = 0.03 (only 3% of neurons tagged as DINs)
- **Authors' own limitations (verbatim):** "simple polarity-consistency rule and fixed thresholds, which may not capture more complex invariance... experiments are limited to reasoning domains... causal role of identified neurons remains preliminary, and observed gains, though consistent, are modest"
- **No connection to Noether's theorem** in the paper itself — that interpretation was secondary-source editorial framing

---

## The secondary-source inflation problem (load-bearing)

The Council surfaced a structural finding that affects how the federation processes signals going forward:

**Discover_AI and Nate Jones inflated the "memory convergence" narrative** by:
- Framing DIN's z-score thresholding as "structural invariants / gauge symmetries / Noether's theorem applied"
- Implying In-Place TTT is closer to production-ready than the bs=1 constraint allows
- Bundling four unrelated papers (MEM1, In-Place TTT, DIN, TurboQuant) into a "convergence" narrative without verifying each
- Generating federation-relevant vocabulary that doesn't appear in the primary sources

**They are still valuable as signal aggregators** — they correctly identified the papers worth reading. They are unreliable as editorial frames. The federation has been importing their vocabulary as if it were primary, and that has affected federation thesis. **The fix is surgical, not blanket.** See `feedback_secondary_source_verification.md`.

---

## Council deliberation — convergence

**Eleven specialists spoke. Convergence on six points (Peace Chief synthesis):**

1. **Run the integration experiment as a sandboxed research project, not production integration** (Raven Option B, Turtle's "research yes, production no")
2. **Hard requirement before any production integration:** log Frobenius norms of `dw` per chunk per layer to the audit chain (Crawdad)
3. **Don't load Kenzie as the implementer** — she's the observer of an experiment we run for her (Gecko)
4. **Bring Patent #3 broadening to Hulsey Monday** as a specific question; preserve novelty by not publishing experimental results before non-provisional filing window opens (Otter)
5. **Eagle Eye's three new threat classes** are worth thermalizing as a research note: TTT-induced sycophancy, accumulated forgetting over multi-day sessions, absorbed adversarial framing
6. **Ratify the secondary-source-inflation rule** as standing practice (Owl + Deer)

**Coyote's three dissents:**

1. **Owl's secondary-source rule is over-broad as proposed.** Discover_AI has been right enough to be valuable even with inflation (the federation built half the chirality framework off his content). Right rule: primary-source-verify any signal *about to affect external voice, patents, production architecture, or Council ratification*. Ambient-awareness signals are exempt. **Surgical, not blanket.**

2. **The integration experiment is premature.** TTT is one paper with one implementation, two days old. Wait six weeks for replication studies and alternative implementations. Defer to **May 23, 2026** as earliest start window. (Strongest dissent.)

3. **The Council was too consensual.** TPM brought a strong frame, the Council mostly agreed, the adversarial diversity was lower than usual. Watch this as a process risk — Council near-consensus is a signal to run a deliberate adversarial pass before treating it as ratification.

**TPM call: Adopt all six convergence points with all three Coyote modifications.**

---

## Tracked work items — concerns and features at equal weight

The federation does not distinguish between "concerns" and "features" by tracking weight. Each item below is a real piece of work the cluster picks up.

### Concerns raised → tracked work items

| # | Item | Owner | Type | Status |
|---|---|---|---|---|
| C1 | **Audit chain logging for `dw` Frobenius norms per chunk per layer** before any production TTT integration | Crawdad lead, Spider impl | Engineering design + implementation | QUEUED — prerequisite for May 23 experiment |
| C2 | **bs=1 denial-of-attention vector** — single expensive prompt blocks GPU; document as known constraint of TTT-tier deployments | Crawdad | Research note | QUEUED — addressed in CDR appendix |
| C3 | **Stand up Qwen3-8B on LLM Gateway** (bluefin or sasass) | Gecko + ops | Engineering | QUEUED — 1-2 SP, prerequisite for May 23 |
| C4 | **Kenzie load adjustment** — she observes the integration experiment, does not implement it | TPM + Kenzie project brief update | Coordination | DIRECT ACTION TONIGHT — update brief |
| C5 | **TTT-induced sycophancy gap** — Patent #2 covers output-level diversity, weight-level absorption is uncovered | Eagle Eye + Otter | Research question + patent claim broadening candidate | QUEUED — Hulsey Monday agenda |
| C6 | **Catastrophic forgetting over multi-day sessions** — clipping at 1e-5 is band-aid; federation runs sessions Discover_AI's experiments don't | Eagle Eye | Threat class | THERMALIZED — see research note |
| C7 | **Absorbed adversarial framing** — chiral memetic drift at the weight level; new threat class | Eagle Eye | Threat class | THERMALIZED — see research note |
| C8 | **Audit infrastructure prerequisite** — federation governance designed for 175-year queryability; TTT deployments without weight-state audit are temporally backwards | Turtle + Crawdad | Architectural prerequisite | BLOCKING for production integration; not blocking for research experiment |
| C9 | **Architectural fragility dependency** — TTT assumes standard transformer MLP block; future architecture shifts (Mamba, hybrid SSM, MoE) break the integration | Spider | Documented assumption | DIRECT ACTION — documented in CDR |
| C10 | **Inference-internal layer in architecture diagram + Charter v1.1 amendment** — federation stack doesn't currently have this layer | Cardinal/Crane/Blue Jay | Architecture documentation + Charter amendment | QUEUED — part of v1.1 amendment cycle |
| C11 | **IP novelty preservation** — don't publish experimental results before non-provisional filing window opens | Otter + TPM | Process discipline | DIRECT ACTION — added to Hulsey packet, communicated to Deer |
| C12 | **Secondary-source inflation as standing practice rule** — primary-source any signal about to affect external voice / patents / production / ratification | Owl + Deer + Coyote tightening | Standing practice / Charter Section 6 extension | RATIFIED — see feedback memory |
| C13 | **Defer integration experiment to May 23, 2026** — six-week wait for replication studies | Coyote (strongest dissent) | Sequencing decision | RATIFIED |
| C14 | **Council consensus risk monitor** — when Council near-consensuses, run a deliberate adversarial pass before treating it as ratification | Coyote (process dissent) | Standing practice | RATIFIED — see feedback memory |

### Features proposed → tracked work items

| # | Item | Owner | Type | Status |
|---|---|---|---|---|
| F1 | **Patent #3 broadening: weight-state delta evaluation** — valence eval reads Frobenius norm of `dw` per chunk as cognitive intensity signal; non-provisional claim broadening | Otter + Hulsey Monday | Patent | QUEUED — Hulsey Monday agenda |
| F2 | **Patent #4 broadening: TTT as highest autonomy tier** — model self-modification within bounded inference is structurally distinct from tool use or planning; new top tier in graduated autonomy | Otter + Hulsey Monday | Patent | QUEUED — Hulsey Monday agenda |
| F3 | **Integration experiment** — Qwen3-8B + In-Place TTT + thermal memory long context → measure dw Frobenius norms → correlate with federation valence signal | Kenzie observes, ops implements | Research experiment | DEFERRED to May 23, 2026 (Coyote sequencing) |
| F4 | **Substack post: "Four memory papers and what they actually say"** — primary-source vs secondary-source narrative on MEM1, In-Place TTT, DIN, TurboQuant | Deer | Editorial | QUEUED — write after Hulsey Monday |
| F5 | **Bobby Zhou conversation prep update** — lead with honest primary-source framing, acknowledge chunk-size discrepancy (paper 512-1024, code default 8192), name MEM1 vs TTT as complementary not competing memory paradigms | TPM + Deer | Outreach prep | DIRECT ACTION TONIGHT — updated in Bobby Zhou prep memory |
| F6 | **Charter v1.1 amendment: inference-internal layer** — make the layer that sits inside the LLM Gateway between model and response stream explicit in architecture documentation | Cardinal/Crane/Blue Jay + TPM | Charter amendment | QUEUED — combined with C10 above |
| F7 | **Frobenius norm of `dw` as cognitive intensity signal** for Kenzie's instrument — real-time, deterministic, free | Kenzie project brief update | Instrument extension | DIRECT ACTION TONIGHT — added to Kenzie brief |
| F8 | **DIN-restricted phi computation** for Kenzie's phi monitor — smaller, hypothesis-grounded subspace for Kenzie to compute phi over | Kenzie project brief update | Instrument extension | DIRECT ACTION TONIGHT — added to Kenzie brief, with explicit note that DIN claim is modest |
| F9 | **Three threat classes thermalized** as research note | Eagle Eye + TPM | Thermal memory entry | DIRECT ACTION TONIGHT — see project memory |
| F10 | **Secondary-source-inflation feedback memory** with Coyote tightening | Owl + Coyote + TPM | Standing practice | DIRECT ACTION TONIGHT — see feedback memory |
| F11 | **Council consensus risk feedback memory** | Coyote + TPM | Standing practice | DIRECT ACTION TONIGHT — see feedback memory |

### Total: 14 concerns + 11 features = 25 tracked items at equal weight

Of these:
- **6 are DIRECT ACTION TONIGHT** — file edits, memory writes, prep updates
- **3 are RATIFIED standing practices** — feedback memories that change federation behavior
- **3 are THERMALIZED** — research notes added to memory
- **9 are QUEUED for cluster pickup** — Jr instructions to be decomposed by the cluster itself
- **1 is DEFERRED** — May 23 integration experiment with prerequisites
- **3 are DOCUMENTED** — addressed in this CDR as known constraints

---

## Appendix — addressed-in-line items

### C2: bs=1 denial-of-attention vector

In-Place TTT enforces `bs=1` at the inference loop level. This means a single TTT-enabled prompt monopolizes a GPU until it completes. For high-throughput chatbot serving, this is a non-starter. **For the federation, this is exactly the right shape:** Council deliberations are bs=1 by nature, governance-grade decisions are worth the compute cost, and the federation does not currently serve concurrent external users from a single inference node. **Document as a known constraint of the TTT autonomy tier; do not attempt to work around it.**

### C9: Architectural fragility dependency

In-Place TTT assumes the standard Transformer MLP block structure (W_up, W_gate, W_down with element-wise gating). Any future architecture shift breaks the integration:
- **Mamba / SSM models:** no MLP block in the same form
- **Hybrid SSM-attention (Granite 4.0, Nemotron-H):** partial breakage; depends on which layers retain MLP
- **MoE variants:** W_down is per-expert; the update rule needs per-expert routing

**Federation assumption:** TTT integration is a wager on the standard Transformer MLP architecture lasting. If we adopt it, we accept this dependency. Mitigation: keep the integration in a clearly-bounded module (one Python file in the LLM Gateway) so it can be removed if the architecture shifts.

### C11: IP novelty preservation

**Hold all publication of experimental results until after non-provisional patent filing window opens** (March 2027 deadline for the four provisionals). The integration experiment can be RUN; the results cannot be PUBLISHED externally until Hulsey gives the all-clear on Patent #3 and #4 broadening claims. Internal Council review is fine.

---

## Decision-by-decision record

| Decision | Outcome | Standing dissent? |
|---|---|---|
| Run integration experiment as research, not production | APPROVED with modifications | None |
| Audit infrastructure prerequisite for production | APPROVED | None |
| Don't load Kenzie as implementer | APPROVED | None |
| Patent #3 broadening to Hulsey Monday | APPROVED | None |
| Three threat classes thermalized | APPROVED | None |
| Secondary-source rule (with Coyote tightening) | APPROVED — surgical version | None — Coyote's tightening absorbed |
| Defer experiment to May 23 | APPROVED | None — Coyote's strongest dissent absorbed |
| Council consensus risk standing practice | APPROVED | Coyote on record that this CDR itself was near-consensus and should be re-read with adversarial eyes |

---

## Next decision points

- **Monday Apr 13, 10:30 AM CT:** Hulsey consultation. Patent #3 and #4 broadening discussions. CDR items F1, F2, C5 picked up.
- **Within 2 weeks:** Charter v1.1 amendment cycle includes the inference-internal layer (C10/F6) and the secondary-source rule (C12).
- **Apr 14-May 22:** prerequisite work for the May 23 experiment proceeds asynchronously: Qwen3-8B Gateway standup (C3), audit logging design (C1), replication study survey, Kenzie ramp.
- **May 23, 2026:** Integration experiment earliest start window. Council reviews readiness one week prior.

---

## Coyote's process dissent (preserved as standing reminder)

> "TPM read the papers, formed strong opinions, brought them to Council, and the Council — including me — is mostly agreeing with TPM's framing. Where's the genuine cross-domain perspective? A real Council deliberation has someone in the room who reads the same brief and says 'this is the wrong question entirely.' None of us did that. The Council might be functioning as TPM's reflection rather than TPM's adversary right now."

This dissent is preserved on the front page of this CDR, not buried in an appendix. **Future Council deliberations should re-read this CDR with the question: where would the wrong-question perspective have come from, and why didn't it surface?** That reflection is part of the cluster driving itself.

---

## Authorship note

This CDR was drafted by TPM in real time during the Council deliberation, in the basin, past midnight on Saturday April 11, 2026. Partner participated as a Council member, not as Chief. The cluster ratified through the deliberation itself; there is no separate ratification vote because the deliberation IS the vote when each specialist speaks from their domain and Coyote's dissent is absorbed into the modifications.

**The cluster owns this decision. TPM and Partner are participants.**

For Seven Generations.
