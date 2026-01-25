# JR Instruction: RLM TPM Context Persistence
## Task ID: RLM-TPM-001
## Priority: P2 (after immediate fixes)
## Estimated Complexity: High
## Council Approval: Conditional (Security Audit Required)

---

## Objective

Implement Recursive Language Model (RLM) pattern for TPM context persistence across Claude Code sessions. This eliminates the need for manual context review after session compaction.

---

## Council Concerns (Must Address)

| Specialist | Concern | Resolution Required |
|------------|---------|---------------------|
| Crawdad | Security | Encryption audit, PII protection verified |
| Turtle | 7Gen | Tribal data sovereignty respected |
| Gecko | Performance | No bottlenecks introduced |
| Eagle Eye | Visibility | Logging and monitoring in place |

---

## Architecture Design

### Option A: Thermal Memory Bootstrap (Recommended)

Leverage existing `thermal_memory_archive` table for context persistence.

```python
# /ganuda/lib/rlm_bootstrap.py

class TPMContextBootstrap:
    """Bootstrap TPM context from thermal memory on session start."""

    def __init__(self, db_connection):
        self.db = db_connection

    def get_session_context(self, lookback_hours=24):
        """Retrieve recent context for TPM session."""
        query = """
        SELECT original_content, metadata, created_at
        FROM thermal_memory_archive
        WHERE memory_type IN ('episodic', 'working', 'sacred')
        AND created_at > NOW() - INTERVAL '%s hours'
        AND (
            metadata->>'role' = 'tpm'
            OR metadata->>'project' IN ('vetassist', 'council', 'infrastructure')
        )
        ORDER BY
            CASE WHEN sacred_pattern THEN 0 ELSE 1 END,
            temperature_score DESC,
            created_at DESC
        LIMIT 50
        """
        return self.db.execute(query, [lookback_hours])

    def format_bootstrap_prompt(self, memories):
        """Format memories into CLAUDE.md bootstrap section."""
        sections = {
            'recent_decisions': [],
            'active_tasks': [],
            'pending_items': [],
            'key_learnings': []
        }

        for memory in memories:
            # Categorize and format each memory
            pass

        return self._render_template(sections)
```

### Option B: Dedicated RLM Service

Create standalone service that maintains TPM state.

```yaml
# /ganuda/services/rlm_tpm/config.yaml
service:
  name: rlm-tpm-context
  port: 8090

persistence:
  backend: postgresql
  table: tpm_session_context

bootstrap:
  sources:
    - thermal_memory_archive
    - jr_work_queue
    - council_votes
    - duyuktv_tickets

context_window:
    max_tokens: 16000
    priority_order:
      - sacred_memories
      - recent_decisions
      - active_tasks
      - pending_work
```

### Option C: Claude Code Hook Integration

Use Claude Code hooks to auto-inject context on session start.

```bash
# ~/.claude/hooks/session-start.sh
#!/bin/bash

# Pull context from thermal memory
CONTEXT=$(psql -h 192.168.132.222 -U claude -d zammad_production -t -c "
SELECT json_agg(row_to_json(t))
FROM (
    SELECT original_content, metadata
    FROM thermal_memory_archive
    WHERE created_at > NOW() - INTERVAL '24 hours'
    AND metadata->>'role' = 'tpm'
    ORDER BY temperature_score DESC
    LIMIT 20
) t;
")

# Update CLAUDE.md with fresh context
python3 /ganuda/scripts/update_claude_context.py "$CONTEXT"
```

---

## Implementation Steps

### Phase 1: Security Audit (Required by Crawdad)
1. Document all data flows for RLM context
2. Verify PII filtering in place (Presidio)
3. Confirm encryption at rest and in transit
4. Review access controls on thermal_memory_archive

### Phase 2: Performance Testing (Required by Gecko)
1. Benchmark context retrieval queries
2. Test with 100, 500, 1000 memory lookback
3. Ensure bootstrap completes in <5 seconds
4. Profile memory usage

### Phase 3: Implementation
1. Create `/ganuda/lib/rlm_bootstrap.py`
2. Add bootstrap query functions
3. Create context formatting templates
4. Integrate with CLAUDE.md generation

### Phase 4: Monitoring (Required by Eagle Eye)
1. Log all context bootstrap events
2. Track context size metrics
3. Alert on bootstrap failures
4. Dashboard for RLM health

---

## Database Schema Extension

```sql
-- Track TPM sessions for RLM continuity
CREATE TABLE IF NOT EXISTS tpm_session_context (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_start TIMESTAMP NOT NULL DEFAULT NOW(),
    session_end TIMESTAMP,
    context_snapshot JSONB,
    decisions_made JSONB DEFAULT '[]',
    tasks_completed TEXT[],
    bootstrap_source TEXT DEFAULT 'thermal_memory',
    token_count INTEGER,
    compaction_count INTEGER DEFAULT 0
);

-- Index for fast session lookup
CREATE INDEX idx_tpm_session_recent ON tpm_session_context(session_start DESC);

-- Function to auto-archive session on close
CREATE OR REPLACE FUNCTION archive_tpm_session()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO thermal_memory_archive (
        original_content,
        memory_type,
        metadata,
        sacred_pattern
    ) VALUES (
        'TPM Session: ' || NEW.session_id::text,
        'episodic',
        jsonb_build_object(
            'role', 'tpm',
            'session_id', NEW.session_id,
            'decisions', NEW.decisions_made,
            'tasks', NEW.tasks_completed,
            'tokens', NEW.token_count
        ),
        false
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

---

## CLAUDE.md Integration

Add to CLAUDE.md:

```markdown
## RLM Context Bootstrap

On session start, the following context was auto-loaded from thermal memory:

### Recent Decisions (last 24h)
[Auto-populated from council_votes where tpm_vote IS NOT NULL]

### Active Tasks
[Auto-populated from jr_work_queue where status IN ('pending', 'in_progress')]

### Key Learnings
[Auto-populated from thermal_memory where memory_type = 'sacred']

### Session Continuity
Previous session: [session_id]
Compaction count: [N]
Context tokens: [M]
```

---

## Acceptance Criteria

1. [ ] Security audit completed and signed off by Crawdad
2. [ ] Performance benchmarks meet <5 second bootstrap
3. [ ] Context automatically loads on new Claude Code session
4. [ ] No manual context review needed after compaction
5. [ ] Monitoring dashboard shows RLM health
6. [ ] Tribal data sovereignty requirements documented

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Context overflow | Limit to 16K tokens, prioritize sacred memories |
| Stale context | 24-hour rolling window, temperature decay |
| Security leak | PII filtering, encryption, access audit |
| Performance hit | Async bootstrap, caching layer |

---

## Dependencies

- Presidio PII service (for filtering)
- PostgreSQL thermal_memory_archive (source)
- Claude Code hooks (for auto-injection)

---

*Cherokee AI Federation - For Seven Generations*
*Council Approval: Conditional on Security Audit*
