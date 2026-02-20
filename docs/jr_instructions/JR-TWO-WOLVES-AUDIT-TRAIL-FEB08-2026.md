# Jr Instruction: Two Wolves Audit Trail for Council Routing

**Task ID:** TWO-WOLVES-AUDIT-001
**Priority:** P1
**Assigned To:** Software Engineer Jr.
**Council Vote:** #8486 Phase 2 (Two Wolves requirement)
**Date:** February 8, 2026
**KB Reference:** KB-TWO-WOLVES-DATA-SOVEREIGNTY-COUNCIL-ROUTING-FEB08-2026.md

## Objective

Add forensic audit trail to the council Long Man routing. Every council vote must record which backend each specialist used, whether data crossed the wire to bmasass, and log per-specialist entries to api_audit_log. The Security Wolf and Privacy Wolf both eat equally.

## Edit 1: Add routing_map to vote() to track per-specialist backend selection

File: `/ganuda/lib/specialist_council.py`

<<<<<<< SEARCH
        # Parallel query all specialists with per-specialist routing
        with ThreadPoolExecutor(max_workers=7) as executor:
            futures = {}
            for sid in SPECIALISTS.keys():
                if high_stakes and deepseek_healthy:
                    backend = DEEPSEEK_BACKEND
                elif deepseek_healthy:
                    backend = SPECIALIST_BACKENDS.get(sid, QWEN_BACKEND)
                else:
                    backend = QWEN_BACKEND
                futures[executor.submit(self._query_specialist, sid, question, backend)] = sid
=======
        # Parallel query all specialists with per-specialist routing
        routing_map = {}  # Two Wolves: track which backend each specialist used
        with ThreadPoolExecutor(max_workers=7) as executor:
            futures = {}
            for sid in SPECIALISTS.keys():
                if high_stakes and deepseek_healthy:
                    backend = DEEPSEEK_BACKEND
                elif deepseek_healthy:
                    backend = SPECIALIST_BACKENDS.get(sid, QWEN_BACKEND)
                else:
                    backend = QWEN_BACKEND
                routing_map[sid] = backend
                futures[executor.submit(self._query_specialist, sid, question, backend)] = sid
>>>>>>> REPLACE

## Edit 2: Add routing_manifest and per-specialist audit logging after vote creation

File: `/ganuda/lib/specialist_council.py`

<<<<<<< SEARCH
        # Log to database
        self._log_vote(vote)

        return vote
=======
        # Two Wolves audit trail (Council Vote #8486, Phase 2)
        routing_manifest = {
            "vote_type": "high_stakes" if high_stakes else "normal",
            "deepseek_healthy": deepseek_healthy,
            "backends_used": list(set(b["description"] for b in routing_map.values())),
            "specialists_on_redfin": [s for s, b in routing_map.items() if b == QWEN_BACKEND],
            "specialists_on_bmasass": [s for s, b in routing_map.items() if b == DEEPSEEK_BACKEND],
            "data_sovereignty": {
                "question_left_redfin": any(b != QWEN_BACKEND for b in routing_map.values()),
                "destination_nodes": list(set(
                    b["url"].split("//")[1].split(":")[0] for b in routing_map.values()
                )),
                "timestamp": datetime.now().isoformat()
            }
        }

        # Log per-specialist backend to api_audit_log (Security Wolf)
        try:
            audit_conn = psycopg2.connect(**DB_CONFIG)
            audit_cur = audit_conn.cursor()
            for resp in responses:
                b = routing_map.get(resp.specialist_id, QWEN_BACKEND)
                backend_ip = b["url"].split("//")[1].split(":")[0]
                if backend_ip == "localhost":
                    backend_ip = "127.0.0.1"
                audit_cur.execute("""
                    INSERT INTO api_audit_log
                        (key_id, endpoint, method, status_code, response_time_ms, tokens_used, client_ip)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    "council-internal",
                    f"/council/specialist/{resp.specialist_id}",
                    "POST",
                    200 if not resp.response.startswith("Error") else 500,
                    resp.response_time_ms,
                    0,
                    backend_ip
                ))
            audit_conn.commit()
            audit_conn.close()
        except Exception as e:
            print(f"[TWO WOLVES] Audit log error: {e}")

        # Log to database with routing manifest
        self._log_vote(vote, routing_manifest=routing_manifest)

        return vote
>>>>>>> REPLACE

## Edit 3: Modify _log_vote() to store routing_manifest in metacognition

File: `/ganuda/lib/specialist_council.py`

<<<<<<< SEARCH
    def _log_vote(self, vote: CouncilVote):
        """Log vote to thermal memory and council_votes table"""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()

            # Log to council_votes
            cur.execute("""
                INSERT INTO council_votes (audit_hash, question, recommendation, confidence, concerns, voted_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """, (vote.audit_hash, vote.question, vote.recommendation, vote.confidence, json.dumps(vote.concerns)))
=======
    def _log_vote(self, vote: CouncilVote, routing_manifest: dict = None):
        """Log vote to thermal memory and council_votes table — Two Wolves audit"""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()

            # Build metacognition with routing manifest (Two Wolves)
            metacognition = {}
            if routing_manifest:
                metacognition["routing_manifest"] = routing_manifest

            # Log to council_votes with metacognition
            cur.execute("""
                INSERT INTO council_votes (audit_hash, question, recommendation, confidence, concerns, metacognition, voted_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
            """, (vote.audit_hash, vote.question, vote.recommendation, vote.confidence, json.dumps(vote.concerns), json.dumps(metacognition) if metacognition else None))
>>>>>>> REPLACE

## Do NOT

- Do not modify gateway.py — this is specialist_council.py only
- Do not hardcode any database passwords
- Do not log the full question text in api_audit_log (it is already in council_votes.question)
- Do not log passwords, API keys, or PII in routing metadata
- Do not modify the vote_first() or vote_with_trails() methods — only vote()

## Success Criteria

1. Normal council vote stores `routing_manifest` in `council_votes.metacognition`
2. `routing_manifest.specialists_on_bmasass` shows `["raven", "turtle"]` for normal votes
3. `routing_manifest.data_sovereignty.question_left_redfin` is `true` for normal votes
4. High-stakes vote shows all 7 specialists on bmasass
5. `api_audit_log` contains 7 entries per vote (one per specialist) with:
   - `endpoint` = `/council/specialist/{name}`
   - `client_ip` = `127.0.0.1` (Qwen) or `192.168.132.21` (DeepSeek)
   - `response_time_ms` populated
6. When DeepSeek is down, `routing_manifest.deepseek_healthy` = `false` and all specialists show redfin
7. No credentials or PII in routing metadata
8. Python syntax valid after all edits
