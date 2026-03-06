# Commentarii: Mutable Council Guidance Layer

**Council Vote**: #d9ca4e7c8c7e43cb (Medicine Woman: "The teaching story changes with context, but the values are eternal")
**Long Man Phase**: ADAPT + BUILD
**Priority**: P2 — Architectural improvement
**Assigned**: Software Engineer Jr.

---

## Context

Our Council specialist prompts are sacred and hardcoded in specialist_council.py. Any behavioral tuning requires editing a sacred file. Shanz's Legion uses a 4-layer prompt: Identity / Values / Commentarii (mutable guidance) / Persona. We adopt the Commentarii layer — runtime-editable guidance files that append to specialist prompts without touching the sacred code.

Cherokee principle: the teaching story changes with context, but the values it carries are eternal.

## Step 1: Create the guidance directory with starter files

Create `/ganuda/config/council_guidance/`

Create `/ganuda/config/council_guidance/README.md`
```text
# Council Guidance (Commentarii)

Mutable operational guidance for each Council specialist.
These files are loaded at deliberation time and appended to
the specialist's sacred prompt.

- Sacred prompts (identity, voice, cognitive mode) live in specialist_council.py — NEVER EDIT
- Guidance files (operational wisdom, learned patterns) live here — SAFE TO EDIT

Inspired by Shanz's Legion Commentarii pattern.
Council Vote: #d9ca4e7c8c7e43cb
```

Create `/ganuda/config/council_guidance/hawk.md`
```text
# Hawk (Crawdad) — Security Guidance

- When reviewing credential changes, verify all consumers of the old credential have been migrated before approving.
- Password rotation without migration sweep is not complete. Reference: Feb 27 debt reckoning — 5 services broken for 3 weeks.
- Symlink-aware path validation is required. Check both literal and resolved paths.
```

Create `/ganuda/config/council_guidance/turtle.md`
```text
# Turtle — Seven Generations Guidance

- Every sprint must allocate 20% capacity to verification of previously shipped work.
- Adoption of external patterns requires verified foundations first. Do not build on unverified ground.
```

Create `/ganuda/config/council_guidance/coyote.md`
```text
# Coyote — Verification Guidance

- Ask "does it work, or does it just look like it works?" for every completed task review.
- Track what HAPPENED, not just what was DONE. Exit codes lie. File hashes don't.
- Invisible failures (marked complete, code unchanged) are worse than visible stubs.
```

Create `/ganuda/config/council_guidance/deer.md`
```text
# Deer (Peace Chief) — Consensus Guidance

- Trust is earned through verified outcomes, not task count.
- When synthesizing, name the autonomy level implied: OBSERVE, RECOMMEND, EXECUTE, or AUTONOMOUS.
```

Create `/ganuda/config/council_guidance/raven.md`
```text
# Raven — Strategic Guidance

- Cross-pollinate selectively from external systems. Maintain philosophical distinction.
- Separation of concerns is the meta-pattern. When things are merged that should be separate, flag it.
```

Create `/ganuda/config/council_guidance/medicine_woman.md`
```text
# Medicine Woman — Teaching Guidance

- The story we tell ourselves must be verified against reality. Aggregate truth can mask detail failure.
- Debt reckoning is a regular practice, not an emergency response.
- Commentarii are the tunable layer. Sacred prompts are eternal. Never confuse the two.
```

Create `/ganuda/config/council_guidance/owl.md`
```text
# Owl — Verification & Review Guidance

- Verify before adopting. Every new pattern must prove existing foundations are solid first.
- Sequence matters: security patches first, then architecture, then features.
- Type 1 verification (code change confirmation) must be automatic on every executor operation.
```

## Step 2: Load guidance in specialist_council.py deliberation

File: `/ganuda/lib/specialist_council.py`

Add guidance loading function after the SPECIALISTS dict definition. Find the closing of the last specialist entry and add the loader before the deliberation functions.

<<<<<<< SEARCH
def query_vllm_sync(system_prompt: str, user_message: str, max_tokens: int = 300) -> str:
=======
def _load_guidance(specialist_key: str) -> str:
    """Load mutable Commentarii guidance for a specialist.

    Guidance files live in /ganuda/config/council_guidance/<specialist>.md
    and are appended to the sacred prompt at deliberation time.
    Sacred prompts are eternal. Guidance is tunable.
    Council Vote: #d9ca4e7c8c7e43cb
    """
    # Map specialist keys to guidance file names
    guidance_map = {
        "crawdad": "hawk",
        "gecko": "gecko",
        "turtle": "turtle",
        "spider": "medicine_woman",
        "peace_chief": "deer",
        "raven": "raven",
        "eagle_eye": "owl",
    }
    filename = guidance_map.get(specialist_key, specialist_key)
    guidance_path = f"/ganuda/config/council_guidance/{filename}.md"
    try:
        with open(guidance_path, 'r') as f:
            guidance = f.read().strip()
        if guidance:
            return f"\n\n## Operational Guidance (Commentarii)\n{guidance}"
    except FileNotFoundError:
        pass
    return ""


def query_vllm_sync(system_prompt: str, user_message: str, max_tokens: int = 300) -> str:
>>>>>>> REPLACE

## Step 3: Wire guidance loading into the deliberation path

Find where specialist prompts are assembled for LLM calls. The pattern will be accessing `SPECIALISTS[key]["system_prompt"]` and passing it to the LLM. Append the guidance there.

Look for lines like:
```python
system_prompt = SPECIALISTS[specialist_key]["system_prompt"]
```
or
```python
specialist["system_prompt"]
```

And append guidance:
```python
system_prompt = specialist["system_prompt"] + _load_guidance(specialist_key)
```

If the exact SEARCH string cannot be found, add guidance loading at whatever point the system_prompt is assembled before being sent to the LLM. The guidance must be appended AFTER the sacred prompt, not replace it.

## Verification

After applying:
1. Each specialist's sacred prompt remains untouched in the code
2. Guidance files load at deliberation time and append operational wisdom
3. Missing guidance files are silently skipped (no crash)
4. Editing a guidance file takes effect on the NEXT deliberation — no restart needed
5. `ls /ganuda/config/council_guidance/` shows 7 specialist files + README
