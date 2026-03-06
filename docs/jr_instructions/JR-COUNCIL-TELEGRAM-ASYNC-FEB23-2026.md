# Jr Instruction: Council Async Conversation on Telegram

**Task ID:** COUNCIL-TELEGRAM
**Kanban:** #1837
**Priority:** 3
**Assigned:** Software Engineer Jr.

---

## Overview

Enable council deliberation via Telegram. Questions sent to a Telegram group get submitted to the gateway for council vote, with results posted back.

---

## Step 1: Create the async Telegram council bridge

Create `/ganuda/scripts/council_telegram_async.py`

```python
#!/usr/bin/env python3
"""Council Telegram Async Bridge.
Receives questions via Telegram, submits to council, returns results."""

import json
import os
import requests
from datetime import datetime

import psycopg2

GATEWAY_URL = "http://localhost:8080"
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
DB_CONFIG = {
    "host": "192.168.132.222",
    "user": "claude",
    "dbname": "zammad_production"
}

def submit_to_council(question, context="Via Telegram"):
    try:
        resp = requests.post(
            f"{GATEWAY_URL}/v1/council/vote",
            json={"question": question, "context": context},
            timeout=120
        )
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

def format_council_response(result):
    if "error" in result:
        return f"Council Error: {result['error']}"
    lines = [
        f"Council Vote #{result.get('audit_hash', 'unknown')[:8]}",
        f"Recommendation: {result.get('recommendation', 'N/A')}",
        f"Confidence: {result.get('confidence', 'N/A')}",
        "",
        "Consensus:",
        result.get("consensus", "No consensus recorded")[:500]
    ]
    if result.get("concerns"):
        lines.append("")
        lines.append("Concerns:")
        for c in result["concerns"][:3]:
            lines.append(f"  - {c}")
    return "\n".join(lines)

def send_telegram(chat_id, text):
    if not BOT_TOKEN:
        print(f"No bot token, would send to {chat_id}: {text[:100]}")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": chat_id,
        "text": text[:4000],
        "parse_mode": "Markdown"
    }, timeout=10)

def log_to_thermal(question, result):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO thermal_memory_archive
            (original_content, temperature_score, sacred_pattern, memory_hash)
            VALUES (%s, 75, false, encode(sha256((%s || now()::text)::bytea), 'hex'))
        """, (
            f"TELEGRAM COUNCIL QUERY: {question[:200]}\nResult: {result.get('recommendation', 'N/A')} (conf={result.get('confidence', 'N/A')})",
            f"telegram-council-{result.get('audit_hash', 'unknown')}-"
        ))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"DB log error: {e}")

def handle_message(chat_id, text):
    if not text.startswith("/council "):
        return
    question = text[9:].strip()
    if not question:
        send_telegram(chat_id, "Usage: /council <your question>")
        return
    send_telegram(chat_id, "Submitting to council...")
    result = submit_to_council(question)
    response = format_council_response(result)
    send_telegram(chat_id, response)
    log_to_thermal(question, result)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        test_q = " ".join(sys.argv[1:])
        result = submit_to_council(test_q)
        print(format_council_response(result))
    else:
        print("Usage: python3 council_telegram_async.py <test question>")
```

---

## Verification

```text
python3 /ganuda/scripts/council_telegram_async.py "Test: What is the federation status?"
```
