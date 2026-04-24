# KB — Council persona-preserve fix (Apr 23 2026)

**Filed:** 2026-04-23 evening
**Commit:** b84de78
**Severity:** High (Council function degradation — empty/shallow specialist responses on high-stakes votes)
**Status:** PARTIAL FIX — bmasass/greenfin paths restored; redfin Qwen3.6 still shows empties under deliberation-first concurrent load (follow-on investigation required)

## Symptom

LMC-14 DELIBERATE vote (audit `1e43924dffdbbe93`, council_vote_first, high_stakes=True):
- 13/13 specialists returned empty reasoning
- Recommendation: CONTESTED, confidence 0.5
- Depth-check re-prompt cycle amplified the failure

Prior day (Apr 21): KB-BMASASS-SPECIALIST-SILENT-BUG documented a related issue where
`_query_specialist_with_prompt` was silencing bmasass specialists by ignoring their
backend's `extra_body` and hardcoding timeout=60. That fix landed, but a second
structural bug persisted in the same function.

## Root cause

`_query_specialist_with_prompt` has a `prompt_override` parameter. When set, line 2226:

```python
if prompt_override:
    system_prompt = INFRASTRUCTURE_CONTEXT + prompt_override + _load_guidance(specialist_id)
```

This **replaces** the specialist's persona system prompt (`spec["system_prompt"]`) entirely
with the override. The original design assumed callers would pass persona-embedded vote
instructions. In practice, FIVE call sites were passing **meta-instructions** (no persona
content):

1. `_reprompt_shallow_voters` — passed `REASONING_REPROMPT` (pure meta)
2. `_run_deliberation_first` non-Coyote loop — passed `deliberation_prompt` (meta)
3. `_run_deliberation_first` Coyote path — passed `coyote_deliberation_prompt` (meta)
4. `_run_deliberation_first` Peace Chief synthesis — passed `synthesis_prompt` (meta)
5. Main vote phase — passed `VOTE_FIRST_PROMPT` / `COYOTE_VOTE_FIRST_PROMPT` (meta)

On Qwen3.6 (high persona-attention sensitivity per
`project_qwen36_system_prompt_sensitivity_apr2026`), stripping persona produced empty
responses. On bmasass Qwen3-30B and Llama-3.3-70B, the models degraded gracefully but still
produced generic output lacking the specialist domain lens the Council depends on.

## Fix

All five sites now route meta-instructions as **suffix on `augmented_question`** (user
message), and call `_query_specialist_with_prompt` with `prompt_override=None` so the
specialist's persona system prompt stays intact.

Pattern:

```python
# Before (persona-stripping):
self._query_specialist_with_prompt(sid, question, meta_instruction)

# After (persona-preserving):
augmented = f"{question}\n\n---\n{meta_instruction}"
self._query_specialist_with_prompt(sid, augmented, None, 2000)
```

`max_tokens=2000` passed explicitly since we lost the `elif prompt_override: tokens=2000`
branch at line 2231.

This matches the Apr 17 pattern where thermal memory context was moved from
system-prompt-suffix to user-message-prefix for the same persona-attention reason.

## Verification

Retry on `_reprompt_shallow_voters` only (audit `3091da717e07eee7`): 4/13 specialists
recovered with substantive reasoning — gecko, spider, crane, blue_jay. 7 still empty.

Retry on all five sites (audit `3df91aa450c28a1b`): same 4 recovered (gecko +
bmasass/greenfin path). 7 redfin Qwen3.6 specialists still empty on initial deliberation pass.

Retry on plain `council_vote` (no high-stakes, no deliberation-first, no re-prompt, audit
`4a24fc3614cd738c`): 7 substantive concerns from 7 different specialists. Diversity 0.255
(healthy). Plain path works cleanly.

**Conclusion:** the fix resolves bmasass + greenfin failure modes. Redfin Qwen3.6 shows a
separate issue under the deliberation-first path — most likely concurrent-request
saturation (8 parallel requests to the same vLLM instance in the deliberation phase, then
another 8 in the vote phase, with `/no_think` mode and 9000+ char user messages). Not root
caused tonight.

## Follow-on investigation (deferred)

Open questions for a later session:

- Is redfin vLLM dropping concurrent requests silently when the worker pool saturates?
- Does `/no_think\n` system prefix interact with long user messages on Qwen3.6?
- Is the 2-round deliberation-first pattern (deliberate → vote) overloading a single
  model instance that needs serialized dispatch?
- Would routing redfin-pinned specialists to greenfin Qwen3-30B during high-stakes mode
  (load split) resolve the saturation?

File as kanban ticket for investigation during next council infra window.

## Impact

- **Restored:** high-stakes Council votes no longer blanket-empty
- **Restored:** deliberation-first mode has persona context
- **Restored:** re-prompt path preserves specialist domain framing
- **Partial:** Qwen3.6 specialists under deliberation-first concurrent load still
  need investigation
- **Workaround available:** plain `council_vote` (non-high-stakes) works cleanly for
  multi-call deliberations until the Qwen3.6-specific issue is root-caused

## Cross-references

- `project_qwen36_system_prompt_sensitivity_apr2026` — the Apr 17 fix pattern this extends
- `KB-BMASASS-SPECIALIST-SILENT-BUG-APR21-2026.md` — Apr 21 bug in same function
- `KB-LMC13-COUNCIL-SYSTEMS-CHECK-APR23-2026.md` — LMC-13 cluster-as-conductor ship
- LMC-14 epic #2029 SAG Harness — the cycle that surfaced this bug
- commit b84de78 — the 5-site fix

## Apr 23 2026

Filed evening of LMC-14 DELIBERATE. Partner framed bug-investigation as Council-member
routine work — TPM shipped 5-site fix + filed KB without asking per
`feedback_tpm_is_council_member_apr2026` directive.
