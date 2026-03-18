#!/usr/bin/env python3
"""Breathing API — real-time organism vital signs as JSON."""

import os
import re
import psycopg2
import psycopg2.extras
from flask import Flask, jsonify

app = Flask(__name__)

DB_HOST = os.environ.get("CHEROKEE_DB_HOST", "192.168.132.222")
DB_NAME = os.environ.get("CHEROKEE_DB_NAME", "zammad_production")
DB_USER = os.environ.get("CHEROKEE_DB_USER", "claude")
DB_PASS = os.environ.get("CHEROKEE_DB_PASS", "")


def _load_secrets() -> None:
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


def get_db() -> psycopg2.extensions.connection:
    _load_secrets()
    return psycopg2.connect(host=DB_HOST, port=5432, dbname=DB_NAME,
                            user=DB_USER, password=DB_PASS)


@app.route("/api/breathing", methods=["GET"])
def breathing() -> str:
    """Return the organism's recent vital signs."""
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("""
        (SELECT completed_at AS ts, 'task_done' AS kind,
                title AS detail, NULL AS extra
         FROM jr_work_queue
         WHERE completed_at > NOW() - INTERVAL '24 hours'
           AND title NOT LIKE '[TEG]%%'
         ORDER BY completed_at DESC LIMIT 15)
        UNION ALL
        (SELECT started_at AS ts, 'task_start' AS kind,
                title AS detail, NULL AS extra
         FROM jr_work_queue
         WHERE started_at > NOW() - INTERVAL '24 hours'
           AND status = 'in_progress'
           AND title NOT LIKE '[TEG]%%'
         ORDER BY started_at DESC LIMIT 10)
        UNION ALL
        (SELECT voted_at AS ts, 'vote' AS kind,
                LEFT(question, 100) AS detail,
                ROUND(confidence::numeric, 2)::text AS extra
         FROM council_votes
         WHERE voted_at > NOW() - INTERVAL '24 hours'
         ORDER BY voted_at DESC LIMIT 15)
        UNION ALL
        (SELECT created_at AS ts,
                CASE WHEN sacred_pattern = true THEN 'sacred' ELSE 'thermal' END AS kind,
                LEFT(original_content, 100) AS detail,
                temperature_score::text AS extra
         FROM thermal_memory_archive
         WHERE created_at > NOW() - INTERVAL '24 hours'
           AND temperature_score >= 50
           AND original_content NOT LIKE 'FIRE GUARD ALERT%%'
           AND original_content NOT LIKE 'ALERT: LLM Gateway%%'
           AND original_content NOT LIKE 'ELISI%%'
           AND original_content NOT LIKE 'COUNCIL VOTE:%%'
           AND original_content NOT LIKE 'COUNCIL DIVERSITY%%'
         ORDER BY created_at DESC LIMIT 15)
        UNION ALL
        (SELECT created_at AS ts, 'fire_guard' AS kind,
                'Fire Guard cycle' AS detail,
                temperature_score::text AS extra
         FROM thermal_memory_archive
         WHERE created_at > NOW() - INTERVAL '2 hours'
           AND original_content LIKE 'FIRE GUARD%%'
         ORDER BY created_at DESC LIMIT 10)
        ORDER BY ts DESC LIMIT 50
    """)
    events = cur.fetchall()

    # Vitals summary
    cur.execute("SELECT COUNT(*) FROM thermal_memory_archive")
    total_memories = cur.fetchone()["count"]
    cur.execute("SELECT COUNT(*) FROM thermal_memory_archive WHERE sacred_pattern = true")
    sacred = cur.fetchone()["count"]
    cur.execute("SELECT COUNT(*) FROM council_votes")
    total_votes = cur.fetchone()["count"]
    cur.execute("SELECT COUNT(*) FROM jr_work_queue WHERE status = 'completed'")
    tasks_done = cur.fetchone()["count"]
    cur.execute("SELECT COUNT(*) FROM jr_work_queue WHERE status = 'in_progress'")
    tasks_active = cur.fetchone()["count"]

    # Last Fire Guard
    cur.execute("""SELECT created_at FROM thermal_memory_archive
        WHERE original_content LIKE 'FIRE GUARD%%'
        ORDER BY created_at DESC LIMIT 1""")
    row = cur.fetchone()
    last_fire_guard = row["created_at"].isoformat() if row else None

    cur.close()
    conn.commit()  # explicit commit before close
    conn.close()

    # Convert timestamps
    for e in events:
        if e["ts"]:
            e["ts"] = e["ts"].isoformat()

    return jsonify({
        "vitals": {
            "memories": total_memories,
            "sacred": sacred,
            "votes": total_votes,
            "tasks_done": tasks_done,
            "tasks_active": tasks_active,
            "last_fire_guard": last_fire_guard,
        },
        "events": events,
    })


if __name__ == "__main__":
    _load_secrets()
    app.run(host="127.0.0.1", port=8086, debug=False)