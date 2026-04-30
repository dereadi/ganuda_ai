"""
Conway-Smith Phase 1 — power-law fit on Council deliberation cost vs recurrence.

Council vote: 8762850ef4b652c7
Companion ticket: duyuktv #2165

Reads council_votes + vote_recurrence_links and tests whether deliberation cost
(latency or token cost) follows a power-law shape over recurrence_index, as
predicted by Conway-Smith's metacognitive skill learning framework.

Phase 1 known limitation (documented): the backfill TOP_K=50 cap clamps
recurrence_index at 50, undersampling the high-recurrence tail. The fit uses
the unclamped portion (idx 1..49) as the primary measurement; the saturated
portion is reported separately. Phase 1.5 will re-run backfill with higher
TOP_K to remove this artifact.

Output: markdown report with per-bucket statistics and a power-law fit
y = a * x^b. Designed for Dawn Mist nightly digest integration.
"""

import math
import sys
from datetime import datetime
from pathlib import Path

import psycopg2

sys.path.insert(0, "/ganuda")
from lib.secrets_loader import get_db_config


def get_conn():
    return psycopg2.connect(**get_db_config())


def power_law_fit(xs, ys):
    """Fit y = a * x^b via log-log linear regression. Returns (a, b, r_squared).

    Returns (None, None, None) if there are too few points or any x/y is non-positive.
    """
    pairs = [(x, y) for x, y in zip(xs, ys) if x > 0 and y > 0]
    if len(pairs) < 3:
        return None, None, None
    log_x = [math.log(x) for x, _ in pairs]
    log_y = [math.log(y) for _, y in pairs]
    n = len(pairs)
    mx = sum(log_x) / n
    my = sum(log_y) / n
    num = sum((lx - mx) * (ly - my) for lx, ly in zip(log_x, log_y))
    den = sum((lx - mx) ** 2 for lx in log_x)
    if den == 0:
        return None, None, None
    b = num / den
    log_a = my - b * mx
    a = math.exp(log_a)
    # R^2
    ss_res = sum((ly - (log_a + b * lx)) ** 2 for lx, ly in zip(log_x, log_y))
    ss_tot = sum((ly - my) ** 2 for ly in log_y)
    r_sq = 1 - (ss_res / ss_tot) if ss_tot > 0 else None
    return a, b, r_sq


def fit_report() -> str:
    conn = get_conn()
    cur = conn.cursor()

    # Per-recurrence-index bucket: average and median deliberation_latency_ms
    # and total_token_cost across all votes with that index.
    cur.execute(
        """
        SELECT
          l.recurrence_index,
          count(DISTINCT l.vote_id_b) AS n_votes,
          count(*) FILTER (WHERE cv.deliberation_latency_ms IS NOT NULL) AS n_with_latency,
          count(*) FILTER (WHERE cv.total_token_cost IS NOT NULL) AS n_with_tokens,
          round(avg(cv.deliberation_latency_ms)::numeric, 1) AS avg_latency_ms,
          round(avg(cv.total_token_cost)::numeric, 1) AS avg_token_cost,
          round(avg(cv.confidence)::numeric, 4) AS avg_confidence,
          round(avg(cv.concern_count)::numeric, 2) AS avg_concerns
        FROM vote_recurrence_links l
        JOIN council_votes cv ON cv.vote_id = l.vote_id_b
        GROUP BY l.recurrence_index
        ORDER BY l.recurrence_index ASC
        """
    )
    rows = cur.fetchall()

    # Per-vote totals + cap-saturation summary
    cur.execute("SELECT count(*) FROM council_votes")
    total_votes = cur.fetchone()[0]
    cur.execute(
        "SELECT count(DISTINCT vote_id_b) FROM vote_recurrence_links"
    )
    recurring_votes = cur.fetchone()[0]
    cur.execute(
        "SELECT count(DISTINCT vote_id_b) FROM vote_recurrence_links WHERE recurrence_index = 50"
    )
    cap_saturated = cur.fetchone()[0]

    # Telemetry coverage
    cur.execute(
        "SELECT count(*) FILTER (WHERE deliberation_latency_ms IS NOT NULL), "
        "count(*) FILTER (WHERE total_token_cost IS NOT NULL) FROM council_votes"
    )
    n_with_latency, n_with_tokens = cur.fetchone()

    cur.close()
    conn.close()

    lines = []
    lines.append(f"# Council Power-Law Fit Report — {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append("")
    lines.append(f"**Source:** Conway-Smith Phase 1 instrumentation (Council vote `8762850ef4b652c7`, ticket #2165)")
    lines.append("")
    lines.append("## Coverage")
    lines.append("")
    lines.append(f"- Total council_votes: **{total_votes}**")
    lines.append(f"- Votes with ≥1 prior similar vote: **{recurring_votes}** ({100.0 * recurring_votes / total_votes:.1f}%)")
    lines.append(f"- Votes saturated at recurrence_index=50 (TOP_K cap): **{cap_saturated}** *(known Phase 1 measurement artifact, addressed in Phase 1.5)*")
    lines.append(f"- Votes with `deliberation_latency_ms` populated: **{n_with_latency}** *(Phase 1 instrumentation only fires on go-forward votes)*")
    lines.append(f"- Votes with `total_token_cost` populated: **{n_with_tokens}**")
    lines.append("")
    lines.append("## Per-recurrence-index distribution")
    lines.append("")
    lines.append("| recurrence_index | n_votes | n_with_latency | avg_latency_ms | n_with_tokens | avg_token_cost | avg_confidence | avg_concerns |")
    lines.append("|---:|---:|---:|---:|---:|---:|---:|---:|")
    for idx, n_votes, n_lat, n_tok, avg_lat, avg_tok, avg_conf, avg_con in rows:
        lines.append(
            f"| {idx} | {n_votes} | {n_lat} | {avg_lat or '—'} | {n_tok} | {avg_tok or '—'} | {avg_conf or '—'} | {avg_con or '—'} |"
        )
    lines.append("")

    # Power-law fits
    lines.append("## Power-law fits")
    lines.append("")
    lines.append("Form: `y = a * x^b` where `x = recurrence_index`, `y = average metric per bucket`.")
    lines.append("Conway-Smith framework predicts `b < 0` for cost metrics (cost decreases with recurrence as proceduralization takes hold) and `b > 0` for confidence/quality metrics.")
    lines.append("")
    lines.append("**Fit windows (Phase 1.5):**")
    lines.append("- `pre-saturation`: recurrence_index 1..199 (avoids the TOP_K=200 cap artifact)")
    lines.append("- `full`: recurrence_index 1..200 (includes saturated bucket; reported for completeness)")
    lines.append("")

    # Phase 1.5 (Apr 28 PM): TOP_K raised from 50 to 200 in the backfill, so the
    # cap-saturation boundary moved from 50 to 200. Window bounds updated.
    metrics = [
        ("avg_latency_ms (deliberation cost)", 4),
        ("avg_token_cost (deliberation cost)", 5),
        ("avg_confidence", 6),
        ("avg_concerns", 7),
    ]
    fit_lines = ["| metric | window | a | b | R² | n |", "|---|---|---:|---:|---:|---:|"]
    for label, col_idx in metrics:
        for window_label, max_idx in [("pre-saturation", 199), ("full", 200)]:
            xs = [r[0] for r in rows if r[0] <= max_idx and r[col_idx] is not None]
            ys = [float(r[col_idx]) for r in rows if r[0] <= max_idx and r[col_idx] is not None]
            a, b, r_sq = power_law_fit(xs, ys)
            if a is None:
                fit_lines.append(f"| {label} | {window_label} | — | — | — | {len(xs)} |")
            else:
                fit_lines.append(
                    f"| {label} | {window_label} | {a:.3f} | {b:+.4f} | {r_sq:.4f} | {len(xs)} |"
                )
    lines.extend(fit_lines)
    lines.append("")

    # Interpretation
    lines.append("## Interpretation")
    lines.append("")
    lines.append("Conway-Smith's metacognitive skill framework predicts deliberation cost on recurring topics should follow a power-law decay (b < 0 for cost metrics) as the system proceduralizes its responses. **Phase 1 instrumentation only began capturing `deliberation_latency_ms` and `total_token_cost` on go-forward votes** (post Apr 28 2026 instrumentation). Historical votes (pre-Apr 28) have NULL telemetry, so the cost-side fits will become meaningful only after sufficient go-forward data accumulates (target: 30 days minimum per the Phase 1 vote conditions).")
    lines.append("")
    lines.append("**Confidence and concerns** are populated for all historical votes and provide a usable signal even before the cost-side data accumulates. Watch for:")
    lines.append("- `avg_confidence` rising with recurrence_index → consistent with proceduralization (Council gets more sure on familiar topics)")
    lines.append("- `avg_concerns` falling with recurrence_index → consistent with proceduralization (fewer novel concerns surface on familiar topics)")
    lines.append("")
    lines.append("**Phase 1.5 known fixes:** raise TOP_K from 50 to ~200, raise similarity threshold from 0.70 to 0.85 to filter the heavy near-duplicate tail.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*Generated by `scripts/council_powerlaw_fit.py`. Conway-Smith Phase 1 instrumentation. Run nightly via Dawn Mist.*")

    return "\n".join(lines)


def main():
    report = fit_report()
    out_path = Path(f"/ganuda/docs/research/COUNCIL-POWERLAW-FIT-{datetime.utcnow().strftime('%Y-%m-%d')}.md")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report)
    print(f"Wrote {out_path} ({len(report)} bytes)")


if __name__ == "__main__":
    main()
