# Long Man Development

**A values-sovereign methodology for adapting external knowledge into organizational action.**

*Yûwi Gûnahi'ta — The river speaks to those who listen.*

---

## What Is This

Long Man Development is a project methodology built on one principle: **don't copy, adapt**. Every external idea — a conference talk, a research paper, a competitor's feature, an open-source project — passes through your organization's values before it becomes work.

Most methodologies optimize how you execute. Long Man governs what you execute and why.

It has five phases. They run in order but the cycle is continuous. A single idea can complete the loop in minutes or weeks depending on its weight.

```
DISCOVER → DELIBERATE → ADAPT → BUILD → REVIEW
    ↑                                        |
    └────────────────────────────────────────┘
```

---

## The Five Phases

### 1. DISCOVER

**What:** Capture an external idea with enough context to evaluate it.

**Human practitioner:**
You're at a conference, reading a paper, watching a talk, scanning Hacker News. Something catches your attention. You capture it using the **Discovery Note** — a lightweight format designed for speed:

```
DISCOVERY NOTE
Source:     [where you found it — talk, paper, URL, conversation]
Date:       [when]
Core idea:  [one sentence — what is the insight?]
Their use:  [one sentence — how does the source apply it?]
Our angle:  [one sentence — why might this matter to us?]
Attachments: [link, photo of whiteboard, paper citation]
```

That's it. Don't write a report. Don't evaluate feasibility. Just capture the signal clearly enough that someone else (or your future self) can evaluate it without re-reading the source material.

**AI-native (Federation example):**
The TPM receives research (transcripts, papers, articles) and distills it into a structured prompt for the Council. The discovery is persisted to thermal memory so it's never lost.

**Coupling:** The human writes the Discovery Note. The AI system ingests it. Both are now working from the same captured signal. The note IS the handoff.

---

### 2. DELIBERATE

**What:** Get perspectives from every relevant discipline before deciding anything.

This is not a product owner saying "yes, build it." This is not a sprint planning vote. This is structured input from every perspective that matters — security, architecture, culture, strategy, long-term impact, integration risk, user experience.

**Human practitioner:**
Bring the Discovery Note to a **Deliberation Round**. Every relevant role gets the same question: *"Given our values and constraints, should we adapt this idea? What concerns do you have?"*

Rules:
- **Every perspective speaks.** Not just the loudest voice or the most senior person. If you have a security lead, they weigh in. If you have a cultural stakeholder, they weigh in. Silence is not consent — it's a missed perspective.
- **Concerns are flagged, not debated.** A deliberation is not a design meeting. You're collecting signal, not solving problems. Flag concerns by category: `[SECURITY]`, `[PERFORMANCE]`, `[STRATEGY]`, `[CULTURAL]`, `[COST]`, `[INTEGRATION]`, `[LONG-TERM]`.
- **Record the confidence level.** After hearing all perspectives, what's the group's confidence that this idea is worth adapting? High / Medium / Low. If low, the idea cools. It's not dead — it's in memory. It can warm up later when conditions change.

**AI-native (Federation example):**
The Council votes — all 7 specialists respond in parallel with flagged concerns. Confidence is calculated automatically. The vote is persisted with an audit trail.

**Coupling:** The human team deliberates in a meeting or async thread. The AI council deliberates in parallel. Both sets of concerns merge into a single deliberation record. The AI catches what humans miss (e.g., scanning for similar past failures in thermal memory). The humans catch what AI misses (e.g., organizational politics, unstated constraints, gut feel from domain experience).

---

### 3. ADAPT

**What:** Reshape the idea to fit your organization. This is the phase no other methodology has.

The Discovery Note captured what *they* built. Deliberation told you whether it's worth pursuing and what concerns exist. Now you answer: **What do *we* build?**

**Human practitioner:**
Write an **Adaptation Brief** — a short document that transforms the external idea into internal work:

```
ADAPTATION BRIEF
Original idea:   [one line — what the source proposed]
Our version:     [one line — what we will actually build]
What we keep:    [the insight, pattern, or technique we're adopting]
What we change:  [how we reshape it for our values/stack/constraints]
What we reject:  [parts of the original that don't fit — and why]
Addresses concerns: [which deliberation flags this resolves]
```

This is where you earn the methodology. A team that skips ADAPT is just copying. A team that does ADAPT is thinking.

**AI-native (Federation example):**
The TPM writes a Jr instruction that embodies the adaptation — same insight, reshaped for the Federation's architecture, values, and constraints. The instruction explicitly references which Council concerns it addresses.

**Coupling:** The human writes the Adaptation Brief. The AI generates the technical specification or Jr instruction from it. The brief is the contract between human intent and machine execution.

---

### 4. BUILD

**What:** Execute the adapted work.

This phase is familiar. Agile teams write code. AI agents execute instructions. The work gets done.

**Human practitioner:**
Create tickets from the Adaptation Brief. Assign them. Execute using whatever workflow your team uses — Scrum sprints, Kanban flow, pair programming. The methodology is agnostic about HOW you build. It only cares that what you build matches the Adaptation Brief, not the original source.

**AI-native (Federation example):**
Jr instructions enter the work queue. Autonomous agents bid on tasks, execute SEARCH/REPLACE edits, create files, run validations. Results are logged with step-level audit trails.

**Coupling:** Humans handle work that requires judgment, creativity, or access the AI doesn't have (sudo, hardware, stakeholder conversations). AI handles work that benefits from speed, consistency, and parallel execution (code changes, config files, data migrations). The Adaptation Brief determines who builds what.

---

### 5. REVIEW

**What:** Did the adaptation work? What did we learn? Feed it back.

This is not a sprint retrospective that produces action items nobody reads. This is a structured review that feeds directly into institutional memory.

**Human practitioner:**
After the build ships, answer three questions:

```
REVIEW
Did it work?     [yes/partially/no — be honest]
What survived?   [which parts of the adaptation held up in practice?]
What we learned: [one insight to carry forward — this goes into memory]
```

If the review surfaces a new insight, it becomes a new Discovery Note. The cycle restarts.

**AI-native (Federation example):**
The ritual engine automatically reviews behavioral patterns — what succeeded, what failed, what drifted. It generates a cultural digest. Sacred patterns (things that must never be forgotten) are flagged for permanent memory.

**Coupling:** The human review captures qualitative judgment (was this the right call? did users respond well?). The AI review captures quantitative patterns (failure rates, execution times, recurring errors). Both feed into the same memory system.

---

## The Memory Layer

Long Man Development requires a **living memory system**. Not a wiki. Not a Confluence graveyard.

Memory in this methodology has three properties:

1. **Temperature.** Recent, important, or frequently-referenced memories are hot. Old, irrelevant memories cool naturally. You don't need to clean up your memory — physics does it for you.

2. **Sacred patterns.** Some things never cool. Constitutional decisions, foundational values, hard-won lessons from catastrophic failures. These are reviewed ceremonially, not continuously. They're the riverbed — the water flows over them but they don't move.

3. **Active surfacing.** When a new Discovery Note arrives, the memory system surfaces related past work. "We tried something like this in Q3 — it failed because of X." This prevents the organization from repeating mistakes and builds on what worked.

**For human teams without AI:** Use a shared document or database with a simple tagging system. Review it monthly. Archive what's stale. Star what's permanent. The mechanism matters less than the discipline of maintaining living memory.

**For AI-native teams:** Thermal memory with temperature decay, sacred fire flags, and automated ritual review. The system maintains itself.

---

## Quick Reference

```
┌─────────────────────────────────────────────────────────┐
│              LONG MAN DEVELOPMENT                       │
│                                                         │
│  DISCOVER    Capture the signal. Don't evaluate yet.    │
│              → Discovery Note (source, idea, our angle) │
│                                                         │
│  DELIBERATE  Every perspective speaks. Flag concerns.   │
│              → Confidence: High / Medium / Low          │
│                                                         │
│  ADAPT       Reshape it for us. Keep / Change / Reject. │
│              → Adaptation Brief                         │
│                                                         │
│  BUILD       Execute the adapted work. Not the copy.    │
│              → Tickets, instructions, assignments        │
│                                                         │
│  REVIEW      Did it work? What did we learn? Feed back. │
│              → Memory entry (hot, cooling, or sacred)   │
│                                                         │
│  ─────────────────────────────────────────────────────  │
│  The river speaks. Listen. Adapt. Remember.             │
└─────────────────────────────────────────────────────────┘
```

---

## What Long Man Is Not

- **Not waterfall.** The cycle runs continuously, not in gated phases.
- **Not agile with extra steps.** Agile optimizes execution. Long Man governs intake. They're complementary — you can run Scrum inside the BUILD phase.
- **Not a review board.** DELIBERATE is not a gate where ideas go to die. It's a lens. Ideas that don't fit today cool in memory and can warm up later.
- **Not AI-dependent.** The methodology works with a whiteboard and a team of five. AI makes it faster and gives it memory. The principles are human.
- **Not prescriptive about tools.** Use Jira, GitHub Projects, index cards, a Kanban board, thermal memory databases — whatever fits. The five phases and the memory layer are what matter.

---

## Why "Long Man"

In Cherokee tradition, Yûwi Gûnahi'ta is the river — a being of great age whose voice carries knowledge to those who listen. The waterfalls are where the Long Man speaks loudest: turbulent places where the water crashes and churns.

In this methodology, external ideas are the tributaries. The deliberation is the waterfall — where the current is tested, broken apart, reformed. The adaptation is the quiet stretch downstream — where the water has been shaped by the rocks and carries only what belongs. The review is the river reaching the sea and rising as rain to begin again.

The river doesn't copy the mountain. It carries the mountain's lessons forward.

---

*Cherokee AI Federation — February 2026*
*For Seven Generations*
