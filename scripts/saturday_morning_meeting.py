import os
import datetime
from typing import List, Dict, Tuple
from ganuda_db import get_connection
from psycopg2.extras import RealDictCursor

def fetch_thermal_rates(conn) -> Dict[str, float]:
    query = """
    SELECT 
        'thermal_write_rate' AS metric, AVG(thermal_write_rate) AS value
    FROM 
        thermal_metrics
    WHERE 
        created_at >= NOW() - INTERVAL '7 days'
    UNION ALL
    SELECT 
        'sacred_thermal_rate' AS metric, AVG(sacred_thermal_rate) AS value
    FROM 
        thermal_metrics
    WHERE 
        created_at >= NOW() - INTERVAL '7 days';
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query)
        results = cursor.fetchall()
    return {row['metric']: row['value'] for row in results}

def fetch_error_classes(conn) -> Dict[str, int]:
    query = """
    SELECT 
        error_pattern, COUNT(*) AS count
    FROM 
        jr_work_queue
    WHERE 
        status = 'failed' AND created_at >= NOW() - INTERVAL '7 days'
    GROUP BY 
        error_pattern;
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query)
        results = cursor.fetchall()
    return {row['error_pattern']: row['count'] for row in results}

def fetch_safety_canary_count(conn) -> int:
    query = """
    SELECT 
        COUNT(*) AS count
    FROM 
        thermal_memories
    WHERE 
        metadata::jsonb ? 'safety_canary' AND created_at >= NOW() - INTERVAL '7 days';
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query)
        result = cursor.fetchone()
    return result['count']

def fetch_council_health(conn) -> Tuple[int, float]:
    query = """
    SELECT 
        COUNT(*) AS count, AVG(confidence) AS avg_confidence
    FROM 
        council_votes
    WHERE 
        created_at >= NOW() - INTERVAL '7 days';
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query)
        result = cursor.fetchone()
    return result['count'], result['avg_confidence']

def fetch_jr_executor_stats(conn) -> Dict[str, int]:
    query = """
    SELECT 
        status, COUNT(*) AS count
    FROM 
        jr_work_queue
    WHERE 
        created_at >= NOW() - INTERVAL '7 days'
    GROUP BY 
        status;
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query)
        results = cursor.fetchall()
    return {row['status']: row['count'] for row in results}

def fetch_kanban_velocity(conn) -> Dict[str, int]:
    query = """
    SELECT 
        status, COUNT(*) AS count, SUM(story_points) AS story_points
    FROM 
        duyuktv_tickets
    WHERE 
        created_at >= NOW() - INTERVAL '7 days'
    GROUP BY 
        status;
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query)
        results = cursor.fetchall()
    return {row['status']: {'count': row['count'], 'story_points': row['story_points']} for row in results}

def fetch_observability_summary(conn) -> str:
    """
    Condensed observability summary for the Saturday Morning Meeting.
    BSM Leg 3 integration — executive-level, not the full report.

    Pulls: rollback rate, connection utilization, and reads the weekly
    report recommendations section if available.
    """
    lines = []

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Rollback rate for primary DB
            cursor.execute("""
                SELECT datname,
                       CASE WHEN (xact_commit + xact_rollback) > 0
                            THEN ROUND(100.0 * xact_rollback / (xact_commit + xact_rollback), 2)
                            ELSE 0 END AS rollback_pct,
                       deadlocks
                FROM pg_stat_database
                WHERE datname = 'zammad_production'
            """)
            row = cursor.fetchone()
            if row:
                lines.append(f"Rollback Rate: {row['rollback_pct']}%")
                lines.append(f"Deadlocks: {row['deadlocks']}")

            # Connection count
            cursor.execute("""
                SELECT COUNT(*) AS total,
                       COUNT(*) FILTER (WHERE state = 'active') AS active,
                       (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') AS max_conn
                FROM pg_stat_activity
            """)
            crow = cursor.fetchone()
            if crow:
                util = round(100.0 * crow['total'] / (crow['max_conn'] or 100), 1)
                lines.append(f"DB Connections: {crow['total']}/{crow['max_conn']} ({util}%), {crow['active']} active")
    except Exception as e:
        lines.append(f"DB metrics unavailable: {e}")

    # Pull recommendations from weekly report if file exists and is fresh
    report_path = "/ganuda/logs/weekly_observability_report.md"
    try:
        if os.path.exists(report_path):
            mtime = os.path.getmtime(report_path)
            age_days = (datetime.datetime.now().timestamp() - mtime) / 86400
            if age_days <= 7:
                with open(report_path, "r") as f:
                    content = f.read()
                # Extract recommendations section
                if "## 6. Recommendations" in content:
                    rec_section = content.split("## 6. Recommendations")[1].split("---")[0].strip()
                    if rec_section and "No actionable" not in rec_section:
                        lines.append(f"Weekly Recs: {rec_section[:200]}")
                    else:
                        lines.append("Weekly Recs: All metrics within thresholds")
    except Exception:
        pass

    return "\n".join(lines) if lines else "Observability data unavailable"


def generate_report() -> str:
    conn = get_connection()
    thermal_rates = fetch_thermal_rates(conn)
    error_classes = fetch_error_classes(conn)
    safety_canary_count = fetch_safety_canary_count(conn)
    council_count, council_avg_confidence = fetch_council_health(conn)
    jr_executor_stats = fetch_jr_executor_stats(conn)
    kanban_velocity = fetch_kanban_velocity(conn)
    obs_summary = fetch_observability_summary(conn)

    report = f"# Saturday Morning Meeting Report - {datetime.date.today().strftime('%Y-%m-%d')}\n\n"

    report += "## Thermal Rates\n"
    report += f"Thermal Write Rate: {thermal_rates['thermal_write_rate']:.1f}\n"
    report += f"Sacred Thermal Rate: {thermal_rates['sacred_thermal_rate']:.1f}\n\n"

    report += "## Error Classes\n"
    for error_class, count in error_classes.items():
        report += f"- {error_class}: {count}\n"
    report += "\n"

    report += "## Safety Canary\n"
    report += f"Count: {safety_canary_count}\n\n"

    report += "## Council Health\n"
    report += f"Count: {council_count}\n"
    report += f"Avg Confidence: {council_avg_confidence:.1f}\n\n"

    report += "## Jr Executor\n"
    report += f"Completed: {jr_executor_stats.get('completed', 0)}\n"
    report += f"Failed: {jr_executor_stats.get('failed', 0)}\n"
    dlq_rate = (jr_executor_stats.get('failed', 0) / (jr_executor_stats.get('completed', 0) + jr_executor_stats.get('failed', 0))) * 100 if (jr_executor_stats.get('completed', 0) + jr_executor_stats.get('failed', 0)) > 0 else 0
    report += f"DLQ Rate: {dlq_rate:.1f}%\n\n"

    report += "## Kanban Velocity\n"
    for status, data in kanban_velocity.items():
        report += f"- {status.capitalize()}: {data['count']} tickets, {data['story_points']} story points\n"
    report += "\n"

    report += "## Observability (BSM Leg 3)\n"
    report += obs_summary + "\n\n"

    conn.commit()  # explicit commit before close
    conn.close()
    return report

def main():
    report = generate_report()
    report_dir = "/ganuda/reports/saturday_morning/"
    if not os.path.exists(report_dir):
        os.makedirs(report_dir)
    report_file = os.path.join(report_dir, f"{datetime.date.today().strftime('%Y-%m-%d')}.md")
    with open(report_file, 'w') as f:
        f.write(report)
    print(report)

if __name__ == "__main__":
    main()