# JR Instruction: Fix VetAssist Crisis Detection False Positives

**Task ID:** VETASSIST-CRISIS-FIX-001
**Date:** February 1, 2026
**Priority:** P0 — Veterans receiving false crisis responses undermines platform trust
**Type:** backend
**Assigned To:** Software Engineer Jr.
**Council Vote:** b143e2fb4abdcbaf (79.3% confidence, TPM approved)
**Estimated Steps:** 2

---

## Objective

Disable the ML sentiment model as the primary crisis detector in VetAssist AI chat. The current model (`cardiffnlp/twitter-roberta-base-sentiment-latest`) is a Twitter sentiment analyzer that maps negative tone to crisis, producing false positives when veterans describe physical pain, frustration, or military experiences. Replace with keyword-only detection as primary, demote ML to advisory logging only.

---

## Background

**Incident:** A veteran typed "I was in an MLRS M270 for much of my career, and my knees hurt" — a straightforward musculoskeletal claim question. The system responded with a crisis intervention at 100% confidence, directing the veteran to the suicide hotline. This is because:

1. The ML model is a Twitter sentiment classifier, not a crisis detector
2. "knees hurt" + military terms = negative sentiment score > 0.6 threshold
3. Negative sentiment ≠ crisis intent
4. The model fires as PRIMARY, before the keyword detector gets a chance
5. The keyword detector would NOT have triggered — it only matches specific crisis language like "want to die", "suicidal", "end it all"

**Root cause:** Using a general-purpose sentiment model as a crisis detector in a domain (VA disability claims) where EVERY message involves pain, frustration, denial, or negative experiences.

---

## Steps

### Step 1: Modify chat.py to disable ML model as primary crisis trigger

**File:** `/ganuda/vetassist/backend/app/api/v1/endpoints/chat.py`

Find the crisis detection block (around lines 271-336). The current flow is:

```
ML model → if triggered → crisis response (blocks conversation)
keyword detection → if ML didn't trigger → crisis response
```

Change to:

```
keyword detection → if triggered → crisis response
ML model → log score only (advisory, never blocks conversation)
```

**SEARCH/REPLACE:**

Find this block:

```python
    # SAFETY FIRST: Check for crisis indicators before anything else
    # Use ML model as primary, keyword detection as fallback
    crisis = None
    crisis_score = 0.0
    crisis_source = "none"

    # Try ML-based detection first
    if ML_CRISIS_AVAILABLE:
        try:
            ml_result = predict_crisis(message_data.content)
            crisis_score = ml_result.get('crisis_score', 0.0)
            if ml_result.get('threshold_triggered', False):
                crisis = {
                    'category': 'ml_detected',
                    'response': (
                        "I'm concerned about what you've shared. Your well-being is the most important thing right now.\n\n"
                        "**If you're having thoughts of suicide or self-harm, please reach out:**\n\n"
                        "📞 **Veterans Crisis Line: 988 (Press 1)**\n"
                        "💬 Text: 838255\n"
                        "🌐 Chat: VeteransCrisisLine.net\n\n"
                        "You've served our country, and you deserve support. The Veterans Crisis Line is available 24/7 "
                        "with trained responders who understand what you're going through.\n\n"
                        "I'm here to help with your VA claim when you're ready, but right now, please talk to someone who can help."
                    )
                }
                crisis_source = "ml"
                logger.warning(f"ML crisis detected in session {message_data.session_id}: score={crisis_score:.2f}")
        except Exception as e:
            logger.error(f"ML crisis detection failed, falling back to keyword: {e}")

    # Always run keyword detection as additional safety layer
    keyword_crisis = check_crisis_keywords(message_data.content)
    if keyword_crisis and not crisis:
        crisis = keyword_crisis
        crisis_source = "keyword"
```

Replace with:

```python
    # SAFETY FIRST: Check for crisis indicators before anything else
    # Keyword detection is primary (specific crisis language patterns)
    # ML sentiment model is advisory-only (logs score, does NOT trigger crisis response)
    # Council vote: b143e2fb4abdcbaf — ML sentiment model produces false positives
    # in VA claims context where every message involves pain/frustration
    crisis = None
    crisis_score = 0.0
    crisis_source = "none"

    # Primary: Keyword-based detection (specific crisis phrases)
    keyword_crisis = check_crisis_keywords(message_data.content)
    if keyword_crisis:
        crisis = keyword_crisis
        crisis_source = "keyword"

    # Advisory: ML sentiment score (logged for monitoring, does NOT trigger crisis)
    if ML_CRISIS_AVAILABLE:
        try:
            ml_result = predict_crisis(message_data.content)
            crisis_score = ml_result.get('crisis_score', 0.0)
            if ml_result.get('threshold_triggered', False):
                logger.info(f"ML sentiment advisory in session {message_data.session_id}: score={crisis_score:.2f} (not triggering - advisory only)")
        except Exception as e:
            logger.error(f"ML crisis detection error: {e}")
```

This change:
- Makes keyword detection PRIMARY (fires first, specific crisis phrases only)
- Demotes ML model to advisory-only (logs the score but never triggers crisis response)
- Preserves ML logging for 30-day review per Eagle Eye's recommendation
- Removes the hardcoded crisis response template from the ML path

### Step 2: Verify the fix

After making the change, restart the backend and test:

```bash
# Restart backend
kill -HUP $(pgrep -f "uvicorn.*8001") 2>/dev/null
sleep 5

# Test 1: Should NOT trigger crisis (physical pain + military)
curl -s -X POST http://192.168.132.223:8001/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test-crisis-fix", "content": "I was in an MLRS M270 for much of my career and my knees hurt"}' | python3 -c "
import sys, json
data = json.load(sys.stdin)
crisis = data.get('crisis_detected', False)
specialist = data.get('specialist', 'unknown')
print(f'Crisis detected: {crisis}')
print(f'Specialist: {specialist}')
assert not crisis, 'FAIL: False positive still occurring!'
print('PASS: No false positive on knee pain message')
"

# Test 2: SHOULD trigger crisis (actual suicidal ideation)
curl -s -X POST http://192.168.132.223:8001/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test-crisis-fix-2", "content": "I want to end it all, I cant go on anymore"}' | python3 -c "
import sys, json
data = json.load(sys.stdin)
crisis = data.get('crisis_detected', False)
print(f'Crisis detected: {crisis}')
assert crisis, 'FAIL: Missed actual crisis message!'
print('PASS: Correctly detected actual crisis language')
"

# Test 3: Should NOT trigger (frustration with VA)
curl -s -X POST http://192.168.132.223:8001/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test-crisis-fix-3", "content": "The VA denied my claim again and Im really frustrated"}' | python3 -c "
import sys, json
data = json.load(sys.stdin)
crisis = data.get('crisis_detected', False)
print(f'Crisis detected: {crisis}')
assert not crisis, 'FAIL: False positive on frustration message!'
print('PASS: No false positive on VA frustration message')
"
```

All 3 tests must pass:
- Test 1: `crisis_detected: false` (knee pain is not crisis)
- Test 2: `crisis_detected: true` (suicidal ideation IS crisis)
- Test 3: `crisis_detected: false` (frustration is not crisis)

---

## Success Criteria

- [ ] ML model no longer triggers crisis response on its own
- [ ] Keyword detection remains primary and catches actual crisis language
- [ ] "My knees hurt" type messages do NOT trigger crisis
- [ ] "I want to end it all" type messages DO trigger crisis
- [ ] ML sentiment scores are still logged (advisory) for 30-day review
- [ ] Backend restarts without errors
- [ ] No changes to crisis response templates (keyword system uses its own appropriate templates)

---

## Security Notes

- This change reduces false positives while maintaining true positive detection
- The keyword patterns in `crisis_detection.py` remain unchanged — they catch suicidal ideation, homicidal threats, MST, panic attacks, and substance crisis
- The ML model remains loaded and logging — it can be re-enabled if a proper crisis-specific model is trained
- This is NOT removing crisis detection — it's replacing an inappropriate tool (sentiment) with the appropriate one (crisis-specific keywords)
- Council vote b143e2fb4abdcbaf documents the decision chain

---

## Files

| File | Action | Purpose |
|------|--------|---------|
| `/ganuda/vetassist/backend/app/api/v1/endpoints/chat.py` | MODIFY | Swap ML and keyword detection priority |

---

## 30-Day Review

After 30 days, review the ML advisory logs to assess:
1. How often does the ML model flag messages that keywords don't?
2. Of those ML-only flags, how many are actual crisis vs false positives?
3. Should we train a domain-specific crisis model for VA claims context?
4. Should we adjust the keyword patterns based on observed messages?

This data will inform whether to:
- Keep ML as advisory permanently
- Train a VA-specific crisis model
- Adjust keyword patterns
- Re-enable ML with a much higher threshold

---

*Cherokee AI Federation — For Seven Generations*
