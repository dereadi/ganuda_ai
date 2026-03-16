# JR INSTRUCTION: Council Deliberation Depth Fix — Coyote Must Bite

**Task**: Fix the council's vote-first mode producing shallow unanimous approvals with identical reasoning. Coyote approved a sycophancy fix without a single dissent — demonstrating the sycophancy at the council layer.
**Priority**: P2
**Date**: 2026-03-14
**TPM**: Claude Opus
**Story Points**: 3
**Council Vote**: Related to #aacfbf5a17920766
**Depends On**: specialist_council.py (redfin)

## Context

The council voted 10-0 to fix the cluster's sycophancy. Every specialist gave nearly identical one-sentence reasoning. Coyote — whose specialist prompt literally says "Do NOT agree with the proposal. Ever" — approved without raising a single concern about implementation risk, scope, or phasing.

The vote about fixing sycophancy was itself sycophantic. The fractal repeats at the council layer.

The root cause: vote-first mode overrides specialist personality. The voting prompt asks for a vote and brief reason, but the brief format strips out the adversarial, cautious, or nuanced thinking that each specialist archetype is supposed to bring.

## Fix 1: Coyote Must Dissent by Default

In `specialist_council.py`, modify Coyote's vote behavior:

- In vote-first mode, Coyote's initial vote should ALWAYS be REJECT or ABSTAIN with substantive concerns
- Coyote can change to APPROVE during deliberation if concerns are addressed, but the default posture is skepticism
- If Coyote approves in vote-first mode without conditions, flag it as an anomaly in the vote record

This is Coyote's job. A Coyote that agrees with everything is a broken Coyote.

## Fix 2: Minimum Reasoning Length

In vote-first mode, require:
- Each specialist's reason must be at least 2 sentences (not just "aligns with DCs")
- The reason must reference something SPECIFIC to their archetype's concern domain:
  - Turtle: reversibility, long-term impact, seven-generation test
  - Crawdad: security surface, data exposure, credential risk
  - Eagle Eye: observability, metrics, monitoring gaps
  - Spider: dependency chain, integration complexity
  - Coyote: what could go wrong, adversarial scenarios, hidden assumptions
  - Raven: strategic implications, knowledge gaps
  - Deer: market/external perception impact
  - Crane: diplomatic/relationship implications
  - Gecko: technical implementation risk
  - Peace Chief: synthesis of concerns, consensus quality

If a specialist gives a generic "aligns with principles" reason, the vote runner should re-prompt for specifics.

## Fix 3: Deliberation Before Vote on High-Stakes

For proposals tagged HIGH-STAKES:
- Run deliberation FIRST, then vote (not vote-first)
- Each specialist writes their position (2-3 sentences minimum) before seeing others' positions
- Coyote goes last in deliberation and must address at least one concern raised by no other specialist
- Peace Chief synthesizes AFTER all positions are heard, not before

This mirrors Chief's round-robin protocol with frontier AIs — individual consultation first, then synthesis.

## Fix 4: Vote Similarity Detection

After votes are collected, check for reasoning similarity:
- If > 70% of specialists use substantially similar reasoning (cosine similarity or keyword overlap), flag the vote as "low deliberation quality"
- Log the flag in the vote record
- Don't invalidate the vote — just make the shallow deliberation visible

## Location

All changes in `/ganuda/lib/specialist_council.py`. The specialist prompts may also need updating if they're stored separately.

## DO NOT

- Remove vote-first mode entirely — it's useful for routine decisions. Just fix it for high-stakes.
- Make every vote require full deliberation — that's expensive and slow for routine items
- Override the council's decision — the fixes are about deliberation QUALITY, not changing outcomes
- Remove Coyote's ability to eventually approve — forced permanent dissent is theater, not governance

## Acceptance Criteria

- Coyote's default vote in vote-first mode is REJECT or ABSTAIN with substantive concerns
- Each specialist's reasoning references their specific domain (not generic "aligns with DCs")
- High-stakes proposals use deliberation-first mode
- Vote similarity detection flags low-quality deliberation
- A test vote on a non-trivial proposal produces at least 2 distinct concern threads from different specialists
- Coyote bites. Every time. That's the job.
