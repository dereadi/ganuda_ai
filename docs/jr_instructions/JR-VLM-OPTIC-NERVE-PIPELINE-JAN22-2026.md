# Jr Task: VLM Optic Nerve Pipeline

Wire the complete vision pipeline: Frame → VLM → Entities → Relationships → Clauses → Brain

**Assigned to:** Software Engineer Jr.
**Node:** bluefin (192.168.132.222)
**Priority:** High
**Depends on:** Entity Extractor, Relationship Storer, Clause Evaluator

## Objective

Create `/ganuda/lib/vlm_optic_nerve.py` - the main pipeline orchestrator that:
1. Receives frames from cameras
2. Sends to VLM for description
3. Extracts entities and relationships
4. Stores in thermal memory
5. Evaluates clauses
6. Escalates to redfin brain when needed

## Implementation

**File:** `/ganuda/lib/vlm_optic_nerve.py`

```python
"""
Cherokee AI Federation - VLM Optic Nerve Pipeline
Complete vision processing: Camera → VLM → Relationships → Brain

Biological Analogy:
- Camera = Retina (light capture)
- VLM = Optic Nerve + V1/V2 (feature extraction)  
- Relationship Storage = Visual Cortex (pattern recognition)
- Clause Evaluation = Association Areas (meaning)
- Redfin Brain = Prefrontal Cortex (decision making)
"""

import httpx
import json
import logging
from typing import Dict, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime

# Import our modules
from vlm_entity_extractor import extract_from_description, extraction_to_dict
from vlm_relationship_storer import store_extraction, StoredExtraction
from vlm_clause_evaluator import evaluate_clauses_for_relationships, ClauseEvaluation

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

VLM_URL = "http://localhost:8090"  # Local bluefin VLM

@dataclass
class VisionResult:
    """Complete result of vision pipeline processing"""
    camera_id: str
    frame_path: str
    timestamp: str
    
    # VLM stage
    vlm_description: str
    vlm_latency_ms: float
    
    # Extraction stage
    entities_found: int
    relationships_found: int
    anomaly_detected: bool
    
    # Storage stage
    entity_memory_ids: Dict[str, int]
    relationship_ids: list
    
    # Evaluation stage
    clauses_triggered: int
    escalated_to_brain: bool
    brain_response: Optional[Dict]
    
    # Overall
    processing_time_ms: float
    success: bool
    error: Optional[str]


def process_frame(frame_path: str, camera_id: str) -> VisionResult:
    """
    Process a single frame through the complete optic nerve pipeline.
    
    This is the main entry point - call this with a frame path and camera ID.
    
    Args:
        frame_path: Path to the image file on bluefin
        camera_id: Identifier for the camera
        
    Returns:
        VisionResult with complete processing details
    """
    start_time = datetime.now()
    
    result = VisionResult(
        camera_id=camera_id,
        frame_path=frame_path,
        timestamp=start_time.isoformat(),
        vlm_description="",
        vlm_latency_ms=0,
        entities_found=0,
        relationships_found=0,
        anomaly_detected=False,
        entity_memory_ids={},
        relationship_ids=[],
        clauses_triggered=0,
        escalated_to_brain=False,
        brain_response=None,
        processing_time_ms=0,
        success=False,
        error=None
    )
    
    try:
        # Stage 1: VLM Description (Optic Nerve)
        logger.info(f"[OPTIC] Processing frame: {frame_path}")
        vlm_start = datetime.now()
        
        vlm_response = httpx.post(
            f"{VLM_URL}/v1/vlm/describe",
            json={"image_path": frame_path, "camera_id": camera_id},
            timeout=120.0
        )
        vlm_data = vlm_response.json()
        
        result.vlm_description = vlm_data.get("description", "")
        result.vlm_latency_ms = vlm_data.get("latency_ms", 0)
        
        if not vlm_data.get("success"):
            raise Exception(f"VLM failed: {vlm_data.get('error')}")
            
        logger.info(f"[OPTIC] VLM description: {result.vlm_description[:100]}...")
        
        # Stage 2: Entity Extraction (V1/V2 Cortex)
        logger.info("[OPTIC] Extracting entities and relationships...")
        extraction = extract_from_description(result.vlm_description, camera_id)
        
        if not extraction:
            raise Exception("Entity extraction failed")
            
        extraction_dict = extraction_to_dict(extraction)
        result.entities_found = len(extraction_dict.get("entities", []))
        result.relationships_found = len(extraction_dict.get("relationships", []))
        result.anomaly_detected = extraction_dict.get("anomaly_detected", False)
        
        logger.info(f"[OPTIC] Extracted: {result.entities_found} entities, {result.relationships_found} relationships")
        
        # Stage 3: Relationship Storage (Visual Cortex)
        logger.info("[OPTIC] Storing in thermal memory...")
        stored = store_extraction(extraction_dict, camera_id, frame_path)
        
        if not stored:
            raise Exception("Relationship storage failed")
            
        result.entity_memory_ids = stored.entity_memory_ids
        result.relationship_ids = stored.relationship_ids
        
        logger.info(f"[OPTIC] Stored: {len(result.relationship_ids)} relationships")
        
        # Stage 4: Clause Evaluation (Association Areas)
        if result.relationship_ids:
            logger.info("[OPTIC] Evaluating clauses...")
            evaluations = evaluate_clauses_for_relationships(result.relationship_ids)
            
            triggered = [e for e in evaluations if e.result]
            result.clauses_triggered = len(triggered)
            
            escalated = [e for e in triggered if e.action == "escalate"]
            result.escalated_to_brain = len(escalated) > 0
            
            if result.escalated_to_brain:
                logger.info(f"[OPTIC] Escalated to redfin brain: {[e.clause_name for e in escalated]}")
        
        # Success!
        result.success = True
        
    except Exception as e:
        logger.error(f"[OPTIC] Pipeline error: {e}")
        result.error = str(e)
        
    finally:
        result.processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        
    return result


def result_to_dict(result: VisionResult) -> Dict[str, Any]:
    """Convert VisionResult to dictionary for JSON serialization."""
    return asdict(result)


# Flask API for SAG integration
def create_app():
    """Create Flask app for SAG Camera UI integration."""
    from flask import Flask, request, jsonify
    
    app = Flask(__name__)
    
    @app.route("/v1/optic/process", methods=["POST"])
    def api_process_frame():
        """Process a frame through the optic nerve pipeline."""
        data = request.json or {}
        frame_path = data.get("frame_path")
        camera_id = data.get("camera_id", "unknown")
        
        if not frame_path:
            return jsonify({"error": "frame_path required"}), 400
            
        result = process_frame(frame_path, camera_id)
        return jsonify(result_to_dict(result))
    
    @app.route("/v1/optic/health", methods=["GET"])
    def api_health():
        """Health check."""
        return jsonify({
            "status": "healthy",
            "service": "vlm_optic_nerve",
            "node": "bluefin",
            "components": ["vlm", "extractor", "storer", "evaluator"]
        })
    
    return app


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--serve":
        # Run as API server
        app = create_app()
        app.run(host="0.0.0.0", port=8093)
    else:
        # Test with sample frame
        test_frame = "/ganuda/data/vision/frames/test/person.jpg"
        result = process_frame(test_frame, "test_camera")
        print(json.dumps(result_to_dict(result), indent=2))
```

## Systemd Service

**File:** `/ganuda/services/vision/optic-nerve.service`

```ini
[Unit]
Description=Cherokee AI - VLM Optic Nerve Pipeline
After=vlm-bluefin.service postgresql.service

[Service]
Type=simple
User=dereadi
WorkingDirectory=/ganuda/lib
Environment="PATH=/home/dereadi/cherokee_venv/bin:/usr/bin"
ExecStart=/home/dereadi/cherokee_venv/bin/python3 /ganuda/lib/vlm_optic_nerve.py --serve
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

## Verification

```bash
# Test pipeline directly
cd /ganuda/lib
python3 vlm_optic_nerve.py

# Or start as service
python3 vlm_optic_nerve.py --serve &
curl -X POST http://localhost:8093/v1/optic/process \
  -H "Content-Type: application/json" \
  -d '{"frame_path": "/ganuda/data/vision/frames/test/person.jpg", "camera_id": "test"}'
```

## Success Criteria

1. Pipeline processes frames end-to-end
2. VLM description extracted
3. Entities and relationships stored
4. Clauses evaluated
5. Escalation to redfin works when triggered
6. API endpoint responds correctly
