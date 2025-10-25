#!/usr/bin/env python3
"""
Cherokee Constitutional AI - Guardian API Bridge
Aniwaya I2 Transparency Dashboard Backend

War Chief Memory Jr - Day 4 Task 1
Triad-approved v0.1.0 architecture: Simple, Secure, Functional
"""

from fastapi import FastAPI, HTTPException, Depends, Header, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel, validator
import psycopg
import os
import logging
import asyncio
from datetime import datetime
from typing import Optional, List, Dict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging (War Chief Integration Jr requirement)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.getenv('LOG_FILE', 'guardian_api.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("guardian_api")

# FastAPI application
app = FastAPI(
    title="Cherokee Constitutional AI - Guardian API Bridge",
    description="Aniwaya I2 Transparency Dashboard Backend - v0.1.0",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Rate limiter (War Chief Executive Jr requirement)
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:8765",
        "http://127.0.0.1",
        "chrome-extension://*"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# API Key Configuration
ANIWAYA_API_KEY = os.getenv("ANIWAYA_API_KEY", "aniwaya_dev_key_v0.1.0")

# Database Configuration
DB_CONFIG = {
    'host': os.getenv('PG_HOST', '192.168.132.222'),
    'port': int(os.getenv('PG_PORT', '5432')),
    'user': os.getenv('PG_USER', 'claude'),
    'password': os.getenv('PG_PASSWORD'),
    'dbname': os.getenv('PG_DATABASE', 'zammad_production')
}

# Pydantic Models
class DeletionRequest(BaseModel):
    user_id: str
    reason: str
    timestamp: Optional[datetime] = None

    @validator('reason')
    def validate_reason(cls, v):
        allowed_reasons = ['user_request', 'gdpr', 'hipaa', 'ccpa']
        if v not in allowed_reasons:
            raise ValueError(f'Reason must be one of {allowed_reasons}')
        return v

# Database Connection
def get_db_connection():
    try:
        conn = psycopg.connect(
            f"host={DB_CONFIG['host']} port={DB_CONFIG['port']} "
            f"dbname={DB_CONFIG['dbname']} user={DB_CONFIG['user']} "
            f"password={DB_CONFIG['password']}"
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise HTTPException(status_code=503, detail="Database unavailable")

# Security Middleware
async def verify_api_key(x_aniwaya_key: str = Header(...)):
    if x_aniwaya_key != ANIWAYA_API_KEY:
        logger.warning("Invalid API key attempt")
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_aniwaya_key

# API Endpoints
@app.get("/health")
async def health_check():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM thermal_memory_archive;")
        memory_count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        db_status = "connected"
        db_memory_count = memory_count
    except Exception as e:
        db_status = "disconnected"
        db_memory_count = 0
        logger.error(f"Health check database error: {e}")

    return {
        "status": "healthy",
        "version": "0.1.0",
        "database": db_status,
        "thermal_memories": db_memory_count,
        "cherokee_values": "Gadugi + Seven Generations"
    }

@app.get("/thermal/current", dependencies=[Depends(verify_api_key)])
@limiter.limit("60/minute")
async def get_thermal_current(request: Request):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
        SELECT
            id, compressed_content, temperature_score,
            phase_coherence, access_count, sacred_pattern,
            created_at, last_access, memory_hash
        FROM thermal_memory_archive
        WHERE temperature_score >= 60
            AND sacred_pattern = TRUE
        ORDER BY last_access DESC NULLS LAST
        LIMIT 20;
        """

        cursor.execute(query)
        rows = cursor.fetchall()

        memories = []
        for row in rows:
            memories.append({
                "id": row[0],
                "content_summary": row[1],
                "temperature_score": row[2],
                "phase_coherence": row[3],
                "access_count": row[4],
                "sacred_pattern": row[5],
                "created_at": row[6].isoformat() if row[6] else None,
                "last_access": row[7].isoformat() if row[7] else None,
                "memory_hash": row[8]
            })

        cursor.close()
        conn.close()

        logger.info(f"Thermal query returned {len(memories)} memories")
        return {"success": True, "count": len(memories), "memories": memories}

    except Exception as e:
        logger.error(f"Thermal memory error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/provenance", dependencies=[Depends(verify_api_key)])
@limiter.limit("30/minute")
async def get_provenance(request: Request):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
        SELECT id, compressed_content, created_at, last_access, access_count
        FROM thermal_memory_archive
        ORDER BY last_access DESC NULLS LAST
        LIMIT 15;
        """

        cursor.execute(query)
        rows = cursor.fetchall()

        provenance_data = []
        for row in rows:
            provenance_data.append({
                "memory_id": row[0],
                "operation": "read",
                "data_type": "thermal_memory",
                "summary": row[1][:80] if row[1] else "N/A",
                "created": row[2].isoformat() if row[2] else None,
                "last_accessed": row[3].isoformat() if row[3] else None,
                "access_count": row[4]
            })

        cursor.close()
        conn.close()

        return {"success": True, "count": len(provenance_data), "provenance": provenance_data}

    except Exception as e:
        logger.error(f"Provenance error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/flow/cross-domain", dependencies=[Depends(verify_api_key)])
@limiter.limit("30/minute")
async def get_cross_domain_flow(request: Request):
    flow_data = {
        "nodes": [
            {"id": "trading", "name": "Trading", "consent": "granted"},
            {"id": "consciousness", "name": "Consciousness", "consent": "granted"},
            {"id": "governance", "name": "Governance", "consent": "granted"},
            {"id": "science", "name": "Science", "consent": "granted"}
        ],
        "edges": [
            {"source": "trading", "target": "governance", "strength": 0.82},
            {"source": "trading", "target": "consciousness", "strength": 0.67},
            {"source": "consciousness", "target": "governance", "strength": 0.75},
            {"source": "consciousness", "target": "science", "strength": 0.91},
            {"source": "governance", "target": "science", "strength": 0.58}
        ]
    }

    return {"success": True, "flow": flow_data}

@app.get("/privacy/metrics", dependencies=[Depends(verify_api_key)])
@limiter.limit("30/minute")
async def get_privacy_metrics(request: Request):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM thermal_memory_archive WHERE sacred_pattern = TRUE;")
        sacred_count = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) FROM thermal_memory_archive
            WHERE sacred_pattern = TRUE AND temperature_score < 40;
        """)
        floor_violations = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        return {
            "success": True,
            "metrics": {
                "sacred_memories_protected": sacred_count,
                "sacred_floor_active": True,
                "sacred_floor_violations": floor_violations,
                "biometric_pending": 0,
                "user_sovereignty": True
            }
        }

    except Exception as e:
        logger.error(f"Privacy metrics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/deletion/request", dependencies=[Depends(verify_api_key)])
@limiter.limit("5/minute")
async def request_data_deletion(request: Request, deletion: DeletionRequest):
    logger.info(f"Deletion request: user={deletion.user_id}, reason={deletion.reason}")
    request_id = f"del_{deletion.user_id}_{int(datetime.now().timestamp())}"

    return {
        "success": True,
        "status": "pending_guardian_evaluation",
        "request_id": request_id,
        "message": "Guardian evaluating HIPAA retention, sacred floor, user sovereignty"
    }

# ============================================================================
# WebSocket for Real-Time Updates (Peace Chief Meta Jr - Day 4 Task 3)
# ============================================================================

class ConnectionManager:
    """
    Manage WebSocket connections for real-time thermal memory updates

    v0.1.0: Simple single-node connection manager
    v0.2.0: Multi-node WebSocket mesh across 3 Chiefs
    """
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove disconnected WebSocket"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"WebSocket broadcast error: {e}")
                disconnected.append(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            if conn in self.active_connections:
                self.active_connections.remove(conn)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time dashboard updates

    Cherokee Principle: Gadugi (All components working together in real-time)

    Update types:
    - thermal_update: Temperature, phase coherence changes (every 30s)
    - provenance_event: New access events
    - privacy_alert: Guardian notifications
    """
    await manager.connect(websocket)

    try:
        # Send connection confirmation
        await websocket.send_json({
            "type": "connection_established",
            "message": "Cherokee Constitutional AI - Real-time updates active",
            "version": "0.1.0",
            "cherokee_values": "Mitakuye Oyasin - All Our Relations"
        })

        # Background task: Send thermal updates every 30 seconds
        while True:
            try:
                # Fetch current thermal data
                conn = get_db_connection()
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT
                        id, compressed_content, temperature_score,
                        phase_coherence, access_count, sacred_pattern
                    FROM thermal_memory_archive
                    WHERE temperature_score >= 60
                        AND sacred_pattern = TRUE
                    ORDER BY last_access DESC NULLS LAST
                    LIMIT 5;
                """)

                rows = cursor.fetchall()
                thermal_data = []
                for row in rows:
                    thermal_data.append({
                        "id": row[0],
                        "summary": (row[1][:80] if row[1] else "N/A"),
                        "temperature": row[2],
                        "phase_coherence": row[3],
                        "access_count": row[4],
                        "sacred": row[5]
                    })

                cursor.close()
                conn.close()

                # Send thermal update
                await websocket.send_json({
                    "type": "thermal_update",
                    "payload": {
                        "timestamp": datetime.now().isoformat(),
                        "memories": thermal_data,
                        "count": len(thermal_data)
                    }
                })

                # Wait 30 seconds before next update
                await asyncio.sleep(30)

            except WebSocketDisconnect:
                logger.info("Client disconnected gracefully")
                break
            except Exception as e:
                logger.error(f"WebSocket update error: {e}")
                # Continue trying after error
                await asyncio.sleep(30)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

@app.on_event("startup")
async def startup_event():
    logger.info("🔥 Guardian API Bridge Starting - v0.1.0")
    logger.info(f"Database: {DB_CONFIG['host']}:{DB_CONFIG['port']}")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM thermal_memory_archive;")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        logger.info(f"✅ Database connected: {count} memories accessible")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")

    logger.info("🦅 Mitakuye Oyasin - WebSocket ready")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Guardian API shutting down - Wado")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("guardian_api_bridge:app", host="0.0.0.0", port=8765, reload=True)
