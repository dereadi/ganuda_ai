# [RECURSIVE] DC-16 Phase 1: Database Reflex Layer — Drop Indexes, Tune Autovacuum, Retention Policies, Fix Fire Guard - Step 14

**Parent Task**: #1288
**Auto-decomposed**: 2026-03-12T17:58:55.938806
**Original Step Title**: Fix Fire Guard false positive — replace TCP socket check with psycopg2 for PostgreSQL

---

### Step 14: Fix Fire Guard false positive — replace TCP socket check with psycopg2 for PostgreSQL

The issue: Fire Guard uses `check_port(ip, 5432)` via TCP socket to check bluefin PostgreSQL.
The socket check sometimes returns false (connection refused or timeout) while psycopg2 connects
and queries fine. Replace with a real DB connection test for the PostgreSQL entry only.

Add a `check_postgres_db` function after the existing `check_port` function, then update
the bluefin REMOTE_CHECKS entry to use `"PostgreSQL-DB"` as a signal for the new check path.

**File:** `/ganuda/scripts/fire_guard.py`

```python
def check_postgres_db(host, port=5432, timeout=5):
    """Check PostgreSQL by actually connecting, not just TCP socket.

    Eliminates false-positive alerts where socket check fails but DB is up.
    DC-16 Phase 1 fix.
    """
    import psycopg2
    try:
        conn = psycopg2.connect(
            host=host, port=port,
            dbname=os.environ.get("CHEROKEE_DB_NAME", "zammad_production"),
            user=os.environ.get("CHEROKEE_DB_USER", "claude"),
            password=os.environ.get("CHEROKEE_DB_PASS", ""),
            connect_timeout=timeout
        )
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        return True
    except Exception:
        return False
```
