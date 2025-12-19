#!/usr/bin/env python3
with open("/ganuda/services/llm_gateway/gateway.py", "r") as f:
    content = f.read()

old_code = """    # Initialize metacognitive council
    meta_council = MetacognitiveCouncil(DB_CONFIG)
    meta_council.start_deliberation(request.question, getattr(request, 'context', None))

    responses = {}
    all_concerns = []

    def query_specialist(name: str) -> tuple:
        spec = SPECIALISTS[name]

        # Get specialist's memory context
        memory_context = get_specialist_context(name)
        enhanced_prompt = spec["system_prompt"] + memory_context"""

new_code = """    # Check for temporal query and get context from thermal memory
    is_temporal, timeframe = detect_temporal_query(request.question)
    temporal_context = ""
    if is_temporal and timeframe:
        temporal_context = get_temporal_context(timeframe)
        print(f"[TEMPORAL] Injecting {timeframe} context into deliberation")

    # Initialize metacognitive council
    meta_council = MetacognitiveCouncil(DB_CONFIG)
    meta_council.start_deliberation(request.question, getattr(request, 'context', None))

    responses = {}
    all_concerns = []

    def query_specialist(name: str) -> tuple:
        spec = SPECIALISTS[name]

        # Get specialist's memory context + temporal context
        memory_context = get_specialist_context(name)
        enhanced_prompt = spec["system_prompt"] + memory_context + temporal_context"""

if old_code in content:
    content = content.replace(old_code, new_code)
    with open("/ganuda/services/llm_gateway/gateway.py", "w") as f:
        f.write(content)
    print("SUCCESS: Added temporal context injection")
else:
    print("ERROR: Pattern not found - may already be patched")
    # Check if already patched
    if "detect_temporal_query(request.question)" in content:
        print("INFO: Temporal detection already present")
