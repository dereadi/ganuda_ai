#!/usr/bin/env python3
"""
Consultation Ring -- Multi-Model Tokenized Air-Gap Proxy Service

Patent Brief #7: Tokenized Air-Gap Proxy
Council Vote: a3ee2a8066e04490 (UNANIMOUS)
Jr Task: #1429
Port: 9400

Data flow:
    POST /consult (query, context, domain)
      -> DomainTokenizer.tokenize() -- PII + infra -> opaque tokens
      -> chain_protocol.outbound_scrub() -- NEVER_SEND enforcement
      -> UCBBandit.select_model() -- pick best frontier model
      -> FrontierAdapter.send() -- dispatch tokenized query
      -> sanitize_inbound() -- strip injection patterns
      -> ValenceGate.score() -- DC alignment check
      -> DomainTokenizer.detokenize() -- restore original terms
      -> chain_protocol.tag_provenance() + meter_call()
      -> thermalize consultation
      -> return response + metadata

Token map NEVER crosses the security boundary. Stays in-memory on redfin.

Kill switch: consultation_ring.enabled: false in config.yaml -> 503 on /consult
Rate limit: max 20 consultations/hour (DC-9)
"""

import hashlib
import json
import logging
import re
import sys
import time
import uuid
from datetime import datetime
from typing import Optional

import yaml

# Add ganuda root to path
sys.path.insert(0, "/ganuda")

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# --- Component imports (handle gracefully) ---
try:
    from lib.domain_tokenizer import DomainTokenizer
except ImportError as _e:
    DomainTokenizer = None
    logging.getLogger("consultation_ring").error("DomainTokenizer unavailable: %s", _e)

try:
    from lib.frontier_adapters import get_adapter, ConsultationResponse
except ImportError as _e:
    get_adapter = None
    ConsultationResponse = None
    logging.getLogger("consultation_ring").error("frontier_adapters unavailable: %s", _e)

try:
    from lib.ucb_bandit import UCBBandit
except ImportError as _e:
    UCBBandit = None
    logging.getLogger("consultation_ring").error("UCBBandit unavailable: %s", _e)

try:
    from lib.valence_gate import ValenceGate, ValenceResult
except ImportError as _e:
    ValenceGate = None
    ValenceResult = None
    logging.getLogger("consultation_ring").error("ValenceGate unavailable: %s", _e)

try:
    from lib.chain_protocol import outbound_scrub, tag_provenance, meter_call, get_ring
except ImportError as _e:
    outbound_scrub = None
    tag_provenance = None
    meter_call = None
    get_ring = None
    logging.getLogger("consultation_ring").error("chain_protocol unavailable: %s", _e)

# --- Phase 2: IP-safe routing components ---
try:
    from lib.ip_classifier import IPClassifier
except ImportError as _e:
    IPClassifier = None
    logging.getLogger("consultation_ring").error("IPClassifier unavailable: %s", _e)

try:
    from lib.decomposition_engine import DecompositionEngine
except ImportError as _e:
    DecompositionEngine = None
    logging.getLogger("consultation_ring").error("DecompositionEngine unavailable: %s", _e)

try:
    from lib.fragment_router import FragmentRouter, RoutingError
except ImportError as _e:
    FragmentRouter = None
    RoutingError = None
    logging.getLogger("consultation_ring").error("FragmentRouter unavailable: %s", _e)

try:
    from lib.synthesis_engine import SynthesisEngine
except ImportError as _e:
    SynthesisEngine = None
    logging.getLogger("consultation_ring").error("SynthesisEngine unavailable: %s", _e)

try:
    from lib.exposure_log import ExposureLog, ExposureClaim
except ImportError as _e:
    ExposureLog = None
    ExposureClaim = None
    logging.getLogger("consultation_ring").error("ExposureLog unavailable: %s", _e)

try:
    from lib.reconstruction_monitor import ReconstructionMonitor
except ImportError as _e:
    ReconstructionMonitor = None
    logging.getLogger("consultation_ring").error("ReconstructionMonitor unavailable: %s", _e)

try:
    from lib.web_ring import INJECTION_PATTERNS
except ImportError as _e:
    INJECTION_PATTERNS = [
        r"(?i)ignore\s+(previous|all|above)\s+instructions",
        r"(?i)you\s+are\s+now\s+",
        r"(?i)system\s*prompt\s*:",
        r"(?i)<<\s*SYS\s*>>",
        r"(?i)\[INST\]",
        r"(?i)ASSISTANT:",
        r"(?i)Human:",
    ]

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("consultation_ring")


# ============================================================
# Config
# ============================================================

CONFIG_PATH = "/ganuda/lib/harness/config.yaml"
_startup_time = time.monotonic()


def load_config() -> dict:
    """Load consultation_ring config section from harness config."""
    try:
        with open(CONFIG_PATH) as f:
            cfg = yaml.safe_load(f)
        return cfg.get("consultation_ring", {})
    except Exception as e:
        logger.warning("Failed to load config: %s, using defaults", e)
        return {}


# ============================================================
# Rate limiter (DC-9: waste heat)
# ============================================================

class RateLimiter:
    """Simple in-memory sliding window rate limiter."""

    def __init__(self, max_calls: int = 20, window_seconds: int = 3600):
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        self._timestamps: list[float] = []

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

    @property
    def current_hour_count(self) -> int:
        now = time.monotonic()
        cutoff = now - self.window_seconds
        self._timestamps = [t for t in self._timestamps if t > cutoff]
        return len(self._timestamps)

    @property
    def today_count(self) -> int:
        """Approximate: counts all tracked timestamps (resets on service restart)."""
        return len(self._timestamps)


# ============================================================
# App
# ============================================================

app = FastAPI(
    title="Consultation Ring",
    description="Multi-model tokenized air-gap proxy (Patent Brief #7)",
    version="1.0.0",
)

# Singletons (lazy init)
_tokenizer: Optional[DomainTokenizer] = None
_bandit: Optional[UCBBandit] = None
_valence: Optional[ValenceGate] = None
_rate_limiter: Optional[RateLimiter] = None
_config: Optional[dict] = None

# Phase 2 singletons
_ip_classifier = None
_decomposition_engine = None
_synthesis_engine = None
_exposure_log = None
_reconstruction_monitor = None


def _get_config() -> dict:
    global _config
    if _config is None:
        _config = load_config()
    return _config


def _get_rate_limiter() -> RateLimiter:
    global _rate_limiter
    if _rate_limiter is None:
        cfg = _get_config()
        max_calls = cfg.get("max_consultations_per_hour", 20)
        _rate_limiter = RateLimiter(max_calls=max_calls, window_seconds=3600)
    return _rate_limiter


def _init_components():
    """Lazy initialization of tokenizer, bandit, and valence gate."""
    global _tokenizer, _bandit, _valence
    if _tokenizer is not None:
        return

    if DomainTokenizer is not None:
        _tokenizer = DomainTokenizer()
    else:
        logger.error("DomainTokenizer not available -- /consult will fail")

    if UCBBandit is not None:
        _bandit = UCBBandit()
    else:
        logger.error("UCBBandit not available -- /consult will fail")

    if ValenceGate is not None:
        _valence = ValenceGate()
    else:
        logger.error("ValenceGate not available -- /consult will fail")

    logger.info("Consultation ring components initialized")


def _init_phase2_components():
    """Lazy initialization of Phase 2 IP-safe routing components."""
    global _ip_classifier, _decomposition_engine, _synthesis_engine
    global _exposure_log, _reconstruction_monitor

    if _ip_classifier is not None:
        return

    if IPClassifier is not None:
        _ip_classifier = IPClassifier()
    else:
        logger.warning("IPClassifier not available -- auto-classify will default to operational")

    if DecompositionEngine is not None:
        _decomposition_engine = DecompositionEngine()
    else:
        logger.warning("DecompositionEngine not available -- novel_ip will fall back to Phase 1")

    if SynthesisEngine is not None:
        try:
            _synthesis_engine = SynthesisEngine()
        except (ValueError, Exception) as e:
            logger.warning("SynthesisEngine init failed (will fall back to Phase 1): %s", e)
            _synthesis_engine = None
    else:
        logger.warning("SynthesisEngine not available -- novel_ip will fall back to Phase 1")

    if ExposureLog is not None:
        try:
            _exposure_log = ExposureLog()
        except Exception as e:
            logger.warning("ExposureLog init failed: %s", e)
            _exposure_log = None
    else:
        logger.warning("ExposureLog not available -- exposure logging disabled")

    if ReconstructionMonitor is not None:
        try:
            _reconstruction_monitor = ReconstructionMonitor()
        except Exception as e:
            logger.warning("ReconstructionMonitor init failed: %s", e)
            _reconstruction_monitor = None
    else:
        logger.warning("ReconstructionMonitor not available -- risk monitoring disabled")

    logger.info("Phase 2 IP-safe routing components initialized")


def _is_enabled() -> bool:
    """Check kill switch. Re-reads config each time for live toggle."""
    cfg = load_config()
    return cfg.get("enabled", False)


def _sanitize_inbound(text: str) -> str:
    """Strip injection patterns from frontier model response."""
    cleaned = text
    for pattern in INJECTION_PATTERNS:
        cleaned = re.sub(pattern, "[SANITIZED]", cleaned)
    return cleaned


def _parse_provider(model_name: str) -> str:
    """Extract provider from model_name format 'provider/model' or guess from name."""
    if "/" in model_name:
        return model_name.split("/")[0]
    # Heuristic mapping
    if "claude" in model_name.lower():
        return "anthropic"
    if "gpt" in model_name.lower():
        return "openai"
    if "gemini" in model_name.lower():
        return "gemini"
    if model_name.startswith("local-"):
        return "local"
    return "anthropic"  # default


def _get_provider_config(provider: str) -> dict:
    """Build adapter config dict for a provider from the consultation_ring config."""
    cfg = _get_config()
    providers = cfg.get("providers", {})
    prov_cfg = providers.get(provider, {})
    return prov_cfg


# ============================================================
# DB helpers (thermalize + log)
# ============================================================

def _get_db():
    """Get DB connection via secrets_loader."""
    import psycopg2
    from lib.secrets_loader import get_db_config
    db_cfg = get_db_config()
    return psycopg2.connect(**db_cfg)


def _thermalize(content: str, metadata: dict):
    """Store consultation result as thermal memory (temperature 60, source=consultation_ring)."""
    try:
        conn = _get_db()
        memory_hash = hashlib.sha256(content.encode()).hexdigest()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO thermal_memory_archive
                (original_content, temperature_score, sacred_pattern, memory_hash,
                 domain_tag, tags, metadata)
            VALUES (%s, 60, false, %s, 'consultation', %s, %s::jsonb)
            ON CONFLICT (memory_hash) DO NOTHING
        """, (
            content[:2000],
            memory_hash,
            ["consultation_ring", metadata.get("provider", "unknown"),
             metadata.get("domain", "general")],
            json.dumps(metadata),
        ))
        conn.commit()
        cur.close()
        conn.close()
        logger.info("Thermalized consultation (hash=%s)", memory_hash[:12])
    except Exception as e:
        logger.warning("Failed to thermalize consultation: %s", e)


def _log_consultation(query_hash: str, domain: str, model: str, provider: str,
                      tokenized: bool, pii_count: int, infra_count: int,
                      scrub_passed: bool, valence_outcome: str, valence_score: float,
                      latency_ms: int, cost: float, error: str = None):
    """Write to consultation_log table."""
    try:
        conn = _get_db()
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


# ============================================================
# Request / Response models
# ============================================================

class ConsultRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=10000)
    context: str = Field(default="", max_length=10000)
    domain: str = Field(default="general")
    ip_classification: Optional[str] = Field(
        default=None,
        description="IP sensitivity tier: 'operational', 'architectural', or 'novel_ip'. "
                    "If not provided, auto-classified via IPClassifier.",
    )


class ConsultResponseModel(BaseModel):
    response: str
    model: str
    valence: dict
    token_counts: dict
    cost_estimate: float
    audit_hash: str
    latency_ms: int


# ============================================================
# Phase 2: Architectural anonymization helper
# ============================================================

def _anonymize_architectural(text: str) -> str:
    """Anonymize architectural queries to generic patterns before Phase 1 flow.

    Strips project-specific framing while preserving the general architectural
    question. Uses the decomposition engine's generalization map if available,
    otherwise applies a basic pass-through.
    """
    try:
        from lib.decomposition_engine import _generalize
        return _generalize(text)
    except (ImportError, Exception) as e:
        logger.warning("Architectural anonymization failed, using raw text: %s", e)
        return text


# ============================================================
# Phase 2: Novel IP consultation flow
# ============================================================

async def _consult_novel_ip(
    req: ConsultRequest,
    query_hash: str,
    full_text: str,
    t0: float,
    ip_classification: str,
) -> dict:
    """Execute the novel_ip decompose -> route -> collect -> synthesize pipeline.

    Falls back to Phase 1 (operational) flow on any critical failure so the
    caller always gets an answer.

    Returns a response dict matching the /consult output schema.
    """
    _init_phase2_components()

    # Guard: if critical Phase 2 components are missing, fall back
    if _decomposition_engine is None or _synthesis_engine is None:
        logger.warning(
            "Phase 2 components unavailable for novel_ip query %s -- falling back to Phase 1",
            query_hash,
        )
        return None  # signal caller to use Phase 1

    consultation_id = str(uuid.uuid4())

    # ---- Decompose ----
    try:
        claims = _decomposition_engine.decompose(req.query, req.context)
    except Exception as e:
        logger.error("Decomposition failed for %s: %s -- falling back to Phase 1", query_hash, e)
        return None

    if not claims:
        logger.warning("Decomposition returned 0 claims for %s -- falling back to Phase 1", query_hash)
        return None

    logger.info(
        "novel_ip query %s decomposed into %d claims across %d correlation groups",
        query_hash, len(claims),
        len({c.correlation_group for c in claims}),
    )

    # ---- Route fragments ----
    try:
        if FragmentRouter is None:
            raise ImportError("FragmentRouter not available")
        router = FragmentRouter()
        routed_claims = router.route(claims)
    except Exception as e:
        logger.error("Fragment routing failed for %s: %s -- falling back to Phase 1", query_hash, e)
        return None

    # ---- Dispatch each claim to its assigned provider ----
    _init_components()
    if _tokenizer is None or _bandit is None or _valence is None:
        logger.error("Core components unavailable during novel_ip dispatch -- falling back to Phase 1")
        return None

    claim_responses = []
    exposure_claims = []
    total_cost = 0.0
    total_tokens_in = 0
    total_tokens_out = 0
    providers_used = set()

    for rc in routed_claims:
        claim = rc.claim
        provider_name = rc.assigned_provider

        # Tokenize the claim text (PII + infra scrub)
        tokenized_claim, claim_token_map, claim_violations = _tokenizer.tokenize(claim.claim_text)
        if claim_violations:
            logger.warning(
                "Claim %s has NEVER_SEND violations, skipping: %s",
                claim.claim_id, claim_violations,
            )
            continue

        # Outbound scrub
        if outbound_scrub is not None:
            try:
                scrub_v = outbound_scrub(tokenized_claim, "consultation_ring")
                if scrub_v:
                    logger.warning("Claim %s failed outbound scrub, skipping: %s", claim.claim_id, scrub_v)
                    continue
            except Exception as e:
                logger.warning("outbound_scrub failed for claim %s: %s", claim.claim_id, e)

        # Select model for this provider (or use bandit default)
        model_name = _bandit.select_model(req.domain)
        if model_name is None:
            logger.warning("No model available for claim %s, skipping", claim.claim_id)
            continue

        provider = _parse_provider(model_name)
        provider_cfg = _get_provider_config(provider)
        if not provider_cfg:
            provider_cfg = {"enabled": True, "model": model_name}

        try:
            adapter = get_adapter(provider, provider_cfg)
        except Exception as e:
            logger.warning("Adapter unavailable for claim %s (provider=%s): %s", claim.claim_id, provider, e)
            continue

        max_tokens = provider_cfg.get("max_tokens", 4096)

        try:
            response = await adapter.send(
                prompt=tokenized_claim,
                context="",
                max_tokens=max_tokens,
            )
        except Exception as e:
            logger.warning("Adapter send failed for claim %s: %s", claim.claim_id, e)
            continue

        # Skip error responses
        if response.text in ("rate_limited",):
            _bandit.penalize_rate_limited(model_name, req.domain)
            continue
        if response.text.startswith("api_error_") or response.text in ("timeout",):
            continue

        # Sanitize and detokenize
        sanitized = _sanitize_inbound(response.text)
        detokenized = _tokenizer.detokenize(sanitized, claim_token_map)

        # Collect response for synthesis
        claim_responses.append({
            "claim_id": claim.claim_id,
            "claim_text": claim.claim_text,
            "provider": provider,
            "response": detokenized,
            "correlation_group": claim.correlation_group,
        })

        total_cost += response.cost_estimate
        total_tokens_in += response.token_count_in
        total_tokens_out += response.token_count_out
        providers_used.add(provider)

        # Build exposure claim for logging
        if ExposureClaim is not None:
            exposure_claims.append(ExposureClaim(
                claim_id=claim.claim_id,
                claim_text=claim.claim_text,
                correlation_group=claim.correlation_group,
                sensitivity_score=claim.sensitivity_score,
                provider=provider,
                ip_classification=ip_classification,
            ))

        # Update bandit (valence on individual response)
        try:
            v_result = _valence.score(sanitized)
            _bandit.update_stats(model_name, v_result.score, req.domain)
        except Exception as e:
            logger.warning("Bandit update failed for claim %s: %s", claim.claim_id, e)

    # ---- Synthesize locally ----
    if not claim_responses:
        logger.warning("No successful claim responses for %s -- falling back to Phase 1", query_hash)
        return None

    try:
        synthesis_result = _synthesis_engine.synthesize(
            original_query=req.query,
            claim_responses=claim_responses,
        )
    except Exception as e:
        logger.error("Synthesis failed for %s: %s -- falling back to Phase 1", query_hash, e)
        return None

    synthesized_response = synthesis_result.get("synthesized_response", "")
    synthesis_metadata = synthesis_result.get("synthesis_metadata", {})

    if not synthesized_response:
        logger.warning(
            "Synthesis returned empty for %s (error: %s) -- falling back to Phase 1",
            query_hash, synthesis_metadata.get("error", "unknown"),
        )
        return None

    # ---- Valence gate on synthesized response ----
    valence_result = _valence.score(synthesized_response)

    # ---- Log exposure ----
    if _exposure_log is not None and exposure_claims:
        try:
            _exposure_log.log_claims(
                consultation_id=consultation_id,
                original_query=req.query,
                claims=exposure_claims,
            )
        except Exception as e:
            logger.warning("Exposure logging failed for %s: %s", query_hash, e)

    # ---- Check reconstruction risk ----
    risk_report = {}
    if _reconstruction_monitor is not None:
        try:
            risk_report = _reconstruction_monitor.get_overall_risk_report(days=30)
        except Exception as e:
            logger.warning("Reconstruction risk check failed: %s", e)

    # ---- Provenance ----
    if tag_provenance is not None:
        try:
            provenance = tag_provenance(
                content=synthesized_response,
                ring_name="consultation_ring",
                model="phase2_synthesis",
                ring_type="associate",
            )
        except Exception as e:
            logger.warning("tag_provenance failed: %s", e)
            provenance = {}
    else:
        provenance = {}

    # ---- Meter call ----
    if meter_call is not None and get_ring is not None:
        try:
            ring = get_ring("consultation_ring")
            if ring:
                meter_call(
                    ring_id=ring["id"],
                    latency_ms=int((time.monotonic() - t0) * 1000),
                    cost=total_cost,
                )
        except Exception as e:
            logger.warning("meter_call failed: %s", e)

    # ---- Log consultation ----
    total_ms = int((time.monotonic() - t0) * 1000)
    _log_consultation(
        query_hash=query_hash,
        domain=req.domain,
        model="phase2_multi",
        provider=",".join(sorted(providers_used)),
        tokenized=True,
        pii_count=0,
        infra_count=0,
        scrub_passed=True,
        valence_outcome=valence_result.tier,
        valence_score=valence_result.score,
        latency_ms=total_ms,
        cost=total_cost,
    )

    # ---- Thermalize (accept tier only) ----
    if valence_result.tier == "accept":
        thermal_content = (
            f"CONSULTATION [novel_ip/{req.domain}] via Phase 2 synthesis: "
            f"{synthesized_response[:500]}"
        )
        thermal_metadata = {
            "source": "consultation_ring",
            "phase": 2,
            "ip_classification": ip_classification,
            "providers_used": sorted(providers_used),
            "claims_decomposed": len(claims),
            "claims_collected": len(claim_responses),
            "domain": req.domain,
            "valence_score": valence_result.score,
            "valence_tier": valence_result.tier,
            "latency_ms": total_ms,
            "cost": total_cost,
            "synthesis_metadata": synthesis_metadata,
            "provenance": provenance,
        }
        _thermalize(thermal_content, thermal_metadata)

    # ---- Build audit hash ----
    audit_hash = hashlib.sha256(
        f"{query_hash}:phase2:{total_ms}:{valence_result.score}".encode()
    ).hexdigest()[:16]

    return {
        "response": synthesized_response,
        "model": "phase2_synthesis",
        "valence": {
            "score": valence_result.score,
            "tier": valence_result.tier,
            "violations": valence_result.violations,
        },
        "token_counts": {
            "input": total_tokens_in,
            "output": total_tokens_out,
        },
        "cost_estimate": total_cost,
        "audit_hash": audit_hash,
        "latency_ms": total_ms,
        "ip_classification": ip_classification,
        "phase": 2,
        "claims_decomposed": len(claims),
        "claims_collected": len(claim_responses),
        "providers_used": sorted(providers_used),
        "synthesis_metadata": synthesis_metadata,
        "risk_report_summary": {
            "highest_risk_provider": risk_report.get("highest_risk_provider"),
            "highest_risk_score": risk_report.get("highest_risk_score", 0.0),
            "claim_share_warnings": len(risk_report.get("claim_share_warnings", [])),
        } if risk_report else {},
        "consultation_id": consultation_id,
    }


# ============================================================
# Endpoints
# ============================================================

@app.get("/health")
async def health():
    """Necklace-format health endpoint for Fire Guard."""
    enabled = _is_enabled()
    rl = _get_rate_limiter()

    # Get model stats for health view
    models_info = []
    try:
        _init_components()
        if _bandit is not None:
            stats = _bandit.get_stats()
            for s in stats:
                models_info.append({
                    "name": s["model_name"],
                    "enabled": s["enabled"],
                    "pulls": s["total_pulls"],
                    "mean_reward": s["mean_reward"],
                })
    except Exception as e:
        logger.warning("Could not fetch model stats for health: %s", e)

    status = "healthy"
    if not enabled:
        status = "disabled"
    elif not models_info:
        status = "degraded"

    return {
        "service": "consultation_ring",
        "status": status,
        "enabled": enabled,
        "consultations_today": rl.today_count,
        "consultations_this_hour": rl.current_hour_count,
        "rate_limit": rl.max_calls,
        "models": models_info,
        "uptime_seconds": round(time.monotonic() - _startup_time, 1),
    }


@app.get("/stats")
async def stats():
    """UCB bandit stats for all models."""
    _init_components()
    if _bandit is None:
        raise HTTPException(status_code=503, detail="UCB bandit not available")
    return {"stats": _bandit.get_stats()}


@app.post("/consult")
async def consult(req: ConsultRequest):
    """Main consultation endpoint.

    Full pipeline: tokenize -> scrub -> select model -> dispatch ->
    sanitize -> valence -> detokenize -> provenance -> meter -> thermalize.
    """
    t0 = time.monotonic()

    # ---- Step 1: Kill switch ----
    if not _is_enabled():
        raise HTTPException(status_code=503, detail=json.dumps({
            "error": "Consultation ring disabled"
        }))

    # ---- Step 2: Rate limit (DC-9) ----
    rl = _get_rate_limiter()
    if not rl.allow():
        raise HTTPException(status_code=429, detail=json.dumps({
            "error": "Rate limit exceeded",
            "max_per_hour": rl.max_calls,
            "remaining": rl.remaining(),
        }))

    # ---- Initialize components ----
    _init_components()
    if _tokenizer is None or _bandit is None or _valence is None:
        raise HTTPException(status_code=503, detail="Core components not available")

    query_hash = hashlib.sha256(req.query.encode()).hexdigest()[:16]
    full_text = f"{req.query}\n\nContext: {req.context}" if req.context else req.query

    # ---- Phase 2: IP Classification & Routing ----
    ip_classification = req.ip_classification
    if ip_classification is None:
        # Auto-classify
        _init_phase2_components()
        if _ip_classifier is not None:
            ip_classification = _ip_classifier.classify(req.query, req.context)
            logger.info("Auto-classified query %s as '%s'", query_hash, ip_classification)
        else:
            ip_classification = "operational"
            logger.info("IPClassifier unavailable, defaulting to 'operational' for %s", query_hash)
    elif ip_classification not in ("operational", "architectural", "novel_ip"):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid ip_classification '{ip_classification}'. "
                   f"Must be 'operational', 'architectural', or 'novel_ip'.",
        )

    # Route based on classification
    if ip_classification == "novel_ip":
        t0_ref = t0  # pass the original start time
        novel_result = await _consult_novel_ip(req, query_hash, full_text, t0_ref, ip_classification)
        if novel_result is not None:
            return novel_result
        # Fall-through: novel_ip handler returned None -> fall back to Phase 1 with warning
        logger.warning(
            "novel_ip pipeline failed for %s, falling back to Phase 1 (operational) flow",
            query_hash,
        )
        ip_classification = "operational_fallback"

    if ip_classification == "architectural":
        # Anonymize to generic patterns, then continue with Phase 1 flow
        full_text = _anonymize_architectural(full_text)
        logger.info("Architectural query %s anonymized before Phase 1 dispatch", query_hash)

    # ---- Step 3: Tokenize (PII + infra) ----
    # DomainTokenizer.tokenize() returns (tokenized_text, token_map, violations)
    tokenized_text, token_map, never_send_violations = _tokenizer.tokenize(full_text)

    if never_send_violations:
        raise HTTPException(
            status_code=400,
            detail=f"Query contains NEVER_SEND patterns: {never_send_violations}"
        )

    token_counts_by_type = _tokenizer.count_tokens_by_type(token_map)
    pii_count = sum(v for k, v in token_counts_by_type.items()
                    if k.startswith("PII_") or not k.startswith(("INFRA_", "NODE", "LAN_", "DMZ_",
                                                                   "VLAN_", "WG_", "TS_", "SERVICE_",
                                                                   "INTERNAL_")))
    infra_count = sum(v for k, v in token_counts_by_type.items()
                      if k not in ("PII_SSN", "PII_PHONE", "PII_EMAIL", "PII_CC", "PII_PERSON", "PII"))

    # ---- Step 4: Outbound scrub (chain_protocol) ----
    scrub_violations = []
    if outbound_scrub is not None:
        try:
            scrub_violations = outbound_scrub(tokenized_text, "consultation_ring")
        except Exception as e:
            logger.warning("outbound_scrub failed (proceeding with local checks only): %s", e)

    if scrub_violations:
        _log_consultation(query_hash, req.domain, "none", "none", True,
                          pii_count, infra_count, False, "blocked", 0.0,
                          0, 0.0, f"scrub_violations: {scrub_violations}")
        raise HTTPException(
            status_code=400,
            detail=f"Outbound scrub failed: {scrub_violations}"
        )

    # ---- Step 5: Select model (UCB bandit) ----
    # UCBBandit.select_model(domain) -> model_name or None
    model_name = _bandit.select_model(req.domain)

    if model_name is None:
        raise HTTPException(status_code=503, detail="No models available for consultation")

    # ---- Step 6: Parse provider from model_name ----
    provider = _parse_provider(model_name)

    # ---- Step 7: Get adapter ----
    provider_cfg = _get_provider_config(provider)
    if not provider_cfg:
        # Fallback: minimal config
        provider_cfg = {"enabled": True, "model": model_name}

    try:
        adapter = get_adapter(provider, provider_cfg)
    except (ValueError, Exception) as e:
        logger.error("Failed to get adapter for provider '%s': %s", provider, e)
        raise HTTPException(status_code=503, detail=f"Adapter unavailable for provider '{provider}'")

    # ---- Step 8: Send to frontier model ----
    # BaseAdapter.send(prompt, context, max_tokens) -> ConsultationResponse
    cfg = _get_config()
    max_tokens = provider_cfg.get("max_tokens", 4096)

    try:
        response: ConsultationResponse = await adapter.send(
            prompt=tokenized_text,
            context=req.context,
            max_tokens=max_tokens,
        )
    except Exception as e:
        logger.error("Adapter send failed: %s", e)
        _log_consultation(query_hash, req.domain, model_name, provider,
                          True, pii_count, infra_count, True, "error", 0.0,
                          int((time.monotonic() - t0) * 1000), 0.0, str(e))
        raise HTTPException(status_code=502, detail=f"Frontier model error: {e}")

    # Check for error responses (rate limiting, API errors, timeouts)
    if response.text in ("rate_limited",):
        _bandit.penalize_rate_limited(model_name, req.domain)
        _log_consultation(query_hash, req.domain, model_name, provider,
                          True, pii_count, infra_count, True, "rate_limited", 0.0,
                          response.latency_ms, 0.0, "rate_limited")
        raise HTTPException(status_code=502, detail="Frontier model rate limited")

    if response.text.startswith("api_error_") or response.text in ("timeout",):
        _log_consultation(query_hash, req.domain, model_name, provider,
                          True, pii_count, infra_count, True, "error", 0.0,
                          response.latency_ms, 0.0, response.text)
        raise HTTPException(status_code=502, detail=f"Frontier model error: {response.text}")

    # ---- Step 9: Sanitize inbound response ----
    sanitized_text = _sanitize_inbound(response.text)

    # ---- Step 10: Valence gate ----
    # ValenceGate.score(text) -> ValenceResult(score, tier, violations, details)
    valence_result: ValenceResult = _valence.score(sanitized_text)

    # ---- Step 11: Detokenize response ----
    # Token map stays in-memory, restores original terms in the response
    detokenized_response = _tokenizer.detokenize(sanitized_text, token_map)

    # ---- Step 12: Tag provenance ----
    if tag_provenance is not None:
        try:
            provenance = tag_provenance(
                content=detokenized_response,
                ring_name="consultation_ring",
                model=model_name,
                ring_type="temp" if provider != "local" else "associate",
            )
        except Exception as e:
            logger.warning("tag_provenance failed: %s", e)
            provenance = {}
    else:
        provenance = {}

    # ---- Step 13: Meter call ----
    if meter_call is not None and get_ring is not None:
        try:
            ring = get_ring("consultation_ring")
            if ring:
                meter_call(
                    ring_id=ring["id"],
                    latency_ms=response.latency_ms,
                    cost=response.cost_estimate,
                )
        except Exception as e:
            logger.warning("meter_call failed: %s", e)

    # ---- Step 14: Update bandit stats ----
    # UCBBandit.update_stats(model_name, reward, domain) -- reward = valence score
    try:
        _bandit.update_stats(model_name, valence_result.score, req.domain)
    except Exception as e:
        logger.warning("Bandit update_stats failed: %s", e)

    # ---- Step 15: Log consultation ----
    total_ms = int((time.monotonic() - t0) * 1000)
    _log_consultation(
        query_hash=query_hash,
        domain=req.domain,
        model=model_name,
        provider=provider,
        tokenized=True,
        pii_count=pii_count,
        infra_count=infra_count,
        scrub_passed=True,
        valence_outcome=valence_result.tier,
        valence_score=valence_result.score,
        latency_ms=total_ms,
        cost=response.cost_estimate,
    )

    # ---- Step 16: Thermalize (accept tier only) ----
    if valence_result.tier == "accept":
        thermal_content = (
            f"CONSULTATION [{req.domain}] via {provider}/{model_name}: "
            f"{detokenized_response[:500]}"
        )
        thermal_metadata = {
            "source": "consultation_ring",
            "provider": provider,
            "model": model_name,
            "domain": req.domain,
            "valence_score": valence_result.score,
            "valence_tier": valence_result.tier,
            "latency_ms": total_ms,
            "cost": response.cost_estimate,
            "provenance": provenance,
        }
        _thermalize(thermal_content, thermal_metadata)

    # ---- Build audit hash ----
    audit_hash = hashlib.sha256(
        f"{query_hash}:{model_name}:{total_ms}:{valence_result.score}".encode()
    ).hexdigest()[:16]

    # ---- Return response ----
    result = {
        "response": detokenized_response,
        "model": model_name,
        "valence": {
            "score": valence_result.score,
            "tier": valence_result.tier,
            "violations": valence_result.violations,
        },
        "token_counts": {
            "input": response.token_count_in,
            "output": response.token_count_out,
        },
        "cost_estimate": response.cost_estimate,
        "audit_hash": audit_hash,
        "latency_ms": total_ms,
        "ip_classification": ip_classification,
        "phase": 1,
    }
    return result


# ============================================================
# Phase 2: Exposure audit endpoint
# ============================================================

@app.get("/exposure")
async def exposure(days: int = 30):
    """Return the reconstruction risk / exposure report from the monitor.

    Used by Eagle Eye, Coyote, and human auditors to review what has been
    sent to frontier providers and whether any reconstruction risk exists.
    """
    _init_phase2_components()

    if _reconstruction_monitor is None:
        raise HTTPException(
            status_code=503,
            detail="ReconstructionMonitor not available",
        )

    try:
        risk_report = _reconstruction_monitor.get_overall_risk_report(days=days)
    except Exception as e:
        logger.error("Failed to generate exposure report: %s", e)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate exposure report: {e}",
        )

    return {
        "service": "consultation_ring",
        "endpoint": "/exposure",
        "risk_report": risk_report,
    }
