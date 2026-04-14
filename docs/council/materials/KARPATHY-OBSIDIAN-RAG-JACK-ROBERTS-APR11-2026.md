# Jack Roberts — Karpathy's Obsidian RAG + Pine Cone Hybrid Memory System — Transcript for Council deliberation

**Presenter:** Jack Roberts (built/sold a startup with 60K customers, runs AI automation business)
**Topic:** Andrej Karpathy's viral (~18M views) tweet on using Claude Code + Obsidian to build a self-updating personal wiki memory system, PLUS Jack's proposed hybrid architecture integrating Pine Cone for exact recall
**Date captured:** April 11, 2026 (Saturday night)
**Filed by:** TPM at Partner's direction — second video on memory systems tonight (first was Justin Sung on six meta models)

---

## Core claim (Karpathy's original)

Use a large language model to build personal knowledge bases for different topics of interest. Data ingestion via Obsidian web clipper or manual. The LLM incrementally compiles a "wiki" — a collection of markdown files in a directory structure — and reads/writes its own memory to supplement its basic context. Gets smarter the more you use it.

## The three-file architecture

Everything lives in three places:
1. **A folder for raw sources** (articles, PDFs, transcripts, web clips)
2. **A folder for the wiki** that Claude writes (summaries, linked structure)
3. **A schema file** (CLAUDE.md equivalent) — "the rules of the game" — conventions, workflows, how Claude should behave as maintainer

## Three operations

1. **Ingest** — drop a new source, Claude reads it, identifies every wiki page it relates to, updates 10-15 pages in a single pass
2. **Query** — ask questions, Claude cycles through the index to find relevant files and reasons over them
3. **Lint** — periodic (every couple weeks) maintenance pass to find contradictions, orphan pages, stale claims that humans would naturally forget about

## Compounding effect

One source updates 10-15 pages. Knowledge stays. Every future query reads from the enriched wiki. Contradictions get ironed out in the process. **"Like your own personal Wikipedia."**

## Four rules for running it well

1. Pick one domain per wiki (one book, one project, one research question — not everything)
2. First session: co-write the rule book with Claude by answering its questions
3. Run two screens: Claude Code on one side, Obsidian graph view on the other
4. Every couple weeks, run the lint/purge pass

## Jack Roberts' critique and hybrid proposal

**What the pure-Obsidian Karpathy approach DOESN'T have** (Jack's list):
- CLAUDE.md grows over time (token tax per session)
- Index file scales linearly with wiki size (750 tokens for 10 files → much more at 10K files)
- No semantic search — goes by topic, not semantics
- Summaries can drift — "callback drift"
- Million-token window fills up quicker
- Not built for very large data sets

**Jack's hybrid proposal:**
- **CLAUDE.md = identity** ("who I am" — voice, rules, read first)
- **Obsidian Rag = reasoning / how I think** (active projects, decision logs, idea gardens, "anywhere structure matters") — the stuff that CHANGES
- **Pine Cone = warehouse / what I've said** (transcripts, research archives, books) — the stuff that DOESN'T change, where exact recall matters
- **Notebook LM = deep dive research** — spin up 200 resources, bring findings back into the long-term memory

**Cost physics**: In Obsidian, Claude has to read the full context window AND type back summaries (expensive). In Pine Cone, embedding cost is ~100× cheaper — Claude isn't involved in ingestion, just a script. Obsidian tokens per query scale linearly; Pine Cone stays flat.

## Jack's analogy layers

- **CLAUDE.md** = identity badge (never changes mid-day)
- **Obsidian** = workshop (where you actively build, notes linked by string, reasoning happens)
- **Pine Cone** = warehouse (big files, transcripts, archives, lives long-term)

## Jack's "magic word" for each

- CLAUDE.md → identity
- Obsidian → reasoning (not memory)
- Pine Cone → recall

## The attachment folder hack (also from Karpathy's tip)

In Obsidian settings, set attachment folder path to a fixed directory (e.g., `raw/assets`), then use the hotkey "download all attachments for current file" so web clippings download images to one place consistently.

## Obsidian Web Clipper Chrome extension

Karpathy mentions Opus/Chrome has an Obsidian web clipper extension — click the extension, specify vault, add to a template that auto-organizes. Relevant for turning a web page into a wiki entry in one click.

---

## Why this is in the Council materials folder

Partner sent this as a second video on memory systems tonight, after the simulated-vs-real-Council correction earlier in the same session. The pattern Jack Roberts describes maps DIRECTLY onto Ganuda's existing four-layer memory substrate:
- CLAUDE.md identity layer → we have global + project CLAUDE.md
- Obsidian wiki workshop → we have 30+ `feedback_*/project_*/reference_*/user_*/deer_signal_*` files in `/home/dereadi/.claude/projects/-ganuda/memory/` with MEMORY.md as boot index
- Pine Cone warehouse → we have `triad_shared_memories` (PostgreSQL + pgvector + HyDE + CRAG + ripple expansion), ~32K rows
- Notebook LM deep dive → we have ii-researcher

Two gaps from Jack's framework worth integrating:
1. **Periodic lint** (offline batch contradiction sweep)
2. **Compounding update discipline** (when a new memory is saved, scan for related existing memories that should cross-reference it)

Full architecture map filed as `reference_ganuda_memory_architecture_layers.md`. Next Council vote on whether to add the lint Jr instruction is deferred to tomorrow so it can benefit from the real Council's input, not be dispatched unilaterally tonight.
