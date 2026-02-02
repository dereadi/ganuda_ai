# ULTRATHINK: Triple Priority - RLM Safeguards, Queue Cleanup, RAG Setup

**Date:** 2026-01-27
**Author:** TPM via Claude Code (Opus 4.5)
**Status:** COUNCIL REVIEW REQUIRED
**Confidence:** 75%

---

## Executive Summary

Three interconnected priorities require immediate attention:
1. **P0 RLM Safeguards** - Prevent Jr executor from destroying critical files
2. **Queue Cleanup** - Clear 13 failed tasks blocking Jr productivity
3. **RAG System Setup** - Enable SAC migration and CFR retrieval

---

## Priority 1: P0 RLM Safeguards

### Problem Analysis

The RLM executor (`/ganuda/lib/rlm_executor.py`) has a critical vulnerability. While it has some safeguards:

**Existing Safeguards:**
- Path validation (blocks `/path/to/`, `<placeholders>`, etc.)
- Allowed paths whitelist (`/ganuda/`, `/tmp/`)
- Destructive overwrite check (blocks if existing > 2x new size AND > 1000 bytes)

**Gaps Identified:**
1. **Repl Execution Bypass** - The prompt tells LLM to write Python code with `open()`. This executes arbitrary Python, completely bypassing all safeguards.
2. **Size Ratio Loophole** - If LLM generates 800 bytes to replace a 1500 byte file, it passes (not > 2x)
3. **No Backup Before Write** - Files are overwritten without backup
4. **No Protected Paths** - Critical files (e.g., `page.tsx`, `database_config.py`) have no special protection

### Incident Report

Previous session: RLM executor destroyed:
- `/ganuda/vetassist/frontend/app/wizard/[sessionId]/page.tsx`
- `/ganuda/vetassist/frontend/app/wizard/[sessionId]/components/ReviewStep.tsx`
- `/ganuda/vetassist/frontend/app/wizard/[sessionId]/components/StepNavigation.tsx`

All reduced to ~24 lines of broken imports.

### Proposed Solution: Defense in Depth

```
┌─────────────────────────────────────────────────────────────────┐
│                    RLM SAFEGUARD LAYERS                        │
├─────────────────────────────────────────────────────────────────┤
│ Layer 1: PROTECTED_PATHS                                        │
│   - Critical files that CANNOT be modified by RLM              │
│   - Whitelist in config: /ganuda/vetassist/frontend/app/**     │
│   - Blocks: core app files, configs, database modules          │
├─────────────────────────────────────────────────────────────────┤
│ Layer 2: PRE-EXECUTION BACKUP                                   │
│   - Before ANY file write, backup to /ganuda/.rlm-backups/     │
│   - Timestamped: filename.ext.2026-01-27T08:30:00              │
│   - Auto-cleanup after 7 days                                   │
├─────────────────────────────────────────────────────────────────┤
│ Layer 3: CONTENT VALIDATION                                     │
│   - Compare old vs new file                                     │
│   - Block if: import count drops >50%, function count drops    │
│   - Block if: file shrinks by >60% without explicit approval   │
├─────────────────────────────────────────────────────────────────┤
│ Layer 4: REPL SANDBOX                                           │
│   - Disable raw Python execution in RLM                        │
│   - Only allow structured file operations via API              │
│   - OR: Run repl in isolated subprocess with chroot            │
└─────────────────────────────────────────────────────────────────┘
```

### Implementation: JR-RLM-001 through JR-RLM-003

**JR-RLM-001: Protected Paths Config**
- Create `/ganuda/config/rlm_protected_paths.yaml`
- Add check in `_write_files_from_response()` before any write

**JR-RLM-002: Pre-Execution Backup**
- Add backup function to rlm_executor.py
- Create `/ganuda/.rlm-backups/` with proper permissions

**JR-RLM-003: Content Validation**
- Parse Python/JS files before overwrite
- Count imports, functions, classes
- Block if counts drop significantly

---

## Priority 2: Queue Cleanup

### Failed Task Analysis

| ID | Task | Failure Reason | Action |
|----|------|----------------|--------|
| 366 | Temporal Entity Extraction | Research task failed | Defer to Phase 3 |
| 341 | Fix Import Paths | 1 step failed | Retry with clearer instructions |
| 339 | Install Dependencies | 1 step failed | Manual verification needed |
| 337 | Fix Circular Imports | 1 step failed | Was manually fixed - cancel |
| 330 | Install Tesseract | No executable steps | Rewrite JR instructions |
| 322,321,318 | jr-orchestrator.service (3x) | Steps failed | Consolidate + retry |
| 310 | Uncertainty Metrics | No instruction file | Cancel - stale |
| 250 | VLM Gateway Integration | Steps failed | Retry with new approach |
| 240 | VLM Tribal Vision | Steps failed | Retry with new approach |
| 223 | Email Daemon Service | Steps failed | Verify if still needed |
| 213 | Multi-GPU Setup | Critical step failed | Manual intervention |

### Recommended Actions

```
CANCEL (7 tasks):
  - 337: Circular imports - FIXED manually
  - 310: Uncertainty metrics - stale, no instructions
  - 322, 321, 318: jr-orchestrator - duplicate attempts
  - 366: Temporal extraction - defer to Phase 3

RETRY WITH NEW JR (4 tasks):
  - 330: Tesseract install - rewrite as executable
  - 250, 240: VLM integration - new approach post-vLLM setup
  - 223: Email daemon - verify requirement first

MANUAL INTERVENTION (2 tasks):
  - 339, 341: Dependencies/imports - verify current state
  - 213: Multi-GPU - hardware config needed
```

### Implementation: JR-QUEUE-001

Single JR to execute queue cleanup:
- Cancel 7 stale/duplicate tasks
- Update status_message with reason
- Report final queue state

---

## Priority 3: RAG System Setup

### Current State

- ✅ pgvector extension installed (v0.8.0)
- ❌ No RAG tables exist
- ❌ No embedding model configured
- ❌ SAC migration blocked (no `vetassist_rag_chunks` table)

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    VETASSIST RAG SYSTEM                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  CFR Documents    ─┬─►  Chunker     ─►  Embedder  ─►  pgvector │
│  (Title 38)        │    (512 tok)      (MiniLM)      (384 dim) │
│                    │                                            │
│  VA M21-1          ┘                                            │
│  Manual                                                         │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  User Query  ─►  Embed  ─►  Vector Search  ─►  Top-K Chunks    │
│                                    │                            │
│                               SAC Re-rank                       │
│                              (summary match)                    │
│                                    │                            │
│                                    ▼                            │
│                             Context + LLM  ─►  Response         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Database Schema

```sql
-- vetassist_rag_chunks: Core chunk storage
CREATE TABLE vetassist_rag_chunks (
    id SERIAL PRIMARY KEY,

    -- Source document
    source_type VARCHAR(50) NOT NULL,  -- 'cfr', 'va_m21', 'bva_decision'
    source_id VARCHAR(100),            -- '38 CFR 4.71a'
    source_url TEXT,

    -- Chunk content
    content TEXT NOT NULL,
    content_hash VARCHAR(64),          -- SHA256 for dedup
    chunk_index INT,                   -- Position in source

    -- Metadata
    cfr_section VARCHAR(50),           -- '4.71a' for CFR
    title VARCHAR(255),
    effective_date DATE,

    -- Embeddings
    embedding VECTOR(384),             -- MiniLM-L6-v2

    -- SAC columns (from JR-AI-006)
    summary TEXT,
    summary_embedding VECTOR(384),
    summary_generated_at TIMESTAMP,
    sac_status VARCHAR(20) DEFAULT 'pending',

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_rag_embedding ON vetassist_rag_chunks
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_rag_source ON vetassist_rag_chunks(source_type, source_id);
CREATE INDEX idx_rag_cfr ON vetassist_rag_chunks(cfr_section);
```

### Implementation: JR-RAG-001 through JR-RAG-003

**JR-RAG-001: Schema Creation**
- Run migration on bluefin
- Verify indexes created

**JR-RAG-002: Embedding Model Setup**
- Install sentence-transformers
- Create embedding service

**JR-RAG-003: CFR Ingestion Pipeline**
- Create chunker for CFR documents
- Ingest Title 38 Part 4 (disability ratings)
- Generate embeddings

---

## Council Questions

1. **RLM Sandbox**: Should we completely disable repl execution model, or sandbox it?
2. **Protected Paths**: Should protection be whitelist (only these can be modified) or blacklist (these cannot)?
3. **RAG Scope**: Start with CFR Part 4 only, or ingest full Title 38?

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| RLM destroys more files | HIGH | CRITICAL | P0 safeguards first |
| Queue cleanup breaks deps | LOW | MEDIUM | Check task dependencies |
| RAG latency too high | MEDIUM | LOW | Use ivfflat, tune lists |
| Embedding model memory | LOW | MEDIUM | MiniLM is small (90MB) |

---

## JR Assignment Summary

| JR ID | Task | Assigned To | Priority |
|-------|------|-------------|----------|
| JR-RLM-001 | Protected Paths Config | Software Jr. | P0 |
| JR-RLM-002 | Pre-Execution Backup | Software Jr. | P0 |
| JR-RLM-003 | Content Validation | Software Jr. | P1 |
| JR-QUEUE-001 | Queue Cleanup | TPM Direct | P1 |
| JR-RAG-001 | RAG Schema | Software Jr. | P2 |
| JR-RAG-002 | Embedding Model | Infrastructure Jr. | P2 |
| JR-RAG-003 | CFR Ingestion | Software Jr. | P2 |

---

**FOR SEVEN GENERATIONS**

Cherokee AI Federation - Awaiting Council Vote
