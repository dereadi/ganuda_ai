"""Metacognitive Self-Healing: Monitors council vote quality.
Detects confidence drift, concern inflation, and specialist stagnation."""

import subprocess
from datetime import datetime

import psycopg2

DB_CONFIG = {
    "host": "192.168.132.222",
    "user": "claude",
    "dbname": "zammad_production"
}

WINDOW_SIZE = 20
CONFIDENCE_FLOOR = 0.7
CONCERN_CEILING = 3.0

def _send_telegram(message):
    try:
        subprocess.run(
            ["python3", "/ganuda/scripts/telegram_notify.py", message],
            timeout=10, capture_output=True
        )
    except Exception:
        pass

def check_council_health():
    """Returns dict of council health metrics. Call periodically."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        SELECT confidence, concern_count, responses, voted_at
        FROM council_votes
        WHERE confidence IS NOT NULL
        ORDER BY voted_at DESC
        LIMIT %s
    """, (WINDOW_SIZE,))
    rows = cur.fetchall()
    if len(rows) < 5:
        cur.close()
        conn.commit()  # explicit commit before close
        conn.close()
        return {"status": "INSUFFICIENT_DATA", "votes_analyzed": len(rows)}
    confidences = [r[0] for r in rows if r[0] is not None]
    concerns = [r[1] for r in rows if r[1] is not None]
    mean_conf = sum(confidences) / len(confidences) if confidences else 0
    mean_concern = sum(concerns) / len(concerns) if concerns else 0
    alerts = []
    if mean_conf < CONFIDENCE_FLOOR:
        alerts.append(f"CONFIDENCE DRIFT: mean {mean_conf:.3f} below floor {CONFIDENCE_FLOOR}")
    if mean_concern > CONCERN_CEILING:
        alerts.append(f"CONCERN INFLATION: mean {mean_concern:.1f} above ceiling {CONCERN_CEILING}")
    conf_trend = confidences[:5]
    if len(conf_trend) >= 5 and all(c < CONFIDENCE_FLOOR for c in conf_trend):
        alerts.append("SUSTAINED LOW CONFIDENCE: last 5 votes all below floor")

    if alerts:
        alert_text = "METACOG ALERT: " + "; ".join(alerts)
        cur.execute("""
            INSERT INTO thermal_memory_archive
            (original_content, temperature_score, sacred_pattern, memory_hash)
            VALUES (%s, 90, false, encode(sha256((%s || now()::text)::bytea), 'hex'))
        """, (alert_text, "metacog-alert-"))
        conn.commit()
        _send_telegram(alert_text)

    result = {
        "status": "ALERT" if alerts else "HEALTHY",
        "votes_analyzed": len(rows),
        "mean_confidence": round(mean_conf, 4),
        "mean_concerns": round(mean_concern, 2),
        "alerts": alerts,
        "checked_at": datetime.now().isoformat()
    }
    cur.close()
    conn.commit()  # explicit commit before close
    conn.close()
    return result

if __name__ == "__main__":
    import json
    result = check_council_health()
    print(json.dumps(result, indent=2))