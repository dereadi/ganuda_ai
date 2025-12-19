#!/usr/bin/env python3
"""
Add /api/tribe/council-votes endpoint to SAG UI
Run on redfin to add the endpoint to app.py
"""

import shutil
from datetime import datetime

APP_FILE = "/ganuda/home/dereadi/sag_unified_interface/app.py"

COUNCIL_VOTES_ENDPOINT = '''
@app.route("/api/tribe/council-votes")
def api_tribe_council_votes():
    """Get recent council votes for Tribe dashboard"""
    import psycopg2
    import psycopg2.extras
    try:
        limit = request.args.get("limit", 20, type=int)

        conn = psycopg2.connect(**event_manager.db_config)
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute("""
            SELECT
                vote_id,
                audit_hash,
                LEFT(question, 200) as question,
                recommendation,
                confidence,
                concern_count,
                concerns,
                tpm_vote,
                voted_at as timestamp,
                vote_finalized
            FROM council_votes
            ORDER BY voted_at DESC
            LIMIT %s
        """, (limit,))

        votes = cur.fetchall()
        cur.close()
        conn.close()

        return jsonify({
            "votes": votes,
            "count": len(votes),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        app.logger.error(f"Error in api_tribe_council_votes: {e}")
        return jsonify({"votes": [], "error": str(e)})

'''

def main():
    # Backup
    backup_path = f"{APP_FILE}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy(APP_FILE, backup_path)
    print(f"Backup created: {backup_path}")

    with open(APP_FILE, 'r') as f:
        content = f.read()

    # Check if endpoint already exists
    if '@app.route("/api/tribe/council-votes")' in content:
        print("Council-votes endpoint already exists, skipping")
        return

    # Find the main block to insert before (unique marker)
    marker = "if __name__ == '__main__':"

    if marker not in content:
        print(f"Error: Could not find marker '{marker}' in app.py")
        return

    # Insert before the main block
    content = content.replace(marker, COUNCIL_VOTES_ENDPOINT + "\n" + marker, 1)

    with open(APP_FILE, 'w') as f:
        f.write(content)

    print("Added /api/tribe/council-votes endpoint successfully!")

if __name__ == "__main__":
    main()
