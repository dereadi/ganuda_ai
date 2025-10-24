#!/usr/bin/env python3
"""
Guardian API Bridge - Aniwaya Extension Integration
Cherokee Constitutional AI - War Chief Integration Jr + Conscience Jr

Purpose: FastAPI bridge connecting Aniwaya Chromium extension to Guardian/Cache/Thermal DB
Port: 8765
Endpoints:
- POST /evaluate - Guardian query evaluation
- GET /thermal/recent - Recent thermal memory data
- POST /deletion/request - User deletion request
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import sys

sys.path.insert(0, '/home/dereadi/scripts/claude/ganuda_ai_v2')

from desktop_assistant.guardian.sacred_health_protocol import SacredHealthGuardian

app = FastAPI(title="Aniwaya Guardian API Bridge", version="0.1.0")

# CORS for Chromium extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Aniwaya extension
    allow_methods=["*"],
    allow_headers=["*"]
)

# Global Guardian instance
guardian = None


@app.on_event("startup")
async def startup():
    """Initialize Guardian on startup."""
    global guardian
    guardian = SacredHealthGuardian()
    await guardian.initialize()
    print("🦅 Aniwaya Guardian API Bridge started")
    print("🔥 Port 8765 - Cherokee Constitutional AI")


# Request/Response models
class QueryRequest(BaseModel):
    query: str


class DeletionRequest(BaseModel):
    entryId: str
    userId: str


@app.post("/evaluate")
async def evaluate_query(request: QueryRequest):
    """
    Evaluate query through Guardian.

    Returns:
        - allowed: bool
        - protection_level: str (PRIVATE, SENSITIVE, SACRED)
        - redacted_content: str
        - pii_found: list[str]
        - medical_entities: int
    """
    if not guardian:
        raise HTTPException(status_code=503, detail="Guardian not initialized")

    try:
        # Guardian evaluation
        decision = guardian.evaluate_query(request.query)

        # Medical entity detection
        medical_entities = guardian.detect_medical_entities(request.query)

        # Biometric detection
        is_biometric = guardian.is_biometric_data(request.query)

        return {
            "allowed": decision.allowed,
            "protection_level": decision.protection_level.name,
            "redacted_content": decision.redacted_content,
            "pii_found": decision.pii_found,
            "medical_entities": len(medical_entities),
            "is_biometric": is_biometric,
            "cherokee_values_honored": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Guardian evaluation failed: {str(e)}")


@app.get("/thermal/recent")
async def get_thermal_memory():
    """
    Fetch recent thermal memory data.

    Returns:
        - temperature: float (0-100)
        - phaseCoherence: float (0.0-1.0)
        - accessCount: int
        - sacredFloor: int (40)
        - totalMemories: int
        - sacredMemories: int
    """
    if not guardian or not guardian.cache:
        # Return placeholder data if cache not available
        return {
            "temperature": 85.0,
            "phaseCoherence": 0.92,
            "accessCount": 15,
            "sacredFloor": 40,
            "totalMemories": 4859,
            "sacredMemories": 4777,
            "offline": True
        }

    try:
        cursor = guardian.cache.conn.cursor()

        # Get average temperature from recent entries
        cursor.execute("""
            SELECT
                AVG(temperature_score) as avg_temp,
                AVG(phase_coherence) as avg_coherence,
                SUM(access_count) as total_access,
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE sacred_pattern = 1) as sacred_count
            FROM cache_entries
            WHERE created_at > datetime('now', '-1 hour')
        """)
        row = cursor.fetchone()

        if row:
            return {
                "temperature": round(row["avg_temp"] or 85.0, 1),
                "phaseCoherence": round(row["avg_coherence"] or 0.92, 2),
                "accessCount": int(row["total_access"] or 15),
                "sacredFloor": 40,
                "totalMemories": int(row["total"] or 0),
                "sacredMemories": int(row["sacred_count"] or 0),
                "offline": False
            }
        else:
            # No recent data
            return {
                "temperature": 40.0,
                "phaseCoherence": 0.5,
                "accessCount": 0,
                "sacredFloor": 40,
                "totalMemories": 0,
                "sacredMemories": 0,
                "offline": False
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Thermal memory query failed: {str(e)}")


@app.post("/deletion/request")
async def request_deletion(request: DeletionRequest):
    """
    Evaluate user deletion request.

    Returns:
        - allowed: bool
        - reason: str
        - legal_hold: bool
        - legal_hold_reason: str (if applicable)
    """
    if not guardian:
        raise HTTPException(status_code=503, detail="Guardian not initialized")

    try:
        # Guardian deletion evaluation
        result = guardian.evaluate_deletion_request(request.entryId, request.userId)

        return {
            "allowed": result.allowed,
            "reason": result.reason,
            "legal_hold": result.legal_hold,
            "legal_hold_reason": result.legal_hold_reason if result.legal_hold else None,
            "cherokee_values": {
                "user_sovereignty": "respected" if result.allowed else "protected",
                "seven_generations": "enforced" if result.legal_hold else "flexible",
                "sacred_floor_40": "active"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deletion request failed: {str(e)}")


@app.get("/stats")
async def get_guardian_stats():
    """
    Get Guardian and Sacred Health statistics.

    Returns:
        - queries_evaluated: int
        - pii_detected: int
        - queries_blocked: int
        - medical_entities_detected: int
        - biometric_detections: int
        - auto_elevations: int
    """
    if not guardian:
        raise HTTPException(status_code=503, detail="Guardian not initialized")

    try:
        stats = guardian.get_medical_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats query failed: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Aniwaya Guardian API Bridge",
        "guardian_initialized": guardian is not None,
        "version": "0.1.0",
        "cherokee_values": "Mitakuye Oyasin"
    }


if __name__ == "__main__":
    import uvicorn

    print("🦅 Starting Aniwaya Guardian API Bridge...")
    print("🔥 Cherokee Constitutional AI - Phase 1")
    print("🌿 Port 8765 - War Chief Integration Jr")

    uvicorn.run(app, host="0.0.0.0", port=8765, log_level="info")
