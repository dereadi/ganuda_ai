# Jr Instruction: Preserve Individual Specialist Responses in Council Votes

**Task**: #1898 — Council API: Preserve Individual Specialist Responses
**Assigned To**: Software Engineer Jr.
**Priority**: P2 (Chief Directive)
**Date**: 2026-02-26

## Context

When the council votes, each specialist's full response is collected in memory but stored in the `responses` JSONB column as a flat dict of `{name: text_string}`. This loses specialist metadata: concern types, response timing, confidence signals. The Chief's directive: "if someone brings up a concern, they should help come up with a solution." To enforce and audit this, we need the individual specialist voices preserved with their full metadata.

## Step 1: Enrich response collection with specialist metadata

File: `/ganuda/services/llm_gateway/gateway.py`

```
<<<<<<< SEARCH
                name, result, concerns, elapsed_ms = future.result()
                responses[name] = result
                all_concerns.extend(concerns)
                specialist_timings[name] = elapsed_ms
=======
                name, result, concerns, elapsed_ms = future.result()
                responses[name] = {
                    "response": result,
                    "concerns": concerns,
                    "has_concern": len(concerns) > 0,
                    "concern_types": [c.split(']')[0].lstrip('[') for c in concerns if '[' in c],
                    "response_time_ms": elapsed_ms,
                    "backend": routing_map.get(name, "unknown")
                }
                all_concerns.extend(concerns)
                specialist_timings[name] = elapsed_ms
>>>>>>> REPLACE
```

## Step 2: Update error case to match new structure

File: `/ganuda/services/llm_gateway/gateway.py`

```
<<<<<<< SEARCH
            except Exception as e:
                name = futures[future]
                responses[name] = f"[ERROR: {str(e)}]"
                specialist_timings[name] = 0
=======
            except Exception as e:
                name = futures[future]
                responses[name] = {
                    "response": f"[ERROR: {str(e)}]",
                    "concerns": [],
                    "has_concern": False,
                    "concern_types": [],
                    "response_time_ms": 0,
                    "backend": routing_map.get(name, "unknown"),
                    "error": str(e)
                }
                specialist_timings[name] = 0
>>>>>>> REPLACE
```

## Step 3: Fix consensus synthesis to read from new structure

The consensus builder at line 1284 reads `responses.items()` expecting `(name, text)`. Now it's `(name, dict)`, so we need to extract the response text.

File: `/ganuda/services/llm_gateway/gateway.py`

```
<<<<<<< SEARCH
    # Consensus synthesis
    response_items = list(responses.items())
    random.shuffle(response_items)
    summaries = [f"- {name}: {resp[:150].replace(chr(10), ' ')}..." for name, resp in response_items]
=======
    # Consensus synthesis
    response_items = list(responses.items())
    random.shuffle(response_items)
    summaries = [f"- {name}: {resp['response'][:150].replace(chr(10), ' ')}..." for name, resp in response_items]
>>>>>>> REPLACE
```

## Step 4: Fix metacognition record to use new structure

File: `/ganuda/services/llm_gateway/gateway.py`

```
<<<<<<< SEARCH
                # Record in metacognition tracer
                confidence = 0.7 - (len(concerns) * 0.1)
                meta_council.record_specialist_response(name, result, confidence)
=======
                # Record in metacognition tracer
                confidence = 0.7 - (len(concerns) * 0.1)
                meta_council.record_specialist_response(name, responses[name]["response"], confidence)
>>>>>>> REPLACE
```

## Verification

After applying these changes:

1. The `responses` JSONB column in `council_votes` will store:
```json
{
  "deer": {
    "response": "full specialist response text...",
    "concerns": ["[7GEN CONCERN] ..."],
    "has_concern": true,
    "concern_types": ["7GEN CONCERN"],
    "response_time_ms": 4523,
    "backend": "qwen"
  },
  "coyote": {
    "response": "full specialist response text...",
    "concerns": ["[DISSENT] ..."],
    "has_concern": true,
    "concern_types": ["DISSENT"],
    "response_time_ms": 5102,
    "backend": "qwen"
  }
}
```

2. Consensus synthesis still works (reads `resp['response']` instead of `resp` directly).
3. The DB INSERT at line 1351 (`json.dumps(responses)`) requires NO change — it serializes the enriched dict automatically.
4. After deploy: `rm -rf __pycache__/` and `sudo systemctl restart llm-gateway` on redfin.

## Notes

- This is backward-compatible: API consumers calling `/v1/council/vote/{hash}` will get the richer structure. Callers that only read `responses[name]` as a string will need updating, but the `/v1/council/vote` return endpoint already wraps this in `specialist_responses`.
- No schema changes needed — `responses` is already JSONB, accepts any valid JSON.
- The `concern_types` extraction uses the existing bracket pattern: `[7GEN CONCERN]`, `[DISSENT]`, `[STRATEGY CONCERN]`, etc.
