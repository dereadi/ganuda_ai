# Jr Instruction: Phase 0 — Memory Retrieval Logging

**Kanban**: #1813
**Priority**: 9 (Phase 0 — foundation for all subsequent phases)
**Assigned Jr**: Software Engineer Jr.
**use_rlm**: false
**Sprint**: RC-2026-02E

## Context

The `thermal_memory_archive` table already has `access_count` (integer) and `last_access` (timestamp) columns, but only 113 of 88,065 memories have `access_count > 0`. The main retrieval paths — `specialist_council.py`, `tribe_memory_search.py` — do NOT increment these counters.

We need retrieval logging as the foundation for the Human Memory Architecture project (#1813). Without knowing how often each memory is accessed, we cannot build reliability inversion or contamination detection.

IMPORTANT: This is purely ADDITIVE logging. Do NOT change retrieval behavior, query logic, or result formatting.

## Step 1: Add retrieval logging to semantic search in specialist_council.py

File: `/ganuda/lib/specialist_council.py`

<<<<<<< SEARCH
        rows = cur.fetchall()
        conn.close()

        if not rows:
            return _keyword_fallback(question, limit)
=======
        rows = cur.fetchall()

        # Phase 0: Log retrieval access for reconsolidation tracking (#1813)
        if rows:
            mem_ids = [r[0] for r in rows]
            cur.execute("""
                UPDATE thermal_memory_archive
                SET access_count = COALESCE(access_count, 0) + 1,
                    last_access = NOW()
                WHERE id = ANY(%s)
            """, (mem_ids,))
            conn.commit()

        conn.close()

        if not rows:
            return _keyword_fallback(question, limit)
>>>>>>> REPLACE

## Step 2: Add retrieval logging to keyword fallback in specialist_council.py

File: `/ganuda/lib/specialist_council.py`

<<<<<<< SEARCH
        rows = cur.fetchall()
        conn.close()

        if not rows:
            return ""

        context_parts = ["RELEVANT THERMAL MEMORIES (keyword retrieval):"]
=======
        rows = cur.fetchall()

        # Phase 0: Log retrieval access for reconsolidation tracking (#1813)
        if rows:
            mem_ids = [r[0] for r in rows]
            cur.execute("""
                UPDATE thermal_memory_archive
                SET access_count = COALESCE(access_count, 0) + 1,
                    last_access = NOW()
                WHERE id = ANY(%s)
            """, (mem_ids,))
            conn.commit()

        conn.close()

        if not rows:
            return ""

        context_parts = ["RELEVANT THERMAL MEMORIES (keyword retrieval):"]
>>>>>>> REPLACE

## Step 3: Add retrieval logging to tribe_memory_search.py semantic search

File: `/ganuda/telegram_bot/tribe_memory_search.py`

<<<<<<< SEARCH
        cur.close()
        conn.close()
        return results
    except Exception as e:
        logger.error("Semantic search failed: %s", e)
        return text_search(query, limit)
=======
        # Phase 0: Log retrieval access for reconsolidation tracking (#1813)
        if results:
            mem_ids = [r["id"] for r in results]
            with conn.cursor() as ucur:
                ucur.execute("""
                    UPDATE thermal_memory_archive
                    SET access_count = COALESCE(access_count, 0) + 1,
                        last_access = NOW()
                    WHERE id = ANY(%s)
                """, (mem_ids,))
            conn.commit()

        cur.close()
        conn.close()
        return results
    except Exception as e:
        logger.error("Semantic search failed: %s", e)
        return text_search(query, limit)
>>>>>>> REPLACE

## Step 4: Add retrieval logging to tribe_memory_search.py text search

File: `/ganuda/telegram_bot/tribe_memory_search.py`

Find the second occurrence of `cur.close()` / `conn.close()` / `return results` pattern in the text_search function and add the same logging block before it.

<<<<<<< SEARCH
        cur.close()
        conn.close()
        return results
    except Exception as e:
        logger.error("Text search failed: %s", e)
        return []
=======
        # Phase 0: Log retrieval access for reconsolidation tracking (#1813)
        if results:
            mem_ids = [r["id"] for r in results]
            with conn.cursor() as ucur:
                ucur.execute("""
                    UPDATE thermal_memory_archive
                    SET access_count = COALESCE(access_count, 0) + 1,
                        last_access = NOW()
                    WHERE id = ANY(%s)
                """, (mem_ids,))
            conn.commit()

        cur.close()
        conn.close()
        return results
    except Exception as e:
        logger.error("Text search failed: %s", e)
        return []
>>>>>>> REPLACE

## Verification

After deployment, run a test query through the council gateway:

```text
curl -s http://192.168.132.223:8080/v1/council/vote -H "Content-Type: application/json" -H "Authorization: Bearer ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5" -d '{"question": "What is the current state of thermal memory?", "context": "Phase 0 retrieval logging test"}'
```

Then verify access_count was incremented:

```text
PGPASSWORD='TYDo5U2NVkXqQ8DHuhIpvRgLUrXf2iZE' psql -h 192.168.132.222 -U claude -d zammad_production -c "SELECT COUNT(*) FROM thermal_memory_archive WHERE last_access > NOW() - INTERVAL '5 minutes';"
```

Should return > 0 rows with updated access_count.

## Notes

- COALESCE handles NULL access_count (most rows currently NULL, not 0)
- commit() before close() ensures the UPDATE persists
- The UPDATE uses ANY(%s) for batch efficiency — one UPDATE for all retrieved memories
- This adds ~1ms per retrieval (single UPDATE with index on id)
- Does NOT change retrieval behavior — purely additive logging
- Does NOT create false memories or modify content — only increments counters
