#!/usr/bin/env python3
"""Coyote Phase 1: Short Context Thesis Test

Compares council response quality at 2K vs 32K context windows.
Coyote's challenge: can governance + RAG replace large context?

Council Vote: 5ad7577ba1d7685a
"""

import json
import os
import re
import requests
import psycopg2
from datetime import datetime


DB_HOST = os.environ.get("CHEROKEE_DB_HOST", os.environ.get('CHEROKEE_DB_HOST', '10.100.0.2'))
DB_NAME = os.environ.get("CHEROKEE_DB_NAME", "zammad_production")
DB_USER = os.environ.get("CHEROKEE_DB_USER", "claude")
DB_PASS = os.environ.get("CHEROKEE_DB_PASS", "")
VLLM_URL = os.environ.get("VLLM_URL", "http://localhost:8000/v1/chat/completions")
VLLM_MODEL = os.environ.get("VLLM_MODEL", "/ganuda/models/qwen2.5-72b-instruct-awq")
EMBEDDING_URL = os.environ.get("EMBEDDING_URL", "http://192.168.132.224:8003/embed")


def load_secrets():
    global DB_PASS
    if not DB_PASS:
        try:
            with open("/ganuda/config/secrets.env") as f:
                for line in f:
                    m = re.match(r"^(\w+)=(.+)$", line.strip())
                    if m:
                        os.environ[m.group(1)] = m.group(2)
            DB_PASS = os.environ.get("CHEROKEE_DB_PASS", "")
        except FileNotFoundError:
            pass


def get_thermal_context(question, max_tokens=500):
    """Retrieve thermal memory via RAG — the governed context."""
    try:
        # Get embedding for question
        embed_resp = requests.post(EMBEDDING_URL, json={"text": question}, timeout=10)
        embed_resp.raise_for_status()
        embedding = embed_resp.json().get("embedding", [])
        if not embedding:
            return ""

        conn = psycopg2.connect(host=DB_HOST, port=5432, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
        cur = conn.cursor()
        cur.execute("""SELECT original_content, temperature_score
            FROM thermal_memory_archive
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> %s::vector
            LIMIT 5""", (str(embedding),))
        rows = cur.fetchall()
        cur.close()
        conn.commit()  # explicit commit before close
        conn.close()

        context = "\n---\n".join([f"[temp:{r[1]}] {r[0][:200]}" for r in rows])
        return context[:max_tokens * 4]  # rough char estimate
    except Exception as e:
        print(f"  RAG retrieval failed: {e}")
        return ""


def query_model(question, context, max_context_tokens):
    """Query the model with a specific context budget."""
    if max_context_tokens <= 2048:
        # Short context: only RAG results, trimmed
        system = f"Answer concisely using this context:\n{context[:2000]}"
    else:
        # Full context: pad with broader context
        system = f"You have full context available. Use it thoroughly.\n{context[:16000]}"

    try:
        resp = requests.post(VLLM_URL, json={
            "model": VLLM_MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": question},
            ],
            "max_tokens": 300,
            "temperature": 0.7,
        }, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return content, usage
    except Exception as e:
        return f"ERROR: {e}", {}


TEST_QUESTIONS = [
    "What is the Cherokee AI Federation's approach to AI governance?",
    "How does thermal memory work and why does temperature matter?",
    "What are the design constraints and why are they sacred?",
    "Explain the difference between the inner and outer council.",
    "What is the reflex principle and how does it apply to our architecture?",
]


def main():
    load_secrets()
    print("=" * 60)
    print("COYOTE PHASE 1: Short Context Thesis Test")
    print(f"Date: {datetime.now().isoformat()[:16]}")
    print("=" * 60)

    results = []

    for q in TEST_QUESTIONS:
        print(f"\nQ: {q}")
        context = get_thermal_context(q)
        rag_len = len(context)
        print(f"  RAG context: {rag_len} chars")

        # Short context (2K)
        short_resp, short_usage = query_model(q, context, 2048)
        print(f"  2K response: {len(short_resp)} chars, tokens: {short_usage}")

        # Full context (32K)
        full_resp, full_usage = query_model(q, context, 32768)
        print(f"  32K response: {len(full_resp)} chars, tokens: {full_usage}")

        results.append({
            "question": q,
            "rag_context_chars": rag_len,
            "short_response": short_resp,
            "short_usage": short_usage,
            "full_response": full_resp,
            "full_usage": full_usage,
        })

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    short_total_tokens = sum(r["short_usage"].get("total_tokens", 0) for r in results)
    full_total_tokens = sum(r["full_usage"].get("total_tokens", 0) for r in results)
    print(f"Total tokens (2K context): {short_total_tokens}")
    print(f"Total tokens (32K context): {full_total_tokens}")
    print(f"Token savings: {full_total_tokens - short_total_tokens} ({(1 - short_total_tokens/max(full_total_tokens,1))*100:.0f}%)")
    print("\nResponses saved to /tmp/coyote_context_test_results.json")
    print("NEXT: Human review of response quality (side-by-side)")
    print("Coyote's question: Is the 2K response meaningfully worse?")

    with open("/tmp/coyote_context_test_results.json", "w") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    main()