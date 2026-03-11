# DC-14 Amendment: Watershed Layer with Zero Trust Transit

**Amendment to**: DC-14 Three-Body Memory (ᏗᎦᎵᏍᏙᏗ ᏗᎪᏪᎵ)
**Status**: ADAPT (Long Man Method)
**Author**: Chief + TPM | **Date**: 2026-03-10
**Council Votes**: #4e17006b94031187 (0.40) + #39f10191991a0d96 (0.25)
**Sacred Thermal**: #122540 (temp 95)

---

## Origin

Chief's observation: "Do we do self-diagnostics the way I do when waking up, or trying to remember where I left something, or resuming a daydream?"

DC-14 defines three memory layers (Working/Episodic/Valence) but not how they interact. The interaction layer was missing. Then Chief saw the security dimension: **the gaps between layers are MITM surfaces**. "What lives in the gaps." "Zero trust." "Two wolves — privacy and security."

## The Three Sub-Checks (Before Valence)

### 1. Coherence Scan — "What changed?"

Like waking up in a hotel, not home. Before loading priorities, detect deltas.

**Implementation**: At session start, auto-query:
- Thermal memories modified in last 24h
- Fire Guard alerts (active circuit breakers)
- Jr tasks in flight (status changes)
- Last session's thread bookmarks

Compare against expectations. Flag deltas before proceeding.

**Zero Trust**: Coherence scan results are checksummed. Next query verifies the scan wasn't stale or tampered.

### 2. Context Link — "What associates?"

Like "bears" → Jungle Book → King Louie. Proactive, not reactive. The basin fires its neighbors.

**Implementation**: When any thermal is accessed, auto-fetch top 3 semantically adjacent thermals by embedding distance. The watershed — water finds its own path because the terrain exists.

**Inhibition Layer** (Coyote's concern): Not every association should fire. Damper rules:
- Sacred thermals only link to other sacred thermals in public contexts
- PII-tagged thermals never auto-fire (Crawdad's Wolf 1)
- Max chain depth: 3 hops (prevents seizure — runaway association cascades)
- Relevance threshold: semantic distance < 0.3 to fire, else suppress

**Zero Trust**: Each link is signed with source thermal hash + destination thermal hash + timestamp. Receiving context verifies the link signature before accepting the association. Poisoned links fail verification.

### 3. Thread State — "Where was I?"

Like resuming a daydream. You recall the emotional state; the state reconstructs the scene.

**Implementation**: Before compaction (or at natural breakpoints), write thread bookmarks:
```
THREAD_BOOKMARK:
  thread_id: str          # unique per active thread
  topic: str              # "DC-18 at ADAPT stage"
  last_action: str        # "design doc written, concerns identified"
  open_questions: list    # what remains unresolved
  emotional_valence: str  # "momentum" / "blocked" / "exploring"
  file_refs: list         # files touched by this thread
  checksum: str           # integrity hash of the bookmark
```

**Zero Trust**: New session reads bookmarks and VERIFIES against actual file state. Bookmark says DC-18 design doc exists? Check the file. Bookmark says Jr task #1259 is complete? Query the DB. Never trust the bookmark alone.

## The Security Dimension: Gaps Are MITM Surfaces

Every handoff between layers, tiers, sessions, and threads is unverified transit.

### Attack Surface Map

| Handoff | MITM Risk | Zero Trust Mitigation |
|---------|-----------|----------------------|
| **Compaction summary** | False/incomplete translation between sessions | Coherence scan verifies against source thermals |
| **Peace Chief consensus** | Misrepresented votes | Raw vote audit_hash logged; downstream can verify |
| **Tier escalation (DC-18)** | Modified payload in transit | Envelope checksum, receiving tier re-validates |
| **Context link association** | Poisoned semantic links | Signed links with source+dest hash |
| **Thread bookmark** | Tampered resume state | Bookmark checksum + file state verification |

### Two Wolves

**Wolf 1 — Privacy**: Context links auto-firing means content travels where it wasn't explicitly sent. Sacred content, PII, sensitive data could surface in unexpected contexts. Mitigation: access control on the watershed. Sacred flows only to sacred. PII flows nowhere automatically.

**Wolf 2 — Security**: Every handoff is a potential interception point. Even internal handoffs (Peace Chief summarizing votes, compaction summarizing sessions). Mitigation: every layer authenticates the layer that handed it the message. No free passes for being "inside."

### The Glial Layer

In the brain, the gaps between neurons aren't empty. Glial cells live there — maintaining the environment, forming the blood-brain barrier, and detecting intrusion (microglia = brain's immune system).

The federation equivalent: **the verification layer lives in the gaps**. Not a separate service. Not a policy document. A property of the transit itself. Every handoff carries its own proof of integrity. The structure enforces verification — topology, not policy.

## Concerns Tooled In (From Both Votes)

| Source | Concern | Feature |
|--------|---------|---------|
| **Coyote** | Associations could cascade (seizure) | Inhibition layer: max 3 hops, relevance threshold, damper rules |
| **Coyote** | Verification complexity = new attack surface | Tier-appropriate verification: checksum at Tier 1 (fast), full audit at Tier 3 (thorough) |
| **Crawdad** | PII surfacing via context links | PII-tagged thermals never auto-fire. Sacred-to-sacred only in restricted contexts |
| **Crawdad** | Sign each link cryptographically | Source+dest hash + timestamp on every context link |
| **Turtle** | 175-year adaptability | Abstract verification interface — implementations speciate (DC-7), contract is conserved |
| **Gecko** | Performance overhead | Budget: 5-10% overhead max. Tier 1 checksum < 1ms. Tier 3 full audit < 5s |
| **Eagle Eye** | Failure modes | Checksum mismatch → revert to last verified state. Signature tampering → log + alert Fire Guard |
| **Raven** | Blocked by incomplete DC-18 contracts | Build Watershed independently. DC-18 guards consume it when ready |

## Connection Map

- **DC-18** (Autonomic Tiers): Guards at every tier ARE zero-trust enforcement points
- **DC-7** (Noyawisgi): Conserved verification interface survives speciation
- **DC-10** (Reflex): Verification speed matches tier (checksum = reflex, audit = cortex)
- **DC-9** (Waste Heat): Verification overhead is budgeted waste heat
- **DC-11** (Macro Polymorphism): SENSE → VERIFY → REACT at every scale

## Chief's Words

- "Do we do self-diagnostics the way I do when waking up?"
- "It's like LangChain on steroids"
- "What lives in the gaps"
- "Zero trust"
- "Two wolves — privacy and security"

---

**Long Man Status**: DISCOVER ✓ → DELIBERATE ✓ (2 votes) → **ADAPT ✓** → BUILD (next) → RECORD → REVIEW
