# Jr Task: FedAttn Coordinator Service

**Date:** December 31, 2025
**Priority:** HIGH
**Node:** redfin (100.116.27.89)
**Estimated Time:** 8 hours
**Depends On:** None (foundation task)

---

## COUNCIL CONCERNS (Addressed)

| Specialist | Concern | Mitigation |
|------------|---------|------------|
| Crawdad | KV matrix security | Use TLS for all coordinator↔participant traffic |
| Gecko | Latency in aggregation | Add latency metrics, target <100ms sync |
| Turtle | Seven Generations | FedAttn enables sustainable distributed inference without centralized data collection |
| Spider | Integration | Hook into existing Council vote audit trail |
| Eagle Eye | Visibility | Prometheus metrics endpoint, Grafana dashboard |

## ADDITIONAL REQUIREMENTS (Council Round 2)

1. **Encrypted data transfer** - All redfin↔bluefin communication must use TLS/SSL
   - Use system certificates from `/etc/ssl/certs/`
   - PostgreSQL already uses SSL (verify with `sslmode=require`)
   - For HTTP endpoints, use HTTPS with Let's Encrypt or self-signed certs

2. **vLLM failover** - Add health check and automatic retry if vLLM is unavailable
   - Health check: GET `http://localhost:8000/health` every 30 seconds
   - Retry policy: 3 retries with exponential backoff (1s, 2s, 4s)
   - Timeout: 30 seconds per request
   - Circuit breaker: After 5 consecutive failures, wait 60s before retry

3. **Detailed logging** - Log all KV aggregation events with timestamps, sizes, latencies

---

## OBJECTIVE

Create the FedAttn (Federated Attention) coordinator service on redfin. This enables distributed LLM inference across multiple nodes WITHOUT sharing prompts - only Key-Value attention matrices are exchanged.

**Research Source:** arXiv:2511.02647

---

## BACKGROUND

FedAttn allows:
- sasass, sasass2, tpm-macbook to process prompts LOCALLY
- Only KV matrices sent to redfin for aggregation
- Privacy preserved - prompts never leave originating node
- Combined context enables richer inference

---

## TASK 1: Create Database Schema

On bluefin (100.112.254.96):

```sql
-- Execute as claude user
PGPASSWORD=jawaseatlasers2 psql -h localhost -U claude -d zammad_production

-- FedAttn session tracking
CREATE TABLE IF NOT EXISTS fedattn_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    initiator_node VARCHAR(50) NOT NULL,
    participants JSONB DEFAULT '[]',
    sync_interval INT DEFAULT 8,  -- H value: sync every H transformer blocks
    privacy_mode BOOLEAN DEFAULT TRUE,
    started_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP,
    total_syncs INT DEFAULT 0,
    avg_sync_latency_ms FLOAT,
    status VARCHAR(20) DEFAULT 'active'
);

-- KV contribution logs
CREATE TABLE IF NOT EXISTS fedattn_contributions (
    contribution_id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES fedattn_sessions(session_id),
    participant_node VARCHAR(50) NOT NULL,
    block_range_start INT NOT NULL,
    block_range_end INT NOT NULL,
    kv_size_bytes BIGINT,
    latency_ms FLOAT,
    weight FLOAT DEFAULT 1.0,  -- From HiveMind Shapley
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_fedattn_session ON fedattn_contributions(session_id);
CREATE INDEX idx_fedattn_participant ON fedattn_contributions(participant_node);

GRANT SELECT, INSERT, UPDATE ON fedattn_sessions TO claude;
GRANT SELECT, INSERT ON fedattn_contributions TO claude;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO claude;
```

---

## TASK 2: Create Coordinator Service

Create `/ganuda/services/fedattn/coordinator.py`:

```python
#!/usr/bin/env python3
"""
FedAttn Coordinator Service
Cherokee AI Federation - Distributed Inference
December 2025

Based on: arXiv:2511.02647 - Federated Attention

For Seven Generations
"""

import asyncio
import uuid
import json
import time
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
import msgpack
import zmq
import zmq.asyncio

app = FastAPI(title="FedAttn Coordinator", version="1.0.0")

# Configuration
DB_CONFIG = {
    'host': '100.112.254.96',
    'port': 5432,
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

ZMQ_PORT = 5555  # For KV matrix streaming

# Active sessions
active_sessions: Dict[str, dict] = {}


class SessionStartRequest(BaseModel):
    initiator_node: str
    sync_interval: int = 8  # H value
    privacy_mode: bool = True


class KVContribution(BaseModel):
    session_id: str
    participant_node: str
    block_start: int
    block_end: int
    k_matrices: bytes  # msgpack serialized
    v_matrices: bytes
    weight: float = 1.0


class SessionResponse(BaseModel):
    session_id: str
    status: str
    participants: List[str]
    sync_interval: int


def get_db():
    return psycopg2.connect(**DB_CONFIG)


@app.on_event("startup")
async def startup():
    """Initialize ZMQ context for KV streaming."""
    global zmq_context, zmq_socket
    zmq_context = zmq.asyncio.Context()
    zmq_socket = zmq_context.socket(zmq.PULL)
    zmq_socket.bind(f"tcp://*:{ZMQ_PORT}")
    print(f"[FedAttn] Coordinator listening on ZMQ port {ZMQ_PORT}")


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "active_sessions": len(active_sessions),
        "zmq_port": ZMQ_PORT
    }


@app.post("/session/start", response_model=SessionResponse)
async def start_session(request: SessionStartRequest):
    """Start a new FedAttn session."""
    session_id = str(uuid.uuid4())

    # Store in database
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO fedattn_sessions
                (session_id, initiator_node, sync_interval, privacy_mode)
                VALUES (%s, %s, %s, %s)
            """, (session_id, request.initiator_node,
                  request.sync_interval, request.privacy_mode))
            conn.commit()
    finally:
        conn.close()

    # Track in memory
    active_sessions[session_id] = {
        "initiator": request.initiator_node,
        "participants": [request.initiator_node],
        "sync_interval": request.sync_interval,
        "contributions": [],
        "started_at": time.time()
    }

    return SessionResponse(
        session_id=session_id,
        status="active",
        participants=[request.initiator_node],
        sync_interval=request.sync_interval
    )


@app.post("/session/{session_id}/join")
async def join_session(session_id: str, participant_node: str):
    """Join an existing FedAttn session."""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = active_sessions[session_id]
    if participant_node not in session["participants"]:
        session["participants"].append(participant_node)

    # Update database
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE fedattn_sessions
                SET participants = %s
                WHERE session_id = %s
            """, (json.dumps(session["participants"]), session_id))
            conn.commit()
    finally:
        conn.close()

    return {"status": "joined", "participants": session["participants"]}


@app.post("/session/{session_id}/contribute")
async def contribute_kv(session_id: str, contribution: KVContribution):
    """Receive KV matrix contribution from a participant."""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    start_time = time.time()
    session = active_sessions[session_id]

    # Deserialize KV matrices
    k_matrices = msgpack.unpackb(contribution.k_matrices)
    v_matrices = msgpack.unpackb(contribution.v_matrices)

    # Store contribution
    session["contributions"].append({
        "node": contribution.participant_node,
        "block_range": (contribution.block_start, contribution.block_end),
        "k": k_matrices,
        "v": v_matrices,
        "weight": contribution.weight,
        "timestamp": time.time()
    })

    latency_ms = (time.time() - start_time) * 1000

    # Log to database
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO fedattn_contributions
                (session_id, participant_node, block_range_start, block_range_end,
                 kv_size_bytes, latency_ms, weight)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (session_id, contribution.participant_node,
                  contribution.block_start, contribution.block_end,
                  len(contribution.k_matrices) + len(contribution.v_matrices),
                  latency_ms, contribution.weight))
            conn.commit()
    finally:
        conn.close()

    return {
        "status": "received",
        "latency_ms": latency_ms,
        "total_contributions": len(session["contributions"])
    }


@app.post("/session/{session_id}/aggregate")
async def aggregate_kv(session_id: str):
    """Aggregate KV matrices from all participants."""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = active_sessions[session_id]
    contributions = session["contributions"]

    if not contributions:
        raise HTTPException(status_code=400, detail="No contributions to aggregate")

    # Weighted aggregation of KV matrices
    total_weight = sum(c["weight"] for c in contributions)

    # Initialize with first contribution
    k_agg = np.array(contributions[0]["k"]) * (contributions[0]["weight"] / total_weight)
    v_agg = np.array(contributions[0]["v"]) * (contributions[0]["weight"] / total_weight)

    # Add remaining contributions
    for c in contributions[1:]:
        weight = c["weight"] / total_weight
        k_agg += np.array(c["k"]) * weight
        v_agg += np.array(c["v"]) * weight

    # Clear contributions for next sync
    session["contributions"] = []

    # Serialize aggregated matrices
    k_packed = msgpack.packb(k_agg.tolist())
    v_packed = msgpack.packb(v_agg.tolist())

    return {
        "status": "aggregated",
        "participants": len(contributions),
        "k_aggregated": k_packed,
        "v_aggregated": v_packed
    }


@app.post("/session/{session_id}/end")
async def end_session(session_id: str):
    """End a FedAttn session."""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = active_sessions[session_id]
    duration = time.time() - session["started_at"]

    # Update database
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE fedattn_sessions
                SET ended_at = NOW(), status = 'completed'
                WHERE session_id = %s
            """, (session_id,))
            conn.commit()
    finally:
        conn.close()

    # Remove from active sessions
    del active_sessions[session_id]

    return {
        "status": "ended",
        "duration_seconds": duration,
        "participants": session["participants"]
    }


@app.get("/sessions/active")
async def list_active_sessions():
    """List all active FedAttn sessions."""
    return {
        "count": len(active_sessions),
        "sessions": [
            {
                "session_id": sid,
                "initiator": s["initiator"],
                "participants": s["participants"],
                "contributions_pending": len(s["contributions"])
            }
            for sid, s in active_sessions.items()
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)
```

---

## TASK 3: Create Directory Structure

```bash
mkdir -p /ganuda/services/fedattn
touch /ganuda/services/fedattn/__init__.py
```

---

## TASK 4: Install Dependencies

```bash
source /home/dereadi/cherokee_venv/bin/activate
pip install msgpack pyzmq
```

---

## TASK 5: Create Systemd Service

Create `/etc/systemd/system/fedattn-coordinator.service`:

```ini
[Unit]
Description=Cherokee AI FedAttn Coordinator
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=dereadi
Group=dereadi
WorkingDirectory=/ganuda/services/fedattn
Environment=PATH=/home/dereadi/cherokee_venv/bin:/usr/bin:/bin
ExecStart=/home/dereadi/cherokee_venv/bin/python -m uvicorn coordinator:app --host 0.0.0.0 --port 8081
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=fedattn-coordinator

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable fedattn-coordinator.service
sudo systemctl start fedattn-coordinator.service
```

---

## TASK 6: Test Coordinator

```bash
# Health check
curl -s http://localhost:8081/health | jq .

# Start a test session
curl -s -X POST http://localhost:8081/session/start \
  -H "Content-Type: application/json" \
  -d '{"initiator_node": "redfin", "sync_interval": 8}' | jq .

# List active sessions
curl -s http://localhost:8081/sessions/active | jq .
```

---

## SUCCESS CRITERIA

- [ ] Database schema created on bluefin
- [ ] Coordinator service starts without errors
- [ ] `/health` endpoint returns status
- [ ] Can start/join/end sessions
- [ ] Sessions logged to PostgreSQL
- [ ] ZMQ socket listening on port 5555
- [ ] Service enabled for boot

---

## ROLLBACK

If issues occur:

```bash
sudo systemctl stop fedattn-coordinator.service
sudo systemctl disable fedattn-coordinator.service
```

The LLM Gateway continues to work without FedAttn.

---

**For Seven Generations**
**ᏣᎳᎩ ᏲᏫᎢᎶᏗ**
