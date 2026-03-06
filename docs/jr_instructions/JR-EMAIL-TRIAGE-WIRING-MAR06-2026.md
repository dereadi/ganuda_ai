# Jr Instruction: Email Triage Wiring — Gmail Daemon to Deer Scout

**Task**: Wire gmail_api_daemon email classifications to Deer Scout for AI/tech/esoterica curation
**Priority**: 5
**Story Points**: 5
**Epic**: #1958

## Context

The Gmail daemon (`/ganuda/email_daemon/gmail_api_daemon.py`) stores emails in the `emails` table. The Deer Scout (`/ganuda/email_daemon/deer_scout.py`) is supposed to triage actionable emails. We need to wire these together so that new emails get classified and interesting ones get stored as thermal memories for the cluster's curiosity.

The `emails` table has columns: `id`, `message_id`, `from_address`, `subject`, `body_text`, `classification`, `ai_summary`, `deer_scouted`, `thermal_temp`, `action_required`, `metadata`.

## Steps

### Step 1: Add thermal memory storage to deer_scout.py

File: `/ganuda/email_daemon/deer_scout.py`

Find the end of the classification logic and add thermal memory storage for high-value emails:

```
<<<<<<< SEARCH
def main():
=======
def store_thermal(subject, summary, classification, temperature=70):
    """Store interesting email findings as thermal memories."""
    import hashlib
    import re
    DB_HOST = os.environ.get("CHEROKEE_DB_HOST", "192.168.132.222")
    DB_NAME = os.environ.get("CHEROKEE_DB_NAME", "zammad_production")
    DB_USER = os.environ.get("CHEROKEE_DB_USER", "claude")
    DB_PASS = os.environ.get("CHEROKEE_DB_PASS", "")
    if not DB_PASS:
        try:
            with open("/ganuda/config/secrets.env") as f:
                for line in f:
                    m = re.match(r"^(\w+)=(.+)$", line.strip())
                    if m:
                        os.environ[m.group(1)] = m.group(2)
            DB_PASS = os.environ.get("CHEROKEE_DB_PASS", "")
        except FileNotFoundError:
            return

    content = f"EMAIL SCOUT: {subject}\nClassification: {classification}\nSummary: {summary}"
    memory_hash = hashlib.sha256(content.encode()).hexdigest()

    try:
        conn = psycopg2.connect(host=DB_HOST, port=5432, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
        cur = conn.cursor()
        cur.execute("""INSERT INTO thermal_memory_archive
            (original_content, temperature_score, sacred_pattern, memory_hash, domain_tag, tags, metadata)
            VALUES (%s, %s, false, %s, 'deer_scout', %s, %s::jsonb)
            ON CONFLICT (memory_hash) DO NOTHING""",
            (content, temperature, memory_hash,
             ['email', 'deer_scout', classification],
             json.dumps({"source": "deer_scout", "subject": subject})))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logging.getLogger('deer_scout').warning(f"Thermal store failed: {e}")


def main():
>>>>>>> REPLACE
```

### Step 2: Call thermal storage for high-value classifications

This depends on the existing classification logic in deer_scout.py. After emails are classified, add a call like:

File: `/ganuda/email_daemon/deer_scout.py`

After the existing classification update, add thermal storage for interesting emails. Find the line that marks emails as scouted and add before it:

```
<<<<<<< SEARCH
                cur.execute("UPDATE emails SET deer_scouted = true WHERE id = %s", (email_id,))
=======
                # Store high-value emails as thermal memories
                if classification in ('ai_tech', 'business', 'esoterica', 'research') and ai_summary:
                    temp = {'ai_tech': 75, 'business': 70, 'esoterica': 80, 'research': 75}.get(classification, 65)
                    store_thermal(subject, ai_summary, classification, temperature=temp)

                cur.execute("UPDATE emails SET deer_scouted = true WHERE id = %s", (email_id,))
>>>>>>> REPLACE
```

## Verification

1. Import check: `python3 -c "from email_daemon.deer_scout import store_thermal; print('OK')"`
2. Dry run: Check that deer_scout processes unscouted emails without errors
