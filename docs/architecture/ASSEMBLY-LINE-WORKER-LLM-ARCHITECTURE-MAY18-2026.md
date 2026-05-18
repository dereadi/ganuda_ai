# Assembly-Line Worker LLM Architecture — Design Doc

**Filed:** 2026-05-18 ~13:10 CDT
**Author:** Stoneclad (TPM) under Partner directive ("how our assembly worker LLMs will be set up")
**Status:** DESIGN — for Council vote. NOT yet authorized for build.
**Substrate:**
- `RESEARCH-MINI-MODEL-WORKFORCE-COHERENCE-MAY17-2026.md` — research synthesis (3 Rings + 3 tools first cohort)
- `LONGHOUSE-MICRO-JR-RING-ROLE-TAXONOMY-MAY17-2026.md` — 26-Ring vision (revised)
- `KB-DARK-FACTORY-MAY18-2026-PM-FIVE-FAILURE-SHAPES-THREE-DEFENSES.md` — empirical failure-shape data
- `reference_mini_llm_assembly_line_github_substrate_may18_2026.md` — Lightning-AI/litgpt + FareedKhan 2.3M-param substrate
- `project_duplo_jr_layer_extension_may17_2026.md` — Sunday-night architectural recognition
- Patent #6 (Duplo-native governance + Necklace architecture)

## Why this design doc exists now

Sunday: Partner proposed 26-Ring assembly-line architecture. Sunday-night research collapsed to 3 Rings + 3 tools with "is there a spec?" heuristic. Monday's dark factory empirically validated the heuristic: **4 of 5 failure shapes were solved by deterministic tools (T1), not models.** The 5th was architectural (cross-gen asymmetry). **No failure shape has yet required a Tier-2 specialist Ring** — but Coyote-discipline says: design now so we can deploy when failure-shape pressure justifies it, not before.

This doc concretizes the worker setup so the federation knows EXACTLY how to ship Tier-2 Rings when Shape 6+ emerges.

## The four tiers (derived from today's empirical findings)

| Tier | Compute class | Examples | Substrate path | Cost per call | Latency target |
|---|---|---|---|---|---|
| **T0 — Architectural** | code (no model) | unified verifier across Gens, R-dispatcher, R-registry | Standard Python | ~0 | <10ms |
| **T1 — Tools (deterministic)** | code (no model) | `verify_file_exists`, `detect_placeholder_stub`, `detect_truncated_execution`, `find_backup`, `surgical_restore`, `quarantine` | Standard Python in `lib/duplo/` | ~0 | <10ms |
| **T2 — Specialist Rings (small LLM)** | 100M-3B params, fine-tuned | R28 stub-detector, R29 task-vs-output-alignment, R30 semantic-novelty-detector | Lightning-AI/litgpt + LoRA on Phi-3-mini / SmolLM-1.7B / Qwen2-1.5B | ~$0.0001 | <100ms |
| **T3 — Mid-tier Inspector** | 8-32B params | R27 audit-emitter, code-writer-Ring, doc-writer-Ring | Lightning-AI/litgpt + LoRA on Llama-3-8B / Phi-3-medium | ~$0.005 | <2s |
| **T4 — Pendant (rare)** | 70B+ | architecture-Ring, council-deliberation-Ring | Existing: Qwen3-30B-A3B on redfin + Llama-3.3-70B on bmasass | ~$0.05 | <30s |

**Today's data confirms**: T1 handled 4/5 shapes. T0 handles the 5th. T2 is not needed YET. T3+T4 already exist.

## R28 stub-detector-Ring — the design proof-of-concept

The FIRST Tier-2 Ring the federation will need (when Shape 6 emerges).

### Purpose
Catch novel hallucination shapes that regex misses. Specifically: semantic stubs that LOOK like real work but contain no real investigation. Examples Coyote will likely produce as Jrs adapt:
- Paraphrased placeholders ("To be researched" instead of "(Awaiting X)")
- Plausible-but-empty conclusions ("Analysis complete; findings detailed above" with nothing above)
- Cited-but-irrelevant content (real grep output but on the WRONG file)

### Model selection (Coyote heterogeneity requirement)
- **Base:** Phi-3-mini (3.8B) — Microsoft, text-heavy training, classification-friendly
- **Alternative:** Qwen2-1.5B (lighter, faster, sufficient for binary classification)
- **NOT:** SmolLM (text generation, weaker on classification)
- **Backup specialist (paired Ring):** SmolLM-1.7B for cross-validation (Coyote pairing requirement — different base model for true redundancy)

### Training pipeline (Lightning-AI/litgpt path)
```
Step 1: Curate data
- Positive (stub): 5 forensics artifacts from today + 50 synthetic stub examples
- Negative (real): 50 real federation artifacts (KBs, audit docs, recovery_enzymes.py, etc.)
- Edge cases: 20 borderline (short-but-real, long-with-some-placeholders)

Step 2: LoRA fine-tune via litgpt
- litgpt finetune --recipe lora --model Phi-3-mini
- Adapter rank: 16 (small, fast)
- Training: 2-3 epochs on ~125 examples
- Hardware: redfin GPU (during off-hours) or bmasass M4 Max (daytime hardline 12-19h)

Step 3: Evaluate
- Held-out test: 20 examples (10 stub, 10 real)
- Target: precision >0.95, recall >0.85 (false-positives more costly than false-negatives)
- Compare against current regex defense (must improve, not regress)

Step 4: Deploy
- vLLM endpoint on redfin: http://redfin:8003/ring/r28-stub-detector
- OR: direct python call via Composer (lighter, no separate service)
- Input: {"artifact_text": "..."}
- Output: {"is_stub": bool, "confidence": 0.0-1.0, "reasoning": "..."}

Step 5: Wire into claim_verifier
- After regex defenses pass, call R28 as final check
- Cascade: T1 regex → T2 R28 → accept
- Fallback: if R28 endpoint down, T1 regex stands alone (graceful degradation)
```

### Latency budget
- Target: <100ms per artifact
- vLLM Phi-3-mini cold-start: ~500ms; warm: ~50-100ms for short input
- Acceptable per Gecko's perf-budget research

### Integration contract
- **Where**: `lib/duplo/registry.py` — register R28 like existing tools
- **Safety class**: `read` (verifier only, no writes)
- **Composer integration**: existing `compose_enzyme()` path works
- **Failure mode**: if R28 returns confidence <0.6, defer to operator (Eagle Eye review queue)

## R-dispatcher — the assembly-line router (T0 architectural layer)

### Purpose
Single entry point that routes verification/operation requests to the right Ring tier.

### Routing logic (deterministic, not ML)
```python
def dispatch_verification(request: Dict) -> Result:
    # T1 cascade first (deterministic, fast)
    for tool in T1_DETERMINISTIC_VERIFIERS:
        result = tool(request)
        if result.confident_fail:
            return result  # short-circuit on clear-fail

    # T2 (specialist Ring) only if T1 unanimous-pass
    if all_t1_passed and T2_ENABLED:
        r28_result = call_ring("r28-stub-detector", request)
        if r28_result.confidence > 0.85:
            return r28_result

    # T3 only if T1+T2 conflict OR high-stakes flag
    if request.high_stakes or t1_t2_conflict:
        r27_result = call_ring("r27-audit-emitter", request)
        return r27_result

    return aggregate(all_results)
```

### Why R-dispatcher is T0 not T2
The routing decision is deterministic (rule-based on tier outcomes). No semantic judgment needed. Per "is there a spec?" — this is a TOOL not a model.

## R-registry extension (extension of `lib/duplo/registry.py`)

### Current state
`ToolRegistry` has `register_tool(name, description, module_path, function_name, parameters, return_type, safety_class)` for Python-callable tools.

### Extension needed for model-backed Rings
Add a `register_ring()` method:
```python
def register_ring(
    name: str,
    description: str,
    base_model: str,           # e.g., "phi-3-mini"
    adapter_path: str,         # LoRA adapter on disk
    endpoint_url: Optional[str],  # vLLM endpoint OR None for in-process
    input_schema: Dict,        # JSON schema for input
    output_schema: Dict,       # JSON schema for output
    latency_p95_ms: int,       # SLA budget
    safety_class: str,
    paired_ring: Optional[str],  # Coyote redundancy pair
) -> None:
```

Backward-compatible — existing `register_tool()` keeps working for T1 tools.

## Deployment topology

### Per-node Ring placement (heterogeneity per Coyote)

| Node | Always-on | Tier | Rings |
|---|---|---|---|
| **redfin** | ✅ | T2/T3 | R28 (Phi-3-mini), R27 (Qwen2-1.5B), code-writer (Llama-3-8B). vLLM endpoint :8003 |
| **bmasass** | Daytime only (until 19:00) | T3/T4 | doc-writer (Qwen3-30B-A3B), pendant tier (Llama-3.3-70B). vLLM endpoint :8001 |
| **bluefin** | ✅ | none | PostgreSQL only — no Rings hosted |
| **greenfin** | ✅ | T1 | embed-text tool (existing); no model Rings |
| **sasass** | ✅ | none | Mac mini, no GPU |
| **sasass2** | ✅ | none | Munki server only |

**Constraint per `reference_bmasass_standalone_mobile_mode_may2026.md`**: bmasass goes mobile after 19:00. Always-on Rings (R28, R27) MUST live on redfin. bmasass hosts ON DEMAND or higher-tier-rare-invocation Rings.

### Fallback path when bmasass mobile
- T4 pendant calls during evening route to redfin's Qwen3-30B-A3B (smaller model, may degrade quality)
- Or to API-tier (Anthropic Claude API) when stakes justify cost
- Council-deliberation-Ring (T4) currently uses specialist_council.py via API — that path works regardless

## Training infrastructure

### Hardware budget
- redfin GPU: 24GB VRAM (existing). Fits Phi-3-mini training with LoRA + 4-bit quant.
- bmasass M4 Max: 128GB unified memory (daytime). Fits Llama-3-8B training with LoRA.
- No new hardware required for R28-R30 (Tier-2 Rings).

### Training cadence
- Initial: 1-2 weeks per Ring (curate + train + evaluate + deploy)
- Re-training: when failure-shape data shifts >10% (per drift_observer)
- Periodic: monthly evaluation on held-out test set

### Data discipline
- All forensics artifacts (from dark factory + future canary runs) go into `/ganuda/data/ring_training/` per Ring
- Curation: TPM-inline or Council-vote-gated for high-stakes Rings
- Version control: training data + adapter + eval results all in git

## Evaluation framework

### Per-Ring CI gate
Every Ring has:
1. Held-out test set in `/ganuda/data/ring_eval/<ring-name>/`
2. CI run via `pytest tests/test_ring_<name>.py` that:
   - Loads the trained adapter
   - Runs against test set
   - Asserts precision/recall thresholds
   - Compares against previous adapter version (no regression)
3. Council-vote required to deploy adapter that regresses any metric

### Federation-wide metrics
- Per-Ring invocation count, latency P95, accuracy on rolling test
- Surfaced via existing observability stack (Conway-Smith Phase 1 instrumentation)
- Medicine Woman alerts on Ring drift (precision drop >5%)

## How this connects to today's findings

| Today's finding | Architecture answer |
|---|---|
| 4 of 5 shapes solved by T1 tools | T1 in `lib/duplo/recovery_enzymes.py` + `claim_verifier.py` already shipped |
| Cross-gen asymmetry (Shape 5) | T0 architectural: unified verifier path (Gen 1 hardening) |
| Adversarial coevolution between Jr + verifier | T2 R28 ready-to-deploy when Shape 6 emerges |
| Lightning-AI/litgpt substrate from Partner | Tier-2/3 training pipeline canonical |
| FareedKhan 2.3M-param reference | Reflex-tier (sub-100M) capability proof — could be R28 floor if Phi-3-mini overkill |
| Coyote heterogeneity dissent | Per-Ring pairing requirement (R28 Phi-3-mini + R28-pair SmolLM-1.7B) |
| Eagle Eye Inspector pattern (R27 from Longhouse) | T3 inspector tier — already in design |
| jr_observer.py (Adaptive Resonance Theory) deployed today | Provides the failure-shape detection that triggers Ring training |
| Patent #6 Duplo-native governance | This entire architecture IS Patent #6 substrate |

## When to BUILD each Ring (gating criteria)

| Ring | Build when | Cost when deployed | Defer until |
|---|---|---|---|
| R28 stub-detector | Shape 6 emerges (regex-evading novel stub) | 1-2 weeks TPM-inline + training | Justified by observed failure |
| R27 audit-emitter | Council vote on Day 2 of jr_observer integration | 2-3 weeks + Council vote | Day 2 jr_observer matures |
| R29 task-vs-output-alignment | Mode D research-pipeline failure has not been root-caused | 3-4 weeks + Council vote | Research-Jr fix shipped (then re-evaluate) |
| R-dispatcher T0 | Before deploying ANY Tier-2 Ring (prerequisite) | 1 week TPM-inline | When R28 training begins |

## Coyote-dissent checks (Sunday's research integrated)

1. **Different base models per pair** ✓ — R28 Phi-3-mini paired with R28-pair SmolLM
2. **Benchmark before sizing** ✓ — Training pipeline runs eval before deploy
3. **Start with 4-6 Rings not 26** ✓ — Current first-cohort: R28 + R27 + R-dispatcher only
4. **Falsification test per Ring** ✓ — Eval threshold defines "this Ring shouldn't exist"
5. **Cross-gen state-conflict** ✓ — R-dispatcher is the unified verifier path (solves Shape 5)

## Open questions reserved for Council vote

1. **R28 build timing** — build now (before Shape 6 emerges) or wait for evidence?
2. **Base model approval** — Phi-3-mini (Microsoft telemetry concerns?) vs Qwen2-1.5B (Chinese) vs Llama-3.2-1B (Meta) vs SmolLM-1.7B (HuggingFace)
3. **vLLM endpoint vs in-process** — separate service (operational overhead) vs python call (slower cold-start)
4. **Forensics-data sharing** — federation-internal vs open-source training data (Patent #6 trade-secret tension)
5. **Adapter versioning** — git-LFS vs separate model-registry service
6. **Pairing semantics** — when R28 + R28-pair disagree, who breaks the tie? (Eagle Eye Inspector? Council escalation?)

## Council vote recommendation

**Propose Option A: Build R-dispatcher first (T0 prerequisite, 1 week), then defer R28 until Shape 6 evidence.**

Reasoning:
- R-dispatcher unblocks ALL future Ring deployment + ends Shape 5 (cross-gen asymmetry)
- Per "is there a spec?" + "don't pre-build" discipline, R28 stays designed-but-unbuilt until failure pressure justifies
- Walmart pitch becomes stronger: "we have the architecture designed and one Ring at proof-of-concept stage; we'll deploy when our own failure observatory tells us it's needed"

## Lineage

- Patent #6 (Duplo-native governance) — this design IS Patent #6 instantiation
- COUNCIL-VOTE-JR-MAKE-IT-RIGHT-MAY18-2026 — Day 2/3/4 sequence integration
- LONGHOUSE-MICRO-JR-RING-ROLE-TAXONOMY — original 26-Ring vision
- RESEARCH-MINI-MODEL-WORKFORCE-COHERENCE — research-validated revision to 3+3 first cohort
- KB-DARK-FACTORY-MAY18-2026-PM — empirical justification for tier model
- reference_mini_llm_assembly_line_github_substrate — Lightning-AI/litgpt + FareedKhan substrate
- feedback_research_validates_before_architecture_revision_may17_2026 — discipline ratifying this design pacing
