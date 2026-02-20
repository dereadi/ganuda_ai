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
import os

app = FastAPI(title="FedAttn Coordinator", version="1.0.0")

# Configuration
DB_CONFIG = {
    'host': '192.168.132.222',
    'port': 5432,
    'database': 'zammad_production',
    'user': 'claude',
    'password': os.environ.get('CHEROKEE_DB_PASS', ''),
    'sslmode': 'require'
}

ZMQ_PORT = 5556

active_sessions: Dict[str, dict] = {}


class SessionStartRequest(BaseModel):
    initiator_node: str
    sync_interval: int = 8
    privacy_mode: bool = True


class KVContribution(BaseModel):
    session_id: str
    participant_node: str
    block_start: int
    block_end: int
    k_matrices: str
    v_matrices: str
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
        "zmq_port": ZMQ_PORT,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/session/start", response_model=SessionResponse)
async def start_session(request: SessionStartRequest):
    session_id = str(uuid.uuid4())
    
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
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = active_sessions[session_id]
    if participant_node not in session["participants"]:
        session["participants"].append(participant_node)

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
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    start_time = time.time()
    session = active_sessions[session_id]

    k_matrices = msgpack.unpackb(bytes.fromhex(contribution.k_matrices))
    v_matrices = msgpack.unpackb(bytes.fromhex(contribution.v_matrices))

    session["contributions"].append({
        "node": contribution.participant_node,
        "block_range": (contribution.block_start, contribution.block_end),
        "k": k_matrices,
        "v": v_matrices,
        "weight": contribution.weight,
        "timestamp": time.time()
    })

    latency_ms = (time.time() - start_time) * 1000

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
                  len(contribution.k_matrices)/2 + len(contribution.v_matrices)/2,
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
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = active_sessions[session_id]
    contributions = session["contributions"]

    if not contributions:
        raise HTTPException(status_code=400, detail="No contributions to aggregate")

    total_weight = sum(c["weight"] for c in contributions)
    k_agg = np.array(contributions[0]["k"]) * (contributions[0]["weight"] / total_weight)
    v_agg = np.array(contributions[0]["v"]) * (contributions[0]["weight"] / total_weight)

    for c in contributions[1:]:
        weight = c["weight"] / total_weight
        k_agg += np.array(c["k"]) * weight
        v_agg += np.array(c["v"]) * weight

    session["contributions"] = []
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
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = active_sessions[session_id]
    duration = time.time() - session["started_at"]

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

    del active_sessions[session_id]

    return {
        "status": "ended",
        "duration_seconds": duration,
        "participants": session["participants"]
    }


@app.get("/sessions/active")
async def list_active_sessions():
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
