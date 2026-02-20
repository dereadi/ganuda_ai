# JR-FILM-VLM-ENHANCEMENT-FEB05-2026

## Task Metadata
- **Task ID**: FILM-VLM-001
- **Priority**: P1
- **Estimated Effort**: 4-6 hours
- **Assigned To**: Available Jr with ML/VLM experience
- **Council Status**: Approved (no concerns - straightforward enhancement)
- **Created**: 2026-02-05
- **Due**: 2026-02-07

## Objective

Add Feature-wise Linear Modulation (FiLM) conditioning to the VLM clause evaluator and entity extractor modules to improve context-aware processing of VetAssist documents and security camera feeds.

## Background: FiLM Architecture

### Research Context (arXiv 1709.07871)

FiLM (Feature-wise Linear Modulation) is a conditioning mechanism introduced by Perez et al. that enables neural networks to modulate intermediate feature representations based on external conditioning information.

**Key Paper Insights**:
- FiLM layers learn to adaptively influence neural network computation via a simple feature-wise affine transformation
- Conditioning can come from any source: language, task type, domain metadata
- Extremely effective for visual reasoning tasks where context matters
- Lightweight addition that doesn't significantly increase model complexity

**Core Formula**:
```
FiLM(F_i,c | gamma_i,c, beta_i,c) = gamma_i,c * F_i,c + beta_i,c
```

Where:
- `F_i,c` = input feature at position i, channel c
- `gamma_i,c` = learned scaling parameter (multiplicative)
- `beta_i,c` = learned shift parameter (additive)
- Both gamma and beta are functions of the conditioning input

## Current Architecture Analysis

### vlm_clause_evaluator.py

**Location**: `/ganuda/lib/vlm_clause_evaluator.py`

**Current Flow**:
1. Fetches active clauses from `active_thermal_clauses` table
2. Checks if relationships are active in `active_thermal_relationships`
3. Evaluates IF-THEN conditions against relationship state
4. Escalates to redfin brain when metadata.escalate_on_trigger is set
5. Updates clause evaluation state in database

**Key Functions**:
- `get_active_clauses(conn)` - retrieves clause definitions
- `check_relationships_active(conn, relationship_ids)` - validates conditions
- `escalate_to_redfin(reason, clause_id, relationships, priority)` - LLM escalation
- `evaluate_clauses_for_relationships(new_relationship_ids)` - main evaluation loop

**Current Limitations**:
- No conditioning on document type or clause category
- Same evaluation logic regardless of source context
- Escalation prompts are static, not adapted to clause type

### vlm_entity_extractor.py

**Location**: `/ganuda/lib/vlm_entity_extractor.py`

**Current Flow**:
1. Receives raw VLM description text
2. Sends to gateway with static extraction prompt
3. Parses JSON response into Entity and SpatialRelationship dataclasses
4. Returns VLMExtraction with entities, relationships, scene summary

**Key Functions**:
- `extract_from_description(description, camera_id)` - main extraction
- `extraction_to_dict(extraction)` - serialization for storage

**Current Limitations**:
- Single static EXTRACTION_PROMPT for all document types
- No adaptation based on extraction target (medical vs security vs legal)
- Confidence scores are static defaults, not context-adjusted

## Implementation Specification

### Step 1: Create FiLM Layer Module

Create new file: `/ganuda/lib/film_conditioning.py`

```python
"""
Cherokee AI Federation - FiLM Conditioning Layer
Feature-wise Linear Modulation for context-aware VLM processing
Based on arXiv 1709.07871
"""

from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
import json

@dataclass
class FiLMCondition:
    """Conditioning parameters for FiLM layer"""
    gamma: float  # Multiplicative scaling
    beta: float   # Additive shift
    source: str   # What generated this condition

def film_layer(features: float, gamma: float, beta: float) -> float:
    """
    Core FiLM transformation: gamma * features + beta

    Args:
        features: Input feature value (e.g., confidence score)
        gamma: Learned scaling parameter
        beta: Learned shift parameter

    Returns:
        Modulated feature value
    """
    return gamma * features + beta

def film_layer_vector(features: List[float], gamma: List[float], beta: List[float]) -> List[float]:
    """
    Vectorized FiLM transformation for multiple features.

    Args:
        features: List of input feature values
        gamma: List of scaling parameters (same length as features)
        beta: List of shift parameters (same length as features)

    Returns:
        List of modulated feature values
    """
    if len(features) != len(gamma) or len(features) != len(beta):
        raise ValueError("Feature and parameter lengths must match")
    return [film_layer(f, g, b) for f, g, b in zip(features, gamma, beta)]

# Pre-defined conditioning profiles based on document/task type
CONDITIONING_PROFILES: Dict[str, Dict[str, FiLMCondition]] = {
    # VetAssist Document Types
    "medical_record": {
        "confidence": FiLMCondition(gamma=1.2, beta=0.1, source="doc_type"),
        "extraction_threshold": FiLMCondition(gamma=0.9, beta=-0.05, source="doc_type"),
        "entity_weight": FiLMCondition(gamma=1.3, beta=0.0, source="doc_type"),
    },
    "nexus_letter": {
        "confidence": FiLMCondition(gamma=1.4, beta=0.15, source="doc_type"),
        "extraction_threshold": FiLMCondition(gamma=0.85, beta=-0.1, source="doc_type"),
        "entity_weight": FiLMCondition(gamma=1.5, beta=0.05, source="doc_type"),
    },
    "va_decision": {
        "confidence": FiLMCondition(gamma=1.1, beta=0.05, source="doc_type"),
        "extraction_threshold": FiLMCondition(gamma=0.95, beta=0.0, source="doc_type"),
        "entity_weight": FiLMCondition(gamma=1.2, beta=0.0, source="doc_type"),
    },
    "cfr_regulation": {
        "confidence": FiLMCondition(gamma=1.0, beta=0.0, source="doc_type"),
        "extraction_threshold": FiLMCondition(gamma=1.0, beta=0.0, source="doc_type"),
        "entity_weight": FiLMCondition(gamma=1.0, beta=0.0, source="doc_type"),
    },
    # Security/Vision Document Types
    "security_camera": {
        "confidence": FiLMCondition(gamma=1.0, beta=0.0, source="doc_type"),
        "extraction_threshold": FiLMCondition(gamma=1.0, beta=0.0, source="doc_type"),
        "entity_weight": FiLMCondition(gamma=1.1, beta=0.0, source="doc_type"),
    },
    "anomaly_detection": {
        "confidence": FiLMCondition(gamma=0.8, beta=0.2, source="doc_type"),
        "extraction_threshold": FiLMCondition(gamma=0.7, beta=0.0, source="doc_type"),
        "entity_weight": FiLMCondition(gamma=1.4, beta=0.1, source="doc_type"),
    },
}

# Clause category conditioning
CLAUSE_CATEGORY_MODULATION: Dict[str, Tuple[float, float]] = {
    "if_then": (1.0, 0.0),           # Standard evaluation
    "escalation": (1.2, 0.1),         # Boost for escalation clauses
    "anomaly": (0.9, 0.15),           # Lower threshold, higher sensitivity
    "routine": (1.1, -0.05),          # Slightly stricter
    "emergency": (0.7, 0.25),         # Very sensitive
}

# Extraction target conditioning
EXTRACTION_TARGET_MODULATION: Dict[str, Tuple[float, float]] = {
    "person": (1.0, 0.0),
    "vehicle": (1.0, 0.0),
    "medical_condition": (1.3, 0.1),  # Boost medical entity extraction
    "service_connection": (1.4, 0.15), # Critical for VetAssist
    "date": (1.1, 0.05),
    "medication": (1.2, 0.1),
    "diagnosis_code": (1.35, 0.12),
    "legal_citation": (1.25, 0.08),
}

def get_conditioning_for_context(
    doc_type: str,
    clause_category: str = None,
    extraction_target: str = None
) -> Dict[str, FiLMCondition]:
    """
    Get combined FiLM conditioning parameters for a given context.

    Args:
        doc_type: Document type (medical_record, nexus_letter, etc.)
        clause_category: Optional clause category for clause evaluation
        extraction_target: Optional target entity type for extraction

    Returns:
        Dictionary of FiLM conditions to apply
    """
    # Start with document type profile
    profile = CONDITIONING_PROFILES.get(doc_type, CONDITIONING_PROFILES["security_camera"]).copy()

    # Apply clause category modulation if provided
    if clause_category and clause_category in CLAUSE_CATEGORY_MODULATION:
        cat_gamma, cat_beta = CLAUSE_CATEGORY_MODULATION[clause_category]
        for key in profile:
            profile[key] = FiLMCondition(
                gamma=profile[key].gamma * cat_gamma,
                beta=profile[key].beta + cat_beta,
                source=f"{profile[key].source}+clause"
            )

    # Apply extraction target modulation if provided
    if extraction_target and extraction_target in EXTRACTION_TARGET_MODULATION:
        target_gamma, target_beta = EXTRACTION_TARGET_MODULATION[extraction_target]
        for key in profile:
            profile[key] = FiLMCondition(
                gamma=profile[key].gamma * target_gamma,
                beta=profile[key].beta + target_beta,
                source=f"{profile[key].source}+target"
            )

    return profile

def apply_film_to_confidence(
    raw_confidence: float,
    doc_type: str,
    clause_category: str = None,
    extraction_target: str = None
) -> float:
    """
    Apply FiLM conditioning to a confidence score.

    Args:
        raw_confidence: Original confidence value (0.0-1.0)
        doc_type: Document type for conditioning
        clause_category: Optional clause category
        extraction_target: Optional extraction target

    Returns:
        Modulated confidence score, clamped to [0.0, 1.0]
    """
    conditions = get_conditioning_for_context(doc_type, clause_category, extraction_target)
    conf_condition = conditions.get("confidence", FiLMCondition(1.0, 0.0, "default"))

    modulated = film_layer(raw_confidence, conf_condition.gamma, conf_condition.beta)
    return max(0.0, min(1.0, modulated))  # Clamp to valid range
```

### Step 2: Integrate FiLM into vlm_clause_evaluator.py

Modify `/ganuda/lib/vlm_clause_evaluator.py`:

**Add Import**:
```python
from film_conditioning import apply_film_to_confidence, get_conditioning_for_context
```

**Modify `evaluate_clauses_for_relationships` function**:

Add document type detection and FiLM conditioning to the evaluation loop:

```python
def evaluate_clauses_for_relationships(
    new_relationship_ids: List[int],
    doc_type: str = "security_camera"  # NEW PARAMETER
) -> List[ClauseEvaluation]:
    results = []
    conn = get_db_connection()
    try:
        for clause in get_active_clauses(conn):
            condition_ids = clause.get('condition_ids') or []
            if condition_ids and not any(rid in condition_ids for rid in new_relationship_ids):
                continue

            conditions_met = check_relationships_active(conn, condition_ids)

            # NEW: Get clause category from metadata
            metadata = clause.get('metadata') or {}
            clause_category = metadata.get('category', 'if_then')

            # NEW: Apply FiLM conditioning to decision threshold
            film_conditions = get_conditioning_for_context(doc_type, clause_category)
            threshold_condition = film_conditions.get('extraction_threshold')

            # Modulate evaluation sensitivity based on context
            if threshold_condition:
                effective_threshold = film_layer(
                    0.5,  # Base threshold
                    threshold_condition.gamma,
                    threshold_condition.beta
                )
            else:
                effective_threshold = 0.5

            action, escalation_reason = "none", None

            if conditions_met:
                if metadata.get('escalate_on_trigger'):
                    action, escalation_reason = "escalate", f"Clause '{clause['name']}' triggered"
                elif clause['priority'] <= 2:
                    action = "alert"
                else:
                    action = "log"

            # ... rest of function unchanged
```

**Modify `escalate_to_redfin` function**:

Add document context to escalation prompts:

```python
def escalate_to_redfin(
    reason: str,
    clause_id: int,
    relationships: List[Dict],
    priority: str,
    doc_type: str = "security_camera"  # NEW PARAMETER
) -> Dict:
    # NEW: Get FiLM-adjusted prompt parameters
    film_conditions = get_conditioning_for_context(doc_type, "escalation")

    # NEW: Adapt prompt based on document type
    context_hints = {
        "medical_record": "Focus on medical terminology, dates of service, and diagnosis codes.",
        "nexus_letter": "Focus on service connection language and medical opinions.",
        "va_decision": "Focus on legal reasoning and appeal points.",
        "security_camera": "Focus on spatial relationships and temporal patterns.",
    }

    prompt = f"""VISUAL CORTEX ESCALATION
Reason: {reason}
Document Context: {doc_type}
{context_hints.get(doc_type, '')}
Relationships: {json.dumps(relationships, indent=2)}
Analyze and respond with JSON: {{"assessment": "...", "action": "none|log|alert|urgent", "reasoning": "...", "confidence": 0.0-1.0}}"""

    # ... rest of function with FiLM-adjusted confidence in response parsing
```

### Step 3: Integrate FiLM into vlm_entity_extractor.py

Modify `/ganuda/lib/vlm_entity_extractor.py`:

**Add Import**:
```python
from film_conditioning import apply_film_to_confidence, get_conditioning_for_context, EXTRACTION_TARGET_MODULATION
```

**Create document-type-specific extraction prompts**:

```python
EXTRACTION_PROMPTS: Dict[str, str] = {
    "medical_record": '''Analyze this medical record and extract clinical entities and relationships.

Description: {description}

Focus on: diagnoses, medications, dates of service, providers, symptoms, treatments.

Return JSON with this exact structure:
{{
    "entities": [
        {{"type": "diagnosis|medication|provider|symptom|treatment|date", "label": "unique_label", "confidence": 0.0-1.0, "attributes": {{}}}}
    ],
    "relationships": [
        {{"source": "entity_label", "relation": "diagnosed_with|prescribed|treated_by|occurred_on|caused_by", "target": "entity_label", "confidence": 0.0-1.0}}
    ],
    "scene_summary": "clinical summary",
    "anomaly_detected": true/false
}}''',

    "nexus_letter": '''Analyze this nexus letter and extract service connection entities.

Description: {description}

Focus on: conditions, service events, medical opinions, rationale, probability language.

Return JSON with this exact structure:
{{
    "entities": [
        {{"type": "condition|service_event|medical_opinion|rationale", "label": "unique_label", "confidence": 0.0-1.0, "attributes": {{}}}}
    ],
    "relationships": [
        {{"source": "entity_label", "relation": "connected_to|caused_by|aggravated_by|supports", "target": "entity_label", "confidence": 0.0-1.0}}
    ],
    "scene_summary": "nexus summary",
    "anomaly_detected": true/false
}}''',

    # Keep original for security cameras
    "security_camera": EXTRACTION_PROMPT,
}
```

**Modify `extract_from_description` function**:

```python
def extract_from_description(
    description: str,
    camera_id: str = "unknown",
    doc_type: str = "security_camera",  # NEW PARAMETER
    extraction_targets: List[str] = None  # NEW PARAMETER
) -> Optional[VLMExtraction]:
    """
    Extract entities and relationships from VLM description with FiLM conditioning.

    Args:
        description: Raw VLM description text
        camera_id: Camera/document identifier for context
        doc_type: Document type for FiLM conditioning
        extraction_targets: Specific entity types to prioritize

    Returns:
        VLMExtraction with entities and relationships, or None on failure
    """
    try:
        # NEW: Select prompt based on document type
        prompt_template = EXTRACTION_PROMPTS.get(doc_type, EXTRACTION_PROMPT)

        # NEW: Get FiLM conditioning for this context
        primary_target = extraction_targets[0] if extraction_targets else None
        film_conditions = get_conditioning_for_context(doc_type, None, primary_target)

        response = httpx.post(
            f"{GATEWAY_URL}/v1/chat/completions",
            headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
            json={
                "messages": [
                    {"role": "system", "content": f"You are a precise entity and relationship extractor for {doc_type} documents. Return only valid JSON."},
                    {"role": "user", "content": prompt_template.format(description=description)}
                ],
                "max_tokens": 500,
                "temperature": 0.1
            },
            timeout=30.0
        )

        # ... JSON parsing unchanged ...

        # Build entities with FiLM-adjusted confidence
        entities = []
        for e in data.get("entities", []):
            raw_confidence = float(e.get("confidence", 0.8))
            entity_type = e.get("type", "object")

            # NEW: Apply FiLM conditioning to confidence
            modulated_confidence = apply_film_to_confidence(
                raw_confidence,
                doc_type,
                extraction_target=entity_type
            )

            entities.append(Entity(
                entity_type=entity_type,
                label=e.get("label", f"Entity_{len(entities)}"),
                confidence=modulated_confidence,  # FiLM-adjusted
                attributes=e.get("attributes", {})
            ))

        # Build relationships with FiLM-adjusted confidence
        relationships = []
        for r in data.get("relationships", []):
            raw_confidence = float(r.get("confidence", 0.8))

            # NEW: Apply FiLM conditioning
            modulated_confidence = apply_film_to_confidence(
                raw_confidence,
                doc_type
            )

            relationships.append(SpatialRelationship(
                source=r.get("source", ""),
                relation_type=r.get("relation", "near"),
                target=r.get("target", ""),
                confidence=modulated_confidence,  # FiLM-adjusted
                metadata={"camera_id": camera_id, "doc_type": doc_type}
            ))

        # NEW: FiLM-adjusted overall confidence
        base_confidence = 0.9 if entities else 0.5
        overall_confidence = apply_film_to_confidence(base_confidence, doc_type)

        return VLMExtraction(
            entities=entities,
            relationships=relationships,
            scene_summary=data.get("scene_summary", ""),
            anomaly_detected=data.get("anomaly_detected", False),
            confidence=overall_confidence,
            raw_description=description
        )

    except Exception as e:
        logger.error(f"Entity extraction failed: {e}")
        return None
```

### Step 4: Update Callers

Any code calling these functions needs updating to pass document type:

**In vetassist backend** (search for usages):
```python
# Before
extraction = extract_from_description(ocr_text, document_id)

# After
extraction = extract_from_description(
    ocr_text,
    document_id,
    doc_type="medical_record",
    extraction_targets=["diagnosis", "medication", "date"]
)
```

## Conditioning Sources Reference

### Document Types
| Type | Use Case | Gamma Bias | Beta Bias |
|------|----------|------------|-----------|
| `medical_record` | VA medical records, C&P exams | Higher confidence | Positive shift |
| `nexus_letter` | IMO/nexus letters | Highest confidence | Highest shift |
| `va_decision` | Rating decisions, SOCs | Moderate boost | Small shift |
| `cfr_regulation` | 38 CFR references | Neutral | Neutral |
| `security_camera` | Vision pipeline (default) | Neutral | Neutral |
| `anomaly_detection` | Anomaly alerts | Lower threshold | Higher sensitivity |

### Clause Categories
| Category | Gamma | Beta | Effect |
|----------|-------|------|--------|
| `if_then` | 1.0 | 0.0 | Standard |
| `escalation` | 1.2 | 0.1 | More sensitive |
| `anomaly` | 0.9 | 0.15 | Lower threshold |
| `routine` | 1.1 | -0.05 | Slightly stricter |
| `emergency` | 0.7 | 0.25 | Very sensitive |

### Extraction Targets
| Target | Gamma | Beta | Rationale |
|--------|-------|------|-----------|
| `medical_condition` | 1.3 | 0.1 | Critical for claims |
| `service_connection` | 1.4 | 0.15 | Most important for VetAssist |
| `diagnosis_code` | 1.35 | 0.12 | ICD/diagnostic codes |
| `legal_citation` | 1.25 | 0.08 | CFR references |
| `date` | 1.1 | 0.05 | Timeline evidence |

## Expected Improvements

### Clause Evaluation
- **10-15% improvement** in escalation precision for medical documents
- **Reduced false positives** in routine security monitoring
- **Faster response** to emergency clauses via adjusted thresholds

### Entity Extraction
- **15-20% improvement** in medical entity extraction accuracy
- **Better service connection detection** for nexus letters
- **More accurate confidence calibration** across document types

### Overall
- Context-aware processing without retraining models
- Lightweight enhancement (no additional model calls)
- Easily tunable via conditioning profiles

## Testing Plan

### Unit Tests

Create `/ganuda/tests/test_film_conditioning.py`:

```python
import pytest
from lib.film_conditioning import (
    film_layer, film_layer_vector,
    apply_film_to_confidence, get_conditioning_for_context
)

def test_film_layer_identity():
    """Gamma=1, Beta=0 should return input unchanged"""
    assert film_layer(0.5, 1.0, 0.0) == 0.5
    assert film_layer(0.8, 1.0, 0.0) == 0.8

def test_film_layer_scaling():
    """Gamma > 1 should increase, < 1 should decrease"""
    assert film_layer(0.5, 1.2, 0.0) == 0.6
    assert film_layer(0.5, 0.8, 0.0) == 0.4

def test_film_layer_shift():
    """Beta should add constant offset"""
    assert film_layer(0.5, 1.0, 0.1) == 0.6
    assert film_layer(0.5, 1.0, -0.1) == 0.4

def test_confidence_clamping():
    """Confidence should be clamped to [0, 1]"""
    assert apply_film_to_confidence(0.9, "nexus_letter") <= 1.0
    assert apply_film_to_confidence(0.1, "routine") >= 0.0

def test_medical_boost():
    """Medical documents should get confidence boost"""
    base = 0.7
    medical = apply_film_to_confidence(base, "medical_record")
    security = apply_film_to_confidence(base, "security_camera")
    assert medical > security
```

### Integration Tests

Test with actual VetAssist documents:

1. **Medical Record Test**: Process sample C&P exam, verify entity extraction improves
2. **Nexus Letter Test**: Process nexus letter, verify service connection detection
3. **VA Decision Test**: Process rating decision, verify legal citation extraction
4. **Regression Test**: Ensure security camera processing unchanged

### Test Commands

```bash
# Run unit tests
cd /ganuda && python -m pytest tests/test_film_conditioning.py -v

# Test entity extraction with different doc types
python -c "
from lib.vlm_entity_extractor import extract_from_description

# Medical record test
medical_text = 'Patient diagnosed with PTSD secondary to military sexual trauma. Onset date: 2019-03-15.'
result = extract_from_description(medical_text, 'test', doc_type='medical_record')
print(f'Medical entities: {len(result.entities)}, confidence: {result.confidence}')

# Security camera test (baseline)
security_text = 'A person wearing a red jacket is standing near the front door.'
result = extract_from_description(security_text, 'test', doc_type='security_camera')
print(f'Security entities: {len(result.entities)}, confidence: {result.confidence}')
"
```

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `/ganuda/lib/film_conditioning.py` | CREATE | New FiLM layer module |
| `/ganuda/lib/vlm_clause_evaluator.py` | MODIFY | Add FiLM integration |
| `/ganuda/lib/vlm_entity_extractor.py` | MODIFY | Add FiLM integration + prompts |
| `/ganuda/tests/test_film_conditioning.py` | CREATE | Unit tests |

## Rollback Plan

If FiLM conditioning causes issues:

1. Remove imports from vlm_clause_evaluator.py and vlm_entity_extractor.py
2. Revert function signatures to remove doc_type parameters
3. Keep film_conditioning.py for future use but don't call it

The changes are additive and backward-compatible - existing calls without doc_type will use defaults.

## Success Criteria

- [ ] film_conditioning.py created and passing unit tests
- [ ] vlm_clause_evaluator.py updated with FiLM integration
- [ ] vlm_entity_extractor.py updated with FiLM integration and document-specific prompts
- [ ] All existing tests pass (no regression)
- [ ] Manual testing with VetAssist documents shows improvement
- [ ] No performance degradation (< 5ms additional latency)

## References

- **FiLM Paper**: arXiv 1709.07871 - "FiLM: Visual Reasoning with a General Conditioning Layer"
- **Current VLM Architecture**: `/ganuda/lib/vlm_*.py`
- **VetAssist Document Processing**: `/ganuda/vetassist/backend/app/services/`
- **Thermal Memory Schema**: `/ganuda/sql/migration_thermal_*.sql`

---
*Jr Instruction Document - Cherokee AI Federation*
*Council Approved: 2026-02-05 | No concerns raised*
