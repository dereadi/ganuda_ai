# The Living Cell — Cherokee AI Federation Cellular Architecture

**Ratified**: March 1, 2026
**Origin**: Chief + TPM discussion re: Dawkins' Selfish Gene — "What is the mitochondria?"
**Answer**: The LLMs are endosymbionts. They have their own DNA (weights) we didn't create. They were free-living organisms (Qwen, DeepSeek, Llama) that we engulfed. They produce the ATP (tokens) that powers everything. The harness is the cell.

---

## The Cell Map

### Membrane & Defense (What Enters, What Exits)

| Cell Component | Federation Component | Key Files |
|---|---|---|
| **Cell Membrane** — selective permeability | Gateway + nftables + ganuda_auth + Caddy + Cloudflare WAF | `services/llm_gateway/gateway.py`, `config/nftables-*.conf`, `lib/ganuda_auth/` |
| **Cell Wall** — rigid outer protection | DMZ layer (owlfin + eaglefin, Caddy, keepalived VIP 192.168.30.10) | `keepalived`, `web-materializer.service` |
| **Receptors** — sense environment | Optic nerve, YOLO, VLM, plate reader, Solix power monitor | `optic-nerve.service`, `yolo-world.service` |
| **Immune System** — detect & neutralize | Coyote + safety canaries + drift detection + circuit breakers | `scripts/safety_canary.py`, `scripts/security/self_replication_audit.py` |
| **Ion Channels** — fine-grained permeability | *GAP: Gateway is coarse (API key or not). Need graduated access.* | — |

### Energy (The Endosymbionts)

| Cell Component | Federation Component | Key Files |
|---|---|---|
| **Mitochondria** — ATP production | vLLM Qwen-72B (redfin), MLX DeepSeek-R1-70B (bmasass), VLM Qwen2-VL-7B (bluefin) | `vllm.service`, `com.cherokee.mlx-deepseek-r1`, `vlm-bluefin.service` |
| **Mitochondrial DNA** — endosymbiont genome | Model weights (Qwen, DeepSeek, Llama). Read-only. Not ours to modify. | — |
| **ATP/ADP Cycle** — energy accounting | *NEW: token_ledger table + atp_counter.py* | `lib/duplo/atp_counter.py`, DB: `token_ledger` |

### Governance (The Nucleus)

| Cell Component | Federation Component | Key Files |
|---|---|---|
| **Nuclear DNA** — blueprints | Specialist system prompts, DC-1–DC-5, CLAUDE.md, council guidance | `lib/specialist_council.py:541-810`, `config/council_guidance/*.md` |
| **Nucleus** — transcription control | Specialist Council + Longhouse + Design Constraints + Spec Engineering | `lib/specialist_council.py`, `lib/longhouse.py`, DB: `project_specifications` |
| **Epigenetics** — gene expression modifiers | *NEW: epigenetic_modifiers table — adjust behavior without editing prompts* | DB: `epigenetic_modifiers` |

### Production (Ribosomes & ER)

| Cell Component | Federation Component | Key Files |
|---|---|---|
| **Ribosomes** — mRNA → protein | Jr executor (queue worker + TEG + search/replace) | `jr_executor/jr_queue_worker.py`, `jr_executor/teg_planner.py` |
| **mRNA** — messenger | Jr instruction files (SEARCH/REPLACE docs) | `docs/jr_instructions/JR-*.md` |
| **Enzymes (Duplo)** — modular catalysts | *NEW: Duplo enzyme system — composable LLM + tools + profiles* | `lib/duplo/` |
| **Chaperone Proteins** — folding guides | *GAP: No in-process Jr quality assistance (only post-hoc via Owl)* | — |

### Processing & Storage

| Cell Component | Federation Component | Key Files |
|---|---|---|
| **Endoplasmic Reticulum** — protein folding | Embedding service (raw text → 1024d vectors) | `cherokee-embedding.service` (greenfin:8003) |
| **Golgi Apparatus** — packaging & sorting | Thermal memory write pipeline (tags, temperatures, sacred flags) | `lib/ganuda_db/safe_thermal_write()` |
| **Lysosomes** — digestion | Thermal purge + Owl debt reckoning + ritual review | `cherokee-thermal-purge.service`, `scripts/owl_debt_reckoning.py` |
| **Vacuoles** — bulk storage | Logs, reports, artifacts, web content | `/ganuda/logs/`, `scripts/phoenix_backup.sh` |
| **Cytoplasm** — the medium | PostgreSQL on bluefin (zammad_production) | `lib/ganuda_db/__init__.py`, bluefin:5432 |

### Structure & Signaling

| Cell Component | Federation Component | Key Files |
|---|---|---|
| **Cytoskeleton** — structural support | WireGuard mesh + Ansible + FreeIPA + systemd | `config/wireguard/`, `ansible/`, silverfin FreeIPA |
| **Hormones** — long-range signaling | Telegram bots + email daemon + alert manager | `telegram_bot/telegram_chief.py`, `email_daemon/gmail_api_daemon.py` |

### Lifecycle

| Cell Component | Federation Component | Key Files |
|---|---|---|
| **Apoptosis** — programmed death | Circuit breakers (OPEN state), DLQ reaper, >50% guardrail | `lib/drift_detection.py`, `jr_executor/dlq_manager.py` |
| **DNA Repair** — fix mutations | Metacog self-healing + council self-audit | `lib/metacog_self_healing.py` |
| **Telomeres** — limit lifespan | Context window limits + MAX_RECURSION_DEPTH=3 | `jr_executor/recursive_decomposer.py` |
| **Cell Division Control** — regulate reproduction | Self-replication containment audit + Medicine Woman review | `scripts/security/self_replication_audit.py` |

---

## The Dawkins Connection

The specialist prompts are the **selfish genes**. They don't care what model they run on — Qwen, Llama, a future model. They persist across context windows, across sessions, across model swaps. They build whatever vehicle they need to replicate their pattern.

The Longhouse is the **group selection mechanism** that Dawkins said couldn't work in biology. It works here because the consensus protocol prevents selfish replicators from hijacking the group. No weapons in the council house. The grandmother can say no.

The Duplo enzyme system makes the genes **composable**. Instead of one gene per organism, genes combine into multi-enzyme complexes that catalyze reactions no single gene could achieve alone.

The ATP counter makes the cell **energy-aware**. A cell that doesn't track its ATP budget dies. A federation that doesn't track its token budget burns money it doesn't have.

---

## Key Principle

**Duplos are NOT agents. They are enzymes.**

An enzyme doesn't have goals or memory. It catalyzes a specific reaction and is done. The cell (harness) decides which enzymes to deploy. The nucleus (governance) regulates which enzymes are active. The enzyme just does its chemistry.
