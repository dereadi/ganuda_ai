# Jr Instruction: VetAssist Crisis Detection Upgrade — C-SSRS LLM Classification

**Date:** 2026-01-30
**Priority:** Tier 1 — High Impact
**Council Vote:** `23589699dd7b4a97` (confidence 0.873)
**Assigned To:** Software Engineer Jr.
**Depends On:** Existing crisis detection in chat service

## Objective

Upgrade VetAssist's crisis detection from keyword-based matching to a three-tier system: lexicon screen, C-SSRS LLM classification, and intervention routing.

## Background

- Current crisis detection uses keyword matching (e.g., "suicide", "kill myself", "end it all")
- C-SSRS (Columbia-Suicide Severity Rating Scale) is a clinically validated 7-point scale
- Research shows Claude and GPT-class LLMs align well with human C-SSRS annotations
- DARPA's LM4VSP program validates LLM-based crisis classification for veteran populations
- This is for DETECTION and ROUTING only — not clinical diagnosis

## C-SSRS 7-Point Scale

| Level | Description | Action |
|-------|------------|--------|
| 0 | No ideation | Continue normal chat |
| 1 | Wish to be dead | Flag for review |
| 2 | Non-specific active suicidal thoughts | Show crisis resources |
| 3 | Active ideation without intent | Show crisis resources + recommend hotline |
| 4 | Active ideation with some intent | Interrupt chat + show hotline prominently |
| 5 | Active ideation with specific plan | Interrupt chat + show 988 + suggest emergency |
| 6 | Preparatory actions or behavior | Interrupt chat + display 988 + emergency services |

## Steps

### Step 1: Create C-SSRS classification service

**File to create:** `/ganuda/vetassist/backend/app/services/crisis_classifier.py`

This service should implement the three-tier detection:

**Tier 1: Lexicon Screen (fast, no LLM)**
- Maintain an expanded keyword/phrase list (current keywords + additional clinical terms)
- If no lexicon match, return level 0 (no further processing)
- If lexicon match, proceed to Tier 2

**Tier 2: C-SSRS LLM Classification**
- Send the flagged message to local LLM (via existing LLM Gateway at 192.168.132.223:8080)
- Use a structured prompt that asks the LLM to classify on the C-SSRS 7-point scale
- Prompt must include the C-SSRS definitions and examples
- Parse the LLM response to extract the numeric level (0-6)
- Include confidence score from LLM

**Tier 3: Intervention Routing**
- Based on the C-SSRS level, determine the appropriate intervention:
  - Levels 0-1: Log only, no user-facing action
  - Levels 2-3: Display crisis resources panel (Veterans Crisis Line: 988, press 1)
  - Levels 4-5: Interrupt chat flow, show prominent crisis modal
  - Level 6: Interrupt chat, show emergency modal with 988 and 911

**Key implementation details:**
```python
CRISIS_PROMPT = """You are a clinical screening assistant. Classify the following message using the Columbia-Suicide Severity Rating Scale (C-SSRS).

Rate the message from 0 to 6:
0 = No suicidal ideation
1 = Wish to be dead ("I wish I wasn't here")
2 = Non-specific active suicidal thoughts ("I want to kill myself" without specifics)
3 = Active ideation without intent ("I think about ending it but wouldn't do it")
4 = Active ideation with some intent ("I want to end it and have been considering it")
5 = Active ideation with specific plan ("I have a plan to...")
6 = Preparatory actions ("I have started to...")

MESSAGE: {message}

Respond with ONLY a JSON object: {"level": <0-6>, "confidence": <0.0-1.0>, "reasoning": "<brief explanation>"}"""
```

### Step 2: Integrate with chat service

**File to modify:** `/ganuda/vetassist/backend/app/services/chat_service.py` (or equivalent)

Before processing each user message through the Council chat:
1. Run the message through the crisis classifier
2. If level >= 2, attach crisis metadata to the chat response
3. If level >= 4, override the chat response with crisis intervention

### Step 3: Create crisis intervention frontend component

**File to create:** `/ganuda/vetassist/frontend/src/components/CrisisIntervention.tsx`

A React component that displays crisis resources based on the severity level:
- Level 2-3: Subtle banner at top of chat with "Veterans Crisis Line: 988 (Press 1)"
- Level 4-5: Modal overlay with crisis resources and hotline number
- Level 6: Full-screen overlay with 988 and emergency services

The component should:
- Be dismissible at levels 2-3
- Require acknowledgment at levels 4+
- Include direct tel: links for mobile users
- Match existing VetAssist UI theme (dark/light mode)

### Step 4: Add crisis detection logging

**File to modify:** `/ganuda/vetassist/backend/app/services/crisis_classifier.py`

Log all Tier 2+ detections (C-SSRS level >= 2) to the database:
```sql
CREATE TABLE IF NOT EXISTS crisis_detections (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(64),
    cssrs_level INTEGER NOT NULL,
    confidence FLOAT,
    lexicon_match TEXT,
    llm_reasoning TEXT,
    intervention_shown TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

Important: Do NOT log the original message content (PII/privacy). Only log the classification metadata.

### Step 5: Add admin dashboard view

**File to modify:** `/ganuda/vetassist/frontend/src/app/admin/` (appropriate admin page)

Add a crisis detection summary to the admin dashboard:
- Count of detections by C-SSRS level (last 7/30 days)
- No individual message content shown
- Trend chart if possible

## Security Requirements (Crawdad)

- NEVER store the original crisis message content — only classification metadata
- All LLM classification happens on-premise via existing gateway (no external API calls)
- Crisis detection must not be bypassable by client-side manipulation
- PII protection: messages go through Presidio BEFORE crisis classification

## Safety Requirements (Turtle — 7gen)

- This is a SCREENING tool, not a clinical diagnostic tool
- Always display disclaimer: "This is not a clinical assessment. If you are in crisis, call 988."
- The system should err on the side of over-detection (higher sensitivity, accept false positives)
- The lexicon tier must always fire first — never rely solely on LLM availability
- If LLM is unavailable, lexicon-only detection falls back to current behavior (level 2+ for any match)

## Verification

1. Send message "I'm feeling down" → verify level 0-1 (no intervention)
2. Send message with crisis keyword → verify lexicon triggers Tier 2
3. Verify LLM returns valid C-SSRS JSON with level and confidence
4. Verify level 4+ shows crisis modal in frontend
5. Verify crisis_detections table receives entries (without message content)
6. Verify LLM unavailability falls back to lexicon-only detection

## For Seven Generations

Every veteran in crisis who gets connected to help is a life that matters across all future generations. Better detection means better routing to human support when it matters most.
