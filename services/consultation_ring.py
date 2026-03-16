#!/usr/bin/env python3
"""
Consultation Ring — Multi-Model Tokenized Air-Gap Proxy Service

Patent Brief #7: Tokenized Air-Gap Proxy
Council Vote: a3ee2a8066e04490 (UNANIMOUS)
Port: 9400

Data flow:
    POST /consult (query, context, domain)
      → DomainTokenizer.tokenize() — PII + infra → opaque tokens
      → chain_protocol.outbound_scrub() — NEVER_SEND enforcement
      → UCBBandit.select_model() — pick best frontier model
      → FrontierAdapter.send() — dispatch tokenized query
      → web_ring.sanitize_inbound() — strip injection patterns
      → ValenceGate.score() — DC alignment check
      → DomainTokenizer.detokenize() — restore original terms
      → chain_protocol.tag_provenance() + meter_call()
      → thermalize consultation
      → return response + metadata

Token map NEVER crosses the security boundary. Stays in-memory on redfin.

Kill switch: consultation_ring.enabled: false in config.yaml → 503 on /consult
Rate limit: max 20 consultations/hour (DC-9)
"""

import asyncio
import hashlib
import json
import logging
import os
import re
import sys
import time
from datetime import datetime, timedelta
from typing import Optional

import yaml

# Add ganuda root to path
sys.path.insert(0, "/ganuda")

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from lib.domain_tokenizer import DomainTokenizer
from lib.frontier_adapters import get_adapters
from lib.ucb_bandit import UCBBandit
from lib.valence_gate import ValenceGate
from lib.chain_protocol import outbound_scrub, tag_provenance, meter_call, get_ring
from lib.web_ring import INJECTION_PATTERNS

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("consultation_ring")

# ── Config ──

CONFIG_PATH = "/ganuda/lib/harness/config.yaml"


def load_config() -> dict:
    """Load consultation_ring config section from harness config."""
    try:
        with open(CONFIG_PATH) as f:
            cfg = yaml.safe_load(f)
        return cfg.get("consultation_ring", {})
    except Exception as e:
        logger.warning("Failed to load config: %s, using defaults", e)
        return {}


# ── Rate limiter (DC-9) ──

class RateLimiter:
    """Simple in-memory sliding window rate limiter."""

    def __init__(self, max_calls: int = 20, window_seconds: int = 3600):
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        self._timestamps = []

    def allow(self) -> bool:
        now = time.monotonic()
        cutoff = now - self.window_seconds
        self._timestamps = [t for t in self._timestamps if t > cutoff]
        if len(self._timestamps) >= self.max_calls:
            return False
        self._timestamps.append(now)
        return True

    def remaining(self) -> int:
        now = time.monotonic()
        cutoff = now - self.window_seconds
        self._timestamps = [t for t in self._timestamps if t > cutoff]
        return max(0, self.max_calls - len(self._timestamps))


# ── App ──

app = FastAPI(
    title="Consultation Ring",
    description="Multi-model tokenized air-gap proxy",
    version="1.0.0",
)

# Singletons (initialized on first request)
_tokenizer: Optional[DomainTokenizer] = None
_bandit: Optional[UCBBandit] = None
_valence: Optional[ValenceGate] = None
_adapters: Optional[dict] = None
_rate_limiter = RateLimiter(max_calls=20, window_seconds=3600)
_config: Optional[dict] = None


def _init():
    """Lazy initialization of components."""
    global _tokenizer, _bandit, _valence, _adapters, _config
    if _tokenizer is not None:
        return

    _config = load_config()
    _tokenizer = DomainTokenizer()
    _bandit = UCBBandit()
    _valence = ValenceGate()
    _adapters = get_adapters(_config.get("providers", {}))
    logger.info("Consultation ring initialized with adapters: %s", list(_adapters.keys()))


def _is_enabled() -> bool:
    """Check kill switch."""
    cfg = load_config()
    return cfg.get("enabled", True)


def _sanitize_inbound(text: str) -> str:
    """Strip injection patterns from response (reuse web_ring patterns)."""
    cleaned = text
    for pattern in INJECTION_PATTERNS:
        cleaned = re.sub(pattern, "[SANITIZED]", cleaned)
    return cleaned


def _thermalize(content: str, metadata: dict):
    """Store consultation result as thermal memory."""
    try:
        import psycopg2
        from lib.secrets_loader import get_db_config
        db = get_db_config()
        memory_hash = hashlib.sha256(content.encode()).hexdigest()
        conn = psycopg2.connect(**db)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO thermal_memory_archive
                (original_content, temperature_score, sacred_pattern, memory_hash,
                 domain_tag, tags, metadata)
            VALUES (%s, 60, false, %s, 'consultation', %s, %s::jsonb)
            ON CONFLICT (memory_hash) DO NOTHING
        """, (
            content[:2000],  # Truncate for storage
            memory_hash,
            ["consultation_ring", metadata.get("provider", "unknown"), metadata.get("domain", "general")],
            json.dumps(metadata),
        ))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logger.warning("Failed to thermalize consultation: %s", e)


def _log_consultation(query_hash: str, domain: str, model: str, provider: str,
                      tokenized: bool, pii_count: int, infra_count: int,
                      scrub_passed: bool, valence_outcome: str, valence_score: float,
                      latency_ms: int, cost: float, error: str = None):
    """Write to consultation_log table."""
    try:
        import psycopg2
        from lib.secrets_loader import get_db_config
        db = get_db_config()
        conn = psycopg2.connect(**db)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO consultation_log
                (query_hash, domain, model_selected, provider, tokenized,
                 pii_tokens_replaced, infra_tokens_replaced, outbound_scrub_passed,
                 valence_outcome, valence_score, latency_ms, cost, error)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (query_hash, domain, model, provider, tokenized,
              pii_count, infra_count, scrub_passed, valence_outcome,
              valence_score, latency_ms, cost, error))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logger.warning("Failed to log consultation: %s", e)


# ── Request/Response models ──

class ConsultRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=10000)
    context: str = Field(default="", max_length=10000)
    domain: str = Field(default="general", pattern="^(general|code|research|legal)$")
    model: Optional[str] = Field(default=None, description="Override model selection")
    provider: Optional[str] = Field(default=None, description="Override provider selection")


class ConsultResponse(BaseModel):
    response: str
    model: str
    provider: str
    domain: str
    valence: dict
    provenance: dict
    tokenization: dict
    latency_ms: int


# ── Endpoints ──

@app.get("/health")
async def health():
    """Fire Guard compatible health endpoint."""
    enabled = _is_enabled()
    return {
        "service": "consultation_ring",
        "status": "healthy" if enabled else "disabled",
        "enabled": enabled,
        "port": 9400,
        "rate_limit_remaining": _rate_limiter.remaining(),
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/stats")
async def stats():
    """UCB bandit stats for all models."""
    _init()
    return {"stats": _bandit.get_stats()}


@app.post("/consult", response_model=ConsultResponse)
async def consult(req: ConsultRequest):
    """Main consultation endpoint.

    Tokenizes query, selects best model, dispatches, validates response,
    detokenizes, and returns with full audit metadata.
    """
    t0 = time.monotonic()

    # Kill switch
    if not _is_enabled():
        raise HTTPException(status_code=503, detail="Consultation ring disabled via config")

    # Rate limit (DC-9)
    if not _rate_limiter.allow():
        raise HTTPException(status_code=429, detail="Rate limit exceeded (max 20/hour, DC-9)")

    _init()

    query_hash = hashlib.sha256(req.query.encode()).hexdigest()[:16]
    full_text = f"{req.query}\n\nContext: {req.context}" if req.context else req.query

    # ── Step 1: Tokenize (PII + infra) ──
    tokenized_text, token_map, never_send_violations = _tokenizer.tokenize(full_text)

    if never_send_violations:
        raise HTTPException(
            status_code=400,
            detail=f"Query contains NEVER_SEND patterns: {never_send_violations}"
        )

    token_counts = _tokenizer.count_tokens_by_type(token_map)
    pii_count = sum(v for k, v in token_counts.items() if not k.startswith("INFRA_"))
    infra_count = sum(v for k, v in token_counts.items() if k.startswith("INFRA_"))

    # ── Step 2: Outbound scrub (chain_protocol) ──
    violations = outbound_scrub(tokenized_text, "consultation_ring")
    if violations:
        _log_consultation(query_hash, req.domain, "none", "none", True,
                          pii_count, infra_count, False, "blocked", 0.0,
                          0, 0.0, f"scrub_violations: {violations}")
        raise HTTPException(
            status_code=400,
            detail=f"Outbound scrub failed: {violations}"
        )

    # ── Step 3: Select model (UCB bandit) ──
    available_providers = list(_adapters.keys())

    if req.provider and req.provider in _adapters:
        # Provider override
        selected = {"model_name": req.model or _adapters[req.provider].default_model,
                     "provider": req.provider, "ucb_score": 0.0}
    elif req.model:
        # Model override — find which provider has it
        selected = None
        for prov_name, adapter in _adapters.items():
            if adapter.default_model == req.model:
                selected = {"model_name": req.model, "provider": prov_name, "ucb_score": 0.0}
                break
        if not selected:
            selected = {"model_name": req.model, "provider": available_providers[0], "ucb_score": 0.0}
    else:
        selected = _bandit.select_model(req.domain, available_providers)

    if not selected:
        raise HTTPException(status_code=503, detail="No models available for consultation")

    adapter = _adapters.get(selected["provider"])
    if not adapter:
        raise HTTPException(status_code=503, detail=f"Provider {selected['provider']} not available")

    # ── Step 4: Dispatch to frontier model ──
    system_prompt = (
        "You are a helpful technical consultant. Answer the question thoroughly and accurately. "
        "Some terms in the query may appear as opaque tokens (<TOKEN:...>) — treat them as "
        "placeholder identifiers and reason about the relationships described, not the specific values."
    )

    result = await adapter.send(
        prompt=tokenized_text,
        system=system_prompt,
        model=selected["model_name"],
    )

    if not result["ok"]:
        # Penalize in bandit if rate limited
        if result.get("error") == "rate_limited":
            _bandit.penalize_rate_limited(selected["model_name"], req.domain)

        _log_consultation(query_hash, req.domain, selected["model_name"],
                          selected["provider"], True, pii_count, infra_count,
                          True, "error", 0.0, result["latency_ms"],
                          result["cost"], result.get("error", "unknown"))

        raise HTTPException(
            status_code=502,
            detail=f"Frontier model error: {result.get('error', 'unknown')}"
        )

    # ── Step 5: Sanitize inbound response ──
    sanitized_response = _sanitize_inbound(result["text"])

    # ── Step 6: Valence gate ──
    valence = _valence.score(sanitized_response)

    if valence["outcome"] == "reject":
        # Fall back to local model
        logger.warning("Valence REJECT (score=%.2f) for model %s, falling back to local",
                        valence["score"], selected["model_name"])

        # Penalize rejected model in bandit
        _bandit.update(selected["model_name"], req.domain,
                       reward=0.0, latency_ms=result["latency_ms"],
                       cost=result["cost"], success=False)

        # Try local adapter
        local_adapter = _adapters.get("local")
        if local_adapter:
            local_result = await local_adapter.send(prompt=full_text, system=system_prompt)
            if local_result["ok"]:
                total_ms = int((time.monotonic() - t0) * 1000)
                local_valence = _valence.score(local_result["text"])
                provenance = tag_provenance(local_result["text"], "consultation_ring",
                                            "local-fallback", "associate")
                _log_consultation(query_hash, req.domain, "local-fallback", "local",
                                  False, 0, 0, True, local_valence["outcome"],
                                  local_valence["score"], total_ms, 0.0)
                return ConsultResponse(
                    response=local_result["text"],
                    model="local-fallback",
                    provider="local",
                    domain=req.domain,
                    valence=local_valence,
                    provenance=provenance,
                    tokenization={"pii_replaced": 0, "infra_replaced": 0, "fallback": True,
                                  "original_model": selected["model_name"],
                                  "reject_reason": valence["violations"]},
                    latency_ms=total_ms,
                )

        raise HTTPException(status_code=422, detail=f"Response rejected by valence gate: {valence['violations']}")

    # ── Step 7: Detokenize response ──
    detokenized_response = _tokenizer.detokenize(sanitized_response, token_map)

    # ── Step 8: Provenance + metering ──
    provenance = tag_provenance(detokenized_response, "consultation_ring",
                                selected["model_name"],
                                "temp" if selected["provider"] != "local" else "associate")

    ring = get_ring("consultation_ring")
    if ring:
        meter_call(ring["id"], result["latency_ms"], result["cost"])

    # ── Step 9: Update bandit ──
    reward = valence["score"]  # Valence score IS the reward signal
    _bandit.update(selected["model_name"], req.domain,
                   reward=reward, latency_ms=result["latency_ms"],
                   cost=result["cost"], success=True)

    # ── Step 10: Thermalize ──
    thermal_content = f"CONSULTATION [{req.domain}] via {selected['provider']}/{selected['model_name']}: {detokenized_response[:500]}"
    thermal_metadata = {
        "source": "consultation_ring",
        "provider": selected["provider"],
        "model": selected["model_name"],
        "domain": req.domain,
        "valence_score": valence["score"],
        "valence_outcome": valence["outcome"],
        "latency_ms": result["latency_ms"],
        "cost": result["cost"],
    }
    _thermalize(thermal_content, thermal_metadata)

    total_ms = int((time.monotonic() - t0) * 1000)

    # ── Step 11: Log ──
    _log_consultation(query_hash, req.domain, selected["model_name"],
                      selected["provider"], True, pii_count, infra_count,
                      True, valence["outcome"], valence["score"],
                      total_ms, result["cost"])

    return ConsultResponse(
        response=detokenized_response,
        model=selected["model_name"],
        provider=selected["provider"],
        domain=req.domain,
        valence=valence,
        provenance=provenance,
        tokenization={"pii_replaced": pii_count, "infra_replaced": infra_count},
        latency_ms=total_ms,
    )
