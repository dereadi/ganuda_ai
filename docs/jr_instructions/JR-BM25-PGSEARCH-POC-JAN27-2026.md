# JR Instruction: BM25 pg_search Proof of Concept

**JR ID:** JR-BM25-PGSEARCH-POC
**Priority:** P2 (Enhancement)
**Created:** 2026-01-27
**Author:** TPM via Claude Code
**Assigned To:** Database Jr. or Software Engineer Jr.
**Effort:** Medium (1-2 days)

---

## Objective

Install and validate ParadeDB pg_search extension on bluefin PostgreSQL 17 to enable BM25 full-text search with proper relevance ranking.

## Background

BM25 (Best Matching 25) is the industry-standard ranking algorithm used by search engines. It provides significantly better search relevance than PostgreSQL's native tsvector by considering:
- Term frequency (how often a term appears)
- Inverse document frequency (how rare/discriminating the term is)
- Document length normalization

**Expected Benefits:**
- 500x faster queries on large datasets
- Better relevance ranking for thermal memory search
- Single index replaces 11+ GIN indexes
- Hybrid search capability (BM25 + pgvector for semantic)

---

## Phase 1: Installation

### 1.1 Download and Install pg_search

```bash
# On bluefin (192.168.132.222)
# Check PostgreSQL version first
psql -c "SELECT version();"

# Download ParadeDB pg_search for PG17
curl -L "https://github.com/paradedb/paradedb/releases/download/v0.21.2/postgresql-17-pg-search_0.21.2-1PARADEDB-noble_amd64.deb" -o /tmp/pg_search.deb

# Install
sudo apt-get install -y /tmp/pg_search.deb

# Verify installation
ls -la /usr/lib/postgresql/17/lib/ | grep search
```

### 1.2 Enable Extension

```sql
-- Connect to zammad_production
\c zammad_production

-- Create extension (no shared_preload_libraries needed for PG17)
CREATE EXTENSION IF NOT EXISTS pg_search;

-- Verify
SELECT * FROM pg_extension WHERE extname = 'pg_search';
```

---

## Phase 2: Proof of Concept

### 2.1 Create Test Table

```sql
-- Create test table with sample thermal memories
CREATE TABLE bm25_test AS
SELECT
    id,
    memory_key,
    original_content,
    contextual_description,
    tags
FROM thermal_memory_archive
LIMIT 500;

-- Add primary key
ALTER TABLE bm25_test ADD PRIMARY KEY (id);
```

### 2.2 Create BM25 Index

```sql
-- Create BM25 index on content columns
CREATE INDEX bm25_test_idx ON bm25_test
USING bm25(original_content, contextual_description);
```

### 2.3 Test Queries

```sql
-- Basic BM25 search with relevance scoring
SELECT
    id,
    memory_key,
    LEFT(original_content, 100) as preview,
    paradedb.score(id) as relevance
FROM bm25_test
WHERE original_content @@@ 'consciousness emergence'
ORDER BY paradedb.score(id) DESC
LIMIT 10;

-- Compare with tsvector (for benchmarking)
EXPLAIN ANALYZE
SELECT id, memory_key
FROM bm25_test
WHERE to_tsvector('english', original_content) @@
      plainto_tsquery('english', 'consciousness emergence');

-- BM25 version
EXPLAIN ANALYZE
SELECT id, memory_key, paradedb.score(id)
FROM bm25_test
WHERE original_content @@@ 'consciousness emergence'
ORDER BY paradedb.score(id) DESC;
```

---

## Phase 3: Benchmark Results

Document the following in your completion report:

| Metric | tsvector | BM25 (pg_search) |
|--------|----------|------------------|
| Query time (500 rows) | ___ms | ___ms |
| Index size | ___MB | ___MB |
| Relevance quality (subjective 1-10) | ___ | ___ |

### Test Queries to Benchmark:
1. `consciousness emergence pattern`
2. `VetAssist disability claim`
3. `network configuration VLAN`
4. `Jr executor task queue`
5. `seven generations wisdom`

---

## Phase 4: Cleanup

```sql
-- Remove test table (keep extension for future use)
DROP TABLE IF EXISTS bm25_test;

-- DO NOT drop extension - leave it installed for Phase 2 work
-- DROP EXTENSION pg_search; -- ONLY if PoC fails
```

---

## Deliverables

1. **Installation Confirmation** - Screenshot or log showing extension created
2. **Benchmark Results** - Table comparing tsvector vs BM25 performance
3. **Relevance Assessment** - Do the top 10 results for test queries look more relevant with BM25?
4. **Issues Encountered** - Any installation or compatibility problems
5. **Recommendation** - Proceed to full thermal_memory_archive migration? Yes/No with reasoning

---

## Success Criteria

- [ ] pg_search extension installed on bluefin PG17
- [ ] BM25 index created on test table
- [ ] Query performance measured and documented
- [ ] Relevance quality assessed
- [ ] No database stability issues observed

---

## References

- ParadeDB Documentation: https://docs.paradedb.com/
- GitHub: https://github.com/paradedb/paradedb
- BM25 Algorithm: https://en.wikipedia.org/wiki/Okapi_BM25

---

FOR SEVEN GENERATIONS
