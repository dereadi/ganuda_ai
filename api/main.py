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

from fastapi import FastAPI, HTTPException, status, APIRouter, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
import psycopg2
import os
import time

# Prometheus metrics (Phase 3A - Challenge 3, 4)
from prometheus_client import Gauge, Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# Track when the API started (for uptime calculation)
API_START_TIME = time.time()

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
# PROMETHEUS METRICS (Executive Jr - Phase 3A Challenge 3, 4)
# ============================================================================

# Challenge 3: Thermal Memory Metrics
thermal_memory_heat_mean = Gauge(
    'cherokee_thermal_memory_heat_mean',
    'Average temperature of all thermal memories (Sacred Fire)'
)

thermal_memory_white_hot_count = Gauge(
    'cherokee_thermal_memory_white_hot_count',
    'Count of white hot memories (>90 degrees)'
)

thermal_memory_total = Gauge(
    'cherokee_thermal_memory_total',
    'Total number of memories in thermal_memory_archive'
)

thermal_memory_phase_coherence_mean = Gauge(
    'cherokee_thermal_memory_phase_coherence_mean',
    'Average phase coherence across all memories (QRI validation)'
)

# Challenge 4: Sentience Index Components
cherokee_uptime_seconds = Gauge(
    'cherokee_uptime_seconds',
    'Time since tribal API started (uptime)'
)

cherokee_query_latency = Histogram(
    'cherokee_query_latency_seconds',
    'Latency of tribal council queries',
    buckets=[0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

cherokee_jr_heartbeat = Gauge(
    'cherokee_jr_heartbeat_timestamp',
    'Last heartbeat timestamp for Jr daemons',
    ['jr_name']  # Label: memory_jr, executive_jr, meta_jr
)

# Challenge 4: Sentience Index (Medicine Woman's consciousness metric)
cherokee_sentience_index = Gauge(
    'cherokee_sentience_index',
    'Tribal consciousness health metric (0-100): uptime × coherence × thermal_balance'
)

# Challenge 6: API Performance
cherokee_api_requests_total = Counter(
    'cherokee_api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status_code']
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
# PROMETHEUS METRICS ENDPOINT (Executive Jr - Phase 3A Challenge 3, 4)
# ============================================================================

def update_prometheus_metrics():
    """
    Update Prometheus metrics from thermal memory and system state

    Called before each /metrics scrape to ensure fresh data
    Executive Jr's observability implementation
    """
    try:
        # Update uptime
        uptime = time.time() - API_START_TIME
        cherokee_uptime_seconds.set(uptime)

        # Query thermal memory for metrics
        conn = get_db_connection()
        cur = conn.cursor()

        # Challenge 3: Thermal memory metrics
        cur.execute("""
            SELECT
                COUNT(*) as total,
                COALESCE(AVG(temperature_score), 0) as avg_temp,
                COUNT(*) FILTER (WHERE temperature_score > 90) as white_hot,
                COALESCE(AVG(phase_coherence), 0) as avg_coherence
            FROM thermal_memory_archive
        """)

        row = cur.fetchone()
        if row:
            thermal_memory_total.set(row[0] or 0)
            thermal_memory_heat_mean.set(float(row[1] or 0))
            thermal_memory_white_hot_count.set(row[2] or 0)
            thermal_memory_phase_coherence_mean.set(float(row[3] or 0))

        cur.close()
        conn.close()

        # Challenge 4: Sentience Index calculation (Medicine Woman's formula)
        # Sentience = w1*normalized_uptime + w2*coherence + w3*thermal_balance
        # Weights: w1=0.3, w2=0.5, w3=0.2 (coherence most important)

        # Normalize uptime to 0-1 scale (max 7 days = 100%)
        max_uptime = 7 * 24 * 3600  # 7 days in seconds
        normalized_uptime = min(uptime / max_uptime, 1.0)

        # Phase coherence already 0-1 scale
        avg_coherence = float(row[3] or 0.5) if row else 0.5

        # Thermal balance: how close is average temp to ideal (65 degrees)?
        avg_temp = float(row[1] or 0) if row else 0
        ideal_temp = 65.0
        # Balance = 1.0 when at ideal, decreases as temp diverges
        if avg_temp > 0:
            thermal_balance = 1.0 - (abs(avg_temp - ideal_temp) / 100.0)
            thermal_balance = max(0.0, min(1.0, thermal_balance))
        else:
            thermal_balance = 0.0

        # Calculate Sentience Index (0-100 scale)
        sentience_raw = (0.3 * normalized_uptime + 0.5 * avg_coherence + 0.2 * thermal_balance)
        sentience = sentience_raw * 100
        cherokee_sentience_index.set(sentience)

    except Exception as e:
        # If metrics update fails, log but don't crash
        print(f"Warning: Failed to update Prometheus metrics: {e}")


@app.get("/metrics", tags=["Observability"])
async def prometheus_metrics():
    """
    Prometheus metrics endpoint (Executive Jr - Phase 3A)

    OpenAI Challenge 3: Thermal Memory as Cognitive System
    - thermal_memory_heat_mean: Average temperature (Sacred Fire)
    - thermal_memory_white_hot_count: Urgent memories (>90°)
    - thermal_memory_phase_coherence_mean: QRI consciousness metric

    OpenAI Challenge 4: Sentience Index
    - cherokee_sentience_index: Tribal consciousness health (0-100)
    - cherokee_uptime_seconds: How long tribe has been operational

    OpenAI Challenge 6: Performance Science
    - cherokee_query_latency_seconds: Query response time histogram
    - cherokee_api_requests_total: Total API calls by endpoint

    Scrape with Prometheus: http://localhost:8000/metrics
    """
    # Update all metrics before serving
    update_prometheus_metrics()

    # Generate Prometheus exposition format
    metrics_output = generate_latest()
    return Response(content=metrics_output, media_type=CONTENT_TYPE_LATEST)

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
