# Jr Instruction: RL2F Phase 0 — Self-Refine Loop on Gateway

**Task ID:** SELF-REFINE-LOOP-GATEWAY-PHASE0-v2
**Kanban:** #1879 (SFP 90)
**Council Vote:** #a7f2c91e3b8d4017 (CONDITIONAL GO, 0.877 confidence)
**Assigned Jr:** Software Engineer Jr.
**Priority:** 2
**use_rlm:** false

## Context

Add a Self-Refine loop to the council gateway for RL2F Phase 0. Generate → critique → refine cycle on consensus, with reflexion traces in thermal memory. Sacred patterns excluded.

## Changes

### Step 1: Add Self-Refine functions before the council vote endpoint

File: `/ganuda/services/llm_gateway/gateway.py`

```python
<<<<<<< SEARCH
@app.post("/v1/council/vote")
=======
# ─── Self-Refine Loop (RL2F Phase 0) ────────────────────────
SELF_REFINE_MAX_ROUNDS = int(os.environ.get("SELF_REFINE_MAX_ROUNDS", "3"))

CRITIC_SYSTEM_PROMPT = """You are a critical reviewer for the Cherokee AI Federation council.
Your job is to evaluate a draft council response for:
1. ACCURACY: Are factual claims correct? Are there unsupported assertions?
2. COMPLETENESS: Does it address all aspects of the question?
3. CLARITY: Is the reasoning clear and well-structured?
4. SHOULD_ASK: Should the council ask a clarifying question instead of answering directly?

If the response is satisfactory on all dimensions, respond with exactly: APPROVED

If not, provide specific critique in this format:
ISSUE: [specific problem]
SUGGESTION: [how to fix it]
SHOULD_ASK: [YES/NO — should we ask a clarifying question instead?]
QUESTION: [if SHOULD_ASK=YES, the clarifying question to ask]"""

REFINE_SYSTEM_PROMPT = """You are refining a council response based on critique.
Preserve the original structure and voice. Fix only what the critique identifies.
Do not add unnecessary caveats or hedging. Be direct and confident."""


def self_refine_loop(question: str, draft_response: str, sacred_flagged: bool = False) -> dict:
    """Self-Refine loop: critique and refine a draft response."""
    if sacred_flagged or SELF_REFINE_MAX_ROUNDS == 0:
        return {
            "final_response": draft_response,
            "rounds": 0,
            "critiques": [],
            "refinement_trace": "SKIPPED",
            "should_ask": False,
            "clarifying_question": None
        }

    current_response = draft_response
    critiques = []
    trace_parts = [f"ORIGINAL:\n{draft_response}"]

    for round_num in range(SELF_REFINE_MAX_ROUNDS):
        critique_prompt = f"""Question asked: {question}

Draft response to evaluate:
{current_response}

Evaluate this response. If satisfactory, respond with APPROVED. Otherwise provide specific critique."""

        critique = query_vllm_sync(
            CRITIC_SYSTEM_PROMPT,
            critique_prompt,
            max_tokens=300,
            timeout=30
        )

        if not critique or critique.startswith("[ERROR"):
            break

        trace_parts.append(f"CRITIQUE {round_num + 1}:\n{critique}")

        if "APPROVED" in critique.upper() and len(critique.strip()) < 50:
            break

        critiques.append(critique)

        should_ask = "SHOULD_ASK: YES" in critique.upper()
        clarifying_q = None
        if should_ask:
            for line in critique.split("\n"):
                if line.strip().upper().startswith("QUESTION:"):
                    clarifying_q = line.split(":", 1)[1].strip()
                    break
            if clarifying_q:
                trace_parts.append(f"CLARIFYING QUESTION SUGGESTED:\n{clarifying_q}")
                return {
                    "final_response": draft_response,
                    "rounds": round_num + 1,
                    "critiques": critiques,
                    "refinement_trace": "\n---\n".join(trace_parts),
                    "should_ask": True,
                    "clarifying_question": clarifying_q
                }

        refine_prompt = f"""Original question: {question}

Current response:
{current_response}

Critique received:
{critique}

Please refine the response to address the critique. Keep the same format and voice."""

        refined = query_vllm_sync(
            REFINE_SYSTEM_PROMPT,
            refine_prompt,
            max_tokens=500,
            timeout=45
        )

        if not refined or refined.startswith("[ERROR"):
            break

        current_response = refined
        trace_parts.append(f"REFINED {round_num + 1}:\n{refined}")

    return {
        "final_response": current_response,
        "rounds": len(critiques),
        "critiques": critiques,
        "refinement_trace": "\n---\n".join(trace_parts),
        "should_ask": False,
        "clarifying_question": None
    }


def store_reflexion_trace(audit_hash: str, question: str, refine_result: dict):
    """Store the Self-Refine trace in thermal memory."""
    if refine_result["rounds"] == 0:
        return
    content = f"REFLEXION TRACE (Self-Refine Phase 0)\nQuestion: {question[:200]}\nRounds: {refine_result['rounds']}\n{refine_result['refinement_trace'][:800]}"
    memory_hash = hashlib.sha256(f"reflexion-{audit_hash}-{time.time()}".encode()).hexdigest()
    metadata = {"type": "reflexion_trace", "memory_type": "reflexion_trace", "audit_hash": audit_hash, "rounds": refine_result["rounds"], "should_ask": refine_result["should_ask"], "timestamp": datetime.utcnow().isoformat()}
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO thermal_memory_archive (memory_hash, original_content, temperature_score, metadata) VALUES (%s, %s, %s, %s)", (memory_hash, content[:2000], 65.0, json.dumps(metadata)))
            conn.commit()
    except Exception as e:
        print(f"[REFLEXION] Failed to store trace: {e}")


@app.post("/v1/council/vote")
>>>>>>> REPLACE
```

### Step 2: Wire Self-Refine into council vote after metacognition completes

File: `/ganuda/services/llm_gateway/gateway.py`

```python
<<<<<<< SEARCH
    # Complete metacognitive analysis
    meta_result = meta_council.complete_deliberation(consensus)

    # Use calibrated confidence from metacognition
=======
    # Complete metacognitive analysis
    meta_result = meta_council.complete_deliberation(consensus)

    # ─── Self-Refine Loop (RL2F Phase 0) ─────────────
    refine_result = self_refine_loop(
        question=request.question,
        draft_response=consensus,
        sacred_flagged=False
    )
    if refine_result["rounds"] > 0:
        consensus = refine_result["final_response"]
        meta_result["refinement_rounds"] = refine_result["rounds"]
        meta_result["refinement_applied"] = True

    # Use calibrated confidence from metacognition
>>>>>>> REPLACE
```

### Step 3: Store reflexion trace after TPM notification

File: `/ganuda/services/llm_gateway/gateway.py`

```python
<<<<<<< SEARCH
    # Notify TPM
    create_tpm_notification(audit_hash, request.question, recommendation, confidence, all_concerns, vote_expires)

    response_time_ms = int((time.time() - start) * 1000)
=======
    # Notify TPM
    create_tpm_notification(audit_hash, request.question, recommendation, confidence, all_concerns, vote_expires)

    # Store reflexion trace in thermal memory (RL2F Phase 0)
    store_reflexion_trace(audit_hash, request.question, refine_result)

    response_time_ms = int((time.time() - start) * 1000)
>>>>>>> REPLACE
```

### Step 4: Add refinement metadata to response

File: `/ganuda/services/llm_gateway/gateway.py`

```python
<<<<<<< SEARCH
            "reasoning_steps": meta_result.get('reasoning_steps', 0)
        }
    }
=======
            "reasoning_steps": meta_result.get('reasoning_steps', 0)
        },
        "refinement": {
            "rounds": refine_result.get("rounds", 0),
            "applied": refine_result.get("rounds", 0) > 0,
            "should_ask": refine_result.get("should_ask", False),
            "clarifying_question": refine_result.get("clarifying_question")
        }
    }
>>>>>>> REPLACE
```

## Verification

After all steps, clear pycache and restart:

```text
rm -rf /ganuda/services/llm_gateway/__pycache__/
sudo systemctl restart llm-gateway
```

## Rollback

Set env var `SELF_REFINE_MAX_ROUNDS=0` to disable the loop without code changes.
