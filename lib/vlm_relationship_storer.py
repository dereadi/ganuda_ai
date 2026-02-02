"""
Cherokee AI Federation - VLM Relationship Storer
Stores extracted entities and relationships in thermal memory
"""

import psycopg2
import hashlib
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

DB_CONFIG = {
    "host": "192.168.132.222",
    "database": "zammad_production",
    "user": "claude",
    "password": "jawaseatlasers2"
}

@dataclass
class StoredExtraction:
    """Result of storing an extraction"""
    entity_memory_ids: Dict[str, int]  # label -> memory_id
    relationship_ids: List[int]
    frame_memory_id: int
    camera_id: str


def get_db_connection():
    """Get database connection."""
    return psycopg2.connect(**DB_CONFIG)


def store_entity_as_memory(
    conn,
    entity_type: str,
    label: str,
    confidence: float,
    camera_id: str,
    attributes: Dict
) -> int:
    """Store an entity as a thermal memory."""
    content = f"VLM Entity: {entity_type} '{label}' detected at {camera_id}. Confidence: {confidence:.0%}"
    memory_hash = hashlib.md5(f"{label}-{camera_id}-vlm".encode()).hexdigest()
    
    with conn.cursor() as cur:
        # Check if entity already exists (by hash)
        cur.execute(
            "SELECT id FROM thermal_memory_archive WHERE memory_hash = %s",
            (memory_hash,)
        )
        existing = cur.fetchone()
        
        if existing:
            # Update last access
            cur.execute(
                "UPDATE thermal_memory_archive SET last_access = NOW(), access_count = access_count + 1 WHERE id = %s",
                (existing[0],)
            )
            return existing[0]
        
        # Compute integrity checksum
        content_checksum = hashlib.sha256(content.encode('utf-8', errors='replace')).hexdigest()

        # Create new memory with checksum
        cur.execute("""
            INSERT INTO thermal_memory_archive
            (memory_hash, original_content, current_stage, temperature_score,
             metadata, content_checksum, domain_tag)
            VALUES (%s, %s, 'WARM', %s, %s, %s, 'operational')
            RETURNING id
        """, (
            memory_hash,
            content,
            confidence * 80,  # Scale confidence to temperature
            json.dumps({
                "type": "vlm_entity",
                "entity_type": entity_type,
                "label": label,
                "camera_id": camera_id,
                "attributes": attributes
            }),
            content_checksum
        ))
        return cur.fetchone()[0]


def store_relationship(
    conn,
    source_memory_id: int,
    relation_type: str,
    target_memory_id: int,
    confidence: float,
    camera_id: str
) -> int:
    """Store a relationship between entities."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT create_thermal_relationship(
                p_source_memory_id := %s,
                p_relationship_type := %s,
                p_target_memory_id := %s,
                p_confidence := %s,
                p_provenance := 'vlm',
                p_metadata := %s
            )
        """, (
            source_memory_id,
            relation_type,
            target_memory_id,
            confidence,
            json.dumps({"camera_id": camera_id, "source": "vlm_extraction"})
        ))
        return cur.fetchone()[0]


def store_frame_memory(
    conn,
    camera_id: str,
    frame_path: str,
    scene_summary: str,
    anomaly_detected: bool
) -> int:
    """Store the frame analysis as a memory."""
    memory_hash = hashlib.md5(f"{frame_path}-analysis".encode()).hexdigest()
    
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO thermal_memory_archive 
            (memory_hash, original_content, current_stage, temperature_score, metadata)
            VALUES (%s, %s, 'FRESH', %s, %s)
            RETURNING id
        """, (
            memory_hash,
            f"Frame Analysis [{camera_id}]: {scene_summary}",
            90 if anomaly_detected else 70,
            json.dumps({
                "type": "vlm_frame_analysis",
                "camera_id": camera_id,
                "frame_path": frame_path,
                "anomaly_detected": anomaly_detected
            })
        ))
        return cur.fetchone()[0]


def store_extraction(
    extraction_dict: Dict,
    camera_id: str,
    frame_path: str = None
) -> Optional[StoredExtraction]:
    """
    Store a complete VLM extraction in thermal memory.
    
    Args:
        extraction_dict: Dictionary from vlm_entity_extractor.extraction_to_dict()
        camera_id: Camera identifier
        frame_path: Optional path to the analyzed frame
        
    Returns:
        StoredExtraction with all created IDs
    """
    try:
        conn = get_db_connection()
        conn.autocommit = False
        
        entity_memory_ids = {}
        relationship_ids = []
        
        # Store entities
        for entity in extraction_dict.get("entities", []):
            mem_id = store_entity_as_memory(
                conn,
                entity["type"],
                entity["label"],
                entity["confidence"],
                camera_id,
                entity.get("attributes", {})
            )
            entity_memory_ids[entity["label"]] = mem_id
            logger.info(f"Stored entity '{entity['label']}' as memory {mem_id}")
        
        # Store relationships
        for rel in extraction_dict.get("relationships", []):
            source_id = entity_memory_ids.get(rel["source"])
            target_id = entity_memory_ids.get(rel["target"])
            
            if source_id and target_id:
                rel_id = store_relationship(
                    conn,
                    source_id,
                    rel["relation"],
                    target_id,
                    rel["confidence"],
                    camera_id
                )
                relationship_ids.append(rel_id)
                logger.info(f"Stored relationship {rel['source']} -{rel['relation']}-> {rel['target']} as {rel_id}")
        
        # Store frame analysis
        frame_memory_id = store_frame_memory(
            conn,
            camera_id,
            frame_path or "unknown",
            extraction_dict.get("scene_summary", ""),
            extraction_dict.get("anomaly_detected", False)
        )
        
        conn.commit()
        conn.close()
        
        return StoredExtraction(
            entity_memory_ids=entity_memory_ids,
            relationship_ids=relationship_ids,
            frame_memory_id=frame_memory_id,
            camera_id=camera_id
        )
        
    except Exception as e:
        logger.error(f"Failed to store extraction: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return None


if __name__ == "__main__":
    # Test storage
    test_extraction = {
        "entities": [
            {"type": "person", "label": "Person_001", "confidence": 0.9, "attributes": {"action": "waiting"}},
            {"type": "object", "label": "Front_Door", "confidence": 0.95, "attributes": {}}
        ],
        "relationships": [
            {"source": "Person_001", "relation": "near", "target": "Front_Door", "confidence": 0.85}
        ],
        "scene_summary": "Person waiting near front door",
        "anomaly_detected": False
    }
    
    result = store_extraction(test_extraction, "front_door_cam", "/test/frame.jpg")
    if result:
        print(f"Stored: {len(result.entity_memory_ids)} entities, {len(result.relationship_ids)} relationships")
        print(f"Entity IDs: {result.entity_memory_ids}")
        print(f"Relationship IDs: {result.relationship_ids}")