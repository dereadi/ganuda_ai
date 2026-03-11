# KB: DC-14 Watershed Layer — Coherence Scan, Context Link, Thread State

**Built:** 2026-03-10 by TPM + Chief (Long Man Method, Leaders Meeting #1)
**Design Doc:** `/ganuda/docs/design/DC-14-WATERSHED-ZERO-TRUST-TRANSIT-MAR10-2026.md`
**Sacred Thermal:** #122540 (temp 95)
**Council Votes:** #4e17006b94031187 (Watershed), #39f10191991a0d96 (Zero Trust Transit)

## What It Is

The interaction layer between DC-14's three memory bodies (Working/Episodic/Valence). Three sub-checks that fire before valence scoring:

1. **Coherence Scan** — "What changed?" Delta detection at session start.
2. **Context Link** — Proactive associative firing between thermal basins.
3. **Thread State** — Active thread bookmarks surviving compaction.

Chief's analogy: "Like LangChain on steroids" — except LangChain is a railroad (developer-defined chains). This is a watershed (experience-carved terrain where water finds its own path).

## Why It Exists

Chief identified two gaps:
- **Functional**: DC-14 defined three memory layers but not how they interact. No boot sequence, no associative flow, no thread preservation.
- **Security**: The gaps between layers are MITM surfaces. Every handoff (compaction summaries, Peace Chief consensus, tier escalations, context links, thread bookmarks) is unverified transit. Chief's directive: **zero trust on all transit**.

Two wolves: **Privacy** (context links surfacing PII into unexpected contexts) and **Security** (every handoff is a potential interception point).

## Components

### 1. Coherence Scan — `/ganuda/scripts/coherence_scan.py`

Session boot sequence. Queries 5 data sources and outputs structured summary:
- Thermal memories modified in last 24h (count + top 5 by temperature)
- Fire Guard circuit breakers (open/half-open)
- Jr tasks in flight
- Last 3 council votes
- Thread bookmarks

**Overhead**: ~47ms total. Reports own timing per section (DC-9 budget).

```bash
python3 scripts/coherence_scan.py --dry-run    # text output
python3 scripts/coherence_scan.py --json       # JSON output
```

### 2. Context Link — `/ganuda/lib/context_link.py`

Proactive associative firing. Given a thermal ID, finds semantically adjacent thermals.

```python
from lib.context_link import get_associated_thermals, get_link_signature, verify_link

# Get 3 nearest thermals, 1 hop
results = get_associated_thermals(thermal_id=122540, max_hops=1, max_results=3)

# Zero trust: sign and verify links
sig = get_link_signature(source_id=122540, dest_id=122521)
valid = verify_link(source_id=122540, dest_id=122521, signature=sig)
```

**Inhibition rules (Coyote)**:
- Max chain depth: 3 hops (prevents seizure)
- Embedding threshold: 0.7 (below = suppress)
- Tag overlap threshold: 2 (fallback path)
- PII tags never auto-fire (Crawdad Wolf 1)
- Sacred thermals only link to sacred thermals

**Zero trust**: Every link carries a sha256 signature (source_hash:dest_hash:timestamp). Receiver verifies within 5-minute rolling window.

### 3. Thread Bookmarks — `/ganuda/lib/thread_bookmarks.py`

Preserves active conversation threads through compaction. Each bookmark has:
- topic, last_action, open_questions, emotional_valence
- file_refs (verified against disk on load)
- checksum (sha256 of topic|action|questions — zero trust)

```python
from lib.thread_bookmarks import save_bookmark, load_bookmarks, format_for_context

save_bookmark(
    topic="DC-18 Autonomic Tiers",
    last_action="ADAPT complete, design doc written",
    open_questions=["Phase 1 triage layer build"],
    valence="momentum",
    file_refs=["/ganuda/docs/design/DC-18-AUTONOMIC-TIERS-IMMUNE-GUARD-MAR10-2026.md"]
)

# Session start: load and verify
bookmarks = load_bookmarks()  # each has ephemeral 'verified' flag
print(format_for_context())   # human-readable for context injection
```

```bash
python3 lib/thread_bookmarks.py --list          # show active
python3 lib/thread_bookmarks.py --save "topic" "action"
python3 lib/thread_bookmarks.py --close "topic"
python3 lib/thread_bookmarks.py --verify         # check all checksums + file refs
```

## Connection Map

- **DC-18** (Autonomic Tiers): Guards at every tier are zero-trust enforcement points
- **DC-10** (Reflex): Verification speed matches tier (checksum=reflex, audit=cortex)
- **DC-9** (Waste Heat): Every component reports its own overhead
- **DC-7** (Noyawisgi): Conserved verification interface survives speciation
- **DC-11** (Macro Polymorphism): SENSE → VERIFY → REACT at every scale

## Gotchas

- `thermal_memory_archive` columns: `original_content` (not `content`), `temperature_score` (not `temperature`), `measured_at` in specialist_health (not `last_check_at`)
- `council_votes` column: `confidence` (not `vote_confidence`), `voted_at` for timestamp
- `jr_work_queue.priority` is integer, not string (no 'P1'/'P2')
- Thread bookmarks file is `/ganuda/config/thread_bookmarks.json` — atomic writes via tempfile+os.replace
- Context link `embedding` column (not `embedding_vector`) — many thermals have NULL embeddings, fallback to tag overlap
- Sacred isolation: if source is sacred, results filtered to sacred only. This is a feature, not a bug.
- PII block tags: `pii`, `credential`, `secret` — hardcoded in context_link.py

## Overhead Budget (DC-9)

Measured on first live run (Mar 10 2026):
```
coherence_scan total:  0.047s
context_link (1-hop):  ~0.1-0.5s (depends on embedding availability)
thread_bookmarks:      <0.001s (file read)
```

All within Gecko's 5-10% overhead budget. Each component reports its own timing.
