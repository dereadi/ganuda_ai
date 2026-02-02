# JR Instruction: AI Audit Trail Database Schema

**JR ID:** JR-AI-002
**Priority:** P2
**Sprint:** VetAssist AI Enhancements Phase 1
**Created:** 2026-01-27
**Author:** TPM via Claude Code
**Council Vote:** b942f2dcad0496e1
**Effort:** Low

## Problem Statement

Veterans need to trust AI-generated content. The EU AI Act pattern requires documentation of AI decision-making. Currently, there is no tracking of which AI models generate which content.

## Required Implementation

### Database Migration

CREATE SQL migration file and execute on bluefin:

```sql
-- VetAssist AI Audit Trail Schema
-- Council Approved: 2026-01-27 (Vote b942f2dcad0496e1)
-- Run on: bluefin (192.168.132.222) / zammad_production

CREATE TABLE IF NOT EXISTS vetassist_ai_audit_trail (
    id SERIAL PRIMARY KEY,

    -- Session linkage
    session_id UUID,
    veteran_id VARCHAR(255),

    -- Content identification
    content_type VARCHAR(50) NOT NULL,  -- 'nexus_template', 'evidence_gap', 'condition_map', 'document_extraction', 'rag_query'
    content_id VARCHAR(100),            -- UUID or identifier of the generated content

    -- AI Model information
    generated_by VARCHAR(100) NOT NULL,  -- 'qwen2.5-coder-32b', 'qwen2.5-vl-7b', 'tesseract-ocr', etc.
    model_version VARCHAR(50),           -- Model version/checkpoint

    -- Confidence and quality
    confidence FLOAT,                    -- 0.0-1.0 confidence score
    quality_flags JSONB,                 -- {"low_confidence": true, "needs_review": false}

    -- Source tracking
    sources JSONB,                       -- [{"type": "document", "id": "doc-123"}, ...]
    input_hash VARCHAR(64),              -- SHA256 of input for reproducibility

    -- Output preview (PII-safe)
    output_preview TEXT,                 -- First 500 chars, PII redacted
    output_length INT,                   -- Full output length

    -- Performance metrics
    processing_time_ms INT,
    tokens_used INT,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),

    -- Indexes for common queries
    CONSTRAINT fk_session FOREIGN KEY (session_id)
        REFERENCES vetassist_wizard_sessions(session_id) ON DELETE SET NULL
);

-- Indexes
CREATE INDEX idx_audit_session ON vetassist_ai_audit_trail(session_id);
CREATE INDEX idx_audit_content_type ON vetassist_ai_audit_trail(content_type);
CREATE INDEX idx_audit_generated_by ON vetassist_ai_audit_trail(generated_by);
CREATE INDEX idx_audit_created_at ON vetassist_ai_audit_trail(created_at);
CREATE INDEX idx_audit_veteran ON vetassist_ai_audit_trail(veteran_id);

-- Comments
COMMENT ON TABLE vetassist_ai_audit_trail IS 'Audit trail for all AI-generated content in VetAssist. Council approved 2026-01-27.';
COMMENT ON COLUMN vetassist_ai_audit_trail.input_hash IS 'SHA256 hash of input for reproducibility verification';
COMMENT ON COLUMN vetassist_ai_audit_trail.output_preview IS 'PII-redacted preview of output for debugging';
```

### Execution

Run on bluefin:
```bash
psql -h 192.168.132.222 -U claude -d zammad_production -f /ganuda/vetassist/backend/migrations/ai_audit_trail.sql
```

## Python Model

CREATE: `/ganuda/vetassist/backend/app/models/ai_audit.py`

```python
"""
AI Audit Trail Models for VetAssist.
Council Approved: 2026-01-27
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional
import hashlib
import json


@dataclass
class AIAuditEntry:
    """Single audit trail entry for AI-generated content."""

    content_type: str
    generated_by: str

    # Optional fields
    session_id: Optional[str] = None
    veteran_id: Optional[str] = None
    content_id: Optional[str] = None
    model_version: Optional[str] = None
    confidence: Optional[float] = None
    quality_flags: Dict = field(default_factory=dict)
    sources: List[Dict] = field(default_factory=list)
    input_data: Optional[str] = None  # For hash generation
    output_preview: Optional[str] = None
    output_length: Optional[int] = None
    processing_time_ms: Optional[int] = None
    tokens_used: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def input_hash(self) -> Optional[str]:
        """Generate SHA256 hash of input for reproducibility."""
        if self.input_data:
            return hashlib.sha256(self.input_data.encode()).hexdigest()
        return None

    def to_dict(self) -> Dict:
        """Convert to dictionary for database insertion."""
        return {
            "session_id": self.session_id,
            "veteran_id": self.veteran_id,
            "content_type": self.content_type,
            "content_id": self.content_id,
            "generated_by": self.generated_by,
            "model_version": self.model_version,
            "confidence": self.confidence,
            "quality_flags": json.dumps(self.quality_flags) if self.quality_flags else None,
            "sources": json.dumps(self.sources) if self.sources else None,
            "input_hash": self.input_hash,
            "output_preview": self.output_preview[:500] if self.output_preview else None,
            "output_length": self.output_length,
            "processing_time_ms": self.processing_time_ms,
            "tokens_used": self.tokens_used,
            "created_at": self.created_at
        }


class AIAuditService:
    """Service for recording AI audit trail entries."""

    def __init__(self):
        from app.core.database_config import get_db_connection
        self.get_connection = get_db_connection

    def record(self, entry: AIAuditEntry) -> int:
        """
        Record an audit trail entry.

        Returns:
            The ID of the inserted record.
        """
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                data = entry.to_dict()

                cur.execute("""
                    INSERT INTO vetassist_ai_audit_trail (
                        session_id, veteran_id, content_type, content_id,
                        generated_by, model_version, confidence, quality_flags,
                        sources, input_hash, output_preview, output_length,
                        processing_time_ms, tokens_used, created_at
                    ) VALUES (
                        %(session_id)s, %(veteran_id)s, %(content_type)s, %(content_id)s,
                        %(generated_by)s, %(model_version)s, %(confidence)s, %(quality_flags)s,
                        %(sources)s, %(input_hash)s, %(output_preview)s, %(output_length)s,
                        %(processing_time_ms)s, %(tokens_used)s, %(created_at)s
                    ) RETURNING id
                """, data)

                record_id = cur.fetchone()[0]
                conn.commit()
                return record_id

        finally:
            conn.close()

    def get_session_audit(self, session_id: str) -> List[Dict]:
        """Get all audit entries for a session."""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM vetassist_ai_audit_trail
                    WHERE session_id = %s
                    ORDER BY created_at DESC
                """, (session_id,))

                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, row)) for row in cur.fetchall()]
        finally:
            conn.close()


# Singleton instance
_audit_service = None

def get_audit_service() -> AIAuditService:
    """Get or create the audit service singleton."""
    global _audit_service
    if _audit_service is None:
        _audit_service = AIAuditService()
    return _audit_service
```

## Verification

```bash
# Test schema exists
psql -h 192.168.132.222 -U claude -d zammad_production -c "\d vetassist_ai_audit_trail"

# Test Python model
cd /ganuda/vetassist/backend
python3 -c "
from app.models.ai_audit import AIAuditEntry, get_audit_service

entry = AIAuditEntry(
    content_type='test',
    generated_by='test-model',
    confidence=0.95
)

print(f'✓ Entry created: {entry.content_type}')
print(f'✓ Input hash: {entry.input_hash}')
print(f'✓ Dict conversion: {len(entry.to_dict())} fields')
"
```

---

FOR SEVEN GENERATIONS
