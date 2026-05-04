"""Federation Ethos Service — SQLite-backed structured ethos store.

Council vote ratifying this build: 9625a058a103f582 (May 4 2026).
Federation-internal Phase 1; HTTP layer pre-positioned for Phase 2 external rollout.

Run:
    /home/dereadi/cherokee_venv/bin/python -m uvicorn lib.ethos_service:app \\
        --host 127.0.0.1 --port 8830

Endpoints (all federation-internal in Phase 1; auth deferred to Phase 2):
    GET  /v1/ethos/health
    GET  /v1/ethos/lookup?term=...&tenant=cherokee_federation
    GET  /v1/ethos/category?category=...&limit=N
    GET  /v1/ethos/list?limit=N
    GET  /v1/ethos/scan?query=...        — keyword scan against term + definition
    POST /v1/ethos/insert                 — write new record
    POST /v1/ethos/supersede              — mark record valid_to=NOW (sacred-pattern blocks)
    POST /v1/ethos/unflag-sacred          — explicit sacred-flag removal w/ justification
    GET  /v1/ethos/audit                  — audit log query

CRITICAL INVARIANT — Sacred-pattern guardrail (Spider [INTEGRATION] requirement):
  - Records with sacred_pattern=1 CANNOT be superseded via /supersede.
  - Removal of sacred flag requires explicit /unflag-sacred call with Council
    audit hash + justification. Both attempts and successful unflags are logged.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

DB_PATH = os.environ.get("ETHOS_DB_PATH", "/ganuda/data/ethos.db")
DEFAULT_TENANT = "cherokee_federation"
ALLOWED_CATEGORIES = (
    "indigenous_teaching",
    "council_voice",
    "patent",
    "dc_principle",
    "sacred_pattern",
    "governance",
    "architectural_commitment",
    "identity",
)


app = FastAPI(
    title="Cherokee AI Federation — Ethos Service",
    version="1.0.0-phase1",
    description="Federation-internal ethos store. Phase 1 = no auth (federation-internal). "
                "Phase 2 will add JWT + license-key + multi-tenant scoping.",
)


# --------------------------------------------------------------------------
# DB helpers
# --------------------------------------------------------------------------

@contextmanager
def db_conn():
    conn = sqlite3.connect(DB_PATH, isolation_level=None)  # autocommit
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()


def compute_audit_hash(tenant_id: str, term: str, definition: str, valid_from: str) -> str:
    payload = f"{tenant_id}||{term}||{definition}||{valid_from}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _audit(conn, *, record_id: Optional[int], tenant_id: str, operation: str,
           actor: str, council_audit_hash: Optional[str], details: dict) -> None:
    conn.execute(
        """INSERT INTO ethos_audit_log
           (record_id, tenant_id, operation, actor, council_audit_hash, details)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (record_id, tenant_id, operation, actor, council_audit_hash, json.dumps(details)),
    )


# --------------------------------------------------------------------------
# Pydantic models
# --------------------------------------------------------------------------

class EthosRecord(BaseModel):
    id: int
    tenant_id: str
    term: str
    category: str
    definition: str
    context: Optional[str]
    source: str
    council_audit_hash: str
    valid_from: str
    valid_to: Optional[str]
    sacred_pattern: bool


class InsertRequest(BaseModel):
    term: str = Field(..., min_length=1, max_length=200)
    category: str
    definition: str = Field(..., min_length=1, max_length=10000)
    context: Optional[str] = Field(None, max_length=50000)
    source: str = Field(..., min_length=1, max_length=500)
    council_audit_hash: str = Field(..., description="External audit hash from Council ratification (NOT the internal record hash)")
    sacred_pattern: bool = False
    tenant_id: str = DEFAULT_TENANT

    @field_validator("category")
    @classmethod
    def valid_category(cls, v: str) -> str:
        if v not in ALLOWED_CATEGORIES:
            raise ValueError(f"category must be one of {ALLOWED_CATEGORIES}")
        return v


class SupersedeRequest(BaseModel):
    record_id: int
    council_audit_hash: str
    new_definition: Optional[str] = None
    justification: Optional[str] = None
    tenant_id: str = DEFAULT_TENANT


class UnflagSacredRequest(BaseModel):
    record_id: int
    council_audit_hash: str
    justification: str = Field(..., min_length=20,
                               description="Council vote required; justification logged in audit chain")
    tenant_id: str = DEFAULT_TENANT


# --------------------------------------------------------------------------
# Read endpoints
# --------------------------------------------------------------------------

@app.get("/v1/ethos/health")
def health():
    with db_conn() as conn:
        n_active = conn.execute(
            "SELECT COUNT(*) FROM ethos_records WHERE valid_to IS NULL"
        ).fetchone()[0]
        n_sacred = conn.execute(
            "SELECT COUNT(*) FROM ethos_records WHERE valid_to IS NULL AND sacred_pattern = 1"
        ).fetchone()[0]
    return {
        "status": "ok",
        "phase": "1-internal",
        "council_ratification": "9625a058a103f582",
        "active_records": n_active,
        "sacred_active": n_sacred,
        "db_path": DB_PATH,
    }


@app.get("/v1/ethos/lookup", response_model=list[EthosRecord])
def lookup(term: str = Query(..., min_length=1), tenant: str = DEFAULT_TENANT):
    with db_conn() as conn:
        rows = conn.execute(
            """SELECT * FROM ethos_records
               WHERE tenant_id = ? AND term = ? AND valid_to IS NULL""",
            (tenant, term),
        ).fetchall()
    return [EthosRecord(**dict(r)) for r in rows]


@app.get("/v1/ethos/category", response_model=list[EthosRecord])
def by_category(category: str = Query(...), limit: int = 100, tenant: str = DEFAULT_TENANT):
    if category not in ALLOWED_CATEGORIES:
        raise HTTPException(400, f"category must be one of {ALLOWED_CATEGORIES}")
    with db_conn() as conn:
        rows = conn.execute(
            """SELECT * FROM ethos_records
               WHERE tenant_id = ? AND category = ? AND valid_to IS NULL
               ORDER BY term LIMIT ?""",
            (tenant, category, limit),
        ).fetchall()
    return [EthosRecord(**dict(r)) for r in rows]


@app.get("/v1/ethos/list", response_model=list[EthosRecord])
def list_all(limit: int = 200, tenant: str = DEFAULT_TENANT):
    with db_conn() as conn:
        rows = conn.execute(
            """SELECT * FROM ethos_records
               WHERE tenant_id = ? AND valid_to IS NULL
               ORDER BY category, term LIMIT ?""",
            (tenant, limit),
        ).fetchall()
    return [EthosRecord(**dict(r)) for r in rows]


# Stopwords that almost never carry ethos signal — skip during tokenization
_STOPWORDS = frozenset({
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "and", "or", "not", "but", "of", "to", "in", "on", "at", "for", "from",
    "with", "by", "as", "if", "than", "that", "this", "these", "those",
    "what", "how", "why", "when", "where", "who", "whom", "which",
    "do", "does", "did", "doing", "have", "has", "had", "having",
    "i", "me", "my", "we", "us", "our", "you", "your", "they", "them", "their",
    "it", "its", "he", "him", "his", "she", "her",
    "can", "could", "may", "might", "should", "would", "will", "shall",
    "shape", "use", "used", "using", "make", "makes", "made",
    "about", "into", "onto", "out", "up", "down", "over", "under",
    "all", "any", "some", "no", "yes",
    "engineering", "federation",  # too generic in this corpus — present in many records
})


def _tokenize(query: str) -> list[str]:
    """Extract content tokens from a query for ethos-record matching."""
    out = []
    seen = set()
    for raw in query.split():
        tok = raw.strip(".,;:!?\"'()[]{}—–-").lower()
        if len(tok) < 3 or tok in _STOPWORDS:
            continue
        if tok in seen:
            continue
        seen.add(tok)
        out.append(tok)
    return out


@app.get("/v1/ethos/scan", response_model=list[EthosRecord])
def scan(query: str = Query(..., min_length=2), limit: int = 10, tenant: str = DEFAULT_TENANT):
    """Keyword scan: tokenize the query, match each token against term /
    definition / context. Returns ranked records (term-match > definition-match,
    sacred-pattern records preferred). Designed for harness use — accepts
    natural-language queries, not just single keywords."""
    tokens = _tokenize(query)
    if not tokens:
        # Fall back to whole-query substring match (handles unusual queries)
        tokens = [query.lower()]
    with db_conn() as conn:
        seen_ids: set[int] = set()
        ordered: list[sqlite3.Row] = []
        # Pass 1: prefer term-matches across all tokens (sacred first)
        for tok in tokens:
            pattern = f"%{tok}%"
            for row in conn.execute(
                """SELECT * FROM ethos_records
                   WHERE tenant_id = ? AND valid_to IS NULL
                     AND lower(term) LIKE ?
                   ORDER BY sacred_pattern DESC, term
                   LIMIT ?""",
                (tenant, pattern, limit),
            ):
                if row["id"] not in seen_ids:
                    seen_ids.add(row["id"])
                    ordered.append(row)
                    if len(ordered) >= limit:
                        break
            if len(ordered) >= limit:
                break
        # Pass 2: backfill with definition / context matches if room remains
        if len(ordered) < limit:
            for tok in tokens:
                pattern = f"%{tok}%"
                for row in conn.execute(
                    """SELECT * FROM ethos_records
                       WHERE tenant_id = ? AND valid_to IS NULL
                         AND (lower(definition) LIKE ? OR lower(context) LIKE ?)
                       ORDER BY sacred_pattern DESC, term
                       LIMIT ?""",
                    (tenant, pattern, pattern, limit),
                ):
                    if row["id"] not in seen_ids:
                        seen_ids.add(row["id"])
                        ordered.append(row)
                        if len(ordered) >= limit:
                            break
                if len(ordered) >= limit:
                    break
    return [EthosRecord(**dict(r)) for r in ordered[:limit]]


@app.get("/v1/ethos/audit")
def audit(limit: int = 100, tenant: str = DEFAULT_TENANT,
          operation: Optional[str] = None):
    sql = """SELECT * FROM ethos_audit_log
             WHERE tenant_id = ?"""
    params: list = [tenant]
    if operation:
        sql += " AND operation = ?"
        params.append(operation)
    sql += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)
    with db_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


# --------------------------------------------------------------------------
# Write endpoints
# --------------------------------------------------------------------------

@app.post("/v1/ethos/insert")
def insert_record(req: InsertRequest, x_federation_actor: str = Header(default="anonymous")):
    valid_from = datetime.now(timezone.utc).isoformat()
    with db_conn() as conn:
        cur = conn.execute(
            """INSERT INTO ethos_records
               (tenant_id, term, category, definition, context, source,
                council_audit_hash, valid_from, sacred_pattern)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (req.tenant_id, req.term, req.category, req.definition, req.context,
             req.source, req.council_audit_hash, valid_from, int(req.sacred_pattern)),
        )
        record_id = cur.lastrowid
        _audit(conn, record_id=record_id, tenant_id=req.tenant_id,
               operation="INSERT", actor=x_federation_actor,
               council_audit_hash=req.council_audit_hash,
               details={"term": req.term, "category": req.category,
                        "sacred_pattern": req.sacred_pattern})
    return {"id": record_id, "valid_from": valid_from, "council_audit_hash": req.council_audit_hash}


@app.post("/v1/ethos/supersede")
def supersede_record(req: SupersedeRequest, x_federation_actor: str = Header(default="anonymous")):
    """Mark a record as superseded (valid_to=NOW). SACRED-PATTERN GUARDRAIL:
    records with sacred_pattern=1 are blocked. Use /unflag-sacred first if
    Council has explicitly ratified removing sacred status."""
    with db_conn() as conn:
        row = conn.execute(
            "SELECT * FROM ethos_records WHERE id = ? AND tenant_id = ?",
            (req.record_id, req.tenant_id),
        ).fetchone()
        if not row:
            raise HTTPException(404, "record not found")
        if row["valid_to"] is not None:
            raise HTTPException(409, "record already superseded")
        if row["sacred_pattern"]:
            # Spider [INTEGRATION] CRITICAL: log the attempt + reject
            _audit(conn, record_id=req.record_id, tenant_id=req.tenant_id,
                   operation="SACRED_BLOCK", actor=x_federation_actor,
                   council_audit_hash=req.council_audit_hash,
                   details={"attempted": "supersede",
                            "term": row["term"],
                            "justification": req.justification or ""})
            raise HTTPException(
                403,
                f"sacred_pattern record (term={row['term']}) cannot be superseded. "
                "Use /v1/ethos/unflag-sacred first if Council has ratified.",
            )
        valid_to = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "UPDATE ethos_records SET valid_to = ? WHERE id = ?",
            (valid_to, req.record_id),
        )
        _audit(conn, record_id=req.record_id, tenant_id=req.tenant_id,
               operation="SUPERSEDE", actor=x_federation_actor,
               council_audit_hash=req.council_audit_hash,
               details={"term": row["term"], "justification": req.justification or ""})
        new_record_id = None
        if req.new_definition:
            valid_from = datetime.now(timezone.utc).isoformat()
            new_hash = compute_audit_hash(
                req.tenant_id, row["term"], req.new_definition, valid_from
            )
            cur = conn.execute(
                """INSERT INTO ethos_records
                   (tenant_id, term, category, definition, context, source,
                    council_audit_hash, valid_from, sacred_pattern)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (req.tenant_id, row["term"], row["category"], req.new_definition,
                 row["context"], row["source"], new_hash, valid_from, 0),
            )
            new_record_id = cur.lastrowid
            _audit(conn, record_id=new_record_id, tenant_id=req.tenant_id,
                   operation="INSERT", actor=x_federation_actor,
                   council_audit_hash=req.council_audit_hash,
                   details={"term": row["term"], "supersedes_id": req.record_id})
    return {"superseded_id": req.record_id, "valid_to": valid_to,
            "new_record_id": new_record_id}


@app.post("/v1/ethos/unflag-sacred")
def unflag_sacred(req: UnflagSacredRequest, x_federation_actor: str = Header(default="anonymous")):
    """Remove sacred_pattern flag. Requires Council audit hash + ≥20-char
    justification. Logged as SACRED_UNFLAG. After this, the record is
    eligible for /supersede via normal flow."""
    with db_conn() as conn:
        row = conn.execute(
            "SELECT * FROM ethos_records WHERE id = ? AND tenant_id = ?",
            (req.record_id, req.tenant_id),
        ).fetchone()
        if not row:
            raise HTTPException(404, "record not found")
        if not row["sacred_pattern"]:
            raise HTTPException(409, "record is not flagged sacred")
        conn.execute(
            "UPDATE ethos_records SET sacred_pattern = 0 WHERE id = ?",
            (req.record_id,),
        )
        _audit(conn, record_id=req.record_id, tenant_id=req.tenant_id,
               operation="SACRED_UNFLAG", actor=x_federation_actor,
               council_audit_hash=req.council_audit_hash,
               details={"term": row["term"], "justification": req.justification})
    return {"id": req.record_id, "sacred_pattern": False,
            "audit_hash": req.council_audit_hash}
