# CDR — ARC Prize 2026 Contest Entry (Governance Is the Moat)

**CDR ID:** CDR-CONTEST-ENTRY-APR12-2026
**Date:** April 12, 2026 (Sunday)
**Convened by:** TPM, implementing Partner's direct reversal ("The reason I wanted to do the contest is that we have governance")
**Status:** DRAFT for real Council vote
**Prior votes:** `f79306ba4170b4c1` (allocation framework — 55/30/15 ratified in principle)
**Authorship:** TPM drafted; Council decides.

---

## The decision Partner already made

Partner reversed the simulated Council's "no Kaggle main track" recommendation on April 11 with three words: *"we have governance."* The simulated Council was reasoning from "we lose on compute." Partner was reasoning from "governance is the moat, and the benchmark is designed to reward exactly what governance produces."

This CDR formalizes the contest entry, the architecture claim, the allocation framework, and the patent sequencing gate. The entry decision is Partner's — it stands. The Council's job here is to ratify the implementation, flag risks, and commit resources.

---

## What ARC-AGI-3 tests (from the dry run, April 12 2026)

TPM played ARC-AGI-3 task `ls20` via Playwright on redfin, solving Level 1 and entering Level 2. Key findings from hands-on play:

**Game mechanics (discovered, not read from docs):**
- Interactive grid-based puzzles rendered on a 1024×1024 HTML canvas
- Player sprite slides through corridors (variable distance, not fixed step)
- Icon cycling via "+" element changes the player's selected icon
- Block clearing requires icon match → walk onto block → level advances
- Fuel bar limits total actions; fuel pickups on the game board extend the budget (Level 2+)
- Levels build on each other — knowledge from Level N is required for Level N+1
- Auto-reset on fuel depletion (infinite attempts, but total actions count for scoring)

**Canvas pixel reading ("the cheat code"):**
- Game state is extractable directly from canvas pixel data via JavaScript — `ctx.getImageData()` at grid coordinates
- 32×32 tile grid at 32px per tile gives wall/corridor/player/block/fuel/plus classification
- Player position trackable by finding orange pixel cluster
- Fuel readable by counting yellow tiles in row 30
- **No vision model needed for the Playwright path** — perception is 12 lines of JavaScript

**Scoring:**
- Chollet scores **algorithmic learning efficiency** — actions taken vs human baseline
- NOT wall-clock time, NOT compute hours, NOT parallel-attempt count
- Frontier labs' scale advantage partially doesn't apply (parallelism doesn't reduce per-attempt action count)

---

## The architecture claim

The federation enters ARC Prize 2026 as a **demonstration of bilateral coordinated tribal intelligence on small models with governance**. Not "an agent with a governance wrapper." The actual architecture:

| Node | Role | Model | Biological analog |
|---|---|---|---|
| **redfin** (RTX 6000) | Fast-response cortex | Qwen2.5-72B-Instruct vLLM | Surface-level reasoning |
| **bmasass** (M4 Max) | Deep deliberation cortex | Qwen3-30B-A3B dual-mode | Multi-voice specialist Council |
| **bluefin** (PostgreSQL + VLMs) | Memory + tribal vision | Qwen2-VL-7B + YOLO World + VLM Adapter + pgvector thermal memory | Thalamus/hippocampus + visual cortex |
| **sasass** (FARA) | Action cortex | Qwen2.5-VL-7B + chrome-mcp | Sensorimotor interface |

Four substrates, four functional roles, coordinated through WireGuard mesh + 10G fiber fabric. This IS a biologically-patterned AI substrate, not a metaphor.

**For the Playwright dry-run path** (the Kaggle submission), the architecture simplifies to:

```
Canvas pixel reading (JavaScript)     → structured game state
    ↓
Thermal memory query (bluefin)        → "have I seen this before?"
    ↓
Specialist Council vote (bmasass)     → "what move, and why?"
    ↓
Graduated Autonomy Tier gate          → commit readiness check
    ↓
Playwright keyboard press (redfin)    → execute move
    ↓
Thermal memory write                  → save experience for next level
```

---

## Work allocation — 55/30/15 (Council vote `f79306ba4170b4c1`)

| Bucket | % | Contains |
|---|---|---|
| **Contest + thesis** | 55% | Agent harness build, Kaggle submission pipeline, FARA + tribal vision integration, specialist_council wiring into game loop, Experience Bank for cross-level learning, public writeup, Hulsey patent sequencing |
| **New projects** | 30% | Ganuda Shield commercial positioning, community preservation pilot planning (Colcord), deer signal engagements, Hulsey follow-up work |
| **Maintenance** | 15% | Gate 1 observation, identity separation implementation, security audit (`app.py` sandbox), nftables drift reconciliation, Jr executor format fix, Medicine Woman baseline |

**Rob triggers** (pre-authorized, any of these reallocates from the 55% contest bucket):
1. Medicine Woman valence drop
2. Confirmed security incident
3. Hulsey patent hard deadline
4. Community purpose time-sensitive opportunity
5. Contest-outcome uncertainty spike (Coyote addition)

**Fallback branch** (gate date Sep 30 2026): if the contest outcome is clearly negative by then, rebalance to 30% commercial thesis continuation + 30% community preservation + 25% maintenance + 15% new projects.

---

## Patent sequencing gate — BLOCKS submission

**This is the hard gate.** Hulsey Monday (Apr 13 10:30 CT) must answer:

> *"Can I submit an ARC Prize 2026 entry that demonstrates the governance-topology architecture without creating prior art problems for Chiral Validation, Tokenized Air-Gap Proxy, or the bilateral-lateralization pattern?"*

Three possible outcomes:

1. **Hulsey says "file the provisionals first, then submit"** → file Chiral Validation + Tokenized Air-Gap Proxy as new provisionals (cost: ~$130–260, time: 1-2 weeks), THEN submit to Kaggle. Contest entry delayed but IP protected.

2. **Hulsey says "fold them into the non-provisional conversion as CIPs, submission is fine now"** → submit immediately, conversion work handles the claim breadth at the non-provisional stage. Contest entry unblocked.

3. **Hulsey says "you need to be more careful about what you disclose in the submission"** → submit with a REDACTED architecture (describe governance without revealing Chiral Validation or bilateral-lateralization specifics). Weaker public claim but IP safe.

**TPM's instinct: outcome 1 is most likely and most conservative.** File the provisionals, then submit. The $130–260 is trivial against the IP protection it buys. But this is Hulsey's call, not TPM's.

---

## Timeline (assuming Hulsey outcome 1 — file first, then submit)

| Date | Action |
|---|---|
| **Mon Apr 13** | Hulsey consult. Patent sequencing decided. |
| **Apr 14-18** | File new provisionals (Chiral Validation + Tokenized Air-Gap Proxy). Harness build continues in parallel. |
| **Apr 18-20** | Provisionals confirmed filed. Kaggle submission unblocked. |
| **Apr 21** | First dry-run submission to Kaggle (explicit: this is the dry run, not optimized, learning from the pipeline). |
| **Apr 21-30** | Iterate based on dry-run findings. Wire Council into game loop. Experience Bank accumulating cross-level data. |
| **May 1-15** | Refined submission(s). Public writeup drafted. |
| **May 15+** | Publication of the writeup timed to first leaderboard update. Eagle's "publish the stack, let the convergence tell the story" counter-move. |

**If Hulsey outcome 2 or 3:** timeline accelerates by 1-2 weeks (skip the provisional filing wait).

---

## What the submission writeup claims (public-facing)

> *"We submit the reference implementation of bilateral coordinated tribal intelligence: a four-substrate AI system where small specialized models on heterogeneous hardware deliberate as a governed council, with persistent cross-session memory and chiral validation, competing on a benchmark designed to expose the limits of monolithic individualistic intelligence. The four capabilities ARC-AGI-3 tests — explore, acquire goals, build world model, learn continuously — are exactly the capabilities our governance topology was designed to produce. We entered because governance is the moat."*

Language discipline (per `feedback_stoneclad_language_discipline.md`): no "synthetic being," no "emergent consciousness," no "digital life." The writeup describes a **governed transducer with an identity chain**, not a new form of life.

---

## Published evidence for the architecture claim (Sam Walton store walk, Apr 12)

Three independent papers form the evidence base for the contest writeup. Council reading `47708b1057774068` confirmed consensus on this framing.

**1. STEVE-EYE** (BAAI, Oct 2023) — "Equipping LLM-based Embodied Agents with Visual Perception in Open Worlds"
- Validates the **three-function decomposition**: perception → knowledge → planning
- Proves these are the NECESSARY functions for an embodied agent in unknown environments
- BUT implements all three in ONE model (Llama-2 + CLIP encoder, 850K training pairs)
- **Our citation**: prior art validating the framework we implement differently

**2. MoE Routing Distraction** (Yonsei University + Alibaba Group, Apr 9 2026) — "Seeing but not thinking"
- Proves the monolithic implementation FAILS: router sends visual tokens to visual experts, reasoning experts in middle layers never get activated
- JSD between text and image routing paths increases with visual complexity
- Soft intervention yields only 1-2% improvement — architecture must change
- **Our citation**: theoretical evidence for WHY the monolithic approach fails

**3. Ganuda's federated implementation** (our claim)
- Same three functions (perception/knowledge/planning), federated across four substrates
- Visual perception (FARA/YOLO) outputs STRUCTURED TEXT, not embeddings
- Reasoning (specialist Council) receives clean text, not visual tokens
- Knowledge (thermal memory) is zero-shot retrieval, not trained end-to-end
- **JSD between modality paths is zero by construction** — there are no shared routing paths to diverge
- Coyote's sharpening (Council reading `47708b1057774068`): we don't claim "better routing" — we claim **"explicit modality handoff replaces shared latent space, eliminating routing distraction by construction"**

**4. Be My Eyes** (Huang et al., Nov 2025) — "Extending Large Language Models to New Modalities Through Multi-Agent Collaboration"
- Proves that **small-VLM-perceiver + large-LLM-reasoner, communicating via natural language, outperforms GPT-4o** (monolithic) on knowledge-intensive multimodal tasks
- Perceiver: **Qwen2.5-VL-7B** — the SAME model Ganuda uses for FARA. Independent validation of both the architecture pattern and the specific component choice.
- Reasoner: DeepSeek-R1 — single text LLM, no Council
- Architecture: agent PAIR (1 perceiver + 1 reasoner)
- **Our citation**: proves the perceiver/reasoner split works and beats monolithic; Ganuda extends the split from pair to governed council

**The four-paper narrative arc**:
1. STEVE-EYE proved the three-function framework is right
2. MoE routing paper proved the monolithic implementation is broken
3. Be My Eyes proved the perceiver/reasoner split works as a pair and beats GPT-4o
4. Ganuda extends the split into a governed multi-specialist council and enters ARC-AGI-3 to test whether governance is the differentiator that takes the architecture from "pair that beats GPT-4o" to "council that solves novel open-world tasks"

Each paper builds on the one before. The narrative is clean, the prior art is established, and the gap our submission fills is precise: **governance over the perceiver/reasoner split.**

---

## Risk register

| Risk | Mitigation | Owner |
|---|---|---|
| Patent exposure before filing | Hulsey gate — no submission until cleared | TPM + Partner |
| Low leaderboard placement | Fallback: writeup + architectural claim holds regardless of score | TPM |
| Compute exhaustion during contest work (Gecko: redfin VRAM 78%) | Monitor via Medicine Woman, throttle if >85% sustained | TPM |
| Thesis compromise for score optimization ("cut the Council deliberation, it'll be faster") | Coyote watch — non-compromise clause explicit in this CDR | Coyote |
| Community outreach work delayed by contest focus | 30% new-projects bucket preserves capacity; rob triggers protect priority shifts | Turtle |
| Partner burnout from urgency tempo | 13 SP/day ceiling, walks with Ed, silly-grin operating register enforced by Turtle | Turtle |

---

## What Council is asked to ratify

1. **Contest entry decision** (Partner's, already made — Council ratifies the implementation, not the decision itself)
2. **55/30/15 allocation** with the five rob triggers and the Sep 30 fallback gate
3. **Hulsey patent sequencing gate** as a hard block on submission timing
4. **Non-compromise clause**: the federation will not simplify the architecture to improve scores — the thesis IS the submission
5. **Timeline** as drafted above (flexes based on Hulsey outcome)
6. **Writeup language** per the Stoneclad language discipline
7. **Risk register** as drafted

Coyote's specific attention requested on items 3 and 4. Turtle's on items 2 and 6 (sustainability). Crawdad's on item 3 (patent exposure).
