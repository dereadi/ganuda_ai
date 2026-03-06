# [RECURSIVE] RL2F Phase 0: Self-Refine Loop on Gateway - Step 1

**Parent Task**: #824
**Auto-decomposed**: 2026-02-22T09:25:04.742836
**Original Step Title**: Add Self-Refine function to gateway

---

### Step 1: Add Self-Refine function to gateway

File: `/ganuda/services/llm_gateway/gateway.py`

Add the following function AFTER the existing `query_vllm_sync` import/definition area (after the SPECIALISTS dict, before the endpoint definitions):

```python
<<<<<<< SEARCH
# ─── Endpoints ───────────────────────────────────────────────
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
    """Self-Refine loop: critique and refine a draft response.

    Returns dict with:
        - final_response: str (refined or original if approved/sacred)
        - rounds: int (number of refinement rounds, 0 if skipped)
        - critiques: list[str] (all critiques received)
        - refinement_trace: str (full trace for thermal memory)
        - should_ask: bool (whether critic recommended asking clarifying question)
        - clarifying_question: str or None
    """
    if sacred_flagged:
        return {
            "final_response": draft_response,
            "rounds": 0,
            "critiques": [],
            "refinement_trace": "SKIPPED: Sacred pattern detected",
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

    refinement_trace = "\n---\n".join(trace_parts)

    return {
        "final_response": current_response,
        "rounds": len(critiques),
        "critiques": critiques,
        "refinement_trace": refinement_trace,
        "should_ask": False,
        "clarifying_question": None
    }


def store_reflexion_trace(audit_hash: str, question: str, refine_result: dict):
    """Store the Self-Refine trace in thermal memory."""
    if refine_result["rounds"] == 0:
        return

    content = f"""REFLEXION TRACE (Self-Refine Phase 0)
Question: {question[:200]}
Rounds: {refine_result['rounds']}
{'CLARIFYING QUESTION SUGGESTED: ' + refine_result['clarifying_question'] if refine_result['should_ask'] else ''}
{refine_result['refinement_trace'][:800]}"""

    memory_hash = hashlib.sha256(
        f"reflexion-{audit_hash}-{time.time()}".encode()
    ).hexdigest()

    metadata = {
        "type": "reflexion_trace",
        "memory_type": "reflexion_trace",
        "audit_hash": audit_hash,
        "rounds": refine_result["rounds"],
        "should_ask": refine_result["should_ask"],
        "timestamp": datetime.utcnow().isoformat()
    }

    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO thermal_memory_archive
                (memory_hash, original_content, temperature_score, metadata)
                VALUES (%s, %s, %s, %s)
            """, (
                memory_hash,
                content[:2000],
                65.0,
                json.dumps(metadata)
            ))
            conn.commit()
    except Exception as e:
        logger.warning(f"Failed to store reflexion trace: {e}")


# ─── Endpoints ───────────────────────────────────────────────
>>>>>>> REPLACE
```
