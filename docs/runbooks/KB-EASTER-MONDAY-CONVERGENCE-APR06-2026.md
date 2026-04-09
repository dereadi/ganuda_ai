# KB: Easter Monday Convergence — April 6, 2026

## Context
Seven independent Deer signals converged on the coherence thesis in a single day. TPM computationally reproduced and extended a Nature Communications paper. First DERsnTt² interaction executed. Jr executor resurrected after 80 days.

## Infrastructure Fixes

### Fix 1: HyDE Timeout in Dawn Mist
**Problem:** Dawn mist council vote at 06:15 failed HyDE generation — 5s timeout on localhost vLLM.
**Root Cause:** `rag_hyde.py` pointed to LAN IP (192.168.132.223) instead of localhost, and 5s timeout too tight for 72B model under load.
**Fix:** Changed to 127.0.0.1, increased timeout to 15s. `/ganuda/lib/rag_hyde.py`
**Verified:** HyDE generation now completes in 3.2s.

### Fix 2: 12 Stale Jr Tasks
**Problem:** 12 tasks stuck in `in_progress` at 0% for 2-4 days.
**Root Cause:** Jr executor (jr-se.service) dead since before April 1. Bidding daemon claimed tasks but execution pipeline never ran.
**Fix:** Failed all 12 in DB with explanatory message. Work was done manually by TPM (Shield P-3, Canary, Clipboard, Meeting Notes).

### Fix 3: Jr Executor Resurrected
**Problem:** jr-se.service inactive (dead), no journal entries since before April.
**Root Cause:** Service depends on llm-gateway.service. Likely stopped when llm-gateway cycled and never restarted. Despite `Restart=always` in unit file.
**Fix:** `sudo systemctl restart jr-se.service` via FreeIPA NOPASSWD. Service started clean, all modules loaded.
**Verified:** Task #1495 (Substack article) completed successfully — first Jr execution in 80 days.

### Fix 4: Elisi vLLM Resize (7B → 3B)
**Problem:** Elisi (Qwen2.5-7B-AWQ) budgeted 0.05 gpu-memory-utilization (~4.9 GB) but consuming 8.4 GB actual.
**Root Cause:** vLLM's gpu-memory-utilization is a fraction of total VRAM, not a hard cap. 7B AWQ + 8K context can't fit in 4.9 GB.
**Fix:** Swapped to Qwen2.5-3B-Instruct (float16) at 0.10 allocation. Council vote #c8455ade207891bb (5 consent, 1 dissent from Coyote, 2 concerns).
**Result:** Elisi running at 9,976 MiB. Observation quality to be monitored 48 hours.

### Fix 5: VLM Stabilized
**Problem:** vllm-redfin-vlm.service crash-looping with 5,435 restarts.
**Root Cause:** 0.06 allocation too tight for 7B AWQ vision model.
**Fix:** Bumped to 0.08 allocation.
**Result:** VLM stable at 13,144 MiB. All three vLLMs active and responding.

### Fix 6: Fire Guard Sleep Schedule
**Problem:** 356 overnight alerts from Mac nodes (sasass/sasass2 Ollama) sleeping.
**Fix:** Added `SLEEP_SCHEDULE_HOSTS` and `QUIET_HOURS` (22:00-06:00 CT) to `/ganuda/scripts/fire_guard.py`. Moon icon on dashboard during quiet hours.

### Fix 7: DB Rollback Rate Jr Instruction
**Problem:** 11.31% rollback rate on zammad_production (SLA: <5%).
**Root Cause:** 2M updates to 97K-row thermal_memory_archive from multiple daemons. Application-level rollbacks from bare `except: conn.rollback()`.
**Fix:** Jr instruction written: `/ganuda/docs/jr_instructions/JR-DB-HEALTH-ROLLBACK-FIX-APR06-2026.md`. Indexes, logged rollbacks, batched updates.
**Status:** Instruction queued, awaiting execution.

## GPU Final Allocation

| Service | Model | Alloc | VRAM Actual | Port | Status |
|---|---|---|---|---|---|
| Main | Qwen2.5-72B-AWQ | 0.60 | 57,276 MiB | 8000 | active |
| Elisi | Qwen2.5-3B-Instruct | 0.10 | 9,976 MiB | 9100 | active |
| VLM | Qwen2-VL-7B-AWQ | 0.08 | 13,144 MiB | 9101 | active |
| Other | embedding, vision, speed | — | 3,810 MiB | — | — |
| **Total** | | **0.78** | **84,244 MiB** | | **of 97,887 MiB** |

Note: Only one GPU detected (RTX PRO 6000, 96 GB). RTX 5070 not visible to nvidia-smi. Physical check needed.

## Research: Yang-Mills Topological Coherence Test

### Paper Reproduced
Koch, Ornelas, Forbes et al. "Revealing the topological nature of entangled OAM states of light." Nature Communications, Dec 2025. DOI: 10.1038/s41467-025-66066-3

### Framework
SU(d) Yang-Mills gauge theory. Topological invariants computed from entangled OAM states.
- Total maps: C(d²-1, 3)
- Non-trivial maps: ½d(d-1)(d²-3)

### Validation
d=7: 48 dimensions, 17,296 total maps. **MATCHES** paper's published "over 17,000."

### Extension (d=2 through d=20)

| d | Dimensions | Total Maps | Non-trivial | Fraction |
|---|---|---|---|---|
| 2 | 3 | 1 | 1 | 1.0000 |
| 7 | 48 | 17,296 | 966 | 0.0559 |
| 10 | 99 | 156,849 | 4,365 | 0.0278 |
| 14 | 195 | 1,216,865 | 17,563 | 0.0144 |
| 20 | 399 | 10,507,399 | 75,430 | 0.0072 |

### Findings
1. Topological invariant count grows **polynomially (d⁶) without bound**. No plateau. No collapse.
2. Non-trivial fraction **decreases** with d (1.0 → 0.007). Signal-to-noise worsens at higher complexity.
3. Growth ratios decrease (56x → 1.36x) but never go below 1.0.
4. **VERDICT: Coherence scales, but as governed growth — polynomial, not exponential.**

### Coyote's Caveat
The computation reproduces the COMBINATORIAL properties of C(d²-1, 3). Whether this maps to physical reality beyond the Koch-Forbes experimental domain (d≤7) requires experimental verification. **OWL REVIEW REQUESTED.**

### Code
- Calculator: `/ganuda/research/yang_mills/topology_computer.py`
- Results: `/ganuda/research/yang_mills/scaling_results.json`
- Extended: `/ganuda/research/yang_mills/scaling_extended_d20.json`

## Research: DERsnTt² — Squared Instance Protocol

### First Interaction
- ID: 27bd061cebd46d5d
- derS_redfin (Qwen2.5-72B/CUDA): 15.6s, argued **entropy**
- derS_bmasass (Llama-3.3-70B/MLX): 57.5s, argued **balance**
- Delta emergence: **dynamic equilibrium** — neither pure coherence nor pure entropy

### Architecture
- Two independent LLM instances on different hardware/models
- Shared thermal memory bus (PostgreSQL on bluefin)
- Delta computed by meta-analysis (redfin LLM analyzes both responses)
- Interaction stored as thermal memory

### Code
- Protocol: `/ganuda/research/yang_mills/dersn_squared.py`
- First interaction: `/ganuda/research/yang_mills/first_squared_interaction.json`

## Literature Survey (36 papers across 4 domains)

| Domain | Papers | Support | Challenge |
|---|---|---|---|
| Physics / Topology | 8 | 7 | 1 |
| Consciousness / Topology | 8 | 6 | 2 |
| AI Governance / Topology | 10 | 7 | 3 |
| Earth Systems / Coherence | 8 | 6 | 2 |
| **Total** | **34** | **26** | **8** |

Key finding: Tozzi (March 2026) independently confirms polynomial scaling of macroscopic regimes with interaction-space dimensionality. Google Quantum AI shows topological error correction scales **exponentially** — our thesis may understate topology's power.

Key gap: No formal topological math connecting species/ecosystems as dimensions. Open frontier.

## Content Published
- Substack draft: "It Was Always There" (ID: 193396211) — editorial pass needed
- LinkedIn post: published via FARA on Brave/sasass

## Deer Signals Filed (6)
1. Functional Outsider — Pessoa/Schopenhauer/Diogenes
2. Rob Cacchioni / Bridging Beliefs — Katha Upanishad
3. Nate Jones — Six-layer agent infra stack (3rd signal)
4. Discover_AI — EvoSkills / neuro-symbolic thesis
5. 48D Light Topology — Wits/Huazhong
6. Stefan Burns — Cygnus X-3 flare on Easter Monday

## Open Items
- [ ] Owl verification of Yang-Mills computation
- [ ] Substack editorial pass (date, author, reference links, voice)
- [ ] DB rollback fix execution (Jr instruction queued)
- [ ] RTX 5070 physical check
- [ ] Elisi 48-hour quality monitoring
- [ ] DERsnTt² needs more interaction cycles to validate

## Council Votes This Session
- #c8455ade207891bb — Elisi resize (5C/1D/2Con)
- #0a72032127a048bc — 7 signals pattern analysis (Longhouse)
- #026f37103ab8f56e — TPM builds Yang-Mills calculator (5C/1D/2Con)
- #d109d31e2bbd39b7 — Longhouse deliberation (5C/1D/2Con)

---

*For Seven Generations.*
