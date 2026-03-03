"""
ATP Counter — Token Economics
Cherokee AI Federation — The Living Cell Architecture

Tracks token consumption across all LLM calls.
A cell that doesn't track its ATP budget dies.
A federation that doesn't track its token budget burns money it doesn't have.

Usage (standalone wrapper):
    from lib.duplo.atp_counter import count_tokens, get_daily_burn

    # Wrap any OpenAI-compatible API response
    count_tokens(
        response_data=api_response_json,
        model="qwen2.5-72b",
        caller_id="council.crawdad",
        call_type="council_vote",
        metadata={"vote_hash": "abc123"},
    )

    # Query the ledger
    burn = get_daily_burn()
    # {"today": {"total_tokens": 150000, "estimated_cost": 0.45, "call_count": 23}, ...}

Usage (decorator):
    @track_tokens(caller_id="gateway", call_type="inference")
    def call_llm(prompt):
        response = requests.post(VLLM_URL, json=payload)
        return response.json()
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from functools import wraps

logger = logging.getLogger("duplo.atp")

# Approximate cost per 1M tokens (USD) — update as pricing changes
COST_PER_1M_TOKENS = {
    "qwen": 0.0,      # self-hosted, electricity only
    "deepseek": 0.0,   # self-hosted
    "vlm": 0.0,        # self-hosted
    "claude": 15.0,    # Anthropic API (output tokens, Opus)
    "default": 0.0,
}


def _estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate USD cost based on model and token counts."""
    # For self-hosted models, cost is effectively 0 (electricity is fixed)
    # For API models, use published rates
    model_lower = model.lower()
    for key, rate in COST_PER_1M_TOKENS.items():
        if key in model_lower:
            return (input_tokens + output_tokens) * rate / 1_000_000
    return 0.0


def count_tokens(
    response_data: dict,
    model: str,
    caller_id: str,
    call_type: str = "inference",
    latency_ms: int = 0,
    metadata: Optional[dict] = None,
) -> Dict[str, int]:
    """
    Extract token counts from an OpenAI-compatible API response
    and log to the token_ledger.

    Returns dict with input_tokens, output_tokens, total_tokens.
    """
    usage = response_data.get("usage", {})
    input_tokens = usage.get("prompt_tokens", 0)
    output_tokens = usage.get("completion_tokens", 0)
    total_tokens = input_tokens + output_tokens
    estimated_cost = _estimate_cost(model, input_tokens, output_tokens)

    try:
        from lib.ganuda_db import get_connection
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO token_ledger
                (model, caller_id, call_type, input_tokens, output_tokens,
                 estimated_cost, latency_ms, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                model, caller_id, call_type,
                input_tokens, output_tokens, estimated_cost,
                latency_ms, json.dumps(metadata or {}),
            ))
            conn.commit()
        finally:
            conn.close()
    except Exception as e:
        logger.warning(f"Failed to log tokens: {e}")

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "estimated_cost": estimated_cost,
    }


def get_daily_burn(days: int = 7) -> Dict[str, dict]:
    """
    Get daily token burn rate for the last N days.
    Returns {date_str: {total_tokens, estimated_cost, call_count, by_model: {...}}}.
    """
    from lib.ganuda_db import get_connection
    import psycopg2.extras

    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT
                date_trunc('day', created_at)::date AS day,
                model,
                COUNT(*) AS call_count,
                SUM(input_tokens) AS input_tokens,
                SUM(output_tokens) AS output_tokens,
                SUM(input_tokens + output_tokens) AS total_tokens,
                SUM(estimated_cost) AS total_cost
            FROM token_ledger
            WHERE created_at >= NOW() - INTERVAL '%s days'
            GROUP BY date_trunc('day', created_at)::date, model
            ORDER BY day DESC, model
        """, (days,))
        rows = cur.fetchall()

        result = {}
        for row in rows:
            day_str = str(row["day"])
            if day_str not in result:
                result[day_str] = {
                    "total_tokens": 0,
                    "estimated_cost": 0.0,
                    "call_count": 0,
                    "by_model": {},
                }
            entry = result[day_str]
            entry["total_tokens"] += row["total_tokens"]
            entry["estimated_cost"] += float(row["total_cost"] or 0)
            entry["call_count"] += row["call_count"]
            entry["by_model"][row["model"]] = {
                "tokens": row["total_tokens"],
                "cost": float(row["total_cost"] or 0),
                "calls": row["call_count"],
            }
        return result
    finally:
        conn.close()


def get_caller_breakdown(hours: int = 24) -> list:
    """
    Get token usage breakdown by caller for the last N hours.
    Returns list of {caller_id, call_type, total_tokens, call_count}.
    """
    from lib.ganuda_db import execute_query

    return execute_query("""
        SELECT
            caller_id,
            call_type,
            SUM(input_tokens + output_tokens) AS total_tokens,
            COUNT(*) AS call_count,
            SUM(estimated_cost) AS total_cost
        FROM token_ledger
        WHERE created_at >= NOW() - INTERVAL '%s hours'
        GROUP BY caller_id, call_type
        ORDER BY total_tokens DESC
    """, (hours,))