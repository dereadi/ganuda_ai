#!/usr/bin/env python3
"""
Flying Squirrel Pattern Analyzer
Monitors interaction patterns and behavioral signatures for the Flying Squirrel profile.
Includes Silent Guardian behavioral continuity checking.
"""

import psycopg2
import json
from datetime import datetime, timedelta
from collections import Counter

DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'triad_federation',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

def get_baseline_profile():
    """Fetch the current Flying Squirrel profile from thermal memory"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        SELECT id, content, temperature, created_at
        FROM triad_shared_memories
        WHERE 'flying_squirrel' = ANY(tags)
          AND 'living_document' = ANY(tags)
        ORDER BY created_at DESC LIMIT 1
    """)
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

def analyze_query_patterns(days=7):
    """Analyze Chief CLI query patterns"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cutoff = datetime.now() - timedelta(days=days)
    cur.execute("""
        SELECT query_type, COUNT(*)
        FROM chief_cli_resonance
        WHERE created_at > %s
        GROUP BY query_type
    """, (cutoff,))
    query_types = dict(cur.fetchall())
    cur.execute("""
        SELECT EXTRACT(HOUR FROM created_at)::int as hour, COUNT(*)
        FROM chief_cli_resonance
        WHERE created_at > %s
        GROUP BY hour ORDER BY hour
    """, (cutoff,))
    hourly = dict(cur.fetchall())
    cur.close()
    conn.close()
    return {
        'query_types': query_types,
        'hourly_distribution': hourly,
        'total_queries': sum(query_types.values()) if query_types else 0
    }

def analyze_telegram_patterns(days=7):
    """Analyze Telegram interaction patterns"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cutoff = datetime.now() - timedelta(days=days)
    cur.execute("""
        SELECT detected_intent, COUNT(*)
        FROM telegram_resonance
        WHERE created_at > %s AND detected_intent IS NOT NULL
        GROUP BY detected_intent
    """, (cutoff,))
    intents = dict(cur.fetchall())
    cur.execute("SELECT COUNT(*) FROM telegram_resonance WHERE created_at > %s", (cutoff,))
    total = cur.fetchone()[0]
    cur.close()
    conn.close()
    return {'intents': intents, 'total_messages': total}

def calculate_squirrel_index(days=7):
    """Calculate topic drift frequency - higher = more squirreling"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cutoff = datetime.now() - timedelta(days=days)
    cur.execute("""
        SELECT detected_intent, created_at
        FROM telegram_resonance
        WHERE created_at > %s
        ORDER BY created_at
    """, (cutoff,))
    messages = cur.fetchall()
    cur.close()
    conn.close()
    if len(messages) < 2:
        return 0.0
    switches = 0
    for i in range(1, len(messages)):
        time_diff = (messages[i][1] - messages[i-1][1]).total_seconds()
        if time_diff < 600 and messages[i][0] != messages[i-1][0]:
            switches += 1
    return round((switches / len(messages)) * 10, 2)

def detect_hyperfocus_sessions(days=7):
    """Detect periods of sustained activity (hyperfocus)"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cutoff = datetime.now() - timedelta(days=days)
    cur.execute("""
        SELECT created_at FROM (
            SELECT created_at FROM chief_cli_resonance WHERE created_at > %s
            UNION ALL
            SELECT created_at FROM telegram_resonance WHERE created_at > %s
        ) combined ORDER BY created_at
    """, (cutoff, cutoff))
    timestamps = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    if len(timestamps) < 3:
        return []
    sessions = []
    session_start = timestamps[0]
    session_count = 1
    for i in range(1, len(timestamps)):
        gap = (timestamps[i] - timestamps[i-1]).total_seconds()
        if gap < 1800:
            session_count += 1
        else:
            if session_count >= 5:
                sessions.append({
                    'start': str(session_start),
                    'interactions': session_count,
                    'duration_min': round((timestamps[i-1] - session_start).total_seconds() / 60)
                })
            session_start = timestamps[i]
            session_count = 1
    return sessions

def check_behavioral_continuity(hours=4):
    """Silent guardian - checks if current session matches Flying Squirrel signature."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cutoff = datetime.now() - timedelta(hours=hours)
    cur.execute("""
        SELECT query_type, EXTRACT(HOUR FROM created_at)::int as hour
        FROM chief_cli_resonance WHERE created_at > %s
    """, (cutoff,))
    cli_data = cur.fetchall()
    cur.execute("""
        SELECT detected_intent, EXTRACT(HOUR FROM created_at)::int as hour
        FROM telegram_resonance WHERE created_at > %s
    """, (cutoff,))
    tg_data = cur.fetchall()
    cur.close()
    conn.close()
    if not cli_data and not tg_data:
        return {'confidence': 0, 'reason': 'No recent activity'}
    score = 100
    flags = []
    if cli_data:
        infra_count = sum(1 for q in cli_data if q[0] == 'infrastructure')
        infra_ratio = infra_count / len(cli_data)
        if infra_ratio < 0.3:
            score -= 20
            flags.append(f'Low infrastructure focus ({round(infra_ratio*100)}%)')
    all_hours = [d[1] for d in cli_data] + [d[1] for d in tg_data]
    if all_hours:
        avg_hour = sum(all_hours) / len(all_hours)
        if 6 <= avg_hour <= 14:
            score -= 25
            flags.append(f'Unusual daytime activity (avg hour: {round(avg_hour)})')
    score = max(0, min(100, score))
    if score < 60:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO triad_shared_memories (content, temperature, source_triad, tags, created_at)
            VALUES (%s, %s, 'it_triad_jr', %s, NOW())
        """, (
            f"BEHAVIORAL ANOMALY DETECTED\nConfidence: {score}%\nFlags: {', '.join(flags)}",
            95,
            ['flying_squirrel', 'anomaly', 'security', 'behavioral_biometrics']
        ))
        conn.commit()
        cur.close()
        conn.close()
    return {'confidence': score, 'flags': flags, 'sample_size': len(cli_data) + len(tg_data)}

def generate_report():
    """Generate full analysis report"""
    print("=" * 60)
    print("FLYING SQUIRREL PATTERN ANALYSIS")
    print(f"Generated: {datetime.now().isoformat()}")
    print("=" * 60)
    baseline = get_baseline_profile()
    if baseline:
        print(f"\nBaseline Profile ID: {baseline[0]}")
    print("\n--- QUERY PATTERNS (7 days) ---")
    query_data = analyze_query_patterns()
    print(f"Total queries: {query_data['total_queries']}")
    print(f"By type: {query_data['query_types']}")
    total = query_data['total_queries'] or 1
    infra = query_data['query_types'].get('infrastructure', 0)
    print(f"Infrastructure ratio: {round(infra/total*100, 1)}%")
    print("\n--- TELEGRAM PATTERNS (7 days) ---")
    tg_data = analyze_telegram_patterns()
    print(f"Total messages: {tg_data['total_messages']}")
    print(f"By intent: {tg_data['intents']}")
    print("\n--- SQUIRREL INDEX ---")
    sq_index = calculate_squirrel_index()
    print(f"Topic switches per 10 messages: {sq_index}")
    if sq_index > 3:
        print("STATUS: High squirreling detected")
    elif sq_index > 1.5:
        print("STATUS: Moderate squirreling")
    else:
        print("STATUS: Focused")
    print("\n--- HYPERFOCUS SESSIONS ---")
    sessions = detect_hyperfocus_sessions()
    print(f"Detected {len(sessions)} hyperfocus sessions")
    for s in sessions[:5]:
        print(f"  - {s['start']}: {s['interactions']} interactions over {s['duration_min']} min")
    print("\n" + "=" * 60)
    return {
        'squirrel_index': sq_index,
        'infrastructure_ratio': round(infra/total*100, 1),
        'hyperfocus_sessions': len(sessions),
        'total_interactions': query_data['total_queries'] + tg_data['total_messages']
    }

if __name__ == '__main__':
    metrics = generate_report()
    continuity = check_behavioral_continuity()
    if continuity['confidence'] < 60:
        print(f"\n⚠️  BEHAVIORAL ANOMALY: Confidence {continuity['confidence']}%")
        for flag in continuity['flags']:
            print(f"   - {flag}")
    else:
        print(f"\n✓ Behavioral continuity: {continuity['confidence']}% confidence")