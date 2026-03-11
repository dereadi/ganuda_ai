# [RECURSIVE] Wire Slack into Fire Guard alerts - Step 2

**Parent Task**: #1154
**Auto-decomposed**: 2026-03-09T14:11:59.252788
**Original Step Title**: Add Slack notification in store_alerts function, after thermal memory write

---

### Step 2: Add Slack notification in store_alerts function, after thermal memory write

<<<<<<< SEARCH
    cur.execute("""INSERT INTO thermal_memory_archive
        (original_content, temperature_score, sacred_pattern, memory_hash, domain_tag, tags, metadata)
        VALUES (%s, 85, false, %s, 'fire_guard', %s, %s::jsonb)
        ON CONFLICT (memory_hash) DO NOTHING""",
        (content, memory_hash,
         ['fire_guard', 'alert', 'health'],
         json.dumps({"source": "fire_guard", "alerts": results["alerts"]})))
    conn.commit()
    cur.close()
    conn.close()
=======
    cur.execute("""INSERT INTO thermal_memory_archive
        (original_content, temperature_score, sacred_pattern, memory_hash, domain_tag, tags, metadata)
        VALUES (%s, 85, false, %s, 'fire_guard', %s, %s::jsonb)
        ON CONFLICT (memory_hash) DO NOTHING""",
        (content, memory_hash,
         ['fire_guard', 'alert', 'health'],
         json.dumps({"source": "fire_guard", "alerts": results["alerts"]})))
    conn.commit()
    cur.close()
    conn.close()

    # Slack notification — terse, real numbers, urgent bypass for silent hours
    try:
        from slack_federation import notify_fire_guard
        alert_count = len(results["alerts"])
        slack_msg = f"{alert_count} ALERT(S): " + "; ".join(results["alerts"])
        notify_fire_guard(slack_msg, urgent=True)
    except Exception as e:
        # Slack is best-effort — never let it break Fire Guard
        import logging
        logging.getLogger("fire_guard").warning("Slack notify failed: %s", e)
>>>>>>> REPLACE

## Verification

After applying, run:
```text
python3 /ganuda/scripts/fire_guard.py
```

If there are active alerts, they should appear in #fire-guard on Slack.
If all services are healthy, no Slack message is sent (by design — no noise).
