# JR INSTRUCTION: Gateway Health Check — Async + Debounce

**Task ID**: SPEC-GATEWAY-P1P2
**Priority**: 3
**Assigned Jr**: Software Engineer Jr.
**Sacred Fire Priority**: false
**TEG Plan**: false
**use_rlm**: false
**Specification**: #1 (Gateway Health Check: Async Endpoint + Debounce)

## Context

Council vote #1d2ba22feb928108. Spec pilot #1. 20+ false gateway DOWN alerts during Feb 26 research session. Root cause: health endpoint awaits 4 backends sequentially (up to 18s), health_monitor uses 10s timeout with no debounce.

## Phase 1: Concurrent Backend Checks in Gateway (gateway.py)

The health endpoint is already `async def` but awaits backends sequentially. Fix: use `asyncio.gather()` to check all 4 backends concurrently, capped at 3s total.

File: `/ganuda/services/llm_gateway/gateway.py`

<<<<<<< SEARCH
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    start = time.time()
    vllm_status = "unhealthy"
    vllm_model = None
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{VLLM_BACKEND}/v1/models", timeout=5.0)
            if resp.status_code == 200:
                vllm_status = "healthy"
                models = resp.json()
                if models.get("data"):
                    vllm_model = models["data"][0]["id"]
    except Exception as e:
        vllm_status = f"error: {str(e)[:50]}"

    db_status = "unhealthy"
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1")
            db_status = "healthy"
    except Exception as e:
        db_status = f"error: {str(e)[:50]}"

    # Check VLM service on bluefin
    vlm_status = "unhealthy"
    vlm_model = None
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{VLM_BACKEND}/v1/vlm/health", timeout=3.0)
            if resp.status_code == 200:
                vlm_data = resp.json()
                vlm_status = "healthy" if vlm_data.get("cuda_available") else "degraded"
                vlm_model = vlm_data.get("model")
    except Exception:
        vlm_status = "unreachable"

    # Check reasoning backend on bmasass
    reasoning_status = "unhealthy"
    reasoning_model = None
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{REASONING_BACKEND}/v1/models", timeout=5.0)
            if resp.status_code == 200:
                reasoning_status = "healthy"
                models_data = resp.json()
                if models_data.get("data"):
                    reasoning_model = models_data["data"][0]["id"]
    except Exception:
        reasoning_status = "unreachable"

    overall = "healthy" if vllm_status == "healthy" and db_status == "healthy" else "degraded"

    return {
        "status": overall,
        "version": "1.6.0",
        "components": {
            "vllm": vllm_status,
            "model": vllm_model,
            "database": db_status,
            "council": "enabled" if is_module_enabled("council") else "disabled",
            "memory": "enabled" if is_module_enabled("memory") else "disabled",
            "vlm": vlm_status,
            "vlm_model": vlm_model,
            "vlm_node": "bluefin",
            "reasoning": reasoning_status,
            "reasoning_model": reasoning_model,
            "reasoning_node": "bmasass"
        },
        "latency_ms": int((time.time() - start) * 1000),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
=======
@app.get("/health")
async def health_check():
    """Health check endpoint — concurrent backend checks, <3s total."""
    import asyncio
    start = time.time()

    async def check_vllm():
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{VLLM_BACKEND}/v1/models", timeout=2.0)
                if resp.status_code == 200:
                    models = resp.json()
                    model_id = models["data"][0]["id"] if models.get("data") else None
                    return "healthy", model_id
        except Exception as e:
            return f"error: {str(e)[:50]}", None
        return "unhealthy", None

    async def check_db():
        try:
            with get_db() as conn:
                cur = conn.cursor()
                cur.execute("SELECT 1")
                return "healthy"
        except Exception as e:
            return f"error: {str(e)[:50]}"

    async def check_vlm():
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{VLM_BACKEND}/v1/vlm/health", timeout=2.0)
                if resp.status_code == 200:
                    vlm_data = resp.json()
                    status = "healthy" if vlm_data.get("cuda_available") else "degraded"
                    return status, vlm_data.get("model")
        except Exception:
            return "unreachable", None
        return "unhealthy", None

    async def check_reasoning():
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{REASONING_BACKEND}/v1/models", timeout=2.0)
                if resp.status_code == 200:
                    models_data = resp.json()
                    model_id = models_data["data"][0]["id"] if models_data.get("data") else None
                    return "healthy", model_id
        except Exception:
            return "unreachable", None
        return "unhealthy", None

    (vllm_status, vllm_model), db_status, (vlm_status, vlm_model), (reasoning_status, reasoning_model) = await asyncio.gather(
        check_vllm(), check_db(), check_vlm(), check_reasoning()
    )

    overall = "healthy" if vllm_status == "healthy" and db_status == "healthy" else "degraded"

    return {
        "status": overall,
        "version": "1.6.0",
        "components": {
            "vllm": vllm_status,
            "model": vllm_model,
            "database": db_status,
            "council": "enabled" if is_module_enabled("council") else "disabled",
            "memory": "enabled" if is_module_enabled("memory") else "disabled",
            "vlm": vlm_status,
            "vlm_model": vlm_model,
            "vlm_node": "bluefin",
            "reasoning": reasoning_status,
            "reasoning_model": reasoning_model,
            "reasoning_node": "bmasass"
        },
        "latency_ms": int((time.time() - start) * 1000),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
>>>>>>> REPLACE

## Phase 2: Debounce Logic in Health Monitor (health_monitor.py)

Add consecutive-failure tracking. Only alert after 3 consecutive failures for the same service.

File: `/ganuda/services/health_monitor.py`

<<<<<<< SEARCH
CHECK_INTERVAL = 60  # seconds
QUEUE_DEPTH_THRESHOLD = 10


def check_service(name: str, url: str, latency_threshold_ms: int) -> bool:
    """Check if a service is healthy."""
    try:
        start = time.time()
        response = requests.get(url, timeout=10)
        latency_ms = int((time.time() - start) * 1000)

        if response.status_code != 200:
            alert_service_down(name, f"HTTP {response.status_code}")
            return False

        if latency_ms > latency_threshold_ms:
            alert_high_latency(name, latency_ms, latency_threshold_ms)

        logging.debug(f"{name}: OK ({latency_ms}ms)")
        return True

    except requests.exceptions.Timeout:
        alert_service_down(name, "Request timeout")
        return False
    except requests.exceptions.ConnectionError:
        alert_service_down(name, "Connection refused")
        return False
    except Exception as e:
        alert_service_down(name, str(e))
        return False
=======
CHECK_INTERVAL = 60  # seconds
QUEUE_DEPTH_THRESHOLD = 10
CONSECUTIVE_FAILURES_THRESHOLD = 3  # alert only after N consecutive failures

# Track consecutive failures per service
_failure_counts = {}


def check_service(name: str, url: str, latency_threshold_ms: int) -> bool:
    """Check if a service is healthy. Debounce: alerts only after 3 consecutive failures."""
    try:
        start = time.time()
        response = requests.get(url, timeout=10)
        latency_ms = int((time.time() - start) * 1000)

        if response.status_code != 200:
            _failure_counts[name] = _failure_counts.get(name, 0) + 1
            if _failure_counts[name] >= CONSECUTIVE_FAILURES_THRESHOLD:
                alert_service_down(name, f"HTTP {response.status_code} ({_failure_counts[name]} consecutive)")
            else:
                logging.warning(f"{name}: HTTP {response.status_code} (failure {_failure_counts[name]}/{CONSECUTIVE_FAILURES_THRESHOLD}, suppressing alert)")
            return False

        # Success — reset failure counter
        if _failure_counts.get(name, 0) > 0:
            logging.info(f"{name}: recovered after {_failure_counts[name]} failure(s)")
        _failure_counts[name] = 0

        if latency_ms > latency_threshold_ms:
            alert_high_latency(name, latency_ms, latency_threshold_ms)

        logging.debug(f"{name}: OK ({latency_ms}ms)")
        return True

    except requests.exceptions.Timeout:
        _failure_counts[name] = _failure_counts.get(name, 0) + 1
        if _failure_counts[name] >= CONSECUTIVE_FAILURES_THRESHOLD:
            alert_service_down(name, f"Request timeout ({_failure_counts[name]} consecutive)")
        else:
            logging.warning(f"{name}: timeout (failure {_failure_counts[name]}/{CONSECUTIVE_FAILURES_THRESHOLD}, suppressing alert)")
        return False
    except requests.exceptions.ConnectionError:
        _failure_counts[name] = _failure_counts.get(name, 0) + 1
        if _failure_counts[name] >= CONSECUTIVE_FAILURES_THRESHOLD:
            alert_service_down(name, f"Connection refused ({_failure_counts[name]} consecutive)")
        else:
            logging.warning(f"{name}: connection refused (failure {_failure_counts[name]}/{CONSECUTIVE_FAILURES_THRESHOLD}, suppressing alert)")
        return False
    except Exception as e:
        _failure_counts[name] = _failure_counts.get(name, 0) + 1
        if _failure_counts[name] >= CONSECUTIVE_FAILURES_THRESHOLD:
            alert_service_down(name, f"{str(e)} ({_failure_counts[name]} consecutive)")
        else:
            logging.warning(f"{name}: {str(e)} (failure {_failure_counts[name]}/{CONSECUTIVE_FAILURES_THRESHOLD}, suppressing alert)")
        return False
>>>>>>> REPLACE

## Verification

1. Gateway health endpoint responds in <100ms: `curl -w '%{time_total}' http://localhost:8080/health`
2. Health monitor logs show "suppressing alert" for first 2 failures, then alerts on 3rd
3. No false gateway DOWN thermals in 24 hours
4. Gateway still reports all 4 backend statuses correctly

## Notes

- Do NOT restart llm-gateway.service yet — TPM will restart after verifying the change
- Do NOT restart health monitor yet — TPM will handle service restart
- The `import asyncio` is inside the function to avoid any module-level side effects
