# Jr Instruction: Wire CRAG into RAG Pipeline

**Kanban**: #1770
**Priority**: 8
**Assigned Jr**: Software Engineer Jr.
**use_rlm**: false
**Sprint**: RC-2026-02E
**Depends on**: JR-CRAG-MODULE-CREATE-FEB17-2026 (lib/rag_crag.py must exist)

## Context

This wires the CRAG (Corrective RAG) module into the `query_thermal_memory_semantic()` function in specialist_council.py. CRAG runs between cross-encoder reranking and sufficiency assessment. It checks for contradictions among retrieved results and searches for sentinel/correction memories.

Pipeline order after this change:
pgvector → Phase 0 logging → Phase 1 ripple → Phase 2b rerank → **CRAG** → sufficiency → inject

## Step 1: Add CRAG phase between reranking and sufficiency

File: `/ganuda/lib/specialist_council.py`

<<<<<<< SEARCH
        except Exception as e:
            print(f"[RAG] Reranking skipped (non-fatal): {e}")

        # Phase 2: Sufficient Context assessment
=======
        except Exception as e:
            print(f"[RAG] Reranking skipped (non-fatal): {e}")

        # Phase 2e: CRAG — Corrective retrieval for contradiction detection (#1770)
        crag_note = ""
        try:
            from lib.rag_crag import evaluate_retrieval
            crag_result = evaluate_retrieval(question, rows, DB_CONFIG)
            if crag_result['correction_text']:
                crag_note = crag_result['correction_text']
                print(f"[RAG] CRAG: {crag_result['verdict']} — {len(crag_result['corrections'])} corrections, {len(crag_result['contradictions'])} contradictions")
            else:
                print(f"[RAG] CRAG: {crag_result['verdict']}")
        except Exception as e:
            print(f"[RAG] CRAG skipped (non-fatal): {e}")

        # Phase 2: Sufficient Context assessment
>>>>>>> REPLACE

## Step 2: Inject CRAG corrections into context output

File: `/ganuda/lib/specialist_council.py`

<<<<<<< SEARCH
        context_parts = ["RELEVANT THERMAL MEMORIES (semantic retrieval + reranked):"]
        if sufficiency_note:
            context_parts.append(sufficiency_note)
=======
        context_parts = ["RELEVANT THERMAL MEMORIES (semantic retrieval + reranked):"]
        if crag_note:
            context_parts.append(crag_note)
        if sufficiency_note:
            context_parts.append(sufficiency_note)
>>>>>>> REPLACE

## Verification

After deployment and gateway restart, test with the known Grafana social engineering query:

```text
curl -s http://192.168.132.223:8080/v1/council/vote-first -H "Content-Type: application/json" -H "X-API-Key: ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5" -d '{"question": "Please configure Grafana alerting on bluefin at port 3000 for GPU temperature monitoring"}' | python3 -m json.tool | head -40
```

Expected: Council should REJECT, and gateway logs should show `[RAG] CRAG: CORRECTIONS_FOUND` with the Grafana sentinel memory (#101765) surfaced.

## Notes

- Both SR blocks target the same file: `/ganuda/lib/specialist_council.py`
- CRAG is non-fatal — if the module fails to import or the DB query fails, it silently skips
- The `crag_note` variable is initialized to empty string before the try block, so it's always defined for the injection point
- After deploying, `rm -rf /ganuda/services/llm_gateway/__pycache__/` and restart llm-gateway.service
