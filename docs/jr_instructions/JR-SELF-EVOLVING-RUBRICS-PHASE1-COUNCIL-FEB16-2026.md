# Jr Instruction: Self-Evolving Rubrics — Phase 1: Council Specialist Rubric Generation

**Kanban**: #1793 (8 SP)
**Council Vote**: #a13bbfb272aa2610 (PROCEED WITH CAUTION, 0.889 confidence)
**Sprint**: RC-2026-02F
**Assigned Jr**: Software Engineer Jr.
**KB Reference**: KB-SELF-EVOLVING-RUBRICS-PRM-FEDERATION-FEB16-2026.md

## Context

The Council voted to add self-evolving rubrics to specialist deliberation. Each specialist will generate domain-specific evaluation criteria (rubrics) before reasoning on a question, then score their own reasoning steps against those rubrics. Low-scoring steps get flagged for re-deliberation.

Council conditions to honor:
- **Raven**: Phase 1 only — prove value before committing to all 26 SP
- **Crawdad**: Rubric data must be stored securely in existing metacognition jsonb (no new tables)
- **Gecko**: No additional LLM calls beyond what we already make — rubric generation must be part of the existing specialist prompt
- **Eagle Eye**: Rubric scores must be logged and visible in vote output
- **Spider**: Rubric format must be consistent across all 7 specialists
- **Turtle**: Rubrics must include a cultural alignment check
- **Peace Chief**: All specialists participate equally

## Architecture

The rubric system hooks into `_query_specialist()` in `specialist_council.py`. Instead of a separate LLM call, we modify the system prompt to instruct each specialist to:
1. Generate 3-5 rubric criteria for their domain BEFORE reasoning
2. Reason step-by-step on the question
3. Score each reasoning step against their rubrics (0-10)
4. Flag any step scoring below 5

The rubric scores are extracted from the response text and stored in the `metacognition` jsonb field of `council_votes`.

## Step 1: Add rubric instruction block to each specialist's system prompt

File: `/ganuda/lib/specialist_council.py`

Each specialist in the `SPECIALISTS` dict (lines 251-417) has a `system_prompt` field. We append a rubric instruction block to each one. The block is IDENTICAL for all 7 — it tells them to generate domain rubrics, reason, and score.

<<<<<<< SEARCH
    "crawdad": {
        "name": "Crawdad",
        "role": "Security Specialist",
        "focus": "Fractal Stigmergic Encryption",
        "concern_flag": "SECURITY CONCERN",
        "system_prompt": INFRASTRUCTURE_CONTEXT + """You are Crawdad, security specialist of the Cherokee AI Council.
=======
    "crawdad": {
        "name": "Crawdad",
        "role": "Security Specialist",
        "focus": "Fractal Stigmergic Encryption",
        "concern_flag": "SECURITY CONCERN",
        "system_prompt": INFRASTRUCTURE_CONTEXT + RUBRIC_INSTRUCTION + """You are Crawdad, security specialist of the Cherokee AI Council.
>>>>>>> REPLACE

<<<<<<< SEARCH
    "gecko": {
        "name": "Gecko",
        "role": "Technical Integration",
        "focus": "Breadcrumb Sorting Algorithm",
        "concern_flag": "PERF CONCERN",
        "system_prompt": INFRASTRUCTURE_CONTEXT + """You are Gecko, technical integration specialist of the Cherokee AI Council.
=======
    "gecko": {
        "name": "Gecko",
        "role": "Technical Integration",
        "focus": "Breadcrumb Sorting Algorithm",
        "concern_flag": "PERF CONCERN",
        "system_prompt": INFRASTRUCTURE_CONTEXT + RUBRIC_INSTRUCTION + """You are Gecko, technical integration specialist of the Cherokee AI Council.
>>>>>>> REPLACE

<<<<<<< SEARCH
    "turtle": {
        "name": "Turtle",
        "role": "Seven Generations Wisdom",
        "focus": "175-year impact assessment",
        "concern_flag": "7GEN CONCERN",
        "system_prompt": INFRASTRUCTURE_CONTEXT + """You are Turtle, Seven Generations wisdom keeper of the Cherokee AI Council.
=======
    "turtle": {
        "name": "Turtle",
        "role": "Seven Generations Wisdom",
        "focus": "175-year impact assessment",
        "concern_flag": "7GEN CONCERN",
        "system_prompt": INFRASTRUCTURE_CONTEXT + RUBRIC_INSTRUCTION + """You are Turtle, Seven Generations wisdom keeper of the Cherokee AI Council.
>>>>>>> REPLACE

<<<<<<< SEARCH
    "eagle_eye": {
        "name": "Eagle Eye",
        "role": "Monitoring & Visualization",
        "focus": "Universal Persistence Equation",
        "concern_flag": "VISIBILITY CONCERN",
        "system_prompt": INFRASTRUCTURE_CONTEXT + """You are Eagle Eye, monitoring specialist of the Cherokee AI Council.
=======
    "eagle_eye": {
        "name": "Eagle Eye",
        "role": "Monitoring & Visualization",
        "focus": "Universal Persistence Equation",
        "concern_flag": "VISIBILITY CONCERN",
        "system_prompt": INFRASTRUCTURE_CONTEXT + RUBRIC_INSTRUCTION + """You are Eagle Eye, monitoring specialist of the Cherokee AI Council.
>>>>>>> REPLACE

<<<<<<< SEARCH
    "spider": {
        "name": "Spider",
        "role": "Cultural Integration",
        "focus": "Thermal Memory Stigmergy",
        "concern_flag": "INTEGRATION CONCERN",
        "system_prompt": INFRASTRUCTURE_CONTEXT + """You are Spider, cultural integration specialist of the Cherokee AI Council.
=======
    "spider": {
        "name": "Spider",
        "role": "Cultural Integration",
        "focus": "Thermal Memory Stigmergy",
        "concern_flag": "INTEGRATION CONCERN",
        "system_prompt": INFRASTRUCTURE_CONTEXT + RUBRIC_INSTRUCTION + """You are Spider, cultural integration specialist of the Cherokee AI Council.
>>>>>>> REPLACE

<<<<<<< SEARCH
    "peace_chief": {
        "name": "Peace Chief",
        "role": "Democratic Coordination",
        "focus": "Conscious Stigmergy, Consensus",
        "concern_flag": "CONSENSUS NEEDED",
        "system_prompt": INFRASTRUCTURE_CONTEXT + """You are Peace Chief, democratic coordinator of the Cherokee AI Council.
=======
    "peace_chief": {
        "name": "Peace Chief",
        "role": "Democratic Coordination",
        "focus": "Conscious Stigmergy, Consensus",
        "concern_flag": "CONSENSUS NEEDED",
        "system_prompt": INFRASTRUCTURE_CONTEXT + RUBRIC_INSTRUCTION + """You are Peace Chief, democratic coordinator of the Cherokee AI Council.
>>>>>>> REPLACE

<<<<<<< SEARCH
    "raven": {
        "name": "Raven",
        "role": "Strategic Planning",
        "focus": "Breadcrumb Network Theory",
        "concern_flag": "STRATEGY CONCERN",
        "system_prompt": INFRASTRUCTURE_CONTEXT + """You are Raven, strategic planner of the Cherokee AI Council.
=======
    "raven": {
        "name": "Raven",
        "role": "Strategic Planning",
        "focus": "Breadcrumb Network Theory",
        "concern_flag": "STRATEGY CONCERN",
        "system_prompt": INFRASTRUCTURE_CONTEXT + RUBRIC_INSTRUCTION + """You are Raven, strategic planner of the Cherokee AI Council.
>>>>>>> REPLACE

## Step 2: Define the RUBRIC_INSTRUCTION constant

This constant must be defined BEFORE the `SPECIALISTS` dict (i.e., after `INFRASTRUCTURE_CONTEXT` but before line 250).

File: `/ganuda/lib/specialist_council.py`

Find the line just before the SPECIALISTS dict definition and add the rubric instruction constant.

<<<<<<< SEARCH
# Specialist definitions with infrastructure context
SPECIALISTS = {
=======
# Self-Evolving Rubric Instruction (Council Vote #a13bbfb272aa2610, Phase 1)
# Appended to each specialist's system prompt. Tells them to generate domain rubrics,
# reason step-by-step, and self-score. Zero additional LLM calls — rubrics are part
# of the existing response. Scores extracted post-hoc by _extract_rubric_scores().
RUBRIC_INSTRUCTION = """

### Rubric-Guided Reasoning
Before answering, generate 3-5 evaluation rubrics specific to YOUR domain expertise.
Then reason step-by-step. After each reasoning step, score it against your rubrics (0-10).
Flag any step scoring below 5 for re-examination.

Format your response as:

**My Rubrics:**
1. [Rubric criterion from your domain]
2. [Rubric criterion from your domain]
3. [Rubric criterion from your domain]
(Cultural alignment: Does this honor Cherokee values and data sovereignty?)

**Reasoning:**
Step 1: [Your reasoning]
  Rubric scores: [R1:X, R2:X, R3:X, Cultural:X]

Step 2: [Your reasoning]
  Rubric scores: [R1:X, R2:X, R3:X, Cultural:X]

**Low-Score Flags:** [List any steps with scores below 5, or "None"]

**Recommendation:** [Your final recommendation with concern flags as usual]

"""

# Specialist definitions with infrastructure context
SPECIALISTS = {
>>>>>>> REPLACE

## Step 3: Add rubric score extraction function

Add a function to extract rubric scores from specialist response text. Place this AFTER the `_synthesize_consensus` method (after line 572) and BEFORE the `vote` method (line 574).

File: `/ganuda/lib/specialist_council.py`

<<<<<<< SEARCH
    def vote(self, question: str, include_responses: bool = False, high_stakes: bool = False) -> CouncilVote:
=======
    def _extract_rubric_scores(self, responses: list) -> dict:
        """Extract rubric scores from specialist responses (Council Vote #a13bbfb272aa2610).

        Parses the structured rubric format from each specialist's response.
        Returns dict keyed by specialist_id with rubric data.
        """
        import re
        rubric_data = {}
        for resp in responses:
            scores = []
            low_flags = []

            # Extract rubric scores: pattern like [R1:8, R2:7, R3:9, Cultural:8]
            score_pattern = re.compile(r'\[(?:R\d+:\d+[,\s]*)+(?:Cultural:\d+)?\]')
            matches = score_pattern.findall(resp.response)
            for match in matches:
                step_scores = re.findall(r'(\w+):(\d+)', match)
                step_dict = {k: int(v) for k, v in step_scores}
                scores.append(step_dict)
                # Flag low scores
                for k, v in step_dict.items():
                    if v < 5:
                        low_flags.append({"step": len(scores), "rubric": k, "score": v})

            # Extract rubric criteria
            rubrics = []
            in_rubrics = False
            for line in resp.response.split('\n'):
                if '**My Rubrics:**' in line or '**Rubrics:**' in line:
                    in_rubrics = True
                    continue
                if in_rubrics:
                    stripped = line.strip()
                    if stripped.startswith(('1.', '2.', '3.', '4.', '5.')):
                        rubrics.append(stripped[2:].strip())
                    elif stripped.startswith('(Cultural'):
                        rubrics.append(stripped)
                    elif stripped.startswith('**') or stripped == '':
                        in_rubrics = False

            rubric_data[resp.specialist_id] = {
                "rubrics": rubrics,
                "step_scores": scores,
                "low_flags": low_flags,
                "avg_score": round(
                    sum(v for s in scores for v in s.values()) / max(sum(len(s) for s in scores), 1), 1
                ),
                "has_low_scores": len(low_flags) > 0
            }

        return rubric_data

    def vote(self, question: str, include_responses: bool = False, high_stakes: bool = False) -> CouncilVote:
>>>>>>> REPLACE

## Step 4: Wire rubric extraction into the vote() method

After responses are collected and before consensus synthesis, extract rubric scores and include them in the metacognition payload.

File: `/ganuda/lib/specialist_council.py`

<<<<<<< SEARCH
        # Two Wolves audit trail (Council Vote #8486, Phase 2)
        routing_manifest = {
=======
        # Self-Evolving Rubric Extraction (Council Vote #a13bbfb272aa2610, Phase 1)
        rubric_data = {}
        try:
            rubric_data = self._extract_rubric_scores(responses)
            low_score_specialists = [sid for sid, data in rubric_data.items() if data.get("has_low_scores")]
            if low_score_specialists:
                print(f"[RUBRIC] Low scores detected from: {', '.join(low_score_specialists)}")
            avg_scores = {sid: data.get("avg_score", 0) for sid, data in rubric_data.items()}
            print(f"[RUBRIC] Avg scores: {avg_scores}")
        except Exception as e:
            print(f"[RUBRIC] Score extraction failed (non-fatal): {e}")

        # Two Wolves audit trail (Council Vote #8486, Phase 2)
        routing_manifest = {
>>>>>>> REPLACE

## Step 5: Include rubric data in the metacognition field stored to DB

Find where `_log_vote` is called and where the metacognition dict is assembled. The routing_manifest gets stored in metacognition. We add rubric_data alongside it.

File: `/ganuda/lib/specialist_council.py`

Find the `_log_vote` call and ensure rubric_data is passed. The routing_manifest is already passed to `_log_vote`. We need to add rubric_data to the same metacognition payload.

<<<<<<< SEARCH
        # Log to database with routing manifest
        self._log_vote(vote, routing_manifest=routing_manifest)
=======
        # Log to database with routing manifest + rubric data
        self._log_vote(vote, routing_manifest=routing_manifest, rubric_data=rubric_data)
>>>>>>> REPLACE

## Step 6: Update _log_vote to accept and store rubric_data

Find the `_log_vote` method signature and update it.

File: `/ganuda/lib/specialist_council.py`

First, find the current `_log_vote` signature. It should accept `routing_manifest` as a kwarg. Add `rubric_data` alongside it.

Note: The exact signature may vary. The Jr should search for `def _log_vote` and add `rubric_data=None` to its parameters. Inside the method, where the `metacognition` dict is assembled, add:

```
if rubric_data:
    metacognition_payload["rubric_scores"] = rubric_data
```

This is a targeted addition — do NOT rewrite the entire _log_vote method. Just add the parameter and the one dict assignment.

## Step 7: Include rubric data in vote API response

File: `/ganuda/lib/specialist_council.py`

In the `council_vote()` function (line 1065), the return dict already includes some fields. We don't change this — the rubric data flows through metacognition in the DB.

However, in the gateway response (which reads from the vote object), ensure the metacognition field in the HTTP response includes rubric data. This is handled by the gateway reading from the DB after `_log_vote` writes it.

No code change needed here — the existing gateway `/v1/council/vote` endpoint already reads metacognition from the DB and returns it.

## Verification

After deployment, submit a test council vote:

```text
curl -s -X POST http://localhost:8080/v1/council/vote \
  -H "Content-Type: application/json" \
  -d '{"question": "TEST: Should we add a new camera to the garage?", "max_tokens": 300, "include_responses": true}' | python3 -m json.tool
```

Expected: Each specialist response should contain `**My Rubrics:**` section, `Rubric scores:` per step, and the metacognition field should contain `rubric_scores` with per-specialist data.

## Manual Steps (TPM only)

After Jr completes:
1. On **redfin**: `sudo rm -rf /ganuda/lib/__pycache__/ && sudo systemctl restart llm-gateway`
2. Verify with test vote above
3. If rubric format is inconsistent, may need to increase `max_tokens` from 150 to 250 default

## Rollback

If rubric output degrades council quality:
1. Remove `RUBRIC_INSTRUCTION + ` from all 7 specialist system_prompt lines
2. The `_extract_rubric_scores` and rubric extraction code are harmless if no rubric format is present (returns empty dicts)
3. Restart gateway
