#!/usr/bin/env python3
"""Add priority column to epigenetic_modifiers for conflict resolution.

Council concern (Coyote #df0c89c9): When high_load (factor 0.5) and
research_mode (factor 2.0) both target the same specialist, which wins?
Higher priority wins. Default priority = 10.

Also fixes target mismatch: seed data has 'crawdad_scan' but specialist
ID is 'crawdad'. Updates to match.
"""
import os
import psycopg2

conn = psycopg2.connect(
    host="192.168.132.222", port=5432, dbname="zammad_production",
    user="claude", password=os.environ.get("CHEROKEE_DB_PASS", "")
)
cur = conn.cursor()

# Add priority column (higher = wins conflict)
cur.execute("""
    ALTER TABLE epigenetic_modifiers
    ADD COLUMN IF NOT EXISTS priority INTEGER DEFAULT 10
""")

# Set priorities: security > high_load > research > night
cur.execute("UPDATE epigenetic_modifiers SET priority = 90 WHERE condition_name = 'security_incident'")
cur.execute("UPDATE epigenetic_modifiers SET priority = 70 WHERE condition_name = 'high_load'")
cur.execute("UPDATE epigenetic_modifiers SET priority = 30 WHERE condition_name = 'research_mode'")
cur.execute("UPDATE epigenetic_modifiers SET priority = 20 WHERE condition_name = 'night_mode'")

# Fix target mismatch: 'crawdad_scan' -> 'crawdad' (matches SPECIALISTS dict key)
cur.execute("""
    UPDATE epigenetic_modifiers
    SET target = 'crawdad'
    WHERE target = 'crawdad_scan'
""")

conn.commit()
print(f"Migration complete. {cur.rowcount} rows updated.")

# Verify
cur.execute("SELECT condition_name, target, modifier_type, priority FROM epigenetic_modifiers ORDER BY priority DESC, condition_name")
for r in cur.fetchall():
    print(f"  {r[0]:20s} {r[1]:15s} {r[2]:10s} priority={r[3]}")

conn.close()