# Jr Task: VLM Entity Extractor Module

Create a module that parses VLM output and extracts Things (entities) and Relationships.

**Assigned to:** Software Engineer Jr.
**Node:** bluefin (192.168.132.222)
**Priority:** High

## Objective

Create `/ganuda/lib/vlm_entity_extractor.py` that:
1. Takes VLM description text
2. Uses LLM to extract entities and relationships
3. Returns structured data for thermal_relationships

## Implementation

**File:** `/ganuda/lib/vlm_entity_extractor.py`

```python
"""
Cherokee AI Federation - VLM Entity Extractor
Optic Nerve Pre-processing: Extract Things and Relationships from VLM output
"""

import json
import httpx
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

GATEWAY_URL = "http://192.168.132.223:8080"
API_KEY = "ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5"

@dataclass
class Entity:
    """A detected thing/object"""
    entity_type: str  # person, vehicle, door, object
    label: str        # Person_001, Red_Car, Front_Door
    confidence: float
    attributes: Dict[str, Any]

@dataclass 
class SpatialRelationship:
    """A relationship between entities"""
    source: str       # Entity label
    relation_type: str  # near, inside, above, holding, etc.
    target: str       # Entity label
    confidence: float
    metadata: Dict[str, Any]

@dataclass
class VLMExtraction:
    """Complete extraction from VLM output"""
    entities: List[Entity]
    relationships: List[SpatialRelationship]
    scene_summary: str
    anomaly_detected: bool
    confidence: float
    raw_description: str

EXTRACTION_PROMPT = '''Analyze this security camera description and extract entities and relationships.

Description: {description}

Return JSON with this exact structure:
{{
    "entities": [
        {{"type": "person|vehicle|animal|object", "label": "unique_label", "confidence": 0.0-1.0, "attributes": {{}}}}
    ],
    "relationships": [
        {{"source": "entity_label", "relation": "near|inside|above|below|holding|entering|exiting|approaching", "target": "entity_label", "confidence": 0.0-1.0}}
    ],
    "scene_summary": "brief summary",
    "anomaly_detected": true/false
}}

Only include entities and relationships explicitly mentioned or strongly implied. Be precise.'''


def extract_from_description(description: str, camera_id: str = "unknown") -> Optional[VLMExtraction]:
    """
    Extract entities and relationships from VLM description.
    
    Args:
        description: Raw VLM description text
        camera_id: Camera identifier for context
        
    Returns:
        VLMExtraction with entities and relationships, or None on failure
    """
    try:
        # Use redfin brain for extraction (higher reasoning)
        response = httpx.post(
            f"{GATEWAY_URL}/v1/chat/completions",
            headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
            json={
                "messages": [
                    {"role": "system", "content": "You are a precise entity and relationship extractor. Return only valid JSON."},
                    {"role": "user", "content": EXTRACTION_PROMPT.format(description=description)}
                ],
                "max_tokens": 500,
                "temperature": 0.1
            },
            timeout=30.0
        )
        
        result = response.json()
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # Parse JSON from response
        # Handle potential markdown code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
            
        data = json.loads(content.strip())
        
        # Build extraction result
        entities = [
            Entity(
                entity_type=e.get("type", "object"),
                label=e.get("label", f"entity_{i}"),
                confidence=float(e.get("confidence", 0.5)),
                attributes=e.get("attributes", {})
            )
            for i, e in enumerate(data.get("entities", []))
        ]
        
        relationships = [
            SpatialRelationship(
                source=r.get("source", ""),
                relation_type=r.get("relation", "related_to"),
                target=r.get("target", ""),
                confidence=float(r.get("confidence", 0.5)),
                metadata={"camera_id": camera_id}
            )
            for r in data.get("relationships", [])
        ]
        
        return VLMExtraction(
            entities=entities,
            relationships=relationships,
            scene_summary=data.get("scene_summary", ""),
            anomaly_detected=data.get("anomaly_detected", False),
            confidence=sum(e.confidence for e in entities) / len(entities) if entities else 0.0,
            raw_description=description
        )
        
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        return None


def extraction_to_dict(extraction: VLMExtraction) -> Dict[str, Any]:
    """Convert extraction to dictionary for JSON serialization."""
    return {
        "entities": [
            {"type": e.entity_type, "label": e.label, "confidence": e.confidence, "attributes": e.attributes}
            for e in extraction.entities
        ],
        "relationships": [
            {"source": r.source, "relation": r.relation_type, "target": r.target, "confidence": r.confidence}
            for r in extraction.relationships
        ],
        "scene_summary": extraction.scene_summary,
        "anomaly_detected": extraction.anomaly_detected,
        "confidence": extraction.confidence
    }


if __name__ == "__main__":
    # Test extraction
    test_desc = "A person is standing near the front door. They appear to be waiting. A red car is parked in the driveway behind them."
    
    result = extract_from_description(test_desc, "front_door_cam")
    if result:
        print(json.dumps(extraction_to_dict(result), indent=2))
    else:
        print("Extraction failed")
```

## Verification

```bash
cd /ganuda/lib
python3 -c "
from vlm_entity_extractor import extract_from_description, extraction_to_dict
import json

result = extract_from_description('A person near the door with a package', 'test_cam')
if result:
    print(json.dumps(extraction_to_dict(result), indent=2))
"
```

## Success Criteria

1. Module loads without errors
2. Extracts entities from test description
3. Extracts relationships between entities
4. Returns structured VLMExtraction dataclass
