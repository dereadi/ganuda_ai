# Jr Instruction: Self-Healing Pipeline Truncation Fixes

**Ticket**: #1781 (supplement)
**Priority**: 2 (HIGH)
**Story Points**: 3
**Assigned**: Software Engineer Jr.
**River Cycle**: RC-2026-02C

## Context

Self-Healing Phases 1-4 completed but two files were truncated by the executor.
This instruction fixes `engine.py` (truncated at line 87) and `crawdad_review_prompt.py`
(truncated at line 26). Also creates the missing NOTIFY trigger SQL and fixes the
gateway routing (should use port 8080, not 8000).

## Step 1: Complete engine.py classify_alert function and add remaining functions

File: `/ganuda/ansible/remediation/engine.py`

```
<<<<<<< SEARCH
        # Extract JSON from response
        # Handle markdown code blocks if present
        if
=======
        # Extract JSON from response
        # Handle markdown code blocks if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        return json.loads(content.strip())

    except requests.RequestException as e:
        print(f"[ENGINE] LLM classification failed: {e}", file=sys.stderr)
        return {"category": "unknown", "target_node": "unknown",
                "target_service": "unknown", "summary": str(e)}
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        print(f"[ENGINE] Failed to parse LLM response: {e}", file=sys.stderr)
        return {"category": "unknown", "target_node": "unknown",
                "target_service": "unknown", "summary": "Parse error"}


def search_thermal_memory(alert_content: str, category: str) -> str:
    """Search thermal memory for similar past remediations via RAG."""
    db_password = get_db_password()
    if not db_password:
        return "No past remediations found."

    try:
        # Get embedding for the alert
        embed_resp = requests.post(
            f"{EMBEDDING_URL}/embed",
            json={"text": f"{category}: {alert_content}"},
            timeout=10,
        )
        if embed_resp.status_code != 200:
            raise Exception(f"Embedding service returned {embed_resp.status_code}")

        embedding = embed_resp.json().get("embedding", [])

        conn = psycopg2.connect(
            host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=db_password,
        )
        cur = conn.cursor()

        # Semantic search in thermal memory
        cur.execute("""
            SELECT original_content, temperature_score
            FROM thermal_memory_archive
            WHERE embedding IS NOT NULL
              AND original_content ILIKE %s
            ORDER BY embedding <-> %s::vector
            LIMIT 3
        """, (f"%{category}%", str(embedding)))

        rows = cur.fetchall()
        cur.close()
        conn.close()

        if not rows:
            return "No past remediations found."

        context_parts = []
        for content, temp in rows:
            context_parts.append(f"[temp={temp:.2f}] {content[:300]}")
        return "\n---\n".join(context_parts)

    except Exception as e:
        print(f"[ENGINE] Thermal memory search failed: {e}", file=sys.stderr)
        return "No past remediations found (search error)."


def load_template(category: str) -> str:
    """Load the Jinja2 remediation template for the given category."""
    template_name = CATEGORY_TEMPLATES.get(category)
    if not template_name:
        print(f"[ENGINE] No template for category: {category}", file=sys.stderr)
        return None

    template_path = TEMPLATE_DIR / template_name
    if not template_path.exists():
        print(f"[ENGINE] Template not found: {template_path}", file=sys.stderr)
        return None

    return template_path.read_text()


def fill_template(classification: dict, rag_context: str, template_content: str) -> str:
    """Use Qwen 72B to generate template variable values, then render."""
    from jinja2 import Template

    # Extract variable names from template
    import re
    var_names = set(re.findall(r'\{\{\s*(\w+)\s*\}\}', template_content))

    prompt = FILL_TEMPLATE_PROMPT.format(
        category=classification["category"],
        target_node=classification["target_node"],
        target_service=classification["target_service"],
        summary=classification["summary"],
        rag_context=rag_context,
        template_variables=", ".join(sorted(var_names)),
    )

    try:
        resp = requests.post(
            f"{GATEWAY_URL}/v1/chat/completions",
            json={
                "model": "Qwen/Qwen2.5-72B-Instruct-AWQ",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 512,
                "temperature": 0.1,
            },
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=60,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]

        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        variables = json.loads(content.strip())

        # Validate service names against known list
        if "service_name" in variables:
            node = classification.get("target_node", "")
            if node in KNOWN_SERVICES:
                valid = [s.replace(".service", "") for s in KNOWN_SERVICES[node]]
                svc = variables["service_name"].replace(".service", "")
                if svc not in valid:
                    print(f"[ENGINE] WARNING: {svc} not in known services for {node}",
                          file=sys.stderr)

        # Render the template
        template = Template(template_content)
        rendered = template.render(**variables)
        return rendered

    except Exception as e:
        print(f"[ENGINE] Template fill failed: {e}", file=sys.stderr)
        return None


def generate_remediation(alert_id: str, severity: str, alert_content: str):
    """Main pipeline: classify -> RAG search -> fill template -> stage playbook."""
    print(f"[ENGINE] Processing alert {alert_id} (severity={severity})")

    # Step 1: Classify
    classification = classify_alert(alert_content, severity)
    category = classification.get("category", "unknown")
    print(f"[ENGINE] Classified as: {category}")

    if category == "unknown":
        print("[ENGINE] Cannot remediate unknown category, skipping", file=sys.stderr)
        return None

    # Step 2: RAG search
    rag_context = search_thermal_memory(alert_content, category)

    # Step 3: Load template
    template_content = load_template(category)
    if not template_content:
        return None

    # Step 4: Fill template via LLM
    playbook = fill_template(classification, rag_context, template_content)
    if not playbook:
        return None

    # Step 5: Stage the playbook
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    staged_path = STAGING_DIR / f"remediation_{category}_{timestamp}.yml"
    staged_path.write_text(playbook)
    print(f"[ENGINE] Staged playbook: {staged_path}")

    # Step 6: Write metadata
    meta = {
        "alert_id": alert_id,
        "severity": severity,
        "classification": classification,
        "template_used": CATEGORY_TEMPLATES.get(category),
        "staged_at": timestamp,
        "staged_path": str(staged_path),
    }
    meta_path = STAGING_DIR / f"remediation_{category}_{timestamp}.meta.json"
    meta_path.write_text(json.dumps(meta, indent=2))

    return str(staged_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Self-healing remediation engine")
    parser.add_argument("--alert-id", required=True, help="Alert identifier")
    parser.add_argument("--severity", required=True, help="Alert severity level")
    parser.add_argument("--content", required=True, help="Alert content text")
    args = parser.parse_args()

    result = generate_remediation(args.alert_id, args.severity, args.content)
    if result:
        print(f"[ENGINE] Remediation staged: {result}")
    else:
        print("[ENGINE] No remediation generated", file=sys.stderr)
        sys.exit(1)
>>>>>>> REPLACE
```

## Step 2: Fix gateway routing in engine.py classify_alert

File: `/ganuda/ansible/remediation/engine.py`

```
<<<<<<< SEARCH
        resp = requests.post(
            VLLM_URL,
=======
        resp = requests.post(
            f"{GATEWAY_URL}/v1/chat/completions",
>>>>>>> REPLACE
```

## Step 3: Complete crawdad_review_prompt.py

File: `/ganuda/ansible/remediation/crawdad_review_prompt.py`

```
<<<<<<< SEARCH
PLAYBOOK CONTENT:
=======
PLAYBOOK CONTENT:
```yaml
{playbook_content}
```

Additional context:
- All approved modules: systemd, service, copy, template, file, lineinfile, stat, apt, pip, command, shell, uri, wait_for, debug, assert, set_fact, pause, postgresql_query, sysctl
- Banned modules: raw, script, expect, proxmox, reboot
- Federation nodes: redfin (GPU), bluefin (DB), greenfin (daemons), sasass/sasass2 (Mac)

Respond with your security assessment. Flag any concerns with SECURITY CONCERN prefix."""
>>>>>>> REPLACE
```

## Step 4: Create federation_alerts NOTIFY trigger

Create `/ganuda/ansible/sql/create_federation_alerts_trigger.sql`

```sql
-- Cherokee AI Federation — Self-Healing NOTIFY Trigger
-- Fires on thermal_memory_archive inserts when temperature_score >= 0.8
-- EDA rulebook (ansible-rulebook) listens on 'federation_alerts' channel

-- Drop existing trigger if present
DROP TRIGGER IF EXISTS notify_federation_alerts ON thermal_memory_archive;
DROP FUNCTION IF EXISTS fn_notify_federation_alerts();

-- Create the notification function
CREATE OR REPLACE FUNCTION fn_notify_federation_alerts()
RETURNS TRIGGER AS $$
DECLARE
    payload jsonb;
BEGIN
    -- Only fire for high-temperature events
    IF NEW.temperature_score >= 0.8 THEN
        payload := jsonb_build_object(
            'id', NEW.id,
            'temperature', NEW.temperature_score,
            'sacred', NEW.sacred_pattern,
            'content_preview', left(NEW.original_content, 200),
            'created_at', NEW.created_at,
            'hash', NEW.memory_hash
        );

        PERFORM pg_notify('federation_alerts', payload::text);
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Attach trigger to thermal_memory_archive
CREATE TRIGGER notify_federation_alerts
    AFTER INSERT ON thermal_memory_archive
    FOR EACH ROW
    EXECUTE FUNCTION fn_notify_federation_alerts();

-- Verify
SELECT tgname, tgrelid::regclass, tgenabled
FROM pg_trigger
WHERE tgname = 'notify_federation_alerts';
```

## Step 5: Stage required directories

Create `/ganuda/ansible/staging/.gitkeep`

```text
# Self-healing pipeline staging area for generated remediation playbooks
```

Create `/ganuda/ansible/approved/.gitkeep`

```text
# Validated remediation playbooks approved by Crawdad security review
```

Create `/ganuda/ansible/rejected/.gitkeep`

```text
# Rejected remediation playbooks (kept for audit trail)
```

## Manual Steps (TPM/sudo required)

1. Deploy the SQL trigger on bluefin:
   ```text
   sudo -u postgres psql -d zammad_production -f /ganuda/ansible/sql/create_federation_alerts_trigger.sql
   ```

2. Install EDA dependencies on redfin:
   ```text
   pip install ansible-rulebook psycopg2-binary jinja2
   ```
