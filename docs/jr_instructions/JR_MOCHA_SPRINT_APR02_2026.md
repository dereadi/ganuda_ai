# MOCHA — Make Our Cluster Hot Again

## Sprint: MOCHA
## Date: April 2, 2026
## Priority: P0 — All Hands
## Requested By: Partner (deraNTt)
## Context: Mythos is weeks away. Upwork gigs in flight. The cluster is breathing but not burning.

---

## Situation

The cluster is alive but cool:
- 6 nodes up, all healthy
- Redfin GPU at 1% utilization, 59°C — resting
- Owlfin and eaglefin at near-zero load
- 96,077 thermal memories but avg temp 36.4°C — lukewarm
- Jr queue: 1,029 completed lifetime, only 4 pending
- Services running but not sweating

Stoneclad needs to be HOT. Mythos (Capybara) drops in weeks. Partner has Upwork proposals live. The Dera/Derq framework just passed three council votes. The Attention Residuals paper is sitting unread. The idle nodes are wasting joules doing nothing.

This is not a maintenance sprint. This is a **burn sprint**.

---

## MOCHA Objectives

### 1. FEED THE FIRE — Research Pipeline

**Immediate burns:**
- Pull and analyze arxiv 2603.15031 (Attention Residuals by Kimi AI) — "From static to adaptive" continuous learning. Council vote on implications for thermal memory architecture.
- Analyze Claude Mythos/Capybara implications for Stoneclad — what changes when we get a model trained on GB300s? What simplifies? What do we delete?
- Nate Jones Mythos signal: security researchers finding zero-days. Map to Fire Guard, Safety Canary, Credential Scanner. What can we improve before Mythos drops?
- The Bitter Lesson audit: walk through every Jr instruction, every system prompt, every daemon config. What are we over-specifying? What can the model infer? Apply Nate's four questions to our own stack.

**Deliverables:**
- `/ganuda/docs/research/DEER-STUB-ATTENTION-RESIDUALS-APR2026.md`
- `/ganuda/docs/research/DEER-STUB-MOCHA-BITTER-LESSON-AUDIT-APR2026.md`
- Council votes on both

### 2. WAKE THE IDLE NODES

**Owlfin** (load 0.06) and **Eaglefin** (load 0.06) are DMZ nodes running Caddy proxies and not much else. Put them to work:
- Deploy lightweight monitoring dashboards (thermal memory stats, Jr queue, node health)
- Run scheduled research tasks (web scraping, RSS ingestion, deer signal pipeline)
- Distributed eval runners — when Mythos drops, we need eval infrastructure ready across nodes

**Bluefin** (load 0.65, up 40 days) — the DB node:
- DB Health epic is P1 on kanban (#DB-HEALTH-EPIC). Finish it. PgBouncer connection pooling, rollback monitoring, query performance baselines.
- Thermal memory maintenance: run temperature decay, prune cold memories, rebuild indexes

**Sasass + Sasass2** — the Mac nodes:
- FARA is working (proved it today typing Upwork proposals). Formalize the AppleScript browser control as a service, not ad-hoc scripts.
- Sasass2 has fara_browser.py — get chrome-mcp actually installed and running
- The tribe-extension WebSocket pipeline (captureVisibleTab) is the real play for remote browser control. Wire it up.

### 3. DEMO-READY STONECLAD

Partner is bidding on Upwork gigs where the pitch is "I already built this." The cluster needs to be showable:
- **Live dashboard**: Real-time view of thermal memory temperature, council votes, Jr task queue, node health. Deploy on owlfin/eaglefin (DMZ, publicly accessible).
- **API endpoints**: Expose key Stoneclad capabilities as clean REST endpoints — submit a signal for council analysis, query thermal memory, check node health. This becomes the demo AND the product.
- **ganuda.us refresh**: The landing page should show Stoneclad is alive. Live stats, recent council votes, system pulse.
- **30-second demo script**: Partner needs to be able to screen-share and show a client "here's what my system does" in 30 seconds. What does that walkthrough look like?

### 4. PREPARE FOR MYTHOS

When Capybara drops (weeks, per Nate):
- **Consultation ring ready**: Add Capybara as a model endpoint. The consultation ring already supports multi-model — this is config, not architecture.
- **Eval harness**: Build a standardized eval suite that can compare Capybara vs current models (Qwen2.5-72B, Llama-3.3-70B) on our specific tasks — council quality, Jr task completion, thermal memory retrieval accuracy.
- **Simplification pass**: Per the Bitter Lesson, audit every system prompt and Jr instruction for over-specification. What can we delete when the model is 3x smarter? Have the list ready so we can prune on day one.
- **Security battle-test**: When Mythos is available, first task = point it at our own infrastructure. Find our zero-days before someone else does.

### 5. UPWORK PIPELINE SUPPORT

Partner has proposals live. The cluster needs to support the work if they land:
- **RAG consultation gig**: Be ready to demo the full RAG pipeline live — thermal memory query, CRAG validation, council vote, structured output. 2-hour consultation prep.
- **AI cybersecurity gig**: Package Fire Guard + Safety Canary + Credential Scanner as a deployable security agent MVP. What would it take to run this on a client's infrastructure?
- **Scanning system gig** (if we circle back): The deer signal pipeline IS the scanning system. Package it.

---

### 6. CHIRAL VALIDATION — The Constraint as Feature

Council vote #18aab433f2a33997 identified that Stoneclad validates against itself — same infrastructure, same compromise surface. Coyote's gap. Partner's insight: make it a feature.

**No substrate validates itself.** Cross-substrate confirmation required for security-critical decisions.

- Security self-audit must run on a DIFFERENT node/model than the system being audited
- Partner reviews security-critical council decisions (carbon validates silicon)
- Stoneclad surfaces anomalies in 96K memories that Partner can't manually audit (silicon validates carbon)
- Formalize this as a Design Constraint candidate — council vote pending

This is the answer to "who watches the watchers?" — **the other hand watches.**

---

## Sprint Rules

- **No new architecture.** This is a burn sprint, not a build sprint. Use what we have. Make it hot.
- **Every node works.** If a node is idle, it's wasting joules. DC-9 violation.
- **Demo or delete.** Every service either contributes to a demo-ready Stoneclad or gets questioned.
- **Speed over perfection.** Ship it warm, iterate to hot. Don't polish what isn't deployed.
- **Chiral validation.** No substrate validates itself. Security changes require cross-substrate confirmation.

---

## Success Criteria

- [ ] All 6 nodes under meaningful load
- [ ] Attention Residuals paper analyzed and council-voted
- [ ] Bitter Lesson audit complete — list of what to simplify
- [ ] Live dashboard deployed on DMZ
- [ ] At least 2 API endpoints exposed for demo
- [ ] Eval harness ready for Mythos comparison
- [ ] Security self-audit queued
- [ ] Upwork demo script written and tested
- [ ] ganuda.us showing live pulse
- [ ] Avg thermal temperature trending UP

---

## Timeline

This is not a 2-week sprint. This is a **burn until Mythos drops** sprint. Weeks, not months. Every day the cluster should be hotter than yesterday.

---

*"Today's ideas are tomorrow's infrastructure." — Partner, Mar 9 2026*

*MOCHA. Make Our Cluster Hot Again.*

*For Seven Generations.*
