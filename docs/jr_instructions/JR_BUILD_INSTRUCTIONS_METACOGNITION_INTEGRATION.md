# Jr Build Instructions: Metacognition Gateway Integration

## Priority: HIGH - Differentiating Feature

---

## Overview

Integrate the Metacognition Module into the LLM Gateway's `/v1/council/vote` endpoint. This adds self-awareness to Cherokee AI's decision-making process.

**Module Location**: `/ganuda/lib/metacognition/`
**Gateway Location**: `/ganuda/services/llm_gateway/gateway.py`
**Patch Script**: `/ganuda/scripts/patches/metacognition_gateway_patch.py`

---

## Quick Deploy (Recommended)

### 1. Database column already added:
```sql
-- Already done by TPM on 2025-12-15
ALTER TABLE council_votes ADD COLUMN IF NOT EXISTS metacognition JSONB;
```

### 2. Apply the patch:
```bash
cd /ganuda/scripts/patches

# Dry run first (see what changes)
python3 metacognition_gateway_patch.py --dry-run

# Apply the patch
python3 metacognition_gateway_patch.py
```

### 3. Restart gateway:
```bash
sudo systemctl restart llm-gateway
```

### 4. Test:
```bash
curl -X POST http://localhost:8080/v1/council/vote \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{"question": "Should we deploy this feature?"}'
```

Verify response includes `metacognition` section with `biases_detected`, `uncertainty_areas`, `coyote_observation`, etc.

---

## Current State

The Metacognition Module is deployed with these components:

| Component | File | Purpose |
|-----------|------|---------|
| ReasoningTracer | `reasoning_tracer.py` | Captures Council's inner monologue |
| BiasDetector | `bias_detector.py` | Identifies 8 cognitive biases |
| UncertaintyCalibrator | `uncertainty_calibrator.py` | Knows what it doesn't know |
| Coyote | `coyote.py` | Metacognitive Trickster (8th Specialist) |
| ResonanceDetector | `resonance.py` | Harmonic pattern detection |
| MetacognitiveCouncil | `council_integration.py` | Wrapper for Council with metacognition |

---

## Integration Points

### 1. Import Metacognition Module

At top of `gateway.py`, add:

```python
# Add after other imports
import sys
sys.path.append('/ganuda/lib')
from metacognition import (
    MetacognitiveCouncil,
    add_metacognition_to_council_response
)
```

### 2. Modify `/v1/council/vote` Endpoint

**Current flow:**
1. Query 7 specialists in parallel
2. Synthesize consensus
3. Calculate confidence
4. Return response

**New flow with metacognition:**
1. Initialize MetacognitiveCouncil
2. Query 7 specialists in parallel
3. Record each response in metacognition tracer
4. Run Coyote observation
5. Detect biases
6. Calibrate uncertainty
7. Analyze resonance
8. Synthesize consensus
9. Add metacognition to response
10. Return enhanced response

### 3. Code Changes

Replace the `council_vote` function with:

```python
@app.post("/v1/council/vote")
async def council_vote(request: CouncilVoteRequest, req: Request, api_key: APIKeyInfo = Depends(validate_api_key)):
    """Query all 7 specialists with metacognitive monitoring"""
    require_module("council")
    start = time.time()
    client_ip = req.client.host if req.client else None

    if api_key.quota_remaining < 100:
        raise HTTPException(status_code=429, detail="Insufficient quota for council vote")

    # Initialize metacognitive council
    meta_council = MetacognitiveCouncil()
    meta_council.start_deliberation(request.question, request.context if hasattr(request, 'context') else None)

    responses = {}
    all_concerns = []

    def query_specialist(name: str) -> tuple:
        spec = SPECIALISTS[name]
        result = query_vllm_sync(spec["system_prompt"], request.question, request.max_tokens)
        concerns = extract_concerns(result, spec["name"])
        return name, result, concerns

    with ThreadPoolExecutor(max_workers=7) as executor:
        futures = {executor.submit(query_specialist, name): name for name in SPECIALISTS.keys()}
        for future in as_completed(futures):
            try:
                name, result, concerns = future.result()
                responses[name] = result
                all_concerns.extend(concerns)

                # Record in metacognition tracer
                confidence = 0.7 - (len(concerns) * 0.1)  # Base confidence adjusted by concerns
                meta_council.record_specialist_response(name, result, confidence)

            except Exception as e:
                name = futures[future]
                responses[name] = f"[ERROR: {str(e)}]"

    # Consensus synthesis
    summaries = [f"- {name}: {resp[:150].replace(chr(10), ' ')}..." for name, resp in responses.items()]
    synthesis_prompt = f'Council asked: "{request.question}"\n\nResponses:\n{chr(10).join(summaries)}\n\nSynthesize in 2-3 sentences.'
    consensus = query_vllm_sync(SPECIALISTS["peace_chief"]["system_prompt"], synthesis_prompt, 200)

    # Complete metacognitive analysis
    meta_result = meta_council.complete_deliberation(consensus)

    # Use calibrated confidence from metacognition
    confidence = meta_result.get('calibrated_confidence', max(0.0, min(1.0, 1.0 - (len(all_concerns) * 0.15))))

    # Adjust recommendation based on metacognition
    bias_count = len(meta_result.get('biases', []))
    if bias_count >= 2:
        recommendation = f"REVIEW REQUIRED: {len(all_concerns)} concerns, {bias_count} biases detected"
    elif len(all_concerns) == 0:
        recommendation = "PROCEED"
    elif len(all_concerns) <= 2:
        recommendation = f"PROCEED WITH CAUTION: {len(all_concerns)} concern(s)"
    else:
        recommendation = f"REVIEW REQUIRED: {len(all_concerns)} concerns"

    audit_hash = hashlib.sha256(f"{time.time()}|{request.question}".encode()).hexdigest()[:16]
    vote_expires = datetime.utcnow() + timedelta(seconds=TPM_VOTE_TIMEOUT_SECONDS)

    # Save vote with metacognition data
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO council_votes
                (audit_hash, question, recommendation, confidence, concern_count, responses, concerns, consensus, tpm_vote, vote_window_expires, metacognition)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'pending', %s, %s)
            """, (audit_hash, request.question[:500], recommendation, confidence, len(all_concerns),
                  json.dumps(responses), json.dumps(all_concerns), consensus, vote_expires,
                  json.dumps(meta_result)))
            conn.commit()
    except Exception as e:
        print(f"[VOTE SAVE ERROR] {e}")

    # Notify TPM
    create_tpm_notification(audit_hash, request.question, recommendation, confidence, all_concerns, vote_expires)

    response_time_ms = int((time.time() - start) * 1000)
    update_quota(api_key.key_id, len(SPECIALISTS) * 100 + 200)
    log_audit(api_key.key_id[:16], "/v1/council/vote", "POST", 200, response_time_ms, 0, client_ip)

    result = {
        "audit_hash": audit_hash,
        "question": request.question,
        "recommendation": recommendation,
        "confidence": confidence,
        "confidence_level": meta_result.get('confidence_level', 'medium'),
        "concerns": all_concerns,
        "consensus": consensus,
        "response_time_ms": response_time_ms,
        "tpm_vote": "pending",
        "vote_window_expires": vote_expires.isoformat() + "Z",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        # Metacognition section
        "metacognition": {
            "biases_detected": meta_result.get('biases', []),
            "uncertainty_areas": meta_result.get('knowledge_gaps', []),
            "coyote_observation": meta_result.get('coyote', {}).get('observation', ''),
            "resonance": meta_result.get('resonance', {}).get('level', ''),
            "self_assessment": meta_result.get('coyote', {}).get('wisdom', ''),
            "reasoning_steps": meta_result.get('reasoning_steps', 0)
        }
    }
    if request.include_responses:
        result["specialist_responses"] = responses
    return result
```

---

## Database Schema Update

Add `metacognition` column to `council_votes` table:

```sql
ALTER TABLE council_votes
ADD COLUMN IF NOT EXISTS metacognition JSONB;
```

---

## New API Response Format

The `/v1/council/vote` response will now include:

```json
{
  "audit_hash": "abc123",
  "question": "Should we deploy to production?",
  "recommendation": "PROCEED WITH CAUTION: 1 concern(s)",
  "confidence": 0.78,
  "confidence_level": "medium",
  "concerns": ["SECURITY CONCERN: Authentication review needed"],
  "consensus": "The council recommends...",
  "metacognition": {
    "biases_detected": [
      {
        "type": "groupthink",
        "severity": "low",
        "evidence": "5 of 7 specialists gave similar recommendations"
      }
    ],
    "uncertainty_areas": [
      {
        "topic": "load testing",
        "reason": "No recent production load data available"
      }
    ],
    "coyote_observation": "The Council may be overconfident - consider what happens if the deployment fails.",
    "resonance": "Harmonious - specialists align on core concerns",
    "self_assessment": "Moderate certainty with gaps in performance data",
    "reasoning_steps": 7
  }
}
```

---

## Testing

### Test 1: Basic Integration

```bash
curl -X POST http://localhost:8080/v1/council/vote \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_KEY" \
  -d '{"question": "Should we deploy this feature to production?"}'
```

Verify response includes `metacognition` section.

### Test 2: Bias Detection

```bash
curl -X POST http://localhost:8080/v1/council/vote \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_KEY" \
  -d '{"question": "As predicted, the tests passed. Should we proceed with the confirmed approach?"}'
```

Should detect confirmation bias due to "as predicted" and "confirmed" language.

### Test 3: Uncertainty Calibration

```bash
curl -X POST http://localhost:8080/v1/council/vote \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_KEY" \
  -d '{"question": "What is the optimal database schema for a Cherokee language learning app?"}'
```

Should show uncertainty since this is a novel domain.

---

## Rollback Plan

If issues arise:
1. Comment out metacognition imports
2. Revert to original `council_vote` function
3. Restart gateway: `sudo systemctl restart llm-gateway`

---

## Success Criteria

- [ ] `/v1/council/vote` returns `metacognition` section
- [ ] Bias detection flags at least 3 bias types
- [ ] Confidence levels are calibrated (high/medium/low)
- [ ] Coyote observations appear in responses
- [ ] No performance degradation >20%
- [ ] Database stores metacognition JSON

---

## Files to Modify

1. `/ganuda/services/llm_gateway/gateway.py` - Add metacognition integration
2. Database - Add `metacognition` column to `council_votes`

---

*For Seven Generations*
