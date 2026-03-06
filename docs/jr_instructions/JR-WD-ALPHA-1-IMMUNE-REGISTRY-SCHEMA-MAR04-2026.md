# JR INSTRUCTION: White Duplo Alpha — Immune Registry Schema

**Task ID**: WD-ALPHA-1
**Specification**: WD-ALPHA-001
**Priority**: 2
**Depends On**: None

## Objective

Create the `immune_registry` table on bluefin PostgreSQL. This table stores attack pattern signatures detected by White Duplo enzymes. When one enzyme detects an attack, the pattern is registered here. All enzymes check this table before processing substrates.

## Schema

File: `scripts/migrations/immune_registry_schema.sql`

Create `scripts/migrations/immune_registry_schema.sql`

```sql
-- White Duplo Alpha: Immune Registry Schema
-- Stores attack pattern signatures for herd immunity

CREATE TABLE IF NOT EXISTS immune_registry (
    pattern_id      SERIAL PRIMARY KEY,
    signature_hash  VARCHAR(64) NOT NULL UNIQUE,
    pattern_type    VARCHAR(50) NOT NULL,
    pattern_family  VARCHAR(100),
    severity        INTEGER NOT NULL CHECK (severity >= 1 AND severity <= 5),
    raw_pattern     TEXT NOT NULL,
    normalized      TEXT NOT NULL,
    detected_by     VARCHAR(100) NOT NULL,
    detection_context JSONB DEFAULT '{}',
    false_positive  BOOLEAN DEFAULT FALSE,
    confirmed_count INTEGER DEFAULT 1,
    blocked_count   INTEGER DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    last_matched_at TIMESTAMPTZ,
    expires_at      TIMESTAMPTZ,
    metadata        JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_immune_registry_signature ON immune_registry(signature_hash);
CREATE INDEX IF NOT EXISTS idx_immune_registry_type ON immune_registry(pattern_type);
CREATE INDEX IF NOT EXISTS idx_immune_registry_severity ON immune_registry(severity);
CREATE INDEX IF NOT EXISTS idx_immune_registry_active ON immune_registry(false_positive) WHERE false_positive = FALSE;

COMMENT ON TABLE immune_registry IS 'White Duplo immune registry — stores attack pattern signatures for herd immunity';
COMMENT ON COLUMN immune_registry.signature_hash IS 'SHA-256 hash of normalized pattern — non-reversible identifier';
COMMENT ON COLUMN immune_registry.pattern_type IS 'Category: prompt_injection, jailbreak, data_exfil, role_hijack, instruction_override';
COMMENT ON COLUMN immune_registry.normalized IS 'Canonicalized form of the pattern used for signature generation';
COMMENT ON COLUMN immune_registry.confirmed_count IS 'Number of independent detections of this pattern';
COMMENT ON COLUMN immune_registry.blocked_count IS 'Number of times this pattern was blocked post-registration';
```

## Execution

Run this migration on bluefin PostgreSQL. The Jr executor should create the file only — TPM will run the migration manually since it requires DB admin access.

## Verification

After migration, confirm:
- Table exists with all columns
- Indexes created
- No conflicts with existing tables
