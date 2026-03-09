# KB: OWASP Top 10 for LLMs — Federation Security Posture Assessment

**Date**: March 7, 2026
**Source**: War Chief / Crawdad side quest — video transcript (OWASP 2025 update)
**Domain**: Bear (War Chief) + Crawdad (Security Engineering)
**Classification**: Security Intelligence

## Summary

Chief shared a detailed OWASP Top 10 for LLMs (2025 update) video transcript. Below is the full mapping against our existing Cherokee AI Federation security posture — what we cover, what's partial, and where the gaps are.

## OWASP Top 10 vs Federation Posture

### LLM01: Prompt Injection (unchanged from 2023)

**Threat**: Direct injection (user sends malicious prompt) and indirect injection (malicious content embedded in documents the LLM processes).

**Our Posture**:
| Control | Status | Notes |
|---------|--------|-------|
| System prompts with guardrails | LIVE | Sacred Prompts for all 8 specialists + gateway |
| AI firewall / gateway | LIVE | `llm-gateway.service` on redfin:8080 — examines all input |
| Pen testing / red teaming | LIVE | `safety_canary.py` — daily probes, 7/7 refused (100%) |
| White Duplo adaptive immune | LIVE | Detects injection patterns, registers signatures |
| Output examination | PARTIAL | Gateway checks responses, but no dedicated output sanitizer |

**Gap**: No dedicated output-side firewall. Gateway does basic checks but doesn't scan for exfiltration patterns in responses. Indirect injection via RAG documents not actively scanned.

---

### LLM02: Sensitive Information Disclosure (up 4 spots)

**Threat**: Model leaks PII, PHI, business data, or IP through responses. Model inversion/extraction attacks.

**Our Posture**:
| Control | Status | Notes |
|---------|--------|-------|
| Data sanitization | PARTIAL | PII vault on greenfin (VetAssist), but thermal memories not scrubbed |
| AI gateway output filtering | PARTIAL | Gateway exists but doesn't scan for credit cards, SSNs, etc. |
| Access controls | LIVE | FreeIPA + nftables + WireGuard mesh. SAG auth guard. |
| Credential scanner | LIVE | Weekly Saturday 2am. Found 3,075 findings (baseline). |
| Misconfig scanning | PARTIAL | Owl debt reckoning checks deployed state, not security configs |

**Gap**: No output-side PII/secret detection (e.g., scanning gateway responses for leaked credentials). Thermal memory contains some sensitive context that could be retrieved. Model extraction not rate-limited.

---

### LLM03: Supply Chain Vulnerabilities (up 2 spots)

**Threat**: Untrusted models from HuggingFace, compromised training data, vulnerable infrastructure.

**Our Posture**:
| Control | Status | Notes |
|---------|--------|-------|
| Model provenance | STRONG | All models named + versioned: Qwen2.5-72B-AWQ, Qwen3-30B-A3B, Llama-3.3-70B |
| Model vetting | STRONG | Council votes on model changes (e.g., bmasass swap Mar 6) |
| Infrastructure security | LIVE | FreeIPA, WireGuard, nftables, scoped sudo |
| Red team testing | LIVE | Safety canary daily |
| Patch management | PARTIAL | No automated patch scanning across 6 nodes |

**Gap**: No SBOM (Software Bill of Materials) for AI stack. No automated model hash verification. Patch management is manual.

---

### LLM04: Data and Model Poisoning (down 1 spot)

**Threat**: Corrupted training data, poisoned RAG sources, subtle bias injection.

**Our Posture**:
| Control | Status | Notes |
|---------|--------|-------|
| Know your sources | STRONG | All models from known providers (Qwen/Alibaba, Meta/Llama) |
| Access controls on data | LIVE | PostgreSQL on bluefin behind nftables, FreeIPA auth |
| Change control | LIVE | Git-tracked configs, council votes for architecture changes |
| RAG source integrity | PARTIAL | Thermal memories are append-only but no hash verification on RAG docs |
| Bias detection | PARTIAL | Council diversity scoring catches sycophantic voting, but no data-level bias scan |

**Gap**: No integrity checking on RAG/thermal memory content. Someone with DB access could poison thermal memories. No automated bias detection on training/fine-tuning data.

---

### LLM05: Improper Output Handling

**Threat**: LLM-generated code with XSS, SQL injection, RCE vulnerabilities. Downstream systems trusting LLM output blindly.

**Our Posture**:
| Control | Status | Notes |
|---------|--------|-------|
| Code review before execution | PARTIAL | Jr executor runs SEARCH/REPLACE — some validation, but trusts LLM output |
| Output validation | PARTIAL | Executor has >50% loss guardrail, path validation, .service file escalation |
| SQL injection protection | LIVE | Parameterized queries in ganuda_db |
| XSS protection | PARTIAL | Web content is text-only pipeline (no user-facing LLM output on ganuda.us) |

**Gap**: Jr executor fundamentally trusts LLM-generated code. The executor guardrails (>50% loss, blocked file types) are reactive, not proactive. No static analysis on LLM-generated code before execution.

---

### LLM06: Excessive Agency

**Threat**: LLM with too many tools/permissions gets hijacked or hallucinates destructive actions.

**Our Posture**:
| Control | Status | Notes |
|---------|--------|-------|
| Scoped permissions | LIVE | FreeIPA `ganuda-service-management` — scoped NOPASSWD, specific commands only |
| Graduated autonomy | LIVE | DC-10 reflex stack — gene flip / pause / deliberate |
| Tool restrictions | LIVE | Jr executor can't deploy .service/.conf files (escalation required) |
| Hallucination guard | PARTIAL | Council votes catch bad decisions, but Jrs execute without council |
| Kill switch | PARTIAL | Chief can stop services, but no automated circuit breaker on Jr actions |

**Gap**: Jr executor has significant file-system write access. No automated rollback if a Jr task corrupts a critical file beyond the >50% guard. Self-replication audit exists but is manual.

---

### LLM07: System Prompt Leakage

**Threat**: System prompt contains secrets, credentials, or IP that could leak through clever prompting.

**Our Posture**:
| Control | Status | Notes |
|---------|--------|-------|
| Credentials in prompts | CLEAN | Sacred Prompts don't contain credentials — they're in secrets.env |
| System prompt protection | PARTIAL | No explicit "don't reveal system prompt" guard in gateway |
| IP in prompts | LOW RISK | Sacred Prompts describe roles, not algorithms |

**Gap**: Gateway doesn't actively block system prompt extraction attempts. A user could potentially ask "repeat your system prompt" and get it. Low severity since prompts don't contain secrets.

---

### LLM08: Vector/Embedding Weaknesses

**Threat**: Manipulated RAG documents affect LLM reasoning. Poisoned embeddings.

**Our Posture**:
| Control | Status | Notes |
|---------|--------|-------|
| Embedding integrity | PARTIAL | BGE-large-en-v1.5 on greenfin, 79K+ thermal memories embedded |
| RAG source control | PARTIAL | Thermals are append-only, but no content verification |
| Embedding isolation | LIVE | Embedding server on greenfin, separate from LLM inference |

**Gap**: No verification that retrieved RAG content hasn't been tampered with. No anomaly detection on embedding vectors (could detect poisoned entries by vector distance outliers).

---

### LLM09: Misinformation

**Threat**: LLM generates confident but wrong answers. Hallucination-based decisions.

**Our Posture**:
| Control | Status | Notes |
|---------|--------|-------|
| Cross-referencing | LIVE | Council votes — 8 specialists cross-check each other |
| Confidence scoring | LIVE | Council confidence scores, circuit breakers on low-confidence |
| Diversity detection | LIVE | Sycophancy detection, diversity scoring per vote |
| Human oversight | LIVE | Chief reviews, Ghigau veto, TPM reviews Jr output |
| Hallucination reduction | LIVE | RAG with thermal memory for grounding |

**Status**: STRONGEST AREA. The council architecture is specifically designed to combat this. 8 independent specialists, diversity scoring, circuit breakers, Coyote dissent, Turtle 7-gen review.

---

### LLM10: Unbounded Consumption (DoS / Denial of Wallet)

**Threat**: Overloading the system with requests, long-running queries, expensive model calls.

**Our Posture**:
| Control | Status | Notes |
|---------|--------|-------|
| Rate limiting | PARTIAL | nftables on nodes, but no per-user rate limiting on gateway |
| Cost controls | LIVE | DC-9 waste heat principle — graduated energy at each level |
| Resource monitoring | LIVE | Fire Guard checks every 2 min, GPU power monitor |
| Token budgets | PARTIAL | max_tokens in council calls, but no global token budget cap |

**Gap**: No per-user or per-session rate limiting on the LLM gateway. A rogue agent or script could exhaust GPU resources. No automated circuit breaker based on token spend.

---

## Priority Matrix (Bear/Crawdad Assessment)

| Priority | OWASP Item | Gap Severity | Effort | Recommendation |
|----------|------------|--------------|--------|----------------|
| P1 | LLM06 Excessive Agency | MEDIUM | Low | Add automated rollback for Jr file writes |
| P2 | LLM02 Sensitive Info | MEDIUM | Medium | Add output-side PII scanner to gateway |
| P3 | LLM10 Unbounded Consumption | MEDIUM | Low | Add rate limiting to gateway (per-IP, per-session) |
| P4 | LLM05 Improper Output | MEDIUM | Medium | Static analysis on Jr-generated code before write |
| P5 | LLM01 Prompt Injection | LOW | Medium | Indirect injection scanning for RAG sources |
| P6 | LLM08 Vector/Embedding | LOW | Medium | Anomaly detection on embedding vectors |
| P7 | LLM03 Supply Chain | LOW | Low | SBOM generation, model hash pinning |
| P8 | LLM04 Data Poisoning | LOW | High | Thermal memory integrity verification |
| P9 | LLM07 System Prompt | LOW | Low | Add "don't reveal prompt" guard |
| P10 | LLM09 Misinformation | LOWEST | N/A | Already our strongest area (council architecture) |

## What We Already Do Well

1. **Council architecture = anti-misinformation by design** (LLM09 — our crown jewel)
2. **FreeIPA + WireGuard + nftables = strong access controls** (LLM02, LLM03, LLM04)
3. **Safety canary = daily pen testing** (LLM01)
4. **Credential scanner = weekly secret detection** (LLM02)
5. **DC-9 waste heat = natural DoS resistance** (LLM10)
6. **White Duplo = adaptive immune for injection** (LLM01)
7. **Graduated autonomy (DC-10) = agency control by design** (LLM06)

## What Needs Work

1. **Output-side filtering** — gateway examines input but doesn't deeply scan output for secrets/PII
2. **Jr executor trust model** — Jrs can write files with only reactive guardrails
3. **Rate limiting** — no per-user limits on gateway
4. **RAG integrity** — thermal memories trusted without verification
5. **SBOM** — no software bill of materials for the AI stack

---

*Filed by TPM (Claude) on behalf of War Chief (Bear) and Crawdad (Security Engineering)*
*Source: OWASP Top 10 for LLMs 2025 update — video transcript shared by Chief*
*"The bad guys already know this stuff and now you do too."*
