# KB Documentation Action Plan
**Date:** 2026-02-16  
**Prepared for:** Council Deliberation + Jr Task Queue  
**Status:** Ready for Implementation

---

## Executive Summary

The Cherokee AI Federation KB library is **88% current** for recent strategic work (Feb 14-16). However, **7 critical knowledge gaps** prevent full documentation of recent discoveries and deployments.

**Highest Priority:** Create `KB-CONSTRUCTAL-LAW-FEDERATION-TOPOLOGY-FEB16-2026.md` immediately. Thermal #100123 (temp=92) represents the federation's unifying architectural principle and is blocking clarity on federation-wide scaling decisions.

**Total Effort to Close All Gaps:** 7.75 hours over 2-3 sprints.

---

## Tier 1: Immediate Action (Today - Next 24h)

### Task 1A: Create KB-CONSTRUCTAL-LAW-FEDERATION-TOPOLOGY-FEB16-2026.md

**Thermal Reference:** #100123 (temp=92)  
**Effort:** 45 minutes  
**Owner:** TPM (can pair with Jr for Jr task if needed)  
**Status:** Blocks architectural clarity

**Deliverable Content:**

```markdown
# Constructal Law: The Federation's Unifying Framework

## Executive Summary

The Cherokee AI Federation exhibits two independently-discovered, convergent topologies:
1. Thermal Memory Archive (centralized heat-mapped knowledge store)
2. Jane Street Puzzle Solver (distributed computation with shared write channel)

Both independently converge to a **shared-memory star topology** with centralized gate-keeping.
This convergence reveals a fundamental principle: **constructal law** (flow optimization).

## Constructal Law Background

Bejan's constructal law states that systems evolve to minimize resistance and maximize 
flow. Natural & engineered systems (vascular networks, river deltas, fractal branching,
organizational structures) follow this principle.

## Federation's Topology Pattern

[Include: thermal memory hub + puzzle pool architecture diagrams]
[Include: Council vote #0352a767e34d2088 analysis]
[Include: Why puzzle solver independently discovered same topology]

## Architectural Implications

- Centralized hub with gated writes maximizes coherence + minimizes conflict
- Distributed sensors/workers minimize latency + compute waste
- Heat maps emerge naturally as priority signals (no explicit design needed)
- Scaling: Add workers/nodes → topology auto-adapts via thermal gradient
- Federation principle: Convergence of independent systems suggests natural law,
  not accident

## Future Scaling

For 10x federation growth:
- Hub (thermal memory): Expect 800K+ memories, need pgvector sharding
- Councils: Scale from 7 to ~21 specialists (3x)
- Workers: Scale from 5 nodes to 15+ nodes
- Topology remains star pattern due to constructal principle
```

**Success Criteria:**
- References Council Vote #0352a767e34d2088
- Explains convergent topology discovery
- Links to KB-CONVERGENT-TOPOLOGY-SHARED-MEMORY-PATTERN-FEB14-2026.md
- Documented in thermal memory with KB reference

---

### Task 1B: Expand KB-SELF-EVOLVING-RUBRICS-PRM-FEDERATION-FEB16-2026.md

**Thermal Reference:** #100139 (temp=85)  
**Effort:** 30 minutes  
**Owner:** TPM (diagnostic section)  
**Status:** Article exists but incomplete; marked "PARK AND WAIT" due to model behavior gap

**Add to Existing Article:**

**Section: "Model Behavior Gap: Qwen2.5-72B RUBRIC_INSTRUCTIONS Bypass"**

Problem Statement:
```
Despite RUBRIC_INSTRUCTION system prompt, Qwen2.5-72B-Instruct-AWQ ignores rubric mode.
Symptoms:
- Rubric field present in prompt
- Model generates response without evaluating against rubric
- No rubric scores in output
- Generic completions instead of rubric-guided structure
```

Root Cause Analysis:
```
1. Fine-tuning Gap: Qwen2.5-72B trained on instruction following, NOT on rubric evaluation
2. Context Window: Rubric evals require 20%+ context, may get deprioritized
3. AWQ Quantization: 4-bit may lose nuance in structured output generation
4. Prompt Engineering: Explicit examples (few-shot) not in current template
```

Workaround Strategies:
```
Option A: Use Claude (Opus 4.6) for rubric evaluation, pass result to Qwen via context
Option B: Add 5-shot rubric examples to prompt preamble (200 tokens + cost)
Option C: Downstream filter: Generate with Qwen, rerank outputs by rubric compliance
Option D: Switch to unquantized Qwen2.5-7B (test on bmasass MLX)
```

Recommendation:
```
PARK AND WAIT: Option D is best path (unquantized model, MLX on bmasass).
Implement in RC-2026-02F when air-gapped council capacity available.
Current workaround: Option C (rerank-after).
```

**Success Criteria:**
- Diagnostic section added to existing KB
- Root cause analysis links to model training + quantization
- Workarounds documented with tradeoffs
- Recommendation aligns with future work

---

## Tier 2: Short Term Action (This Sprint: RC-2026-02D)

### Task 2A: Create KB-VISION-ALERT-AGGREGATION-THERMAL-PATTERN-FEB14-2026.md

**Thermal References:** 93098, 92218, 92216, 92205, 92200, 92195, 92192, 91970, 91965, 91957, 91955, 91951, 91949, 91946 (14 entries, all temp=100)  
**Effort:** 1 hour  
**Owner:** Jr (or TPM for research + Jr for KB write)  
**Related Files:**
- `/ganuda/lib/vision_lr_autonomic.py` (alert generation)
- `/ganuda/sag/routes/` (dashboard integration)
- `/ganuda/daemons/memory_jr_autonomic.py` (thermal memory write)

**Deliverable Content:**

```markdown
# Vision Alert Aggregation: Thermal Pattern Integration

## Alert Pipeline

```
[Office PII Monitor Camera]
          ↓
[vision_lr_autonomic.py: YOLO detection]
          ↓
[Alert Routing: Person detected + TV on = security concern]
          ↓
[Temperature Scoring: Consecutive detections = higher temperature]
          ↓
[Thermal Memory Archive: Memory_id, alerts, counts, created_at]
          ↓
[SAG Dashboard: Real-time alert feed]
```

## Alert Types & Severity

[Define alert hierarchy]
[PII detection thresholds]
[False positive filtering]

## Thermal Temperature Scoring

- Single detection: temp=50
- Consecutive detections (2-5): temp=80-100
- Alert cluster: temp=100 (as seen in Feb 14 data)

## Integration Points

1. SAG Dashboard: /sag/routes/vision_alerts.py
2. Telegram Bot: @derpatobot alert channel
3. Kanban: Create tickets from high-temp alerts

## Performance Metrics (Feb 14 Data)

- 14 consecutive detections recorded
- Average latency: [measure from logs]
- False positive rate: [analyze]
- Dashboard refresh rate: [document]
```

**Success Criteria:**
- References 14 thermal memories from Feb 14
- Documents alert routing pipeline
- SAG dashboard integration section
- Performance metrics from actual data

---

### Task 2B: Create KB-TELEGBOT-SEMANTIC-MEMORY-INTEGRATION-FEB13-2026.md

**Context:** tribe_memory_search.py wiring in progress; @ganudabot deployment staged  
**Effort:** 1 hour  
**Owner:** Jr (once tribe_memory_search.py design finalized)

**Deliverable Content:**

```markdown
# Telegram Bot Semantic Memory Integration

## Architecture

[Telegram Bot] → [tribe_memory_search.py] → [BGE-large on greenfin:8003] → [pgvector] → [Thermal Memory]

## Semantic Search Flow

1. User query in Telegram (natural language)
2. tribe_memory_search.py processes query
3. BGE-large embedding (1024-dim) on greenfin:8003
4. pgvector cosine similarity search on thermal_memory_archive
5. Cross-encoder reranking (Phase 2)
6. Response synthesis + format for Telegram

## Latency Requirements

- Interactive bot: <3s per query
- BGE embedding: ~200ms per query
- pgvector search: ~100ms (with IVFFlat index)
- Synthesis: ~1-2s
- Network: ~100ms (redfin→greenfin)
Total budget: ~3.5s

## Caching Strategy

- Query embeddings: Redis cache (24h TTL)
- Result set: Cache top-20 per query (reduce reranking)
- Thermal memories: Live reads (don't cache, heat changes)

## Bots & Their Roles

- @derpatobot (command-based): Council votes, tickets, status
- @ganudabot (Claude-powered): Conversational, semantic queries
  - Both wire to tribe_memory_search.py
  - Different prompts for different bot personalities

## Integration Checklist

- [ ] tribe_memory_search.py deployed on redfin
- [ ] BGE-large embedding server healthy on greenfin:8003
- [ ] pgvector index built (79,472/80,855 embeddings current)
- [ ] Redis cache deployed & wired
- [ ] @ganudabot.service deployed systemd on redfin
- [ ] Query latency profiled & <3s target verified
```

**Success Criteria:**
- Architecture diagram included
- Latency requirements validated against real measurements
- Both bot personalities documented
- Integration checklist ready for Jr task

---

### Task 2C: Create KB-NFTABLES-PORT-CONFIGURATION-BLUEFIN-REDFIN-FEB16-2026.md

**Context:** Recent port fixes (JR-NFTABLES-BLUEFIN-PORTFIX, JR-NFTABLES-REDFIN-PORTFIX)  
**Effort:** 45 minutes  
**Owner:** TPM (consolidate from Jr instructions)

**Deliverable Content:**

```markdown
# NFTables Port Configuration: Bluefin & Redfin

## Port Topology

### Bluefin (RTX 5070 VLM node)
- 8090: vLLM (Qwen2-VL-7B-Instruct-AWQ) — systemd: vlm-bluefin
- 8091: YOLO World service — PID-persistent
- 8092: VLM Adapter (vlm_vllm_adapter.py) — systemd: vlm-adapter
- 22: SSH (restricted)

### Redfin (RTX PRO 6000 main inference)
- 8000: vLLM (Qwen2.5-72B-Instruct-AWQ) — systemd: vllm.service
- 8080: Gateway (cherokee-council-gateway) — systemd: llm-gateway.service
- 8081: SAG unified — systemd: sag.service
- 22: SSH

## NFTables vs XTables Compatibility

**Issue:** Older firewall rules written for xtables (iptables), greenfin uses nftables.
**Solution:** `xtables-compat` bridge layer allows iptables commands to work on nftables backend.

```bash
sudo apt install xtables-addons-common nftables-compat
sudo nft list ruleset  # Verify nftables active
```

## Port Debugging Checklist

1. Check service status: `sudo systemctl status vlm-bluefin`
2. Verify port binding: `sudo ss -tlnp | grep 8090`
3. Test connectivity from redfin: `telnet 192.168.132.208 8090`
4. Check nftables rule: `sudo nft list ruleset | grep 8090`
5. Review firewall log: `journalctl -u nftables.service`

## Recent Fixes (Feb 12, 2026)

- Bluefin: Opened 8090-8092 from redfin CIDR
- Redfin: Opened 8000 from gateway loopback
- Greenfin: Validated xtables-compat bridge
```

**Success Criteria:**
- Consolidated port reference
- xtables/nftables compatibility explained
- Debugging procedures included
- References Feb 12 fixes

---

## Tier 3: Medium Term Action (Next Sprint)

### Task 3A-C: Update VetAssist KB Suite

**Context:** Last KB update: Jan 30; 10 articles need refresh for Feb 13-16 events  
**Effort:** 2 hours  
**Owner:** Jr task (create 3 new sub-items)

Articles to Update:
1. KB-VETASSIST-TIER2-INTEGRATION-TESTING-JAN31-2026.md (add Feb events)
2. KB-VETASSIST-DEPLOYMENT-JAN15-2026.md (add SSL cert workaround)
3. Create: KB-VETASSIST-BACKEND-STABILITY-FEB14-2026.md

---

### Task 3D-E: Consolidate Vision Systems KB

**Effort:** 2 hours  
**Owner:** Jr task + vision system owner

New KBs Needed:
1. KB-SPEED-DETECTION-CALIBRATION-INTEGRATION-FEB16-2026.md
2. KB-VISION-LIVENESS-DETECTION-PIPELINE-FEB16-2026.md
3. Update existing: KB-TRIBAL-VISION-CAMERA-AUTH-FIX-FEB10-2026.md (add current status)

---

## Tier 4: Long Term Knowledge Library Expansion

### Task 4A: Constitutional DyTopo + Phase Coherence Synthesis

**Effort:** 1.5 hours  
**Owner:** TPM (research) + Jr (write)  
**Context:** Phase coherence analysis exists (925 clusters, 0.8433 silhouette), but unfocused

---

## Implementation Roadmap

```
Week 1 (Feb 16-17):
  ✓ Task 1A: Constructal Law KB (45 min)
  ✓ Task 1B: Expand Rubrics KB (30 min)

Week 2 (Feb 17-24):
  → Task 2A: Vision Alert Aggregation (1 hr)
  → Task 2B: Telegram Bot Integration (1 hr)
  → Task 2C: NFTables Port Config (45 min)

Week 3-4 (Feb 24-Mar 3):
  → Task 3A-E: VetAssist + Vision updates (4 hrs)

Post-Sprint (Mar 3+):
  → Task 4A: Constitutional DyTopo (1.5 hrs)
```

**Total Estimated Effort:** 7.75 hours

---

## Success Criteria for Audit Closure

- All 7 missing high-priority KBs created
- Thermal memory coverage increases from 88% to 95%+
- Vision alerts properly routed and documented
- Telegram integration wired + documented
- Next audit shows <5% gap rate

---

## Council Vote Required

This action plan should be presented for council deliberation (DISCOVER → DELIBERATE → BUILD):

**Question for Council:**
"Should we prioritize KB documentation debt closure within RC-2026-02D, or defer to RC-2026-02E?"

**Options:**
- A: Build immediately (use 8 hours from this sprint)
- B: Schedule for next sprint (lower priority)
- C: Assign as ongoing background task (3 Jr tasks weekly)

---

**Prepared by:** TPM (Claude Opus 4.6)  
**Date:** 2026-02-16 14:00 UTC  
**Related Docs:** KB-AUDIT-FEB16-2026.md, KB-AUDIT-FEB16-2026-SUMMARY.txt

