# [RECURSIVE] Diamond 3: Sycophancy Detection — Council Diversity Monitor - Step 1

**Parent Task**: #959
**Auto-decomposed**: 2026-03-01T08:01:53.217998
**Original Step Title**: Add diversity check after vote creation (after the CouncilVote construction, around line 1109)

---

### Step 1: Add diversity check after vote creation (after the CouncilVote construction, around line 1109)

```python
<<<<<<< SEARCH
        # Log to database
=======
        # Run diversity check (non-blocking — failure does not affect vote)
        try:
            from lib.council_diversity_check import check_diversity
            diversity = check_diversity(responses, audit_hash)
            if diversity:
                print(f"[COUNCIL] Diversity: {diversity.overall_diversity:.3f} "
                      f"({'HEALTHY' if diversity.is_healthy else f'{len(diversity.flagged_pairs)} FLAGGED PAIRS'})")
        except Exception as e:
            print(f"[COUNCIL] Diversity check skipped: {e}")

        # Log to database
>>>>>>> REPLACE
```

**NOTE**: If "# Log to database" does not exist verbatim at that location, search for the next code block after the `CouncilVote(...)` construction and the sacred dissent thermal write (from GHIGAU-001). The diversity check goes AFTER the vote object is created but BEFORE database logging.

## What NOT To Change

- Do NOT modify the embedding service on greenfin
- Do NOT block the vote on diversity check failure — this is advisory, non-blocking
- Do NOT modify specialist prompts based on diversity scores (that's a future step)
- Do NOT modify drift_detection.py

## Verification

1. Import check: `python3 -c "from lib.council_diversity_check import check_diversity, DiversityReport; print('OK')"`
2. Test embedding connectivity: `python3 -c "from lib.council_diversity_check import _get_embeddings; r = _get_embeddings(['test one', 'test two']); print(f'{len(r)} embeddings, {len(r[0])}d')"`
3. Run a council vote and check for `[COUNCIL] Diversity:` in the output
4. Check thermal alerts: `SELECT * FROM thermal_memory_archive WHERE metadata->>'type' = 'diversity_alert' ORDER BY id DESC LIMIT 5;`

## Future Work (NOT in this instruction)

- Automated prompt differentiation when diversity stays low across N votes
- Per-specialist diversity trend tracking (is Crawdad consistently echoing Gecko?)
- Integration with drift_detection circuit breakers
- Dashboard in OpenObserve showing diversity over time

## References

- CONSENSAGENT (Virginia Tech, ACL 2025 Findings) — sycophancy detection
- Free-MAD (arXiv:2509.11035) — anti-conformity mechanisms
- Existing diagnostic: /ganuda/scripts/council_diversity_diagnostic.py
- Embedding service: greenfin:8003 (BGE-large-en-v1.5, 1024d)
