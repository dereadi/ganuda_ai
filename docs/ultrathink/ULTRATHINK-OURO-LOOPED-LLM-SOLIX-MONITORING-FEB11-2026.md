# ULTRATHINK: Ouro Looped LLMs + Solix 3800 Plus UPS Monitoring

**Date**: February 11, 2026
**Trigger**: Second power outage (Feb 10→11) + Ouro paper discovery
**Council Votes**: 2 deliberations completed
**Thermals**: #84024 (power outage), #84025 (Ouro discovery)
**Kanban**: #1763 (Solix monitoring), #1764 (Ouro evaluation)
**KB**: KB-OURO-LOOPED-LLM-FEDERATION-IMPACT-FEB11-2026.md

---

## Part 1: Ouro Looped Language Models — Third Scaling Axis

### What Is This

"Scaling Latent Reasoning via Looped Language Models" (arXiv:2510.25741) from ByteDance/NeuroDump introduces **looped transformers** — the same weights iterated 4x per token through an exit-gated loop. A 2.6B model matches 7-8B standard models. A 1.4B matches 4B. **2-3x parameter efficiency** through iteration, not expansion.

This is a **third scaling axis**: parameters, data, and now **loops**.

### Council Deliberation

**Vote**: PROCEED WITH CAUTION (confidence 0.889)
**Consensus**: Evaluate Ouro across all three GPU nodes.
**Concern**: Raven raised STRATEGY CONCERN — risk of adopting unproven architecture when Qwen 72B is stable and performing well.

### What We Found (Deep Dive)

**4 Model Variants Available** (Apache 2.0, Hugging Face):
| Model | HF Link | Matches |
|-------|---------|---------|
| Ouro-1.4B | ByteDance/Ouro-1.4B | ~4B standard |
| Ouro-2.6B | ByteDance/Ouro-2.6B | ~8B standard |
| Ouro-1.4B-Thinking | ByteDance/Ouro-1.4B-Thinking | ~4B reasoning |
| Ouro-2.6B-Thinking | ByteDance/Ouro-2.6B-Thinking | ~8B reasoning |

**Architecture** (Ouro-2.6B):
- 24 layers, 2048 hidden, SwiGLU, RoPE, Sandwich RMSNorm
- 49,152 vocab, 4K context (extendable to 64K)
- 4 recurrent steps (configurable via `total_ut_steps`)
- Adaptive exit via `early_exit_threshold` (default 1.0)

**Training**: 7.7T tokens across 4 stages (pre-training 6T → annealing 2.6T → long context 20B → mid-training 300B)

### Critical Integration Caveats

1. **vLLM: Adaptive exit NOT supported.** When running in vLLM, the model always executes full `total_ut_steps`. You get parameter efficiency but NOT dynamic compute allocation. This is the biggest limitation for our redfin deployment.

2. **transformers version pinned**: Requires `transformers < 4.56.0` (recommend 4.54.1). Compatibility issues with newer versions.

3. **GitHub code "Coming Soon"**: OuroHub GitHub org has NO public repos yet. Training/inference code not released. Only HF model weights available.

4. **No quantization variants published**: No AWQ, GPTQ, or GGUF. We'd need to quantize ourselves for memory-constrained deployment.

5. **Custom architecture**: Requires `trust_remote_code=True` — the looped transformer isn't in standard transformers library.

### Federation Node Analysis

#### Redfin — RTX PRO 6000 96GB Blackwell

**Current**: Qwen2.5-72B-Instruct-AWQ → 86GB VRAM, 32.4 tok/s
**Ouro option**: Ouro-2.6B-Thinking at FP16 ≈ ~6GB VRAM

**Honest assessment**: The 2.6B matches ~8B, not 72B. We'd be trading a 72B for an 8B-equivalent. That's a massive capability downgrade for the council. The parameter efficiency is impressive at the small model scale but doesn't yet challenge 72B-class models.

**Where Ouro DOES make sense on redfin**: As a **secondary model** alongside the 72B. With adaptive exit disabled in vLLM, we'd run it at 4 fixed loops. At ~6GB, it could co-exist with the 72B in the remaining 10GB of VRAM. Use case: fast pre-filtering, simple routing decisions, Jr task triage — anything that doesn't need 72B depth.

#### Bluefin — RTX 5070 12GB

**Current**: Qwen2-VL-7B-AWQ → 7.4GB VRAM (vision only, no text reasoning)
**Ouro option**: Ouro-1.4B or 2.6B as reasoning co-processor in remaining ~5GB

**This is the best fit.** Bluefin has zero text reasoning capability today. A 1.4B Ouro model (~3GB FP16, likely ~1.5GB INT4) would add reasoning alongside the VLM without displacing it. Even at 4B-equivalent performance, that's a new capability on a node that currently only does vision.

**Blocker**: No published quantized weights. We'd need to quantize Ouro-1.4B ourselves (AutoAWQ or similar). And vLLM won't give us adaptive exit, so we'd use raw transformers inference.

#### bmasass — M4 Max 128GB Unified Memory

**Current**: MLX DeepSeek-R1-Distill-Qwen-32B-4bit (~20GB)
**Ouro option**: Ouro-2.6B-Thinking via MLX

**Potential but unproven.** MLX would need a custom implementation for the looped architecture (exit gates, recurrent steps). No MLX port exists. The DeepSeek-R1-32B is a proven reasoning model. Replacing it with an unproven 8B-equivalent is Raven's strategy concern materialized.

**Better play**: Wait for larger Ouro models (14B, 32B) or MLX community port. Keep DeepSeek-R1 as primary.

### Recommended Evaluation Strategy

**Phase 1 — Benchmark (This Week, Jr Task)**:
- Download Ouro-2.6B-Thinking on redfin
- Run against our council voting prompts using transformers (not vLLM)
- Compare output quality to Qwen2.5-7B-Instruct baseline
- Measure: latency per token × loop count, VRAM usage, quality score

**Phase 2 — Bluefin Co-Processor (If Phase 1 Passes)**:
- Quantize Ouro-1.4B to INT4
- Deploy alongside VLM on bluefin
- Expose as reasoning endpoint for vision pipeline decisions

**Phase 3 — Watch & Wait**:
- Monitor OuroHub for larger models (14B+), quantized weights, MLX ports
- The architecture is sound — the models just need to scale up before they challenge our 72B

### Raven's Concern — Response

Raven is right to flag this. The Qwen 72B stack is battle-tested across hundreds of council votes. Ouro is research-grade, code isn't even public yet, and 2.6B matching 8B isn't enough to replace 72B. But the *architecture* is the real discovery — looped pre-training as a scaling strategy. We should **evaluate, not adopt**. Benchmark now, deploy when models scale up or when we need the parameter efficiency on constrained nodes (bluefin).

---

## Part 2: Solix 3800 Plus UPS Monitoring

### The Problem

Two power outages (Feb 7, Feb 11) with zero automated alerting. The Solix 3800 Plus solar battery powers the entire federation cluster. Both times: full manual recovery, crash-looping services, lost firewall rules, hours of downtime. **If monitoring had been in place, TPM would have received a 6-hour warning before battery depletion.**

### Council Deliberation

**Vote**: PROCEED (confidence 0.875)
**Consensus**: Layered approach — smart plug (immediate) + NUT/API (secondary)
**Concerns**: None raised.
**Self-assessment**: *"The rabbit who only looks for the hawk above misses the snake below."*

### Recommended Architecture (Council-Aligned)

#### Layer 1 — Smart Plug Energy Monitor (Immediate, ~$25)

Deploy a WiFi smart plug with energy monitoring (TP-Link Kasa KP115 or Shelly Plug S) on the Solix AC output circuit.

**How it works**:
- Plug monitors wattage flowing from Solix to the cluster's power strip/PDU
- When wattage drops below threshold (Solix battery depleting) → triggers alert
- When wattage hits zero → Solix is dead, initiate graceful shutdown
- Integration via local API (Kasa/Shelly both have documented HTTP APIs)
- A Python daemon on redfin polls the plug every 60 seconds

**Alert thresholds**:
| Battery State | Wattage Pattern | Alert Level | Action |
|--------------|----------------|-------------|--------|
| Healthy | >200W stable | None | Normal operation |
| Grid down, battery discharging | Declining trend | WARNING | Telegram alert to TPM |
| Battery <50% | Wattage dropping faster | ALERT | Prepare graceful shutdown script |
| Battery <20% | Low wattage | CRITICAL | Execute graceful shutdown |
| Battery dead | 0W | EMERGENCY | Nodes should already be off |

**Why this first**: No reverse engineering, no Bluetooth, no custom drivers. Works today. A Jr can build the polling daemon and Telegram alerts in one session.

#### Layer 2 — Solix API Investigation (Research)

The Anker Solix ecosystem may expose:
- **Local Bluetooth LE API**: Solix app communicates via BLE. Could potentially be sniffed and reverse-engineered. Risk: firmware updates could break it.
- **Anker Cloud API**: The Solix app syncs to Anker cloud. If an API exists, we could poll it. Risk: depends on internet connectivity (which may be down during power outage).
- **USB/Serial**: The Solix 3800 has USB-C ports for charging. Unknown if any expose a data interface that NUT could use.

**This is research-phase only.** The smart plug gets us 90% of the value immediately.

#### Layer 3 — Graceful Shutdown Orchestration

A shutdown script on redfin (as the gateway/coordinator) that:

1. Receives alert from smart plug daemon
2. SSH to each node in reverse dependency order:
   - greenfin → stop promtail, monitoring
   - bluefin → stop VLM services, checkpoint PostgreSQL, stop postgres
   - redfin → stop Jr pipeline, gateway, vLLM, SAG
   - bmasass → stop MLX services (if reachable)
3. Issue `shutdown -h +5` on each node with 5-minute delay
4. Send final Telegram: "Federation shutting down — battery critical. ETA to shutdown: 5 minutes."

#### Layer 4 — Persistent Recovery (Post-Outage Hardening)

From KB-POWER-FAILURE-RECOVERY-FEB07-2026, still-open items:
- Persist greenfin nftables rules: `nft list ruleset > /etc/nftables.conf`
- Add firewall persistence to Ansible playbooks
- Validate ALL .env files match current credentials after each rotation
- Systemd `After=` dependencies so services start in correct order

### Recommended Execution

**Immediate (TPM direct)**:
- Order smart plug (TP-Link Kasa KP115 or Shelly Plug S)
- Write Jr instruction for polling daemon + Telegram alerting + graceful shutdown script

**Jr Task (Wave 2)**:
- Build Solix monitoring daemon (`/ganuda/services/power_monitor/`)
- Integrate with existing Telegram alerting (telegram_chief)
- Build graceful shutdown orchestrator
- Research Solix BLE/cloud API options

**Ansible (Wave 3)**:
- Add power monitoring to federation playbooks
- Add firewall persistence rules
- Add credential validation post-rotation check

---

## Synthesis: How These Two Items Connect

The compute crisis (thermal #82859) and the power crisis are the same problem viewed from different angles: **infrastructure sovereignty**.

Ouro looped models promise more reasoning per watt — exactly what a solar-powered, battery-backed federation needs. If you're running on finite stored energy, a 2.6B model that reasons like an 8B model extends your battery runway by ~3x compared to running the 8B directly. On a Solix 3800 with declining battery, that's the difference between 2 hours of inference and 6 hours.

The Nate Hagens insight applies at every scale: from global data centers to a single solar battery in Oklahoma. Compute efficiency isn't just a cost optimization — it's a resilience multiplier.

*"The rabbit who only looks for the hawk above misses the snake below."*
*"Even the wisest owl cannot see its own back."*

The Council sees both directions. Now we build.

---

## Action Items Summary

| Item | Priority | Owner | Status |
|------|----------|-------|--------|
| Fix SAG crash-loop (import os) | P0 | TPM | DONE ✅ |
| Restart tribal-vision, grafana, promtail, research-worker | P0 | TPM (needs sudo) | PENDING |
| Order smart plug for Solix monitoring | P1 | TPM | NEW |
| Jr instruction: Solix monitoring daemon | P1 | Jr (pending instruction) | NEW |
| Jr instruction: Ouro benchmark on redfin | P2 | Jr (pending instruction) | NEW |
| Ouro-1.4B quantization for bluefin | P3 | Jr (after benchmark) | FUTURE |
| MLX Ouro port for bmasass | P3 | Watch & wait | FUTURE |

---

*For Seven Generations — sovereignty starts with keeping the lights on.*
