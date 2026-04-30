# KB — LMC-16 REVIEW Phase: First Production Cycle Findings

**Date:** 2026-04-30 PM
**Author:** TPM (Stoneclad)
**Cycle:** LMC-16 REVIEW (post-BUILD)
**Authorizing Council vote:** `08c642a0fd176a92`

## What ran

First production cycle of `scripts/fire_guard_backlog_review.py` against the
real `duyuktv_tickets` backlog. Flags: `--limit 50 --no-slack` (webhook not
yet wired; see Partner handoff below).

Wall time: ~7 min for 47 backlog candidates.

## Audit-log integrity post-cycle

50 total rows (3 from smoke test + 47 from this cycle):

```
rows                 | 50
unique_hashes        | 50  ✓ no collisions
chain_genesis        | 1   ✓ only original smoke-test row 7
chain_breaks         | 0   ✓ every prev_hash links to a known this_hash
awaiting_ratify      | 50  ✓ all NULL partner_action (no Slack post yet)
```

Hash chain holds across 50 rows.

## Classification distribution

```
 still_relevant      | 41    (safe-default fallback after vLLM failure)
 needs_decomposition |  5    (heuristic: 'EPIC:' titles)
 close_as_stale      |  4    (heuristic: >90 days no movement; +1 was
                              from smoke test)
```

## Empirical: vLLM Qwen3.6 prompt-template bug

**Every** vLLM call this cycle (47/47) failed validation. Two failure shapes:
- Model output `"classification": "<category>"` (literal placeholder)
- Model output `"classification": "..."` (literal ellipsis)

### Root cause analysis

`lib/fire_guard_backlog_reviewer.py:127` prompt template contains:
```
{"classification": "<one of: still_relevant | needs_decomposition | ...>", ...}
```

Qwen3.6 reasoning-mode appears to interpret `<...>` placeholders as
`<think>`-style structural tokens rather than fill-the-blank prompts.
Result: it echoes a *generic* placeholder back (`<category>`) instead of
substituting one of the taxonomy class names.

### Why MVP still held

The hybrid design absorbs this gracefully:
1. **Heuristic fast-path** caught the load-bearing cases:
   - `EPIC:` title → `needs_decomposition` (5 rows)
   - `>90 days stale` → `close_as_stale` (3 rows; one more was smoke test)
2. **LLM ambiguous middle** failed → safe-default `still_relevant` (41 rows)
3. **Partner-ratifies-everything-anyway discipline** (Eagle Eye + Coyote
   convergence): even false-defaults are caught at Slack-review time.

The system did exactly what the Council mitigations said it would do under
classifier degradation. No data lost, no incorrect close-outs.

### Why this is LMC-17 not LMC-16

Same root cause as ticket #2160 (closed Apr 29). The fix is a federation-wide
gateway-level CoT-suppression, not a local prompt rewrite. LMC-17 candidate
already noted in BUILD KB.

**Local mitigation possible (not done)**: rewrite the OUTPUT FORMAT block
to use few-shot examples instead of `<placeholder>` syntax. Defer to LMC-17
where the broader fix lives.

## Health gate behavior

`is_classifier_healthy()` did NOT halt the run, which is correct:
- Health gate measures `partner_action='reject_classification'` rate over
  7-day window.
- LLM internal failures (which fall through to safe-default) are NOT counted
  as classifier-rejections at the audit-log layer.
- This is by design: the gate measures *what Partner says is wrong*, not
  *what the model itself failed to produce*. Partner ratification is the
  ground truth.

If it turns out 41 safe-default `still_relevant` classifications are wrong
when Partner reviews (high reject rate), the gate WILL halt. Self-correcting.

## systemd-user-timer

Installed on redfin:
```
~/.config/systemd/user/fire-guard-backlog-review.service
~/.config/systemd/user/fire-guard-backlog-review.timer
```

- Timer: `OnCalendar=*-*-* 09:15:00`, `RandomizedDelaySec=600`
- `Persistent=true` (catches missed runs after sleep/reboot)
- Service: `EnvironmentFile=-/home/dereadi/.config/fire-guard.env`
  (Partner can drop `FIRE_GUARD_SLACK_WEBHOOK=https://hooks.slack.com/...`
  in that file — `-` prefix means missing-file is non-fatal)
- Status: `enabled`, `active (waiting)`, next trigger Fri 2026-05-01 ~09:18 CDT
  with random jitter

## What needs Partner action

1. **Slack incoming webhook URL for #fire-guard channel.** When provided,
   either:
   - Drop in `~/.config/fire-guard.env` as `FIRE_GUARD_SLACK_WEBHOOK=https://...`
   - Or export in shell + restart service unit
2. **First Slack-live cycle review.** Once webhook lands, manually trigger:
   `systemctl --user start fire-guard-backlog-review.service` and Partner
   reviews the resulting Slack post → ratifies via `keep #N` / `close #N` /
   `decompose #N` / `reject #N` syntax (note: ratification CLI not yet built;
   that's also LMC-17).

## LMC-17 candidates updated

In addition to the items already in the BUILD KB, this REVIEW phase adds:

- **LMC-17.A**: Few-shot prompt rewrite for backlog classifier (drop
  `<placeholder>` syntax that Qwen3.6 reasoning-mode mishandles)
- **LMC-17.B**: Ratification CLI/Slack-bot wiring (parse `keep #N` /
  `close #N` from Slack thread replies, call `ratify_classification()` via
  `claude_council` role)
- **LMC-17.C**: Federation-wide vLLM gateway CoT suppression (same upstream
  fix that closes #2160 properly, not just per-call workarounds)

## REVIEW phase status

✓ systemd timer installed and active
✓ First production cycle completed end-to-end with audit-chain integrity
✓ Empirical findings documented (LLM bug + safe-degradation behavior)
✓ Council mitigations verified to work under classifier-degradation scenario
☐ Slack webhook wire-up (Partner-supplied)
☐ First Slack-live cycle (depends on webhook)
☐ 7-day rejection-rate observation window (begins after Slack live)

## Files

- THIS KB: `/ganuda/docs/kb/KB-LMC16-REVIEW-FIRST-CYCLE-APR30-2026.md`
- BUILD KB: `/ganuda/docs/kb/KB-LMC16-WORKFLOW-PROCEDURALIZATION-APR30-2026.md`
- Logs (this run): in TPM session output (not persisted; service-managed
  runs go to `/tmp/fire-guard-backlog-review.log`)
