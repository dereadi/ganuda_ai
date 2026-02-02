# JR Instruction: Improve ii-researcher Answer Synthesis

**JR ID:** JR-IMPROVE-II-RESEARCHER-SYNTHESIS-JAN28-2026
**Priority:** P1 (Quality)
**Assigned To:** AI Research Jr.

---

## Problem

ii-researcher returns raw URL lists instead of synthesized, actionable answers.

**Example failure:**
- **Question:** "I tripped on a teapot while on duty and chipped my tail bone"
- **Expected:** VA rating info, diagnostic codes, evidence requirements
- **Actual:** Generic medical URLs about spinal fractures (YouTube, Wikipedia, WebMD)

Veterans need actionable guidance, not link dumps.

---

## Requirements

Research results MUST include:

1. **Direct answer** to the veteran's question
2. **Applicable diagnostic codes** (38 CFR Part 4)
3. **Rating criteria** with percentages
4. **Evidence needed** for service connection
5. **Source citations** from authoritative sources (VA.gov, 38 CFR, BVA decisions)

---

## Root Cause Identified

**Wrong model for the task.** ii-researcher is configured to use `qwen2.5-coder-32b-awq` (a coding model) via vLLM. Coding models are optimized for code completion, not research synthesis and reasoning.

**Config file:** `/ganuda/services/ii-researcher/.env`
```
R_MODEL=/ganuda/models/qwen2.5-coder-32b-awq
R_REPORT_MODEL=/ganuda/models/qwen2.5-coder-32b-awq
```

**Result:** Model returns raw links (0.5 confidence) instead of synthesized answers.

---

## Solutions (choose one)

### Option A: Switch to general-purpose model
Load Qwen2.5-72B-Instruct or Llama-3.1-70B on vLLM for research tasks.

### Option B: Post-process with Claude API
Add synthesis step after ii-researcher returns raw results:
1. ii-researcher gathers sources
2. Send sources + question to Claude API
3. Claude synthesizes actionable answer

### Option C: Dedicated VA Research RAG
Build a RAG system with:
- 38 CFR indexed
- M21-1 manual indexed
- BVA decisions indexed
- VA rating criteria database

This would be more reliable than web search for VA-specific questions.

---

## Acceptance Criteria

Research for "tailbone injury VA rating" should return something like:

```
## VA Rating for Coccyx (Tailbone) Injury

**Diagnostic Code:** DC 5236 - Sacroiliac injury and weakness

**Rating Criteria:**
- 40%: Unfavorable ankylosis of entire spine
- 20%: Forward flexion of thoracolumbar spine ≤30 degrees
- 10%: Forward flexion >60 degrees but ≤85 degrees
- 0%: Full range of motion with painful motion

**Service Connection Requirements:**
1. Current diagnosis of coccyx injury/coccydynia
2. In-service event, injury, or illness
3. Nexus linking current condition to service

**Recommended Evidence:**
- Service treatment records showing injury
- Current medical records documenting ongoing symptoms
- Nexus letter from physician
- Buddy statements if applicable

**Sources:**
- 38 CFR § 4.71a, DC 5236
- VA M21-1, Part III, Subpart iv, Chapter 4
```

---

FOR SEVEN GENERATIONS
