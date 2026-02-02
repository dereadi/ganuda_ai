# JR Instruction: AI Audit Trail Integration

**JR ID:** JR-AI-003
**Priority:** P2
**Sprint:** VetAssist AI Enhancements Phase 1
**Created:** 2026-01-27
**Author:** TPM via Claude Code
**Council Vote:** b942f2dcad0496e1
**Depends On:** JR-AI-002 (Audit Trail Schema)
**Effort:** Low

## Problem Statement

After creating the audit trail schema (JR-AI-002), we need to integrate audit logging into existing AI services.

## Required Modifications

### 1. Nexus Template Generator

MODIFY: `/ganuda/vetassist/backend/app/services/nexus_template_generator.py`

Find the `generate_template` method and add audit logging:

```python
# Add import at top of file
from app.models.ai_audit import AIAuditEntry, get_audit_service
import time

# In the generate_template method, wrap the generation:
def generate_template(self, session_id: str, condition: str, ...) -> NexusTemplate:
    start_time = time.time()
    audit_service = get_audit_service()

    # ... existing generation code ...

    # After generating template, record audit
    processing_time = int((time.time() - start_time) * 1000)

    audit_entry = AIAuditEntry(
        session_id=session_id,
        content_type='nexus_template',
        content_id=f"nexus-{session_id}-{condition}",
        generated_by='qwen2.5-coder-32b',
        model_version='awq',
        confidence=template.completeness_score,
        quality_flags={
            "has_gaps": len(template.gaps_identified) > 0,
            "needs_review": template.completeness_score < 0.7
        },
        sources=[{"type": "session", "id": session_id}],
        input_data=f"{session_id}:{condition}",
        output_preview=f"Nexus template for {condition}",
        output_length=len(str(template)),
        processing_time_ms=processing_time
    )

    audit_service.record(audit_entry)

    return template
```

### 2. Evidence Gap Analyzer

MODIFY: `/ganuda/vetassist/backend/app/services/evidence_gap_analyzer.py`

Find the `analyze` method and add audit logging:

```python
# Add import at top of file
from app.models.ai_audit import AIAuditEntry, get_audit_service
import time

# In the analyze method:
def analyze(self, session_id: str, condition: str) -> GapAnalysis:
    start_time = time.time()
    audit_service = get_audit_service()

    # ... existing analysis code ...

    processing_time = int((time.time() - start_time) * 1000)

    audit_entry = AIAuditEntry(
        session_id=session_id,
        content_type='evidence_gap',
        content_id=f"gap-{session_id}-{condition}",
        generated_by='evidence_gap_analyzer',
        confidence=analysis.completeness_score,
        quality_flags={
            "has_critical_gaps": analysis.has_critical_gaps,
            "nexus_strength": analysis.nexus_strength
        },
        sources=[{"type": "session", "id": session_id}],
        input_data=f"{session_id}:{condition}",
        output_preview=analysis.summary[:500] if analysis.summary else None,
        processing_time_ms=processing_time
    )

    audit_service.record(audit_entry)

    return analysis
```

### 3. Condition Mapping Endpoint

MODIFY: `/ganuda/vetassist/backend/app/api/v1/endpoints/conditions.py`

Find the condition mapping endpoint and add audit logging:

```python
# Add import at top of file
from app.models.ai_audit import AIAuditEntry, get_audit_service
import time

# In the map_condition endpoint:
@router.post("/map")
def map_condition(description: str, session_id: Optional[str] = None):
    start_time = time.time()
    audit_service = get_audit_service()

    # ... existing mapping code ...

    processing_time = int((time.time() - start_time) * 1000)

    # After getting results
    if results:
        audit_entry = AIAuditEntry(
            session_id=session_id,
            content_type='condition_map',
            generated_by='cfr_semantic_search',
            confidence=results[0].match_score if results else 0.0,
            input_data=description,
            output_preview=f"Mapped to: {results[0].condition_name}" if results else "No match",
            processing_time_ms=processing_time
        )
        audit_service.record(audit_entry)

    return results
```

### 4. RAG Query Service

MODIFY: `/ganuda/vetassist/backend/app/services/rag_query.py`

Find the `query_with_context` method and add audit logging:

```python
# Add import at top of file
from app.models.ai_audit import AIAuditEntry, get_audit_service
import time

# In query_with_context method:
def query_with_context(self, query: str, session_id: Optional[str] = None, ...):
    start_time = time.time()
    audit_service = get_audit_service()

    # ... existing query code ...

    processing_time = int((time.time() - start_time) * 1000)

    audit_entry = AIAuditEntry(
        session_id=session_id,
        content_type='rag_query',
        generated_by='rag_query_service',
        confidence=max(c["score"] for c in result["citations"]) if result["citations"] else 0.0,
        sources=[{"type": "cfr", "id": c["url"]} for c in result["citations"][:5]],
        input_data=query,
        output_preview=result["context"][:500],
        output_length=len(result["context"]),
        processing_time_ms=processing_time
    )
    audit_service.record(audit_entry)

    return result
```

## API Endpoint for Audit Access

CREATE: Add to `/ganuda/vetassist/backend/app/api/v1/endpoints/` a new endpoint or add to existing:

```python
# In an appropriate router file (e.g., dashboard.py or create audit.py)

@router.get("/sessions/{session_id}/ai-audit")
def get_session_ai_audit(
    session_id: str,
    user_id: str = Depends(get_current_user)
):
    """
    Get AI audit trail for a session.
    Shows which AI features generated which content.
    """
    from app.models.ai_audit import get_audit_service

    audit_service = get_audit_service()
    entries = audit_service.get_session_audit(session_id)

    # Format for display
    return {
        "session_id": session_id,
        "audit_entries": [
            {
                "id": e["id"],
                "content_type": e["content_type"],
                "generated_by": e["generated_by"],
                "confidence": e["confidence"],
                "created_at": e["created_at"].isoformat() if e["created_at"] else None,
                "processing_time_ms": e["processing_time_ms"]
            }
            for e in entries
        ],
        "total_entries": len(entries)
    }
```

## Verification

```bash
cd /ganuda/vetassist/backend
python3 -c "
from app.models.ai_audit import AIAuditEntry, get_audit_service
import uuid

# Create test entry
entry = AIAuditEntry(
    session_id=str(uuid.uuid4()),
    content_type='test_integration',
    generated_by='test-jr-ai-003',
    confidence=0.99,
    input_data='test input',
    output_preview='test output'
)

service = get_audit_service()
record_id = service.record(entry)
print(f'✓ Recorded audit entry with ID: {record_id}')

# Verify retrieval
entries = service.get_session_audit(entry.session_id)
print(f'✓ Retrieved {len(entries)} entries for session')
"
```

---

FOR SEVEN GENERATIONS
