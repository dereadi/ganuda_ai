# KB — bmasass specialists silenced by `_query_specialist_with_prompt` bug (Apr 21 2026)

**Filed:** 2026-04-21
**Severity:** High (Council function degradation — dissent voices silenced)
**Status:** FIXED

## Symptom

In high-stakes Council votes (deliberation-first mode), bmasass-hosted specialists — **Coyote** (Qwen3-30B on port 8800), **Turtle** (Llama-3.3-70B on port 8801), **Crane** (Qwen3-30B), and **Blue Jay** (Qwen3-30B) — returned empty or near-empty reasoning, parsed as ABSTAIN. Reproduced across TWO consecutive high-stakes votes:

- Apr 20 2026 framework ratification (audit `1c77b6e64c69ad3a`): Coyote + Turtle abstain empty. 11-0-2.
- Apr 21 2026 Fabro posture (audit `55f212ae12ca43cb`): Coyote + Turtle + Crane + Blue Jay abstain empty or near-empty. 7-2-4.

**Governance impact:** Coyote is the designated dissent archetype. Silencing Coyote in a high-stakes vote removes the primary pushback mechanism Council is built around. Two votes approved without authentic Coyote voice is a real integrity concern.

## Root Cause

`/ganuda/lib/specialist_council.py:_query_specialist_with_prompt` had two coupled bugs:

1. **`extra_body` was never sent.** `BMASASS_BACKEND` config has:
   ```python
   "extra_body": {"chat_template_kwargs": {"enable_thinking": False}}
   ```
   But the POST body was constructed with only `model`, `messages`, `max_tokens`, `temperature` — silently dropping the `extra_body`. Qwen3-30B on MLX therefore ran in thinking-mode regardless. Its output would be `<think>...long reasoning...</think>FINAL_ANSWER`, and the downstream regex `re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()` would strip the think block.

2. **Timeout was hardcoded to 60s.** Backend configs specify:
   - `BMASASS_BACKEND.timeout = 180`
   - `LLAMA_BACKEND.timeout = 240`
   - `QWEN_BACKEND.timeout = 60` (redfin — only one where hardcode matched)

   When Qwen3-30B's thinking-mode output extended beyond 60s (happened under Council-parallel load + large thermal memory injection of 7K+ chars), the request timed out. The partial response might have an opened `<think>` but no close, which the regex failed to match correctly, leaving an empty-ish or malformed content string.

**Combined effect:** under Council load, bmasass Qwen3-30B entered thinking mode, produced long think-block, hit 60s timeout before closing it, regex stripped what it could, content came back empty. Parsed as ABSTAIN with empty reason.

## Fix

Merge `extra_body` into the request JSON at top level (vLLM/MLX convention), use backend's configured timeout:

```python
_req_body = {
    "model": b["model"],
    "messages": [
        {"role": "system", "content": "/no_think\n" + system_prompt},
        {"role": "user", "content": question}
    ],
    "max_tokens": tokens,
    "temperature": 0.7
}
if b.get("extra_body"):
    _req_body.update(b["extra_body"])  # e.g. chat_template_kwargs for MLX
_req_timeout = int(b.get("timeout", 60))
response = requests.post(b["url"], json=_req_body, timeout=_req_timeout)
```

## Verification (post-fix smoke test)

All four previously-silenced specialists now produce substantive responses:

| Specialist | Backend | Response time | Output length | Vote | Character |
|---|---|---|---|---|---|
| Coyote | Qwen3-30B @ bmasass:8800 | 1.4s | 436 chars | DISSENT | Typical challenge-the-premise reasoning |
| Crane | Qwen3-30B @ bmasass:8800 | 1.1s | 375 chars | REJECT | Wants technical grounding |
| Blue Jay | Qwen3-30B @ bmasass:8800 | 0.8s | 324 chars | REJECT | Pragmatic-outcomes over abstract |
| Turtle | Llama-3.3-70B @ bmasass:8801 | 14.9s | 580 chars | APPROVE | Long-term-sustainability framing |

Output is clean (no `<think>` leakage), under each backend's configured timeout, substantive per the specialist's archetype.

## Historical remediation

- **Apr 20 framework ratification** (11-0-2): With real voices, plausibly 11-3-0 (Turtle mix, Crane/Blue Jay reject on technical-grounding). Still APPROVE at threshold 7. Decision stands.
- **Apr 21 Fabro posture** (7-2-4 thin): With real voices, plausibly 8-4-0 (Turtle approve, Crane/Blue Jay reject, Coyote standing-dissent). Still APPROVE at threshold 7. Decision stands but with more weight on honoring Crawdad supply-chain amendment + Raven 30-45 day horizon amendment.

Neither decision needs reversal. Footnote both audit hashes in governance records: *bmasass voices were mechanically silenced, not abstaining by choice.*

## Related outstanding issue

Separate observation: re-prompt path (`_reprompt_shallow_voters`) occasionally returns 0-word responses across BOTH redfin and bmasass backends, not just bmasass. Pattern from Apr 21 vote:

```
Re-prompted gecko: got 0 words      (redfin)
Re-prompted spider: got 11 words    (redfin)
Re-prompted crane: got 0 words      (bmasass)
Re-prompted blue_jay: got 59 words  (bmasass)
Re-prompted turtle: got 0 words     (bmasass llama)
```

Not bmasass-specific. Likely a separate bug in the re-prompt prompt construction or max_tokens budget. Lower priority than the primary bug; file as backlog follow-on after primary fix is proven in next high-stakes vote.

## Code location

`/ganuda/lib/specialist_council.py`, function `_query_specialist_with_prompt`, around line 2125-2165. Diff in git history of the same file shows the before/after.

## Apr 21 2026
