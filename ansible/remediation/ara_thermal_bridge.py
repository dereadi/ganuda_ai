#!/usr/bin/env python3
"""
Cherokee AI Federation — ARA to Thermal Memory Bridge

Reads playbook execution results from ARA's REST API and writes
them to thermal_memory_archive as learning memories.

This closes the self-healing feedback loop:
  Alert → Classify → Generate → Validate → Execute → Record → Learn

Usage:
    python ara_thermal_bridge.py --playbook-id <ara_playbook_id>
    python ara_thermal_bridge.py --recent  # Process last hour of executions
"""

import argparse
import json
import os
import sys
import hashlib
from datetime import datetime, timedelta

import requests
import psycopg2

# Configuration
ARA_URL = os.environ.get("ARA_API_URL", "http://localhost:8888/api/v1")
DB_HOST = "192.168.132.222"
DB_NAME = "zammad_production"
DB_USER = "claude"
EMBEDDING_URL = "http://192.168.132.224:8003"


def get_db_password():
    """Load DB password from secrets_loader or environment."""
    try:
        sys.path.insert(0, "/ganuda/lib")
        from secrets_loader import get_secret
        return get_secret("DB_PASSWORD")
    except Exception:
        return os.environ.get("DB_PASSWORD", "")


def fetch_playbook_results(playbook_id: str = None, recent: bool = False) -> list:
    """Fetch execution results from ARA REST API."""
    results = []

    try:
        if playbook_id:
            resp = requests.get(
                f"{ARA_URL}/playbooks/{playbook_id}",
                timeout=10,
            )
            resp.raise_for_status()
            results.append(resp.json())
        elif recent:
            # Get playbooks from the last hour
            since = (datetime.utcnow() - timedelta(hours=1)).isoformat()
            resp = requests.get(
                f"{ARA_URL}/playbooks",
                params={"started_after": since, "order": "-started"},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", [])
    except requests.RequestException as e:
        print(f"ARA API error: {e}", file=sys.stderr)
    except Exception as e:
        print(f"Unexpected error fetching ARA results: {e}", file=sys.stderr)

    return results


def fetch_task_results(playbook_id: str) -> list:
    """Fetch individual task results for a playbook from ARA."""
    try:
        resp = requests.get(
            f"{ARA_URL}/results",
            params={"playbook": playbook_id, "order": "started"},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json().get("results", [])
    except Exception as e:
        print(f"Error fetching task results: {e}", file=sys.stderr)
        return []


def build_thermal_memory(playbook: dict, task_results: list) -> str:
    """Build a thermal memory entry from ARA playbook results."""
    status = playbook.get("status", "unknown")
    duration = playbook.get("duration", "unknown")
    path = playbook.get("path", "unknown")
    started = playbook.get("started", "unknown")

    content = f"SELF-HEALING EXECUTION RESULT\n"
    content += f"Playbook: {path}\n"
    content += f"Status: {status.upper()}\n"
    content += f"Duration: {duration}\n"
    content += f"Started: {started}\n"

    # Summarize task results
    ok_count = 0
    changed_count = 0
    failed_count = 0
    skipped_count = 0

    for task in task_results:
        task_status = task.get("status", "unknown")
        if task_status == "ok":
            ok_count += 1
        elif task_status == "changed":
            changed_count += 1
        elif task_status == "failed":
            failed_count += 1
        elif task_status == "skipped":
            skipped_count += 1

    content += f"Tasks: {ok_count} ok, {changed_count} changed, {failed_count} failed, {skipped_count} skipped\n"

    # Include failed task details
    for task in task_results:
        if task.get("status") == "failed":
            content += f"\nFAILED TASK: {task.get('name', 'unnamed')}\n"
            result_data = task.get("result", {})
            if isinstance(result_data, dict):
                msg = result_data.get("msg", "")
                if msg:
                    content += f"  Error: {msg[:200]}\n"

    # Learning summary
    if status == "completed" and failed_count == 0:
        content += "\nLEARNING: Remediation succeeded. This playbook pattern is validated.\n"
    elif failed_count > 0:
        content += f"\nLEARNING: Remediation had {failed_count} failures. Review task errors above.\n"
    else:
        content += f"\nLEARNING: Playbook status={status}. May need manual investigation.\n"

    return content


def get_embedding(text: str) -> list:
    """Get embedding vector from the embedding service."""
    try:
        resp = requests.post(
            f"{EMBEDDING_URL}/embed",
            json={"text": text[:500]},
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json().get("embedding")
    except Exception:
        pass
    return None


def write_to_thermal_memory(content: str, metadata: dict):
    """Write execution result to thermal_memory_archive."""
    db_password = get_db_password()
    memory_hash = hashlib.sha256(content.encode()).hexdigest()

    # Determine temperature based on outcome
    status = metadata.get("status", "unknown")
    if status == "completed" and metadata.get("failed_count", 0) == 0:
        temperature = 0.5  # Successful — warm but not hot
    else:
        temperature = 0.8  # Failed — hot, needs attention

    # Get embedding for semantic search
    embedding = get_embedding(content)

    try:
        conn = psycopg2.connect(
            host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=db_password
        )
        cur = conn.cursor()

        if embedding:
            cur.execute(
                """INSERT INTO thermal_memory_archive
                (original_content, temperature_score, sacred_pattern, memory_hash, metadata, embedding)
                VALUES (%s, %s, false, %s, %s, %s::vector)
                ON CONFLICT (memory_hash) DO NOTHING""",
                (content, temperature, memory_hash, json.dumps(metadata), str(embedding)),
            )
        else:
            cur.execute(
                """INSERT INTO thermal_memory_archive
                (original_content, temperature_score, sacred_pattern, memory_hash, metadata)
                VALUES (%s, %s, false, %s, %s)
                ON CONFLICT (memory_hash) DO NOTHING""",
                (content, temperature, memory_hash, json.dumps(metadata)),
            )

        conn.commit()
        conn.close()
        print(f"  Written to thermal memory (hash: {memory_hash[:12]}...)")
    except Exception as e:
        print(f"  ERROR writing to thermal memory: {e}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="ARA to Thermal Memory Bridge")
    parser.add_argument("--playbook-id", help="Specific ARA playbook ID to process")
    parser.add_argument("--recent", action="store_true", help="Process last hour of executions")
    args = parser.parse_args()

    if not args.playbook_id and not args.recent:
        print("ERROR: Specify --playbook-id or --recent")
        sys.exit(1)

    print(f"[{datetime.now().isoformat()}] ARA → Thermal Memory Bridge")

    playbooks = fetch_playbook_results(
        playbook_id=args.playbook_id,
        recent=args.recent,
    )

    if not playbooks:
        print("No playbook results found.")
        sys.exit(0)

    print(f"Processing {len(playbooks)} playbook(s)...")

    for pb in playbooks:
        pb_id = pb.get("id", "unknown")
        print(f"\n  Playbook {pb_id}: {pb.get('path', 'unknown')}")

        task_results = fetch_task_results(str(pb_id))
        content = build_thermal_memory(pb, task_results)

        failed_count = sum(1 for t in task_results if t.get("status") == "failed")
        metadata = {
            "type": "self_healing_execution",
            "ara_playbook_id": str(pb_id),
            "status": pb.get("status", "unknown"),
            "duration": str(pb.get("duration", "")),
            "failed_count": failed_count,
            "timestamp": datetime.now().isoformat(),
        }

        write_to_thermal_memory(content, metadata)

    print(f"\nDone. Processed {len(playbooks)} playbook result(s) into thermal memory.")


if __name__ == "__main__":
    main()