# JR Instruction: Disagreement Collapse Rate — Behavioral Sycophancy Metric

**Task ID**: DCR-001
**Priority**: 3 (of 10)
**Assigned Jr**: Software Engineer Jr.
**Sacred Fire**: false
**Use RLM**: false
**TEG Plan**: false

## Context

Long Man ADAPT Phase. Council votes: ed5c12c7ab7e9ba7 (research intake), d62ef0627f45f2bd (DELIBERATE, unanimous ADAPT on Paper 2).

Paper: "Peacemaker or Troublemaker: How Sycophancy Shapes Multi-Agent Debate" (arXiv:2509.23055)

Key findings from the paper:
- NAR-SS correlation of 0.902: when agents change their minds, it is overwhelmingly sycophantic capitulation, not genuine reasoning
- 2-3 debate rounds optimal; longer debates DEGRADE accuracy
- Heterogeneous agents + troublemaker tension = best results
- Disagreement Collapse Rate (DCR) measures when correct answers get abandoned through social pressure

We already have Diamond 3 (council_diversity_check.py) which uses cosine similarity between specialist responses. DCR adds a BEHAVIORAL metric — it tracks whether specialists shift positions between votes, and whether that shift correlates with convergence rather than independent reasoning.

Since our council uses single-round voting, DCR for us means: across recent votes on similar topics, are specialists converging to identical positions over time? Are they losing their distinct voices?

## Acceptance Criteria

1. New function `compute_dcr()` in `lib/council_diversity_check.py`
2. DCR computes rolling diversity trend across last N council votes (default 20)
3. Detects "voice drift" — when a specialist's position becomes statistically indistinguishable from another's across multiple votes
4. Returns a DCR report alongside the existing DiversityReport
5. Integrated into the vote() diversity check — runs after the pairwise cosine check
6. Non-blocking: failure does not affect vote outcomes

## Step 1: Add DCR to council_diversity_check.py

File: `lib/council_diversity_check.py`

Add ABOVE the `check_diversity` function:

```python
<<<<<<< SEARCH
def check_diversity(responses, audit_hash: str = "") -> Optional[DiversityReport]:
=======
@dataclass
class DCRReport:
    """Disagreement Collapse Rate — behavioral sycophancy metric.

    Tracks whether specialists are losing distinct voices over time.
    arXiv:2509.23055 (Peacemaker or Troublemaker, Sept 2025).
    """
    dcr_score: float                    # 0.0 = healthy disagreement, 1.0 = total collapse
    drifting_pairs: List[Tuple[str, str, float]]  # pairs converging over time
    vote_window: int                    # how many recent votes were analyzed
    is_healthy: bool                    # True if no pairs drifting


def compute_dcr(window: int = 20) -> Optional[DCRReport]:
    """Compute Disagreement Collapse Rate across recent council votes.

    Looks at the last `window` votes where responses were stored.
    For each specialist pair, computes mean cosine similarity across the window.
    If a pair's mean similarity is INCREASING over the window (regression slope > 0)
    AND their latest similarity exceeds the threshold, they are flagged as drifting.

    This is our adaptation of arXiv:2509.23055's DCR for single-round voting.
    """
    import psycopg2
    import os
    import numpy as np

    try:
        conn = psycopg2.connect(
            host='192.168.132.222',
            database='zammad_production',
            user='claude',
            password=os.environ.get('CHEROKEE_DB_PASS', '')
        )
        cur = conn.cursor()

        # Get recent votes that have stored responses
        cur.execute("""
            SELECT audit_hash, responses
            FROM council_votes
            WHERE responses IS NOT NULL
              AND responses != 'null'
              AND jsonb_array_length(responses) > 1
            ORDER BY voted_at DESC
            LIMIT %s
        """, (window,))
        rows = cur.fetchall()
        conn.close()

        if len(rows) < 5:
            logger.info("[DCR] Not enough votes with responses for DCR analysis")
            return None

        # Extract per-specialist response texts across votes
        # vote_responses[vote_idx] = {specialist_id: response_text}
        vote_responses = []
        for _hash, responses_json in rows:
            if not responses_json:
                continue
            vote_map = {}
            for r in responses_json:
                sid = r.get('specialist_id', r.get('name', ''))
                text = r.get('response', '')
                if sid and text:
                    vote_map[sid] = text
            if vote_map:
                vote_responses.append(vote_map)

        if len(vote_responses) < 5:
            return None

        # Get all specialist IDs that appear in at least half the votes
        from collections import Counter
        all_sids = Counter()
        for vm in vote_responses:
            for sid in vm:
                all_sids[sid] += 1
        threshold = len(vote_responses) // 2
        active_sids = [sid for sid, count in all_sids.items() if count >= threshold]

        if len(active_sids) < 2:
            return None

        # For each pair, compute similarity per vote and check for upward trend
        drifting = []
        pair_scores = []

        for i, sid_a in enumerate(active_sids):
            for sid_b in active_sids[i+1:]:
                # Collect per-vote similarities for this pair
                pair_sims = []
                for vm in vote_responses:
                    if sid_a in vm and sid_b in vm:
                        # Simple word overlap as a fast proxy (no embedding call needed)
                        words_a = set(vm[sid_a].lower().split())
                        words_b = set(vm[sid_b].lower().split())
                        if words_a and words_b:
                            jaccard = len(words_a & words_b) / len(words_a | words_b)
                            pair_sims.append(jaccard)

                if len(pair_sims) < 5:
                    continue

                mean_sim = sum(pair_sims) / len(pair_sims)
                pair_scores.append(mean_sim)

                # Check for upward trend (linear regression slope)
                n = len(pair_sims)
                x_mean = (n - 1) / 2
                y_mean = mean_sim
                numerator = sum((i - x_mean) * (s - y_mean) for i, s in enumerate(pair_sims))
                denominator = sum((i - x_mean) ** 2 for i in range(n))
                slope = numerator / denominator if denominator > 0 else 0

                # Flag if trending upward AND recent similarity is high
                recent_sim = sum(pair_sims[:3]) / 3  # most recent 3 votes
                if slope > 0.01 and recent_sim > 0.4:
                    drifting.append((sid_a, sid_b, round(recent_sim, 4)))

        # DCR score: proportion of pairs that are drifting
        total_pairs = len(active_sids) * (len(active_sids) - 1) // 2
        dcr_score = len(drifting) / total_pairs if total_pairs > 0 else 0.0

        report = DCRReport(
            dcr_score=round(dcr_score, 4),
            drifting_pairs=drifting,
            vote_window=len(vote_responses),
            is_healthy=len(drifting) == 0,
        )

        if drifting:
            pair_names = ", ".join(f"{a}+{b} ({s})" for a, b, s in drifting)
            logger.warning(
                f"[DCR] {len(drifting)} drifting pair(s) across {len(vote_responses)} votes: "
                f"{pair_names}. DCR score: {dcr_score:.3f}"
            )
        else:
            logger.info(
                f"[DCR] Healthy — no voice drift across {len(vote_responses)} votes. "
                f"DCR score: {dcr_score:.3f}"
            )

        return report

    except Exception as e:
        logger.warning(f"[DCR] Computation failed (non-fatal): {e}")
        return None


def check_diversity(responses, audit_hash: str = "") -> Optional[DiversityReport]:
>>>>>>> REPLACE
```

## Step 2: Wire DCR into specialist_council.py diversity check

File: `lib/specialist_council.py`

Find the existing diversity check block (added in Diamond 3) and add DCR after it:

```python
<<<<<<< SEARCH
        except Exception as e:
            print(f"[COUNCIL] Diversity check skipped: {e}")

        # Log to database
=======
        except Exception as e:
            print(f"[COUNCIL] Diversity check skipped: {e}")

        # DCR behavioral sycophancy check (arXiv:2509.23055, Long Man ADAPT March 2 2026)
        try:
            from lib.council_diversity_check import compute_dcr
            dcr = compute_dcr(window=20)
            if dcr:
                print(f"[COUNCIL] DCR: {dcr.dcr_score:.3f} "
                      f"({'HEALTHY' if dcr.is_healthy else f'{len(dcr.drifting_pairs)} DRIFTING PAIRS'}) "
                      f"over {dcr.vote_window} votes")
        except Exception as e:
            print(f"[COUNCIL] DCR check skipped: {e}")

        # Log to database
>>>>>>> REPLACE
```

## What NOT To Change

- Do NOT modify the existing check_diversity() function
- Do NOT block the vote on DCR failure — this is advisory, non-blocking
- Do NOT change specialist prompts based on DCR (future work)
- Do NOT use embedding calls for DCR — Jaccard word overlap is fast and sufficient for trend detection

## Verification

1. Import check: `python3 -c "from lib.council_diversity_check import compute_dcr, DCRReport; print('OK')"`
2. Run DCR standalone: `python3 -c "from lib.council_diversity_check import compute_dcr; r = compute_dcr(); print(r)"`
3. Run a council vote and check for `[COUNCIL] DCR:` in the output
4. If fewer than 5 votes have stored responses, DCR returns None (expected for now)

## Notes for Jr

- DCR uses Jaccard word overlap, NOT cosine similarity of embeddings. This is intentional — it avoids the greenfin embedding call (which has been returning 404) and is fast enough for trend detection.
- The function queries council_votes.responses JSONB directly. Votes that did not store responses (include_responses=False) are skipped.
- The slope threshold (0.01) and similarity threshold (0.4) are initial values — these should be tuned after we have 50+ votes with stored responses.
- The `numpy` import in the function is defensive — it is NOT actually used in this implementation. Remove if executor complains about missing module.
- DCR is a TREND metric (are voices converging over time?). Diversity check is a POINT metric (are voices similar right now?). Both are needed.

## Future Work (NOT in this instruction)

- When DCR flags drifting pairs, automatically adjust specialist prompt temperature
- Track per-specialist DCR over time (is Gecko always echoing Spider?)
- Dashboard in OpenObserve showing DCR trend line
- If DCR > 0.5 for 5 consecutive votes, trigger Longhouse session
- Wire DCR into dawn mist standup
