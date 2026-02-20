# Jr Instruction: Council Hybrid Backend Routing — Long Man Pattern (v2)

**Task ID:** COUNCIL-HYBRID-ROUTE-001
**Priority:** P1
**Assigned To:** Software Engineer Jr.
**Council Vote:** #8486 (approved, hybrid of options b+c)
**Date:** February 8, 2026
**Note:** v2 — reformatted for executor SEARCH/REPLACE compatibility

## Objective

Apply 4 surgical edits to `/ganuda/lib/specialist_council.py` to enable per-specialist backend routing (Long Man pattern). Raven and Turtle route to DeepSeek-R1 on bmasass for depth. Others use Qwen on redfin for speed. High-stakes votes send all specialists deep.

## Edit 1: Add backend configuration constants

File: `/ganuda/lib/specialist_council.py`

<<<<<<< SEARCH
DB_CONFIG = get_db_config()


def query_vllm_sync(system_prompt: str, user_message: str, max_tokens: int = 300) -> str:
=======
DB_CONFIG = get_db_config()

# Backend configuration — Long Man pattern (Council Vote #8486)
QWEN_BACKEND = {
    "url": "http://localhost:8000/v1/chat/completions",
    "model": "/ganuda/models/qwen2.5-coder-32b-awq",
    "timeout": 60,
    "description": "Fast path — Qwen2.5-Coder-32B on redfin RTX 6000"
}

DEEPSEEK_BACKEND = {
    "url": "http://192.168.132.21:8800/v1/chat/completions",
    "model": "mlx-community/DeepSeek-R1-Distill-Qwen-32B-4bit",
    "timeout": 120,
    "description": "Deep path — DeepSeek-R1-32B on bmasass M4 Max"
}

SPECIALIST_BACKENDS = {
    "raven": DEEPSEEK_BACKEND,
    "turtle": DEEPSEEK_BACKEND,
    "crawdad": QWEN_BACKEND,
    "gecko": QWEN_BACKEND,
    "eagle_eye": QWEN_BACKEND,
    "spider": QWEN_BACKEND,
    "peace_chief": QWEN_BACKEND,
}


def check_backend_health(backend):
    """Health check a backend before voting"""
    try:
        health_url = backend["url"].replace("/v1/chat/completions", "/health")
        r = requests.get(health_url, timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def query_vllm_sync(system_prompt: str, user_message: str, max_tokens: int = 300) -> str:
>>>>>>> REPLACE

## Edit 2: Modify _query_specialist to accept backend parameter

File: `/ganuda/lib/specialist_council.py`

<<<<<<< SEARCH
    def _query_specialist(self, specialist_id: str, question: str) -> SpecialistResponse:
        """Query a single specialist via vLLM"""
        spec = SPECIALISTS[specialist_id]
        start_time = datetime.now()

        try:
            response = requests.post(
                VLLM_URL,
                json={
                    "model": "/ganuda/models/qwen2.5-coder-32b-awq",
                    "messages": [
                        {"role": "system", "content": spec["system_prompt"]},
                        {"role": "user", "content": question}
                    ],
                    "max_tokens": self.max_tokens,
                    "temperature": 0.7
                },
                timeout=60
            )
=======
    def _query_specialist(self, specialist_id: str, question: str, backend: dict = None) -> SpecialistResponse:
        """Query a single specialist via vLLM — Long Man routing (Council Vote #8486)"""
        spec = SPECIALISTS[specialist_id]
        b = backend or SPECIALIST_BACKENDS.get(specialist_id, QWEN_BACKEND)
        start_time = datetime.now()
        max_tokens = self.max_tokens
        if b == DEEPSEEK_BACKEND:
            max_tokens = max(max_tokens, 500)
        print(f"[COUNCIL] {specialist_id} -> {b['description']}")

        try:
            response = requests.post(
                b["url"],
                json={
                    "model": b["model"],
                    "messages": [
                        {"role": "system", "content": spec["system_prompt"]},
                        {"role": "user", "content": question}
                    ],
                    "max_tokens": max_tokens,
                    "temperature": 0.7
                },
                timeout=b["timeout"]
            )
>>>>>>> REPLACE

## Edit 3: Modify vote() for per-specialist routing with health check

File: `/ganuda/lib/specialist_council.py`

<<<<<<< SEARCH
    def vote(self, question: str, include_responses: bool = False) -> CouncilVote:
        """Query all 7 specialists in parallel and synthesize consensus"""
        responses = []

        # Parallel query all specialists
        with ThreadPoolExecutor(max_workers=7) as executor:
            futures = {
                executor.submit(self._query_specialist, sid, question): sid
                for sid in SPECIALISTS.keys()
            }
=======
    def vote(self, question: str, include_responses: bool = False, high_stakes: bool = False) -> CouncilVote:
        """Query all 7 specialists in parallel — Long Man routing (Council Vote #8486)"""
        responses = []

        # Health check deep backend before routing
        deepseek_healthy = check_backend_health(DEEPSEEK_BACKEND)
        if not deepseek_healthy:
            print("[COUNCIL] [TWO WOLVES WARNING] Deep backend unreachable — all specialists falling back to fast path")

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
>>>>>>> REPLACE

## Edit 4: Update INFRASTRUCTURE_CONTEXT

File: `/ganuda/lib/specialist_council.py`

<<<<<<< SEARCH
| tpm-macbook | local | Command Post | Claude Code CLI, TPM workstation |

SERVICES:
- vLLM: Nemotron-9B on 96GB Blackwell GPU (27 tok/sec)
- LLM Gateway v1.2: OpenAI-compatible API with Council voting
=======
| tpm-macbook | local | Command Post | Claude Code CLI, TPM workstation |
| bmasass | 192.168.132.21 | Mac Hybrid | MLX DeepSeek-R1-32B (8800) |

SERVICES:
- vLLM: Qwen2.5-Coder-32B-AWQ on 96GB Blackwell RTX PRO 6000 (~65 tok/sec)
- MLX: DeepSeek-R1-Distill-Qwen-32B-4bit on M4 Max 128GB (~23 tok/sec)
- LLM Gateway v1.6.0: OpenAI-compatible API with Council voting + Long Man routing
>>>>>>> REPLACE

## Do NOT

- Do not remove existing VLLM_URL / VLLM_MODEL constants (other code references them)
- Do not change the council vote API response format
- Do not modify gateway.py
- Do not hardcode any database passwords

## Success Criteria

1. Normal council votes complete with Raven+Turtle using DeepSeek-R1
2. High-stakes council votes route all specialists to DeepSeek-R1
3. Backend selection logged per specialist per vote
4. Fallback to Qwen when DeepSeek unreachable, with TWO WOLVES WARNING logged
5. No regression in vote response format
