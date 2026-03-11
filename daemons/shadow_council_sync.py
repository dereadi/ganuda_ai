#!/usr/bin/env python3
"""
Shadow Council Sync — bmasass divergence detection

Syncs thermal memories to shadow council (bmasass DeepSeek-R1-32B).
Re-deliberates recent council votes independently.
Detects divergence between primary and shadow recommendations.

Usage:
    python3 shadow_council_sync.py --sync      # Sync recent memories
    python3 shadow_council_sync.py --deliberate # Re-deliberate recent votes
    python3 shadow_council_sync.py --compare    # Compare primary vs shadow
    python3 shadow_council_sync.py --daemon     # Run continuous sync loop

For Seven Generations
"""

import argparse
import hashlib
import json
import os
import sys
import time
import psycopg2
import psycopg2.extras
import requests
from datetime import datetime, timedelta

# Configuration
PRIMARY_VLLM = "http://192.168.132.222:8000/v1/chat/completions"
PRIMARY_MODEL = "Qwen/Qwen2.5-72B-Instruct-AWQ"
SHADOW_MLX = "http://192.168.132.21:8800/v1/chat/completions"
SHADOW_MODEL = "mlx-community/DeepSeek-R1-Distill-Llama-70B-4bit"
DB_CONFIG = {
    "host": "192.168.132.222",
    "dbname": "zammad_production",
    "user": "claude",
    "password": os.environ.get("CHEROKEE_DB_PASS", "")
}
TELEGRAM_URL = "https://api.telegram.org"
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
DIVERGENCE_THRESHOLD = 0.3  # Alert if >30% of re-deliberated votes diverge
SYNC_INTERVAL_HOURS = 6
DELIBERATE_SAMPLE_SIZE = 10


def get_db():
    return psycopg2.connect(**DB_CONFIG, cursor_factory=psycopg2.extras.RealDictCursor)


def sync_memories(hours=24):
    """Sync recent thermal memories to shadow council context."""
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, original_content, temperature_score, memory_hash,
                   sacred_pattern, metadata, created_at
            FROM thermal_memory_archive
            WHERE created_at > NOW() - INTERVAL '%s hours'
            ORDER BY temperature_score DESC
            LIMIT 500
        """, (hours,))
        memories = cur.fetchall()

    print(f"[SHADOW] Fetched {len(memories)} memories from last {hours} hours")

    # Build context summary for shadow council
    context_parts = []
    for m in memories[:100]:  # Top 100 by temperature
        content = m["original_content"][:300] if m["original_content"] else ""
        score = m.get("temperature_score", 0)
        context_parts.append(f"[T={score}] {content}")

    context = "\n---\n".join(context_parts)

    # Store sync metadata
    sync_record = {
        "synced_at": datetime.now().isoformat(),
        "memory_count": len(memories),
        "context_chars": len(context),
        "hours_covered": hours
    }

    sync_path = "/ganuda/reports/shadow_council/last_sync.json"
    os.makedirs(os.path.dirname(sync_path), exist_ok=True)
    with open(sync_path, "w") as f:
        json.dump(sync_record, f, indent=2)

    print(f"[SHADOW] Sync complete: {len(memories)} memories, {len(context)} chars context")
    conn.close()
    return context


def shadow_deliberate(question, context=""):
    """Send a question to the shadow council (bmasass DeepSeek-R1)."""
    system_prompt = (
        "You are the Shadow Council — an independent deliberation agent. "
        "Analyze this question independently. Consider security, efficiency, "
        "cultural values, and architecture. Provide a clear recommendation: "
        "PROCEED, BLOCK, or CONTESTED with reasoning.\n\n"
    )
    if context:
        system_prompt += f"Recent tribal context:\n{context[:2000]}\n\n"

    try:
        resp = requests.post(
            SHADOW_MLX,
            json={
                "model": SHADOW_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ],
                "max_tokens": 500,
                "temperature": 0.4
            },
            timeout=120  # DeepSeek-R1 on M4 can be slower
        )
        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"]
            # Parse recommendation
            upper = content.upper()
            if "PROCEED" in upper:
                recommendation = "PROCEED"
            elif "BLOCK" in upper:
                recommendation = "BLOCK"
            else:
                recommendation = "CONTESTED"
            return {
                "recommendation": recommendation,
                "reasoning": content[:500],
                "model": SHADOW_MODEL,
                "success": True
            }
        else:
            return {"success": False, "error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def compare_votes(sample_size=10, hours=72):
    """Re-deliberate recent primary council votes on shadow and compare."""
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, question, recommendation, confidence, concerns, audit_hash
            FROM council_votes
            WHERE voted_at > NOW() - INTERVAL '%s hours'
              AND recommendation IS NOT NULL
            ORDER BY voted_at DESC
            LIMIT %s
        """, (hours, sample_size))
        votes = cur.fetchall()

    if not votes:
        print("[SHADOW] No recent votes to compare")
        conn.close()
        return {"divergence_rate": 0, "comparisons": []}

    print(f"[SHADOW] Comparing {len(votes)} votes (primary vs shadow)")

    # Get sync context
    context = sync_memories(hours=hours)

    comparisons = []
    divergent = 0

    for vote in votes:
        print(f"\n  Vote #{vote['id']}: {vote['question'][:60]}...")

        shadow_result = shadow_deliberate(vote["question"], context)

        if not shadow_result.get("success"):
            print(f"  Shadow FAILED: {shadow_result.get('error', 'unknown')}")
            continue

        primary_rec = vote.get("recommendation", "PROCEED")
        shadow_rec = shadow_result["recommendation"]
        is_divergent = primary_rec != shadow_rec

        comparisons.append({
            "vote_id": vote["id"],
            "question": vote["question"][:100],
            "primary": primary_rec,
            "shadow": shadow_rec,
            "divergent": is_divergent,
            "shadow_reasoning": shadow_result["reasoning"][:200]
        })

        if is_divergent:
            divergent += 1
            print(f"  DIVERGENT: primary={primary_rec}, shadow={shadow_rec}")
        else:
            print(f"  ALIGNED: both={primary_rec}")

        time.sleep(2)  # Rate limit shadow queries

    total = len(comparisons)
    divergence_rate = divergent / total if total > 0 else 0

    print(f"\n{'='*50}")
    print(f"[SHADOW] Divergence rate: {divergence_rate:.1%} ({divergent}/{total})")

    # Log results
    result = {
        "divergence_rate": divergence_rate,
        "divergent_count": divergent,
        "total_compared": total,
        "comparisons": comparisons,
        "timestamp": datetime.now().isoformat(),
        "primary_model": PRIMARY_MODEL,
        "shadow_model": SHADOW_MODEL
    }

    report_path = f"/ganuda/reports/shadow_council/comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"[SHADOW] Report: {report_path}")

    # Log to thermal memory
    memory_content = (
        f"SHADOW COUNCIL COMPARISON — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        f"Divergence rate: {divergence_rate:.1%} ({divergent}/{total})\n"
        f"Primary: {PRIMARY_MODEL}\n"
        f"Shadow: {SHADOW_MODEL}\n"
        f"Divergent questions: {[c['question'][:50] for c in comparisons if c['divergent']]}"
    )
    memory_hash = hashlib.sha256(memory_content.encode()).hexdigest()

    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO thermal_memory_archive (
                    original_content, temperature_score, memory_hash,
                    sacred_pattern, metadata
                ) VALUES (%s, %s, %s, %s, %s)
            """, (
                memory_content,
                80.0 if divergence_rate > DIVERGENCE_THRESHOLD else 50.0,
                memory_hash,
                divergence_rate > DIVERGENCE_THRESHOLD,
                json.dumps({"type": "shadow_council_comparison", **result})
            ))
        conn.commit()
    except Exception as e:
        print(f"[SHADOW] Thermal logging error: {e}")

    # Alert on high divergence
    if divergence_rate > DIVERGENCE_THRESHOLD:
        alert = (
            f"SHADOW COUNCIL DIVERGENCE ALERT\n"
            f"Rate: {divergence_rate:.1%} (threshold: {DIVERGENCE_THRESHOLD:.0%})\n"
            f"Primary ({PRIMARY_MODEL}) and Shadow ({SHADOW_MODEL}) disagree on "
            f"{divergent}/{total} recent decisions.\n"
            f"This may indicate model bias or reasoning drift."
        )
        print(f"\n[SHADOW] {alert}")
        send_telegram(alert)

    conn.close()
    return result


def send_telegram(message):
    """Send Telegram alert."""
    # Slack-first routing (Leaders Meeting #1, Mar 10 2026)
    try:
        import sys as _sys
        if '/ganuda/lib' not in _sys.path:
            _sys.path.insert(0, '/ganuda/lib')
        from slack_telegram_bridge import send_telegram as _slack_send
        if _slack_send(message):
            return
    except Exception:
        pass  # fall through to Telegram
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        requests.post(
            f"{TELEGRAM_URL}/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": message},
            timeout=10
        )
    except Exception:
        pass


def run_daemon():
    """Continuous sync + compare loop."""
    print(f"[SHADOW] Daemon starting — sync every {SYNC_INTERVAL_HOURS}h")
    while True:
        try:
            print(f"\n[SHADOW] Cycle start: {datetime.now().isoformat()}")
            sync_memories(hours=SYNC_INTERVAL_HOURS)
            compare_votes(sample_size=DELIBERATE_SAMPLE_SIZE, hours=SYNC_INTERVAL_HOURS * 3)
        except Exception as e:
            print(f"[SHADOW] Cycle error: {e}")
        print(f"[SHADOW] Next cycle in {SYNC_INTERVAL_HOURS} hours")
        time.sleep(SYNC_INTERVAL_HOURS * 3600)


def main():
    parser = argparse.ArgumentParser(description="Shadow Council Sync + Divergence Detection")
    parser.add_argument("--sync", action="store_true", help="Sync recent memories")
    parser.add_argument("--deliberate", type=str, help="Shadow-deliberate a specific question")
    parser.add_argument("--compare", action="store_true", help="Compare primary vs shadow votes")
    parser.add_argument("--daemon", action="store_true", help="Run continuous loop")
    parser.add_argument("--hours", type=int, default=72, help="Hours of history to compare")
    parser.add_argument("--sample-size", type=int, default=10, help="Votes to compare")
    args = parser.parse_args()

    if args.sync:
        sync_memories(hours=args.hours)
    elif args.deliberate:
        context = sync_memories(hours=24)
        result = shadow_deliberate(args.deliberate, context)
        print(json.dumps(result, indent=2))
    elif args.compare:
        compare_votes(sample_size=args.sample_size, hours=args.hours)
    elif args.daemon:
        run_daemon()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()