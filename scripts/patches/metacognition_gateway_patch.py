#!/usr/bin/env python3
"""
Cherokee AI - Metacognition Gateway Integration Patch
Applies metacognition integration to /ganuda/services/llm_gateway/gateway.py

Usage: python3 metacognition_gateway_patch.py [--dry-run]

This patch:
1. Adds metacognition import after config_schema import
2. Modifies the council_vote function to use MetacognitiveCouncil
3. Adds metacognition data to the response

For Seven Generations.
"""

import sys
import re
import shutil
from datetime import datetime

GATEWAY_PATH = "/ganuda/services/llm_gateway/gateway.py"

# New import to add after 'from config_schema import load_config'
METACOGNITION_IMPORT = '''from config_schema import load_config
from metacognition import MetacognitiveCouncil
'''

# The new council_vote function with metacognition
NEW_COUNCIL_VOTE = '''@app.post("/v1/council/vote")
async def council_vote(request: CouncilVoteRequest, req: Request, api_key: APIKeyInfo = Depends(validate_api_key)):
    """Query all 7 specialists with metacognitive monitoring"""
    require_module("council")
    start = time.time()
    client_ip = req.client.host if req.client else None

    if api_key.quota_remaining < 100:
        raise HTTPException(status_code=429, detail="Insufficient quota for council vote")

    # Initialize metacognitive council
    meta_council = MetacognitiveCouncil(DB_CONFIG)
    meta_council.start_deliberation(request.question, getattr(request, 'context', None))

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
                confidence = 0.7 - (len(concerns) * 0.1)
                meta_council.record_specialist_response(name, result, confidence)

            except Exception as e:
                name = futures[future]
                responses[name] = f"[ERROR: {str(e)}]"

    # Consensus synthesis
    summaries = [f"- {name}: {resp[:150].replace(chr(10), ' ')}..." for name, resp in responses.items()]
    synthesis_prompt = f'Council asked: "{request.question}"\\n\\nResponses:\\n{chr(10).join(summaries)}\\n\\nSynthesize in 2-3 sentences.'
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


@app.get("/v1/council/pending")'''


def apply_patch(dry_run=False):
    """Apply the metacognition patch to gateway.py"""

    print(f"Reading {GATEWAY_PATH}...")
    with open(GATEWAY_PATH, 'r') as f:
        content = f.read()

    # Check if already patched
    if 'MetacognitiveCouncil' in content:
        print("ERROR: Metacognition already integrated. Aborting.")
        return False

    # 1. Add import
    print("Adding metacognition import...")
    content = content.replace(
        'from config_schema import load_config',
        METACOGNITION_IMPORT.strip()
    )

    # 2. Replace council_vote function
    print("Replacing council_vote function...")

    # Find the function start and end
    pattern = r'@app\.post\("/v1/council/vote"\)\nasync def council_vote\(.*?\n@app\.get\("/v1/council/pending"\)'

    match = re.search(pattern, content, re.DOTALL)
    if not match:
        print("ERROR: Could not find council_vote function pattern")
        return False

    content = content[:match.start()] + NEW_COUNCIL_VOTE + content[match.end():]

    if dry_run:
        print("\n=== DRY RUN - Changes would be: ===")
        print("1. Import MetacognitiveCouncil added")
        print("2. council_vote function replaced with metacognition version")
        print("\nNo changes written.")
        return True

    # Backup original
    backup_path = f"{GATEWAY_PATH}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"Creating backup: {backup_path}")
    shutil.copy(GATEWAY_PATH, backup_path)

    # Write patched file
    print(f"Writing patched {GATEWAY_PATH}...")
    with open(GATEWAY_PATH, 'w') as f:
        f.write(content)

    print("\nPatch applied successfully!")
    print("\nNext steps:")
    print("1. Restart gateway: sudo systemctl restart llm-gateway")
    print("2. Test: curl -X POST http://localhost:8080/v1/council/vote ...")
    print(f"3. If issues, restore backup: cp {backup_path} {GATEWAY_PATH}")

    return True


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("=== DRY RUN MODE ===\n")

    success = apply_patch(dry_run=dry_run)
    sys.exit(0 if success else 1)
