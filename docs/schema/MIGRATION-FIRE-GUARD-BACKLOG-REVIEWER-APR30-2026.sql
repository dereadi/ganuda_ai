-- Migration: LMC-16 Workflow Proceduralization — Fire Guard Backlog Reviewer
-- Date: 2026-04-30
-- Authorizing Council vote: 08c642a0fd176a92 (DELIBERATE phase, Diversity 0.358 HEALTHY)
-- DISCOVER doc: /ganuda/docs/lm_workflow_proceduralization_discover.md
-- ADAPT plan:   /ganuda/docs/lm_workflow_proceduralization_adapt_plan.md
--
-- Concerns absorbed (per Council audit 08c642a0fd176a92):
--   Crawdad CRITICAL: append-only audit log via DB trigger (Sacred-Pattern pattern reuse)
--   Crawdad HIGH:     trusted timestamp via PostgreSQL NOW()
--   Eagle Eye:        manual-only close for MVP (enforced via classification value enum, no auto-close path)
--   Spider:           single-writer audit log (immutable trigger blocks UPDATE/DELETE)
--   Turtle 7GEN:      versioned taxonomy table for future-generation evolution
--
-- TRANSACTIONAL DISCIPLINE: file does NOT include inner BEGIN/COMMIT.
-- Caller wraps:  psql ... -c "BEGIN; \i this_file.sql; COMMIT;"
-- Dry-run wrap:  psql ... -c "BEGIN; \i this_file.sql; ROLLBACK;"

-- ============================================================================
-- Part 1 — classification_audit_log: append-only hash-chained classification record
-- ============================================================================

CREATE TABLE IF NOT EXISTS classification_audit_log (
  id                   BIGSERIAL PRIMARY KEY,
  ticket_id            INTEGER NOT NULL REFERENCES duyuktv_tickets(id),
  classification       VARCHAR(32) NOT NULL,
  rationale            TEXT,
  prev_hash            VARCHAR(64),
  this_hash            VARCHAR(64) NOT NULL UNIQUE,
  classified_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  council_audit_hash   VARCHAR(64),
  taxonomy_version_id  INTEGER,
  partner_ratified_at  TIMESTAMPTZ,
  partner_action       VARCHAR(32),
  CHECK (classification IN ('still_relevant','needs_decomposition','close_as_stale','active_epic_continuation','backlog_candidate')),
  CHECK (partner_action IS NULL OR partner_action IN ('keep','close','decompose','reject_classification'))
);

COMMENT ON TABLE classification_audit_log IS
  'Append-only audit trail of Fire Guard backlog reviewer classifications. Authorizing Council vote 08c642a0fd176a92. Prev_hash + this_hash form a hash chain for tamper-detection (Crawdad CRITICAL mitigation). Partner_action populated only after Slack ratification (Coyote dissent + Eagle Eye discipline: manual-only close).';

COMMENT ON COLUMN classification_audit_log.classification IS
  'One of: still_relevant (keep in backlog as-is), needs_decomposition (Epic blob to split), close_as_stale (>14-day rule violation, no recovery path), active_epic_continuation (intake routing: belongs in active Epic), backlog_candidate (intake routing: file as new backlog ticket).';

COMMENT ON COLUMN classification_audit_log.partner_action IS
  'Populated by Partner ratification path. NULL = awaiting ratification. reject_classification = classifier got it wrong, signals classifier-health-degradation per Eagle Eye SLA (>20% rejection over 7-day window halts classifier).';

CREATE INDEX IF NOT EXISTS idx_classification_audit_ticket
  ON classification_audit_log(ticket_id, classified_at DESC);

CREATE INDEX IF NOT EXISTS idx_classification_audit_unratified
  ON classification_audit_log(classified_at DESC)
  WHERE partner_action IS NULL;

CREATE INDEX IF NOT EXISTS idx_classification_audit_rejections
  ON classification_audit_log(classified_at DESC)
  WHERE partner_action = 'reject_classification';

-- ============================================================================
-- Part 2 — classification_taxonomy_versions: versioned class definitions (Turtle 7GEN)
-- ============================================================================

CREATE TABLE IF NOT EXISTS classification_taxonomy_versions (
  version_id            SERIAL PRIMARY KEY,
  introduced_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  council_audit_hash    VARCHAR(64),
  taxonomy_definition   JSONB NOT NULL,
  superseded_at         TIMESTAMPTZ,
  superseded_by_version INTEGER REFERENCES classification_taxonomy_versions(version_id),
  notes                 TEXT,
  CHECK (taxonomy_definition ? 'classes')
);

COMMENT ON TABLE classification_taxonomy_versions IS
  'Versioned classification taxonomy. Turtle 7GEN concern absorbed: future TPMs can introduce new classes / refine definitions via Council vote without infrastructure rewrite. Superseded versions preserved for audit-trail continuity.';

CREATE INDEX IF NOT EXISTS idx_taxonomy_active
  ON classification_taxonomy_versions(introduced_at DESC)
  WHERE superseded_at IS NULL;

-- ============================================================================
-- Part 3 — Immutable-append trigger on classification_audit_log
-- ============================================================================

CREATE OR REPLACE FUNCTION classification_audit_immutable()
RETURNS TRIGGER AS $$
BEGIN
  RAISE EXCEPTION 'classification_audit_log is append-only (LMC-16 Crawdad CRITICAL mitigation, Council audit 08c642a0fd176a92). UPDATE and DELETE forbidden. To correct a classification, INSERT a new row with rationale referencing the prior this_hash.';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_classification_audit_immutable ON classification_audit_log;
CREATE TRIGGER trg_classification_audit_immutable
BEFORE UPDATE OR DELETE ON classification_audit_log
FOR EACH ROW EXECUTE FUNCTION classification_audit_immutable();

-- ============================================================================
-- Part 4 — Allow partner_action UPDATE via dedicated function (Eagle Eye discipline)
-- The trigger above blocks ALL UPDATE; a separate function bypasses it for the
-- specific case of recording Partner ratification (only the partner_action +
-- partner_ratified_at columns).
-- ============================================================================

CREATE OR REPLACE FUNCTION ratify_classification(
  p_audit_id      BIGINT,
  p_partner_action VARCHAR(32)
) RETURNS VOID AS $$
DECLARE
  v_existing_action VARCHAR(32);
BEGIN
  IF p_partner_action NOT IN ('keep','close','decompose','reject_classification') THEN
    RAISE EXCEPTION 'invalid partner_action: %', p_partner_action;
  END IF;

  -- Check if already ratified (idempotency / no double-ratification)
  SELECT partner_action INTO v_existing_action
    FROM classification_audit_log WHERE id = p_audit_id;

  IF v_existing_action IS NOT NULL THEN
    RAISE EXCEPTION 'classification_audit_log id % already ratified with action %', p_audit_id, v_existing_action;
  END IF;

  -- Bypass the immutable trigger using session-replication-role discipline
  SET LOCAL session_replication_role = 'replica';
  UPDATE classification_audit_log
    SET partner_action = p_partner_action,
        partner_ratified_at = NOW()
    WHERE id = p_audit_id;
  SET LOCAL session_replication_role = 'origin';
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION ratify_classification IS
  'Records Partner ratification of a classification. Idempotent (rejects double-ratification). Session-replication-role bypass scoped to this function only; immutable trigger remains active for all other paths.';

-- ============================================================================
-- Part 5 — Grants for claude_council role (LMC-15 Stage 4 SET ROLE pattern)
-- ============================================================================

GRANT SELECT ON classification_taxonomy_versions TO claude_council;
GRANT SELECT, INSERT ON classification_audit_log TO claude_council;
GRANT USAGE, SELECT ON SEQUENCE classification_audit_log_id_seq TO claude_council;
GRANT EXECUTE ON FUNCTION ratify_classification(BIGINT, VARCHAR) TO claude_council;
-- duyuktv_tickets read needed by get_unratified_classifications JOIN
GRANT SELECT ON duyuktv_tickets TO claude_council;

-- ============================================================================
-- Part 6 — Initial taxonomy v1 entry (will be inserted by build script after migration apply)
-- ============================================================================
-- (Not in this migration; populated post-apply via Step 2 module init.)

-- ============================================================================
-- Verification queries (run after migration applies)
-- ============================================================================
-- \d classification_audit_log
-- \d classification_taxonomy_versions
-- SELECT count(*) FROM classification_audit_log;
-- SELECT count(*) FROM classification_taxonomy_versions;
-- SELECT tgname FROM pg_trigger WHERE tgrelid='classification_audit_log'::regclass AND NOT tgisinternal;

-- ============================================================================
-- ROLLBACK (Turtle 7GEN reversibility)
-- ============================================================================
-- BEGIN;
--   DROP FUNCTION IF EXISTS ratify_classification(BIGINT, VARCHAR);
--   DROP TRIGGER IF EXISTS trg_classification_audit_immutable ON classification_audit_log;
--   DROP FUNCTION IF EXISTS classification_audit_immutable();
--   DROP TABLE IF EXISTS classification_audit_log;
--   DROP TABLE IF EXISTS classification_taxonomy_versions;
-- COMMIT;
