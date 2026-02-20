# Jr Instruction: Gateway Long Man Routing + Two Wolves Audit Trail

**Task ID:** GATEWAY-LONGMAN-TWO-WOLVES-001
**Priority:** P0
**Assigned To:** Software Engineer Jr.
**Council Vote:** #8486 (Long Man routing) + #8486 Phase 2 (Two Wolves audit)
**Date:** February 8, 2026
**KB Reference:** KB-TWO-WOLVES-DATA-SOVEREIGNTY-COUNCIL-ROUTING-FEB08-2026.md

## Background

The `/v1/council/vote` endpoint in gateway.py has its own specialist query pipeline that does NOT call `specialist_council.py`'s `vote()` method. The Long Man routing and Two Wolves audit trail deployed to specialist_council.py are NOT active for production API calls through the gateway.

This instruction brings gateway.py up to parity:
- **Long Man routing**: Raven + Turtle → DeepSeek-R1 on bmasass:8800 for reasoning depth. Others → Qwen on redfin for speed. High-stakes → all deep. Health check with fallback.
- **Two Wolves audit**: routing_manifest in council_votes.metacognition + per-specialist api_audit_log entries with backend IP.

## Edit 1: Add SPECIALIST_ROUTING map, model constants, and health check function

File: `/ganuda/services/llm_gateway/gateway.py`

<<<<<<< SEARCH
REASONING_MODELS = {"deepseek-r1", "deepseek-r1-32b", "reasoning"}
DB_CONFIG = {
=======
REASONING_MODELS = {"deepseek-r1", "deepseek-r1-32b", "reasoning"}

# Long Man routing: per-specialist backend map (Council Vote #8486)
# Raven (strategy) and Turtle (7-gen wisdom) route to DeepSeek-R1 for reasoning depth
DEEPSEEK_MODEL = "mlx-community/DeepSeek-R1-Distill-Qwen-32B-4bit"
QWEN_MODEL = "/ganuda/models/qwen2.5-coder-32b-awq"
SPECIALIST_ROUTING = {
    "raven": {"url": REASONING_BACKEND, "model": DEEPSEEK_MODEL, "timeout": 120},
    "turtle": {"url": REASONING_BACKEND, "model": DEEPSEEK_MODEL, "timeout": 120},
    # All others default to Qwen on redfin (fast path)
}


def check_council_backend_health(url):
    """Check if a council backend is reachable before routing"""
    try:
        health_url = url + "/health"
        r = requests.get(health_url, timeout=5)
        return r.status_code == 200
    except Exception:
        return False


DB_CONFIG = {
>>>>>>> REPLACE

## Edit 2: Modify query_vllm_sync to accept optional backend URL, model, and timeout

File: `/ganuda/services/llm_gateway/gateway.py`

<<<<<<< SEARCH
def query_vllm_sync(system_prompt: str, user_message: str, max_tokens: int = 300) -> str:
    """Synchronous vLLM query for thread pool"""
    try:
        response = requests.post(
            f"{VLLM_BACKEND}/v1/chat/completions",
            json={
                "model": "/ganuda/models/qwen2.5-coder-32b-awq",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "max_tokens": max_tokens,
                "temperature": 0.7
            },
            timeout=60
        )
=======
def query_vllm_sync(system_prompt: str, user_message: str, max_tokens: int = 300,
                     backend_url: str = None, model: str = None, timeout: int = 60) -> str:
    """Synchronous vLLM query for thread pool — Long Man routing aware (Council #8486)"""
    target_url = backend_url or f"{VLLM_BACKEND}/v1/chat/completions"
    target_model = model or QWEN_MODEL
    try:
        response = requests.post(
            target_url,
            json={
                "model": target_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "max_tokens": max_tokens,
                "temperature": 0.7
            },
            timeout=timeout
        )
>>>>>>> REPLACE

## Edit 3: Add Long Man routing + timing to query_specialist inner function and ThreadPoolExecutor

File: `/ganuda/services/llm_gateway/gateway.py`

<<<<<<< SEARCH
    responses = {}
    all_concerns = []

    def query_specialist(name: str) -> tuple:
        spec = SPECIALISTS[name]

        # Get specialist's memory context + temporal context
        memory_context = get_specialist_context(name)
        enhanced_prompt = spec["system_prompt"] + memory_context + temporal_context

        # Inject YAML-based constraints
        triggered_concerns_list = []
        if HAS_CONSTRAINTS:
            constraint_prompt, triggered_concerns_list = build_constraint_prompt(name, request.question)
            if constraint_prompt:
                enhanced_prompt = enhanced_prompt + constraint_prompt
                if triggered_concerns_list:
                    print(f"[CONSTRAINT] {spec['name']}: Triggered {len(triggered_concerns_list)} concerns - {triggered_concerns_list}")

        result = query_vllm_sync(enhanced_prompt, request.question, request.max_tokens)
        concerns = extract_concerns(result, spec["name"])

        # Update specialist memory
        update_specialist_memory(name, request.question, concerns)

        return name, result, concerns

    with ThreadPoolExecutor(max_workers=7) as executor:
        futures = {executor.submit(query_specialist, name): name for name in SPECIALISTS.keys()}
        for future in as_completed(futures):
            try:
                name, result, concerns = future.result()
                responses[name] = result
                all_concerns.extend(concerns)

                # Record in metacognition tracer
                confidence = 0.7 - (len(concerns) * 0.1)
                meta_council.record_specialist_response(name, result, confidence)

            except Exception as e:
                name = futures[future]
                responses[name] = f"[ERROR: {str(e)}]"
=======
    responses = {}
    all_concerns = []
    specialist_timings = {}  # Two Wolves: per-specialist response times

    # Long Man routing: check DeepSeek health once before dispatching (Council Vote #8486)
    deepseek_healthy = check_council_backend_health(REASONING_BACKEND)
    high_stakes = any(kw in request.question.lower() for kw in [
        "sovereignty", "security", "constitutional", "sacred",
        "override", "rollback", "delete", "destroy"
    ])
    routing_map = {}  # Two Wolves: track which backend each specialist used

    def query_specialist(name: str) -> tuple:
        spec = SPECIALISTS[name]
        spec_start = time.time()

        # Long Man routing: select backend per specialist
        routing = SPECIALIST_ROUTING.get(name)
        if high_stakes and deepseek_healthy:
            # All specialists go deep on high-stakes questions
            backend_url = f"{REASONING_BACKEND}/v1/chat/completions"
            model = DEEPSEEK_MODEL
            timeout = 120
            max_tokens = max(request.max_tokens, 500)
            routing_map[name] = "deepseek"
        elif routing and deepseek_healthy:
            backend_url = f"{routing['url']}/v1/chat/completions"
            model = routing["model"]
            timeout = routing["timeout"]
            max_tokens = max(request.max_tokens, 500)
            routing_map[name] = "deepseek"
        else:
            backend_url = None  # default to VLLM_BACKEND (Qwen on redfin)
            model = None
            timeout = 60
            max_tokens = request.max_tokens
            routing_map[name] = "qwen"

        # Get specialist's memory context + temporal context
        memory_context = get_specialist_context(name)
        enhanced_prompt = spec["system_prompt"] + memory_context + temporal_context

        # Inject YAML-based constraints
        triggered_concerns_list = []
        if HAS_CONSTRAINTS:
            constraint_prompt, triggered_concerns_list = build_constraint_prompt(name, request.question)
            if constraint_prompt:
                enhanced_prompt = enhanced_prompt + constraint_prompt
                if triggered_concerns_list:
                    print(f"[CONSTRAINT] {spec['name']}: Triggered {len(triggered_concerns_list)} concerns - {triggered_concerns_list}")

        print(f"[LONG MAN] {name} -> {'DeepSeek@bmasass' if routing_map.get(name) == 'deepseek' else 'Qwen@redfin'}")
        result = query_vllm_sync(enhanced_prompt, request.question, max_tokens,
                                  backend_url=backend_url, model=model, timeout=timeout)
        elapsed_ms = int((time.time() - spec_start) * 1000)
        concerns = extract_concerns(result, spec["name"])

        # Update specialist memory
        update_specialist_memory(name, request.question, concerns)

        return name, result, concerns, elapsed_ms

    with ThreadPoolExecutor(max_workers=7) as executor:
        futures = {executor.submit(query_specialist, name): name for name in SPECIALISTS.keys()}
        for future in as_completed(futures):
            try:
                name, result, concerns, elapsed_ms = future.result()
                responses[name] = result
                all_concerns.extend(concerns)
                specialist_timings[name] = elapsed_ms

                # Record in metacognition tracer
                confidence = 0.7 - (len(concerns) * 0.1)
                meta_council.record_specialist_response(name, result, confidence)

            except Exception as e:
                name = futures[future]
                responses[name] = f"[ERROR: {str(e)}]"
                specialist_timings[name] = 0
>>>>>>> REPLACE

## Edit 4: Add routing_manifest to metacognition + per-specialist audit log entries

File: `/ganuda/services/llm_gateway/gateway.py`

<<<<<<< SEARCH
    # Save vote with metacognition data
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO council_votes
                (audit_hash, question, recommendation, confidence, concern_count, responses, concerns, consensus, tpm_vote, vote_window_expires, metacognition)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'pending', %s, %s)
            """, (audit_hash, request.question[:500], recommendation, confidence, len(all_concerns),
                  json.dumps(responses), json.dumps(all_concerns), consensus, vote_expires,
                  json.dumps(meta_result)))
            conn.commit()
    except Exception as e:
        print(f"[VOTE SAVE ERROR] {e}")

    # Notify TPM
=======
    # Two Wolves audit trail: build routing manifest (Council Vote #8486 Phase 2)
    routing_manifest = {
        "vote_type": "high_stakes" if high_stakes else "normal",
        "deepseek_healthy": deepseek_healthy,
        "backends_used": list(set(routing_map.values())),
        "specialists_on_redfin": [s for s, b in routing_map.items() if b == "qwen"],
        "specialists_on_bmasass": [s for s, b in routing_map.items() if b == "deepseek"],
        "data_sovereignty": {
            "question_left_redfin": any(b == "deepseek" for b in routing_map.values()),
            "destination_nodes": list(set(
                "192.168.132.21" if b == "deepseek" else "127.0.0.1" for b in routing_map.values()
            )),
            "timestamp": datetime.utcnow().isoformat()
        }
    }

    # Merge routing manifest into metacognition
    meta_result["routing_manifest"] = routing_manifest

    # Save vote with metacognition + routing manifest
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO council_votes
                (audit_hash, question, recommendation, confidence, concern_count, responses, concerns, consensus, tpm_vote, vote_window_expires, metacognition)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'pending', %s, %s)
            """, (audit_hash, request.question[:500], recommendation, confidence, len(all_concerns),
                  json.dumps(responses), json.dumps(all_concerns), consensus, vote_expires,
                  json.dumps(meta_result)))
            conn.commit()
    except Exception as e:
        print(f"[VOTE SAVE ERROR] {e}")

    # Two Wolves: per-specialist audit log entries (Security Wolf)
    try:
        with get_db() as conn:
            cur = conn.cursor()
            for spec_name in SPECIALISTS.keys():
                backend_label = routing_map.get(spec_name, "qwen")
                backend_ip = "192.168.132.21" if backend_label == "deepseek" else "127.0.0.1"
                status = 200 if not responses.get(spec_name, "").startswith("[ERROR") else 500
                cur.execute("""
                    INSERT INTO api_audit_log
                        (key_id, endpoint, method, status_code, response_time_ms, tokens_used, client_ip)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    "council-internal",
                    f"/council/specialist/{spec_name}",
                    "POST",
                    status,
                    specialist_timings.get(spec_name, 0),
                    0,
                    backend_ip
                ))
            conn.commit()
    except Exception as e:
        print(f"[TWO WOLVES] Audit log error: {e}")

    # Notify TPM
>>>>>>> REPLACE

## Do NOT

- Do not modify specialist_council.py — this is gateway.py only
- Do not hardcode any database passwords — gateway uses get_db() context manager
- Do not modify the consensus synthesis call (line ~1024) — Peace Chief always synthesizes on Qwen
- Do not change the `/v1/chat/completions` endpoint routing — only `/v1/council/vote`
- Do not change the existing `VLLM_BACKEND` or `REASONING_BACKEND` variable values
- Do not log the full question text in api_audit_log (it is already in council_votes.question)
- Do not log passwords, API keys, or PII in routing metadata

## Success Criteria

1. Normal council vote: `routing_manifest.specialists_on_bmasass` shows `["raven", "turtle"]`
2. Normal council vote: `routing_manifest.specialists_on_redfin` shows the other 5 specialists
3. Normal council vote: `routing_manifest.data_sovereignty.question_left_redfin` is `true`
4. High-stakes vote (question contains "sovereignty", "security", etc.): all 7 specialists on bmasass
5. `api_audit_log` contains 7 entries per vote with `key_id = 'council-internal'`:
   - `endpoint` = `/council/specialist/{name}`
   - `client_ip` = `127.0.0.1` (Qwen) or `192.168.132.21` (DeepSeek)
   - `response_time_ms` populated from per-specialist timing
6. When DeepSeek is down: `routing_manifest.deepseek_healthy` = `false`, all specialists on redfin
7. Consensus synthesis still routes through Qwen (Peace Chief prompt, not affected)
8. Existing callers of `query_vllm_sync()` without backend params still work (default behavior unchanged)
9. Python syntax valid after all edits
10. `[LONG MAN]` log lines visible in gateway stdout showing per-specialist routing
