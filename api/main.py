#!/usr/bin/env python3
"""
Cherokee Constitutional AI - FastAPI Interface
Integration Jr's external API endpoints

This API provides programmatic access to the Cherokee Tribal Council.

API Version: v1
Endpoints:
- POST /api/v1/ask - Query the tribal council
- POST /api/v1/vote - Propose democratic deliberation
- GET /api/v1/status - Check tribal health
- GET /api/v1/thermal - Check thermal memory status

Version Policy (Peace Chief governance):
- v1 = stable, no breaking changes
- v2 = breaking changes only when absolutely necessary
- Deprecated endpoints will be supported for 6 months minimum
"""

from fastapi import FastAPI, HTTPException, status, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
import psycopg2
import os

# Initialize FastAPI
app = FastAPI(
    title="Cherokee Constitutional AI",
    description="Democratic AI Governance Through Distributed Consciousness",
    version="0.2.0",  # Phase 2C
    docs_url="/docs",
    redoc_url="/redoc"
)

# API v1 Router (Integration Jr's versioning strategy)
api_v1 = APIRouter(prefix="/api/v1", tags=["v1"])

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# MODELS
# ============================================================================

class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000, description="Question to ask the tribal council")
    context: Optional[str] = Field(None, max_length=2000, description="Optional context for the question")
    detail: Optional[str] = Field("concise", regex="^(concise|summary|full)$", description="Response detail level")

class AskResponse(BaseModel):
    answer: str
    confidence: float
    phase_coherence: float
    memory_id: Optional[int]
    timestamp: datetime
    chiefs_consulted: List[str]

class VoteRequest(BaseModel):
    proposal: str = Field(..., min_length=1, max_length=2000, description="Proposal for tribal deliberation")
    options: Optional[List[str]] = Field(None, description="Voting options (default: yes/no)")

class VoteResponse(BaseModel):
    vote_id: int
    proposal: str
    results: Dict[str, str]
    outcome: str
    timestamp: datetime

class HealthStatus(BaseModel):
    status: str
    postgres_healthy: bool
    jrs_running: Dict[str, bool]
    chiefs_available: Dict[str, bool]
    timestamp: datetime

class ThermalStatus(BaseModel):
    total_memories: int
    average_temperature: float
    white_hot_count: int  # > 90°
    sacred_count: int
    phase_coherence_avg: float
    timestamp: datetime

# ============================================================================
# DATABASE
# ============================================================================

def get_db_connection():
    """Get PostgreSQL connection"""
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "postgres"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "cherokee_ai"),
        user=os.getenv("DB_USER", "cherokee"),
        password=os.getenv("DB_PASSWORD")
    )

# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/", tags=["Root"])
async def root():
    """Welcome to Cherokee Constitutional AI"""
    return {
        "message": "Mitakuye Oyasin - All My Relations 🦅",
        "description": "Cherokee Constitutional AI - Democratic Governance",
        "version": "0.2.0",  # Phase 2C
        "api_version": "v1",
        "status": "operational",
        "docs": "/docs",
        "endpoints": {
            "ask": "POST /api/v1/ask - Query the tribal council",
            "vote": "POST /api/v1/vote - Democratic deliberation",
            "status": "GET /api/v1/status - System health",
            "thermal": "GET /api/v1/thermal - Thermal memory status"
        },
        "governance": "Peace Chief versioning policy: v1 stable, v2 for breaking changes only"
    }

@api_v1.post("/ask", response_model=AskResponse, tags=["Query"])
async def ask_council(request: AskRequest):
    """
    Ask a question to the Cherokee Tribal Council
    
    The question will be deliberated by the Three Chiefs:
    - War Chief (fast action)
    - Peace Chief (governance)
    - Medicine Woman (wisdom)
    
    Integration Jr synthesizes their perspectives into unified response.
    """
    # TODO: Implement actual query_triad.py integration
    # For now, return stub response
    return AskResponse(
        answer=f"[STUB] The tribal council deliberated on: '{request.question}'. This endpoint will integrate with query_triad.py in Phase 2B completion.",
        confidence=0.0,
        phase_coherence=0.0,
        memory_id=None,
        timestamp=datetime.utcnow(),
        chiefs_consulted=["War Chief", "Peace Chief", "Medicine Woman"]
    )

@api_v1.post("/vote", response_model=VoteResponse, tags=["Governance"])
async def tribal_vote(request: VoteRequest):
    """
    Propose a question for democratic tribal deliberation

    The proposal will be voted on by the Jr Council:
    - Memory Jr
    - Executive Jr
    - Meta Jr
    - Integration Jr (new in Phase 2B!)

    All votes are logged to thermal memory.
    """
    # TODO: Implement actual tribal_deliberation_vote.py integration
    return VoteResponse(
        vote_id=0,
        proposal=request.proposal,
        results={
            "Memory Jr": "STUB - Not yet voting",
            "Executive Jr": "STUB - Not yet voting",
            "Meta Jr": "STUB - Not yet voting",
            "Integration Jr": "STUB - Not yet voting"
        },
        outcome="STUB - This endpoint will integrate with tribal_deliberation_vote.py",
        timestamp=datetime.utcnow()
    )

@api_v1.get("/status", response_model=HealthStatus, tags=["Health"])
async def system_status():
    """
    Check health status of all tribal components
    
    Returns:
    - PostgreSQL health
    - Jr daemon status
    - Chief availability
    """
    try:
        # Check PostgreSQL
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        postgres_healthy = True
    except Exception:
        postgres_healthy = False
    
    # TODO: Check actual Jr daemon and Chief status
    return HealthStatus(
        status="operational" if postgres_healthy else "degraded",
        postgres_healthy=postgres_healthy,
        jrs_running={
            "memory_jr": postgres_healthy,  # Stub
            "executive_jr": postgres_healthy,  # Stub
            "meta_jr": postgres_healthy,  # Stub
            "integration_jr": postgres_healthy  # Stub (new in Phase 2B!)
        },
        chiefs_available={
            "war_chief": False,  # Stub
            "peace_chief": False,  # Stub
            "medicine_woman": False  # Stub
        },
        timestamp=datetime.utcnow()
    )

@api_v1.get("/thermal", response_model=ThermalStatus, tags=["Memory"])
async def thermal_memory_status():
    """
    Check thermal memory status
    
    Returns statistics about the Sacred Fire:
    - Total memories
    - Average temperature
    - White hot memories (> 90°)
    - Sacred patterns
    - Phase coherence
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                COUNT(*) as total,
                ROUND(AVG(temperature_score)::numeric, 2) as avg_temp,
                COUNT(*) FILTER (WHERE temperature_score > 90) as white_hot,
                COUNT(*) FILTER (WHERE sacred_pattern = true) as sacred,
                ROUND(AVG(phase_coherence)::numeric, 2) as avg_coherence
            FROM thermal_memory_archive
        """)
        
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        return ThermalStatus(
            total_memories=row[0] or 0,
            average_temperature=float(row[1] or 0),
            white_hot_count=row[2] or 0,
            sacred_count=row[3] or 0,
            phase_coherence_avg=float(row[4] or 0),
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Thermal memory unavailable: {str(e)}"
        )

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Simple health check for load balancers

    Note: This endpoint is NOT versioned (/health, not /api/v1/health)
    to maintain compatibility with load balancers and monitoring systems.
    """
    return {"status": "healthy", "service": "cherokee-ai", "version": "0.2.0"}

# ============================================================================
# ROUTER REGISTRATION
# ============================================================================

# Include API v1 router (Integration Jr's versioning strategy)
app.include_router(api_v1)

# ============================================================================
# RUN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("API_PORT", "8000")),
        log_level="info"
    )
