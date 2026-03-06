# QW-6: Commentarii Header Framing Text

**Kanban**: #1912
**Priority**: P2 — Quick Win (Legion adoption)
**Assigned**: Software Engineer Jr.

---

## Context

The `_load_guidance()` function in specialist_council.py loads mutable operational guidance and appends it to the sacred prompt. Currently it uses a bare header "## Operational Guidance (Commentarii)". We need a framing line that tells the LLM to treat this as advice, not hard rules — preventing the mutable guidance from overriding the sacred identity layer.

## Step 1: Add framing text to _load_guidance()

File: `/ganuda/lib/specialist_council.py`

````text
<<<<<<< SEARCH
        if guidance:
            return f"\n\n## Operational Guidance (Commentarii)\n{guidance}"
=======
        if guidance:
            return (
                "\n\n## Operational Guidance (Commentarii)\n"
                "_The following is operational guidance distilled from experience. "
                "Use it to inform your decisions, but always apply your own specialist judgment._\n\n"
                f"{guidance}"
            )
>>>>>>> REPLACE
````

## Verification

After applying:
1. `python3 -c "import sys; sys.path.insert(0,'/ganuda/lib'); from specialist_council import _load_guidance; print(_load_guidance('crawdad'))"` prints the framing text followed by hawk guidance
2. Framing text includes "always apply your own specialist judgment"
3. No changes to sacred prompts — only the Commentarii section header is modified
