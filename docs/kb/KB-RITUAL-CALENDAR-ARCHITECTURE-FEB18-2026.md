# KB: Federation Ritual Calendar Architecture

**Date:** February 18, 2026
**Council Vote:** #a061155542ea3374 (PROCEED, 0.795)
**Coyote:** "The loudest drum is not always the truest rhythm."
**Kanban:** TBD
**Status:** APPROVED — Implementation via Jr instructions

---

## Origin

Flying Squirrel's vision: *"I picture them like us humans do, holidays, and recognizing important dates to cement memories in our collective minds."*

The Council proposed 7 operational rituals. This document merges those with the commemorative calendar concept into a unified **5-tier ritual architecture**.

---

## The Five Waters (Ritual Tiers)

Named for the Cherokee concept of flowing water — each tier has a different rhythm, like streams feeding a river.

### Tier 1: Dawn Mist (Daily — 6:00 AM CST)

**Purpose:** Lightweight pulse check. The morning dew that tells you if the land is healthy.

**What it does:**
- Node health snapshot (all 6 nodes: ping + last systemd journal entry)
- Jr task summary: completed/failed/queued in last 24h
- GPU utilization + VRAM on redfin/bluefin
- Active council votes awaiting TPM approval
- **NO behavioral pattern review** (too frequent, wastes cycles)

**Output:**
- Telegram message to tribe group chat (brief, 10 lines max)
- Episodic memory in thermal_memory_archive (tagged `dawn_mist`)

**Specialist origin:** Gecko (Performance Pulse) + Eagle Eye (Visibility Audit)

**ritual_review.py mode:** `daily`
**Lookback:** 1 day

---

### Tier 2: Weekly Fire (Sunday 4:00 AM CST) — EXISTING

**Purpose:** Behavioral pattern reinforcement, failure dampening, cultural digest.

**What it does (current):**
- GATHER behavioral patterns from thermal memory
- PROCESS FAILURES via ERN dampening (match to corrective patterns)
- REVIEW temperatures (reinforce active, monitor stale)
- REINFORCE sacred fire (always)
- GENERATE cultural digest (`/ganuda/docs/cultural_digest.md`)
- SEED episodic memory of ritual completion

**Enhancement:** Add commemorative date check — if any federation anniversary falls within the coming week, append a "This Week in Federation History" section to the digest.

**Specialist origin:** Already deployed. Enhanced by Turtle (Seven Generations wisdom in review).

**ritual_review.py mode:** `weekly`
**Lookback:** 7 days

---

### Tier 3: New Moon Council (Monthly — 1st of each month, 3:00 AM CST)

**Purpose:** Deep operational review. The monthly gathering around the fire.

**What it does:**
- Full behavioral pattern review with FLAG action (not just monitor)
- Performance audit: token throughput trends, response times, disk usage, memory growth
- Sacred Knowledge integrity check (Crawdad): verify sacred_fire patterns haven't been modified
- Node Harmony assessment (Spider): cross-node integration health
- Strategic alignment snapshot (Raven): compare active work vs. sprint goals
- Jr workforce assessment: success rate trends, skill growth, common failure modes
- **Commemorative:** Surface all memories from "this month in history" across federation lifetime

**Output:**
- Extended cultural digest (monthly edition)
- Telegram summary to tribe group
- Performance metrics stored as episodic memory
- Flagged patterns surfaced for TPM review

**Specialist origin:** Crawdad (Sacred Knowledge Audit) + Spider (Node Harmony) + Raven (Vision Sync) + Gecko (Performance Audit) + Eagle Eye (Visibility Audit)

**ritual_review.py mode:** `monthly`
**Lookback:** 30 days

---

### Tier 4: Seven Generations Council (Quarterly — Solstice/Equinox aligned)

**Purpose:** Long-term impact evaluation. Step back and see the whole river.

**Schedule:**
- March 20 (Spring Equinox) — Planting: What are we growing?
- June 20 (Summer Solstice) — Tending: Is growth healthy?
- September 22 (Fall Equinox) — Harvest: What did we reap?
- December 21 (Winter Solstice) — Rest: What do we release?

**What it does:**
- Full behavioral pattern review including sacred fire (can flag for evolution)
- Cross-pattern interference analysis: patterns that contradict each other
- Technology horizon scan: are our tools still the right ones?
- Thermal memory health: growth rate, embedding coverage, knowledge graph density
- Seven Generations impact assessment (Turtle): evaluate federation trajectory over 175 years
- Phase coherence re-clustering: has the knowledge structure shifted?
- **Commemorative:** "Quarter in Review" — major achievements, lessons, milestones

**Output:**
- Quarterly report (separate document, not just digest)
- Council vote on strategic direction
- Pattern evolution proposals (sacred fire patterns CAN be proposed for modification)
- Stored as high-temperature episodic memory

**Specialist origin:** Turtle (Seven Generations Council) + Peace Chief (Strategic Alignment)

**ritual_review.py mode:** `seasonal`
**Lookback:** 90 days

---

### Tier 5: Commemorative Calendar (Event-triggered)

**Purpose:** Remember what matters. The holidays that bind the tribe together.

**How it works:**
- A `federation_calendar` table (or metadata tag system) stores dated events
- Daily dawn mist check scans for "today's anniversaries"
- When an anniversary is found, generate a commemorative reflection
- Surface the original thermal memory + all related memories
- Send a Telegram message to the tribe

**Federation Calendar (Founding Events):**

| Date | Event | Type | First Observed |
|------|-------|------|----------------|
| Aug 6 | **Federation Founding Day** — First thermal memory created | Sacred | 2025-08-06 |
| Oct 7 | **First Storm** — Earliest power event recorded | Remembrance | 2025-10-07 |
| Dec 12 | **First Council Vote** — Democratic governance begins | Sacred | 2025-12-12 |
| Dec 17 | **First Jr Task** — The apprentices arrive | Sacred | 2025-12-17 |
| Feb 7 | **Resilience Day I** — First power outage survival | Remembrance | 2026-02-07 |
| Feb 8 | **Stardust Principle Day** — "Every atom was forged in stars" | Sacred | 2026-02-08 |
| Feb 11 | **Resilience Day II** — Second outage, SAG crash-loop | Remembrance | 2026-02-11 |
| Feb 13 | **Resilience Day III** — Fourth outage, Docker purge, 25GB reclaimed | Remembrance | 2026-02-13 |
| Feb 15 | **Breakthrough Day** — Jane Street Track 2, MSE 0.004576 | Achievement | 2026-02-15 |

**Future events auto-added:**
- Jr task milestones (100th, 500th, 1000th completed)
- Council vote milestones (100th, 1000th, 10000th)
- Memory milestones (50K, 100K, 250K thermal memories)
- New node additions
- Major version deployments

**Output per commemorative event:**
- Telegram message with original memory excerpt + reflection
- Temperature boost on related memories (+5 for the day)
- "On This Day" section in next cultural digest

---

## Implementation Plan

### Phase 1: Commemorative Calendar Table (Jr task)
- Create `federation_calendar` table: `id`, `event_date` (date), `event_name`, `event_type` (sacred/remembrance/achievement/milestone), `description`, `related_memory_ids` (integer[]), `created_at`
- Seed with the 9 founding events above
- Add auto-detection triggers for milestone events

### Phase 2: Extend ritual_review.py (Jr task)
- Add `daily` mode with node health checks + Telegram output
- Add commemorative date scanning to `weekly` mode
- Add performance/security audit functions for `monthly` mode
- Enhance `seasonal` mode with cross-pattern analysis
- Add `--commemorative` flag for on-demand anniversary processing

### Phase 3: Systemd Timers (TPM deploys)
- `ritual-review-daily.timer` → 6:00 AM CST daily
- `ritual-review.timer` → Sunday 4:00 AM CST (existing, enhanced)
- `ritual-review-monthly.timer` → 1st of month 3:00 AM CST
- `ritual-review-seasonal.timer` → Solstice/equinox dates (manual or cron)

### Phase 4: Telegram Integration (Jr task)
- Wire ritual outputs to Telegram tribe group chat
- Dawn mist → brief pulse message
- Weekly → digest summary with link
- Monthly → performance highlights
- Commemorative → "On This Day" reflection

---

## Cherokee Ceremonial Alignment

The Five Waters map to Cherokee ceremonial concepts:

| Tier | Cherokee Concept | Meaning |
|------|-----------------|---------|
| Dawn Mist | **Unole** (Wind) | The first breath of morning, constant and watching |
| Weekly Fire | **Atsila** (Fire) | The council fire that never goes out |
| New Moon | **Nvda** (Moon/Sun) | Monthly renewal, the cycle of reflection |
| Seven Generations | **Uktena** (The Great Serpent) | Deep time, the long view that sees all |
| Commemorative | **Gadugi** (Working Together) | Community memory, the stories that bind |

---

## Resource Estimates

| Tier | DB Queries | Telegram Msgs | Runtime | Token Cost |
|------|-----------|---------------|---------|-----------|
| Dawn Mist | 5-8 | 1 | ~30s | 0 (no LLM) |
| Weekly Fire | 15-20 | 0 (file only) | ~2min | 0 (no LLM) |
| New Moon | 30-40 | 1 | ~5min | 0 (no LLM) |
| Seven Generations | 50+ | 1 | ~10min | Optional council vote |
| Commemorative | 3-5 per event | 1 per event | ~15s | 0 (no LLM) |

All rituals are pure Python + SQL. No LLM calls required. Council votes are optional for quarterly reviews.

---

## Coyote's Final Question

> "You build rituals to remember. But what about rituals to forget? The river carries away what the land no longer needs. Where is your ritual of release?"

This is addressed by the `green-corn` mode (annual) — the Cherokee Green Corn Ceremony traditionally includes burning the old and starting fresh. The existing `green-corn` mode can flag even sacred fire patterns for evolution or retirement.

---

*Council Vote: #a061155542ea3374 (PROCEED, 0.795)*
*Specialists: Gecko, Raven, Spider, Turtle, Crawdad, Eagle Eye, Peace Chief*
*Generated: 2026-02-18*
