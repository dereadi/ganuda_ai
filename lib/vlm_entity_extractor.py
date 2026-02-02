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

        # Parse JSON from response - handle markdown code blocks
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        data = json.loads(content)

        # Build entities
        entities = []
        for e in data.get("entities", []):
            entities.append(Entity(
                entity_type=e.get("type", "object"),
                label=e.get("label", f"Entity_{len(entities)}"),
                confidence=float(e.get("confidence", 0.8)),
                attributes=e.get("attributes", {})
            ))

        # Build relationships
        relationships = []
        for r in data.get("relationships", []):
            relationships.append(SpatialRelationship(
                source=r.get("source", ""),
                relation_type=r.get("relation", "near"),
                target=r.get("target", ""),
                confidence=float(r.get("confidence", 0.8)),
                metadata={"camera_id": camera_id}
            ))

        return VLMExtraction(
            entities=entities,
            relationships=relationships,
            scene_summary=data.get("scene_summary", ""),
            anomaly_detected=data.get("anomaly_detected", False),
            confidence=0.9 if entities else 0.5,
            raw_description=description
        )

    except Exception as e:
        logger.error(f"Entity extraction failed: {e}")
        return None


def extraction_to_dict(extraction: VLMExtraction) -> Dict:
    """Convert VLMExtraction to dictionary for storage."""
    if not extraction:
        return {}
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
    test_description = "A person wearing a red jacket is standing near the front door. A white sedan is parked in the driveway."
    extraction = extract_from_description(test_description, "test_camera")
    if extraction:
        print(f"Entities: {len(extraction.entities)}")
        for e in extraction.entities:
            print(f"  - {e.entity_type}: {e.label} ({e.confidence:.0%})")
        print(f"Relationships: {len(extraction.relationships)}")
        for r in extraction.relationships:
            print(f"  - {r.source} {r.relation_type} {r.target}")
        print(f"Anomaly: {extraction.anomaly_detected}")
    else:
        print("Extraction failed")
