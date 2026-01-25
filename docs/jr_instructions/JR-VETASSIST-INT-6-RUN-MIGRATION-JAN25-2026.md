# JR Instruction: VetAssist Integration Part 6 - Run Database Migration

**Task ID:** VETASSIST-INT-MIGRATE-001
**Priority:** P1
**Type:** infrastructure
**Assigned:** Infrastructure Jr.

---

## Objective

Execute the SQL migration on goldfin to add document classification fields and create evidence tracking tables.

---

## Deliverable

Run the migration script on the goldfin database server.

### Prerequisites

- Migration file exists at: `/ganuda/vetassist/backend/migrations/001_add_classification_fields.sql`
- Database: `vetassist` on goldfin (192.168.132.225 or goldfin.tail8df74e.ts.net)
- User: `vetassist_app`

### Execution

SSH to goldfin and run:

```bash
# Connect to goldfin
ssh dereadi@goldfin.tail8df74e.ts.net

# Run the migration
psql -h localhost -U vetassist_app -d vetassist -f /ganuda/vetassist/backend/migrations/001_add_classification_fields.sql

# Verify tables created
psql -h localhost -U vetassist_app -d vetassist -c "\dt vetassist_*"
```

### Expected Results

After migration, these objects should exist:
1. `vetassist_documents` table with new columns:
   - `document_type VARCHAR(50)`
   - `classification_confidence FLOAT`
   - `parsed_data JSONB`
   - `ocr_text TEXT`
   - `processing_status VARCHAR(20)`
   - `processing_error TEXT`

2. New table: `vetassist_evidence_gaps`
3. New table: `vetassist_dd214_data`
4. Indexes: `idx_vetassist_docs_type`, `idx_vetassist_docs_status`, `idx_evidence_gaps_veteran`, `idx_evidence_gaps_session`, `idx_dd214_document`

---

## Success Criteria

- Migration runs without errors
- All three table alterations/creations complete
- Indexes created successfully

---

## For Seven Generations

Reliable database schema enables consistent evidence tracking across veteran sessions.
