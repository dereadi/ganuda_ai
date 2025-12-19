# JR INSTRUCTIONS: Fix Cascaded Vote Database Save
## JR-BUGFIX-CASCADED-DB-SAVE-DEC17-2025
## December 17, 2025

### OBJECTIVE
Fix the database save error in cascaded council vote where concerns array isn't being serialized properly.

---

## BUG DESCRIPTION

**File:** /ganuda/services/llm_gateway/gateway.py

**Error Message:**
```
[DB ERROR] Failed to save cascaded vote: can't adapt type 'dict'
```

**Cause:** The `concerns` parameter is being passed as a Python list of dicts instead of JSON string.

---

## TASK 1: Fix the cascaded vote DB insert

**File:** /ganuda/services/llm_gateway/gateway.py

**Find this code block (around line 350-380):**
```python
        # Save to database with cascaded mode flag
        audit_hash = hashlib.sha256(f"{time.time()}|{request.question}".encode()).hexdigest()[:16]
        try:
            with get_db() as conn:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO council_votes
                    (audit_hash, question, consensus, confidence, concerns, vote_mode, stages_completed, blocked_by)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    audit_hash,
                    request.question,
                    result.get('consensus', ''),
                    result.get('confidence', 0),
                    result.get('votes', []),
                    'cascaded',
                    result.get('stages_completed'),
                    result.get('blocked_by')
                ))
                conn.commit()
        except Exception as e:
            print(f"[DB ERROR] Failed to save cascaded vote: {e}")
```

**Replace with:**
```python
        # Save to database with cascaded mode flag
        audit_hash = hashlib.sha256(f"{time.time()}|{request.question}".encode()).hexdigest()[:16]
        try:
            with get_db() as conn:
                cur = conn.cursor()
                # Serialize votes list to JSON for JSONB column
                import json
                votes_json = json.dumps(result.get('votes', []))
                cur.execute("""
                    INSERT INTO council_votes
                    (audit_hash, question, consensus, confidence, concerns, vote_mode, stages_completed, blocked_by)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    audit_hash,
                    request.question,
                    result.get('consensus', ''),
                    result.get('confidence', 0),
                    votes_json,
                    'cascaded',
                    result.get('stages_completed'),
                    result.get('blocked_by')
                ))
                conn.commit()
        except Exception as e:
            print(f"[DB ERROR] Failed to save cascaded vote: {e}")
```

---

## Verification

```bash
cd /ganuda/services/llm_gateway && grep -A5 "votes_json = json.dumps" gateway.py && echo "Fix applied"
```

---

## SUCCESS CRITERIA

1. Cascaded votes save to database without error
2. `SELECT * FROM council_votes WHERE vote_mode = 'cascaded'` returns rows

---

*Jr Instructions issued: December 17, 2025*
*For Seven Generations - Cherokee AI Federation*
